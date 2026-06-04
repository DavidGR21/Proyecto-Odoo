# -*- coding: utf-8 -*-
import random
import logging
from datetime import datetime, timezone, timedelta
from lxml import etree
from odoo import models

_logger = logging.getLogger(__name__)


class SriXmlGenerator(models.AbstractModel):
    _name = 'sri.xml.generator'
    _description = 'Generador de XML para el SRI (XSD 2.1.0)'

    # ── Generación de la Clave de Acceso (49 dígitos) ─────────────────────────

    def _calcular_digito_modulo11(self, cadena):
        """
        Calcula el dígito verificador usando el algoritmo Módulo 11
        con factores de chequeo ponderados del 2 al 7.
        """
        factores = [2, 3, 4, 5, 6, 7]
        total = 0
        for i, digito in enumerate(reversed(cadena)):
            total += int(digito) * factores[i % len(factores)]
        residuo = total % 11
        if residuo == 0:
            return '0'
        elif residuo == 1:
            return '1'
        else:
            return str(11 - residuo)

    def _generar_clave_acceso(self, fecha_emision, tipo_comprobante, ruc,
                               ambiente, establecimiento, punto_emision,
                               secuencial, tipo_emision='1'):
        """
        Genera la clave de acceso de 49 dígitos del SRI.

        Estructura:
        - Posición 1-8:   Fecha de emisión (ddmmaaaa)
        - Posición 9-10:  Tipo de comprobante
        - Posición 11-23: RUC del emisor
        - Posición 24:    Tipo de ambiente (1=Pruebas, 2=Producción)
        - Posición 25-27: Serie - Establecimiento
        - Posición 28-30: Serie - Punto de emisión
        - Posición 31-39: Secuencial
        - Posición 40-47: Código numérico (8 dígitos aleatorios)
        - Posición 48:    Tipo de emisión (1=Normal)
        - Posición 49:    Dígito verificador (Módulo 11)
        """
        fecha_str = fecha_emision.strftime('%d%m%Y')
        codigo_numerico = str(random.randint(10000000, 99999999))

        # 48 dígitos sin el verificador
        clave_sin_verificador = (
            f"{fecha_str}"
            f"{tipo_comprobante}"
            f"{ruc}"
            f"{ambiente}"
            f"{establecimiento}"
            f"{punto_emision}"
            f"{secuencial}"
            f"{codigo_numerico}"
            f"{tipo_emision}"
        )

        digito_verificador = self._calcular_digito_modulo11(clave_sin_verificador)
        clave_acceso = clave_sin_verificador + digito_verificador

        _logger.info('SRI: Clave de acceso generada: %s (%d dígitos)',
                     clave_acceso, len(clave_acceso))
        return clave_acceso

    # ── Generación del XML de Factura ─────────────────────────────────────────

    def generar_factura_xml(self, documento):
        """
        Genera el XML de una factura según el esquema XSD 2.1.0 del SRI.
        
        :param documento: record de sri.documento.electronico
        :return: bytes del XML generado
        """
        company = self.env.company
        factura = documento.facturacion_id

        # Obtener secuencial
        secuencial = company.sri_get_next_secuencial()
        establecimiento = company.sri_establecimiento or '001'
        punto_emision = company.sri_punto_emision or '001'

        # Fecha de emisión - usar siempre hora Ecuador (-05:00)
        # El contenedor Docker corre en UTC; sin esta conversión la fecha
        # puede quedar 1 día adelante respecto a Ecuador y el SRI la rechaza
        # con error 65 (FECHA EMISIÓN EXTEMPORANEA).
        ec_tz = timezone(timedelta(hours=-5))
        fecha_ecuador_hoy = datetime.now(ec_tz).date()
        fecha_emision = factura.fecha_factura or fecha_ecuador_hoy

        # Si la fecha de la factura es futura respecto a Ecuador, corregir
        if fecha_emision > fecha_ecuador_hoy:
            fecha_emision = fecha_ecuador_hoy

        # Generar clave de acceso
        clave_acceso = self._generar_clave_acceso(
            fecha_emision=fecha_emision,
            tipo_comprobante='01',  # Factura
            ruc=company.vat or '0000000000001',
            ambiente=company.sri_ambiente or '1',
            establecimiento=establecimiento,
            punto_emision=punto_emision,
            secuencial=secuencial,
            tipo_emision=company.sri_tipo_emision or '1',
        )

        # Guardar datos en el documento
        documento.clave_acceso = clave_acceso
        documento.secuencial = secuencial
        documento.establecimiento = establecimiento
        documento.punto_emision = punto_emision
        documento.ambiente = company.sri_ambiente or '1'

        # ── Construir el XML ──────────────────────────────────────────────────

        root = etree.Element('factura', id='comprobante', version='2.1.0')

        # === infoTributaria ===
        info_trib = etree.SubElement(root, 'infoTributaria')
        self._add_element(info_trib, 'ambiente', company.sri_ambiente or '1')
        self._add_element(info_trib, 'tipoEmision', company.sri_tipo_emision or '1')
        self._add_element(info_trib, 'razonSocial',
                          company.sri_razon_social or company.name)
        if company.sri_nombre_comercial:
            self._add_element(info_trib, 'nombreComercial',
                              company.sri_nombre_comercial)
        self._add_element(info_trib, 'ruc', company.vat or '0000000000001')
        self._add_element(info_trib, 'claveAcceso', clave_acceso)
        self._add_element(info_trib, 'codDoc', '01')
        self._add_element(info_trib, 'estab', establecimiento)
        self._add_element(info_trib, 'ptoEmi', punto_emision)
        self._add_element(info_trib, 'secuencial', secuencial)
        self._add_element(info_trib, 'dirMatriz',
                          company.sri_direccion_matriz or company.street or 'S/N')

        # === infoFactura ===
        info_factura = etree.SubElement(root, 'infoFactura')
        self._add_element(info_factura, 'fechaEmision',
                          fecha_emision.strftime('%d/%m/%Y'))
        if company.sri_direccion_establecimiento:
            self._add_element(info_factura, 'dirEstablecimiento',
                              company.sri_direccion_establecimiento)
        if company.sri_contribuyente_especial:
            self._add_element(info_factura, 'contribuyenteEspecial',
                              company.sri_contribuyente_especial)
        self._add_element(info_factura, 'obligadoContabilidad',
                          'SI' if company.sri_obligado_contabilidad else 'NO')

        # Datos del comprador
        partner = factura.propietario_id
        tipo_id = factura.tipo_identificacion_cliente or '05'  # Cédula por defecto
        self._add_element(info_factura, 'tipoIdentificacionComprador', tipo_id)
        self._add_element(info_factura, 'razonSocialComprador',
                          partner.name or 'CONSUMIDOR FINAL')
        self._add_element(info_factura, 'identificacionComprador',
                          factura.identificacion_cliente or partner.vat or '9999999999999')

        # Totales
        subtotal = factura.subtotal or 0.0
        impuesto_total = factura.impuesto_total or 0.0
        total = factura.total or 0.0

        self._add_element(info_factura, 'totalSinImpuestos',
                          f'{subtotal:.2f}')
        self._add_element(info_factura, 'totalDescuento', '0.00')

        # totalConImpuestos
        total_con_impuestos = etree.SubElement(info_factura, 'totalConImpuestos')
        
        impuestos_agrupados = factura._get_impuestos_agrupados()
        if not impuestos_agrupados:
            impuestos_agrupados = {
                'IVA 0%': {
                    'base': subtotal,
                    'monto': 0.0,
                    'codigo_porcentaje': '0'
                }
            }
            
        for tax_info in impuestos_agrupados.values():
            total_impuesto_elem = etree.SubElement(total_con_impuestos, 'totalImpuesto')
            self._add_element(total_impuesto_elem, 'codigo', '2')  # IVA
            self._add_element(total_impuesto_elem, 'codigoPorcentaje', tax_info['codigo_porcentaje'])
            self._add_element(total_impuesto_elem, 'baseImponible', f"{tax_info['base']:.2f}")
            self._add_element(total_impuesto_elem, 'valor', f"{tax_info['monto']:.2f}")

        self._add_element(info_factura, 'importeTotal', f'{total:.2f}')
        self._add_element(info_factura, 'moneda', 'DOLAR')

        # Pagos
        pagos = etree.SubElement(info_factura, 'pagos')
        pago = etree.SubElement(pagos, 'pago')
        forma_pago = factura.sri_forma_pago or '01'
        self._add_element(pago, 'formaPago', forma_pago)
        self._add_element(pago, 'total', f'{total:.2f}')

        # === detalles ===
        detalles = etree.SubElement(root, 'detalles')
        for linea in factura.linea_ids:
            detalle = etree.SubElement(detalles, 'detalle')
            # Código principal
            codigo_principal = 'SRV'
            if linea.tipo_linea == 'cita':
                codigo_principal = f'CITA-{linea.cita_id.id if linea.cita_id else 0}'
            elif linea.tipo_linea == 'medicamento':
                codigo_principal = f'MED-{linea.inventario_id.id if linea.inventario_id else 0}'
            elif linea.tipo_linea == 'producto':
                codigo_principal = f'PROD-{linea.inventario_id.id if linea.inventario_id else 0}'
            elif linea.tipo_linea == 'servicio':
                codigo_principal = f'SRV-{linea.inventario_id.id if linea.inventario_id else 0}'

            self._add_element(detalle, 'codigoPrincipal', codigo_principal)
            self._add_element(detalle, 'descripcion',
                              linea.nombre_item or linea.descripcion or 'Servicio')
            self._add_element(detalle, 'cantidad', f'{linea.cantidad:.2f}')
            self._add_element(detalle, 'precioUnitario',
                              f'{linea.precio_unitario:.2f}')
            self._add_element(detalle, 'descuento', '0.00')
            self._add_element(detalle, 'precioTotalSinImpuesto',
                              f'{linea.subtotal:.2f}')

            # Impuestos por línea
            linea_taxes = linea.impuesto_ids
            if not linea_taxes:
                l_tarifa = 0.0
                l_codigo_porcentaje = '0'
            else:
                tax = linea_taxes[0]
                l_tarifa = tax.amount
                if l_tarifa == 15:
                    l_codigo_porcentaje = '4'
                elif l_tarifa == 12:
                    l_codigo_porcentaje = '2'
                elif l_tarifa == 14:
                    l_codigo_porcentaje = '3'
                else:
                    l_codigo_porcentaje = '0' if l_tarifa == 0 else '4'

            impuestos_det = etree.SubElement(detalle, 'impuestos')
            impuesto_det = etree.SubElement(impuestos_det, 'impuesto')
            self._add_element(impuesto_det, 'codigo', '2')  # IVA
            self._add_element(impuesto_det, 'codigoPorcentaje', l_codigo_porcentaje)
            self._add_element(impuesto_det, 'tarifa', f'{l_tarifa:.0f}')
            self._add_element(impuesto_det, 'baseImponible',
                              f'{linea.subtotal:.2f}')
            self._add_element(impuesto_det, 'valor',
                              f'{linea.impuesto_linea:.2f}')

        # Serializar
        xml_bytes = etree.tostring(
            root, xml_declaration=True, encoding='UTF-8', pretty_print=True)
        return xml_bytes

    def _add_element(self, parent, tag, text):
        """Agrega un sub-elemento con texto al nodo padre."""
        elem = etree.SubElement(parent, tag)
        elem.text = str(text) if text is not None else ''
        return elem
