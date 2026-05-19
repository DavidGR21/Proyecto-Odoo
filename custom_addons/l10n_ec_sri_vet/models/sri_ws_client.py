# -*- coding: utf-8 -*-
import base64
import logging
from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from zeep import Client
    from zeep.transports import Transport
    from requests import Session
    HAS_ZEEP = True
except ImportError:
    HAS_ZEEP = False
    _logger.warning('Librería zeep no disponible. Instalar con: pip install zeep')

# URLs de los Web Services del SRI
SRI_WS_URLS = {
    '1': {  # Pruebas
        'recepcion': 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl',
        'autorizacion': 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl',
    }
}


class SriWsClient(models.AbstractModel):
    _name = 'sri.ws.client'
    _description = 'Cliente SOAP para Web Services del SRI'

    def _get_client(self, servicio, ambiente='1'):
        """
        Crea un cliente SOAP para el servicio indicado.

        :param servicio: 'recepcion' o 'autorizacion'
        :param ambiente: '1' (Pruebas) o '2' (Producción)
        :return: zeep.Client
        """
        if not HAS_ZEEP:
            raise UserError(
                'La librería zeep no está instalada.\n'
                'Ejecute: pip install zeep')

        url = SRI_WS_URLS.get(ambiente, SRI_WS_URLS['1']).get(servicio)
        if not url:
            raise UserError(f'URL no encontrada para servicio={servicio}, ambiente={ambiente}')

        try:
            session = Session()
            session.verify = True
            transport = Transport(session=session, timeout=30)
            client = Client(url, transport=transport)
            _logger.info('SRI WS: Cliente creado para %s (%s)', servicio, url)
            return client
        except Exception as e:
            _logger.error('SRI WS: Error conectando a %s: %s', url, str(e))
            raise UserError(
                f'Error al conectar con el Web Service del SRI:\n{str(e)}\n\n'
                f'URL: {url}')

    def enviar_comprobante(self, xml_firmado_bytes, ambiente='1'):
        """
        Envía un comprobante electrónico firmado al Web Service de Recepción del SRI.

        :param xml_firmado_bytes: bytes del XML firmado
        :param ambiente: '1' (Pruebas) o '2' (Producción)
        :return: dict con 'estado' y 'mensaje'
        """
        try:
            client = self._get_client('recepcion', ambiente)
            # El WS recibe el XML en base64
            xml_b64 = base64.b64encode(xml_firmado_bytes).decode('utf-8')

            respuesta = client.service.validarComprobante(xml_b64)

            estado = respuesta.estado if hasattr(respuesta, 'estado') else 'DESCONOCIDO'
            mensajes = []

            if hasattr(respuesta, 'comprobantes') and respuesta.comprobantes:
                for comp in respuesta.comprobantes.comprobante:
                    if hasattr(comp, 'mensajes') and comp.mensajes:
                        for msg in comp.mensajes.mensaje:
                            tipo = getattr(msg, 'tipo', '')
                            identificador = getattr(msg, 'identificador', '')
                            mensaje_text = getattr(msg, 'mensaje', '')
                            info_adicional = getattr(msg, 'informacionAdicional', '')
                            mensajes.append(
                                f'[{tipo}] {identificador}: {mensaje_text} '
                                f'- {info_adicional}')

            resultado = {
                'estado': estado,
                'mensaje': '\n'.join(mensajes) if mensajes else estado,
            }

            _logger.info('SRI WS Recepción: estado=%s', estado)
            return resultado

        except UserError:
            raise
        except Exception as e:
            _logger.error('SRI WS Recepción error: %s', str(e))
            return {
                'estado': 'ERROR',
                'mensaje': f'Error de comunicación con el SRI:\n{str(e)}',
            }

    def consultar_autorizacion(self, clave_acceso, ambiente='1'):
        """
        Consulta la autorización de un comprobante en el Web Service del SRI.

        :param clave_acceso: clave de acceso de 49 dígitos
        :param ambiente: '1' (Pruebas) o '2' (Producción)
        :return: dict con 'estado', 'numero_autorizacion', 'fecha_autorizacion',
                 'xml_autorizado', 'mensaje'
        """
        try:
            client = self._get_client('autorizacion', ambiente)
            respuesta = client.service.autorizacionComprobante(clave_acceso)

            resultado = {
                'estado': 'NO_ENCONTRADO',
                'numero_autorizacion': '',
                'fecha_autorizacion': None,
                'xml_autorizado': '',
                'mensaje': '',
            }

            if hasattr(respuesta, 'autorizaciones') and respuesta.autorizaciones:
                autorizaciones = respuesta.autorizaciones.autorizacion
                if autorizaciones:
                    auth = autorizaciones[0]
                    resultado['estado'] = getattr(auth, 'estado', 'DESCONOCIDO')
                    resultado['numero_autorizacion'] = getattr(
                        auth, 'numeroAutorizacion', '')
                    resultado['fecha_autorizacion'] = getattr(
                        auth, 'fechaAutorizacion', None)
                    resultado['xml_autorizado'] = getattr(
                        auth, 'comprobante', '')

                    mensajes = []
                    if hasattr(auth, 'mensajes') and auth.mensajes:
                        for msg in auth.mensajes.mensaje:
                            tipo = getattr(msg, 'tipo', '')
                            identificador = getattr(msg, 'identificador', '')
                            mensaje_text = getattr(msg, 'mensaje', '')
                            info_adicional = getattr(msg, 'informacionAdicional', '')
                            mensajes.append(
                                f'[{tipo}] {identificador}: {mensaje_text} '
                                f'- {info_adicional}')
                    resultado['mensaje'] = '\n'.join(mensajes) if mensajes else resultado['estado']

            _logger.info('SRI WS Autorización: estado=%s, clave=%s',
                         resultado['estado'], clave_acceso)
            return resultado

        except UserError:
            raise
        except Exception as e:
            _logger.error('SRI WS Autorización error: %s', str(e))
            return {
                'estado': 'ERROR',
                'mensaje': f'Error consultando autorización:\n{str(e)}',
            }
