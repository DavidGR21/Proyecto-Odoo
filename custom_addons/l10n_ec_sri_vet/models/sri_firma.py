# -*- coding: utf-8 -*-
"""
Firma Electrónica XAdES-BES para el SRI de Ecuador.

Implementación nativa usando cryptography + lxml, sin depender de signxml.
El SRI exige estrictamente el formato XAdES-BES con:
  - QualifyingProperties / SignedProperties
  - SigningCertificate con digest del certificado
  - DataObjectFormat apuntando al comprobante
  - Firma RSA-SHA1 (requerido por el validador Java del SRI)

NOTA IMPORTANTE SOBRE CANONICALIZACIÓN:
  El SignedInfo debe ser canonicalizado EN CONTEXTO del documento final
  (después de ser insertado en el árbol XML), ya que la canonicalización
  inclusiva (C14N 1.0) incluye namespaces heredados de los ancestros.
  Firmar el SignedInfo como elemento standalone produce una firma que
  el SRI rechaza con "firma y/o certificados alterados".
"""
import base64
import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta

from lxml import etree
from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.primitives.serialization.pkcs12 import (
        load_key_and_certificates,
    )
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    _logger.warning(
        'Librería cryptography no disponible. '
        'Instalar con: pip install cryptography')

# ── Constantes de Namespaces ──────────────────────────────────────────────────
DS_NS = 'http://www.w3.org/2000/09/xmldsig#'
ETSI_NS = 'http://uri.etsi.org/01903/v1.3.2#'
C14N_ALG = 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
ENVELOPED_SIG = 'http://www.w3.org/2000/09/xmldsig#enveloped-signature'
SHA1_ALG = 'http://www.w3.org/2000/09/xmldsig#sha1'
RSA_SHA1_ALG = 'http://www.w3.org/2000/09/xmldsig#rsa-sha1'


def _ds(tag):
    return f'{{{DS_NS}}}{tag}'


def _etsi(tag):
    return f'{{{ETSI_NS}}}{tag}'


def _sha1_digest_b64(data):
    """Calcula SHA-1 digest y retorna en base64."""
    return base64.b64encode(hashlib.sha1(data).digest()).decode('ascii')


def _c14n(node):
    """Canonicalización C14N 1.0 inclusiva (en contexto del árbol)."""
    return etree.tostring(node, method='c14n', exclusive=False,
                          with_comments=False)


def _uid():
    return str(uuid.uuid4()).replace('-', '')


class SriFirmaElectronica(models.AbstractModel):
    _name = 'sri.firma.electronica'
    _description = 'Firma Electrónica XAdES-BES para el SRI'

    def firmar_xml(self, xml_bytes, p12_bytes, password):
        """
        Firma un XML con XAdES-BES para el SRI de Ecuador.

        El flujo de firma sigue estrictamente este orden:
        1. Comprobante digest (antes de insertar la firma)
        2. Ensamblado completo de la Signature con placeholders
        3. Inserción en el documento
        4. Cálculo de digests en contexto (SignedProperties, KeyInfo)
        5. Relleno de valores en SignedInfo
        6. Canonicalización de SignedInfo EN CONTEXTO → firma RSA
        7. Seteo del SignatureValue

        :param xml_bytes: bytes del XML a firmar
        :param p12_bytes: bytes del archivo .p12
        :param password: str contraseña del .p12
        :return: bytes del XML firmado
        """
        if not HAS_CRYPTO:
            raise UserError(
                'La librería cryptography no está instalada.\n'
                'Ejecute: pip install cryptography')

        try:
            # ══════════════════════════════════════════════════════════════
            # PASO 1: Extraer clave y certificados del PKCS#12
            # ══════════════════════════════════════════════════════════════
            private_key, certificate, additional_certs = \
                load_key_and_certificates(
                    p12_bytes,
                    password.encode('utf-8') if isinstance(password, str)
                    else password,
                    default_backend()
                )

            if not private_key or not certificate:
                raise UserError(
                    'No se pudo extraer la clave privada o el certificado '
                    'del archivo .p12. Verifique que el archivo y la '
                    'contraseña sean correctos.')

            # ══════════════════════════════════════════════════════════════
            # PASO 2: Extraer datos del certificado
            # ══════════════════════════════════════════════════════════════
            cert_der = certificate.public_bytes(serialization.Encoding.DER)
            cert_b64 = base64.b64encode(cert_der).decode('ascii')
            cert_sha1 = _sha1_digest_b64(cert_der)

            issuer_name = certificate.issuer.rfc4514_string()
            serial_number = str(certificate.serial_number)

            pub_key = certificate.public_key()
            pub_numbers = pub_key.public_numbers()
            modulus_bytes = pub_numbers.n.to_bytes(
                (pub_numbers.n.bit_length() + 7) // 8, byteorder='big')
            modulus_b64 = base64.b64encode(modulus_bytes).decode('ascii')
            exponent_bytes = pub_numbers.e.to_bytes(
                (pub_numbers.e.bit_length() + 7) // 8, byteorder='big')
            exponent_b64 = base64.b64encode(exponent_bytes).decode('ascii')

            # ══════════════════════════════════════════════════════════════
            # PASO 3: Parsear XML y calcular digest del comprobante
            #         ANTES de insertar la Signature (enveloped transform)
            # ══════════════════════════════════════════════════════════════
            root = etree.fromstring(xml_bytes)
            root.set('id', 'comprobante')

            comprobante_c14n = _c14n(root)
            comprobante_digest = _sha1_digest_b64(comprobante_c14n)

            # ══════════════════════════════════════════════════════════════
            # PASO 4: Generar IDs únicos
            # ══════════════════════════════════════════════════════════════
            sig_id = f'Signature{_uid()}'
            sig_value_id = f'SignatureValue{_uid()}'
            signed_info_id = f'Signature-SignedInfo{_uid()}'
            signed_props_id = f'Signature-SignedProperties{_uid()}'
            cert_id = f'Certificate{_uid()}'
            ref_id = f'Reference-ID-{_uid()}'
            signed_props_ref_id = f'SignedPropertiesID{_uid()}'
            object_id = f'Signature-Object{_uid()}'

            # ══════════════════════════════════════════════════════════════
            # PASO 5: Construir la estructura completa de la Signature
            #         con placeholders para digest/signature values
            # ══════════════════════════════════════════════════════════════

            # -- Signature (raíz de la firma) --
            signature_elem = etree.SubElement(
                root, _ds('Signature'),
                Id=sig_id,
                nsmap={'ds': DS_NS, 'etsi': ETSI_NS})

            # -- SignedInfo --
            signed_info = etree.SubElement(
                signature_elem, _ds('SignedInfo'),
                Id=signed_info_id)

            etree.SubElement(
                signed_info, _ds('CanonicalizationMethod'),
                Algorithm=C14N_ALG)

            etree.SubElement(
                signed_info, _ds('SignatureMethod'),
                Algorithm=RSA_SHA1_ALG)

            # Reference 1: SignedProperties
            ref_sp = etree.SubElement(
                signed_info, _ds('Reference'),
                Id=signed_props_ref_id,
                Type='http://uri.etsi.org/01903#SignedProperties',
                URI=f'#{signed_props_id}')
            etree.SubElement(ref_sp, _ds('DigestMethod'), Algorithm=SHA1_ALG)
            dv_sp = etree.SubElement(ref_sp, _ds('DigestValue'))
            dv_sp.text = ''  # placeholder

            # Reference 2: KeyInfo
            ref_ki = etree.SubElement(
                signed_info, _ds('Reference'),
                URI=f'#{cert_id}')
            etree.SubElement(ref_ki, _ds('DigestMethod'), Algorithm=SHA1_ALG)
            dv_ki = etree.SubElement(ref_ki, _ds('DigestValue'))
            dv_ki.text = ''  # placeholder

            # Reference 3: Comprobante (enveloped)
            ref_doc = etree.SubElement(
                signed_info, _ds('Reference'),
                Id=ref_id,
                URI='#comprobante')
            transforms = etree.SubElement(ref_doc, _ds('Transforms'))
            etree.SubElement(
                transforms, _ds('Transform'),
                Algorithm=ENVELOPED_SIG)
            etree.SubElement(ref_doc, _ds('DigestMethod'), Algorithm=SHA1_ALG)
            dv_doc = etree.SubElement(ref_doc, _ds('DigestValue'))
            dv_doc.text = comprobante_digest  # ya lo calculamos

            # -- SignatureValue (placeholder) --
            sig_value_elem = etree.SubElement(
                signature_elem, _ds('SignatureValue'),
                Id=sig_value_id)
            sig_value_elem.text = ''

            # -- KeyInfo --
            key_info = etree.SubElement(
                signature_elem, _ds('KeyInfo'),
                Id=cert_id)

            x509_data = etree.SubElement(key_info, _ds('X509Data'))
            x509_cert = etree.SubElement(x509_data, _ds('X509Certificate'))
            x509_cert.text = cert_b64

            key_value = etree.SubElement(key_info, _ds('KeyValue'))
            rsa_key_value = etree.SubElement(key_value, _ds('RSAKeyValue'))
            modulus_elem = etree.SubElement(rsa_key_value, _ds('Modulus'))
            modulus_elem.text = modulus_b64
            exponent_elem = etree.SubElement(rsa_key_value, _ds('Exponent'))
            exponent_elem.text = exponent_b64

            # -- Object → QualifyingProperties → SignedProperties --
            object_elem = etree.SubElement(
                signature_elem, _ds('Object'),
                Id=object_id)

            qualifying_props = etree.SubElement(
                object_elem, _etsi('QualifyingProperties'),
                Target=f'#{sig_id}')

            signed_props = etree.SubElement(
                qualifying_props, _etsi('SignedProperties'),
                Id=signed_props_id)

            signed_sig_props = etree.SubElement(
                signed_props, _etsi('SignedSignatureProperties'))

            signing_time = etree.SubElement(
                signed_sig_props, _etsi('SigningTime'))
            # Usar timezone-aware para obtener hora Ecuador real
            ec_tz = timezone(timedelta(hours=-5))
            now_ec = datetime.now(ec_tz)
            signing_time.text = now_ec.strftime('%Y-%m-%dT%H:%M:%S-05:00')

            signing_cert_el = etree.SubElement(
                signed_sig_props, _etsi('SigningCertificate'))
            cert_node = etree.SubElement(signing_cert_el, _etsi('Cert'))

            cert_digest_el = etree.SubElement(cert_node, _etsi('CertDigest'))
            etree.SubElement(
                cert_digest_el, _ds('DigestMethod'), Algorithm=SHA1_ALG)
            cert_dv = etree.SubElement(cert_digest_el, _ds('DigestValue'))
            cert_dv.text = cert_sha1

            issuer_serial_el = etree.SubElement(
                cert_node, _etsi('IssuerSerial'))
            iss_name_el = etree.SubElement(
                issuer_serial_el, _ds('X509IssuerName'))
            iss_name_el.text = issuer_name
            iss_serial_el = etree.SubElement(
                issuer_serial_el, _ds('X509SerialNumber'))
            iss_serial_el.text = serial_number

            signed_data_props = etree.SubElement(
                signed_props, _etsi('SignedDataObjectProperties'))
            data_obj_fmt = etree.SubElement(
                signed_data_props, _etsi('DataObjectFormat'),
                ObjectReference=f'#{ref_id}')
            desc_el = etree.SubElement(data_obj_fmt, _etsi('Description'))
            desc_el.text = 'contenido comprobante'
            mime_el = etree.SubElement(data_obj_fmt, _etsi('MimeType'))
            mime_el.text = 'text/xml'

            # ══════════════════════════════════════════════════════════════
            # PASO 6: Ahora todo está EN EL ÁRBOL. Calcular los digests
            #         en contexto (con namespaces heredados correctos)
            # ══════════════════════════════════════════════════════════════
            signed_props_digest = _sha1_digest_b64(_c14n(signed_props))
            key_info_digest = _sha1_digest_b64(_c14n(key_info))

            # Rellenar los placeholders
            dv_sp.text = signed_props_digest
            dv_ki.text = key_info_digest

            # ══════════════════════════════════════════════════════════════
            # PASO 7: Canonicalizar SignedInfo EN CONTEXTO y firmar
            #         Esto es CRÍTICO: el SRI verifica la firma sobre
            #         el SignedInfo canonicalizado en contexto del
            #         documento completo (con namespaces del ancestro)
            # ══════════════════════════════════════════════════════════════
            signed_info_c14n = _c14n(signed_info)

            _logger.debug(
                'SRI DEBUG: SignedInfo C14N (%d bytes):\n%s',
                len(signed_info_c14n),
                signed_info_c14n.decode('utf-8', errors='replace')[:2000])

            signature_value = private_key.sign(
                signed_info_c14n,
                padding.PKCS1v15(),
                hashes.SHA1()
            )
            sig_value_elem.text = base64.b64encode(
                signature_value).decode('ascii')

            # ══════════════════════════════════════════════════════════════
            # PASO 8: Serializar el XML firmado
            # ══════════════════════════════════════════════════════════════
            xml_firmado = etree.tostring(
                root,
                xml_declaration=True,
                encoding='UTF-8',
                pretty_print=True
            )

            _logger.info('SRI: XML firmado correctamente con XAdES-BES')
            return xml_firmado

        except UserError:
            raise
        except Exception as e:
            _logger.error('SRI: Error al firmar XML: %s', str(e),
                          exc_info=True)
            raise UserError(
                f'Error al firmar el XML con el certificado electrónico:\n'
                f'{str(e)}')
