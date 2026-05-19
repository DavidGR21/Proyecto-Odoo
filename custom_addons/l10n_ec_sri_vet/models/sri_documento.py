# -*- coding: utf-8 -*-
import base64
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SriDocumentoElectronico(models.Model):
    _name = 'sri.documento.electronico'
    _description = 'Documento Electrónico SRI'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Número', compute='_compute_name', store=True)

    facturacion_id = fields.Many2one(
        'veterinaria.facturacion',
        string='Factura Veterinaria',
        required=True, ondelete='cascade'
    )

    tipo_comprobante = fields.Selection([
        ('01', 'Factura'),
        ('04', 'Nota de Crédito'),
        ('05', 'Nota de Débito'),
    ], string='Tipo de Comprobante', default='01', required=True)

    # ── Clave de Acceso y Autorización ────────────────────────────────────────
    clave_acceso = fields.Char('Clave de Acceso', size=49, readonly=True, copy=False)
    numero_autorizacion = fields.Char('Nro. Autorización', readonly=True, copy=False)
    fecha_autorizacion = fields.Datetime('Fecha de Autorización', readonly=True, copy=False)
    ambiente = fields.Selection([
        ('1', 'Pruebas'),
        ('2', 'Producción'),
    ], string='Ambiente', default='1', readonly=True)

    # ── Estado ────────────────────────────────────────────────────────────────
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('generado', 'XML Generado'),
        ('firmado', 'XML Firmado'),
        ('enviado', 'Enviado al SRI'),
        ('autorizado', 'Autorizado'),
        ('rechazado', 'Rechazado'),
        ('error', 'Error'),
    ], string='Estado SRI', default='borrador', tracking=True)

    # ── XML almacenados ───────────────────────────────────────────────────────
    xml_sin_firma = fields.Binary('XML Sin Firma', readonly=True, copy=False)
    xml_sin_firma_filename = fields.Char('Nombre XML sin firma')
    xml_firmado = fields.Binary('XML Firmado', readonly=True, copy=False)
    xml_firmado_filename = fields.Char('Nombre XML firmado')
    xml_autorizado = fields.Binary('XML Autorizado', readonly=True, copy=False)
    xml_autorizado_filename = fields.Char('Nombre XML autorizado')

    # ── Mensajes del SRI ──────────────────────────────────────────────────────
    mensaje_sri = fields.Text('Mensajes del SRI', readonly=True, copy=False)

    # ── Datos de la factura (para el RIDE) ────────────────────────────────────
    secuencial = fields.Char('Secuencial', size=9, readonly=True, copy=False)
    establecimiento = fields.Char('Establecimiento', size=3, readonly=True)
    punto_emision = fields.Char('Punto de Emisión', size=3, readonly=True)

    # ── Computes ──────────────────────────────────────────────────────────────

    @api.depends('establecimiento', 'punto_emision', 'secuencial')
    def _compute_name(self):
        for rec in self:
            if rec.establecimiento and rec.punto_emision and rec.secuencial:
                rec.name = f"{rec.establecimiento}-{rec.punto_emision}-{rec.secuencial}"
            else:
                rec.name = 'Nuevo'

    # ── Flujo principal ───────────────────────────────────────────────────────

    def action_generar_xml(self):
        """Paso 1: Genera el XML sin firma según XSD 2.1.0 del SRI."""
        self.ensure_one()
        generator = self.env['sri.xml.generator']
        xml_bytes = generator.generar_factura_xml(self)
        self.xml_sin_firma = base64.b64encode(xml_bytes)
        self.xml_sin_firma_filename = f"factura_{self.clave_acceso}.xml"
        self.estado = 'generado'
        self.message_post(body='XML generado correctamente.')
        _logger.info('SRI: XML generado para documento %s', self.name)

    def action_firmar_xml(self):
        """Paso 2: Firma el XML con XAdES-BES usando el certificado .p12."""
        self.ensure_one()
        company = self.env.company
        if not company.sri_certificado_p12 or not company.sri_certificado_password:
            raise UserError('Debe configurar el certificado .p12 y su contraseña en la compañía.')

        firma = self.env['sri.firma.electronica']
        xml_sin_firma = base64.b64decode(self.xml_sin_firma)
        p12_data = base64.b64decode(company.sri_certificado_p12)

        xml_firmado = firma.firmar_xml(xml_sin_firma, p12_data, company.sri_certificado_password)
        self.xml_firmado = base64.b64encode(xml_firmado)
        self.xml_firmado_filename = f"factura_{self.clave_acceso}_firmado.xml"
        self.estado = 'firmado'
        self.message_post(body='XML firmado correctamente con certificado electrónico.')
        _logger.info('SRI: XML firmado para documento %s', self.name)

    def action_enviar_sri(self):
        """Paso 3: Envía el XML firmado al Web Service de Recepción del SRI."""
        self.ensure_one()
        ws_client = self.env['sri.ws.client']
        xml_firmado = base64.b64decode(self.xml_firmado)

        resultado = ws_client.enviar_comprobante(xml_firmado, self.ambiente)
        self.mensaje_sri = resultado.get('mensaje', '')

        if resultado.get('estado') == 'RECIBIDA':
            self.estado = 'enviado'
            self.message_post(body='Comprobante enviado al SRI. Estado: RECIBIDA')
            _logger.info('SRI: Comprobante enviado, clave=%s', self.clave_acceso)
            # Intentar autorización inmediata
            self.action_consultar_autorizacion()
        else:
            self.estado = 'rechazado'
            self.message_post(
                body=f'Comprobante rechazado por el SRI:\n{self.mensaje_sri}')
            _logger.warning('SRI: Comprobante rechazado, clave=%s, msg=%s',
                            self.clave_acceso, self.mensaje_sri)

    def action_consultar_autorizacion(self):
        """Paso 4: Consulta la autorización del comprobante en el SRI."""
        self.ensure_one()
        ws_client = self.env['sri.ws.client']
        resultado = ws_client.consultar_autorizacion(self.clave_acceso, self.ambiente)

        if resultado.get('estado') == 'AUTORIZADO':
            self.estado = 'autorizado'
            self.numero_autorizacion = resultado.get('numero_autorizacion', '')
            # Odoo Datetime fields requieren datetimes "naive" (sin timezone).
            # El SRI puede devolver un datetime con tz, hay que convertirlo.
            fecha_auth = resultado.get('fecha_autorizacion')
            if fecha_auth and hasattr(fecha_auth, 'replace'):
                fecha_auth = fecha_auth.replace(tzinfo=None)
            self.fecha_autorizacion = fecha_auth
            if resultado.get('xml_autorizado'):
                self.xml_autorizado = base64.b64encode(
                    resultado['xml_autorizado'].encode('utf-8'))
                self.xml_autorizado_filename = f"factura_{self.clave_acceso}_autorizado.xml"
            self.mensaje_sri = resultado.get('mensaje', 'AUTORIZADO')
            self.message_post(body=f'✅ Comprobante AUTORIZADO por el SRI.\n'
                                   f'Autorización: {self.numero_autorizacion}')
            _logger.info('SRI: AUTORIZADO clave=%s, auth=%s',
                         self.clave_acceso, self.numero_autorizacion)
        else:
            self.mensaje_sri = resultado.get('mensaje', 'No autorizado')
            if resultado.get('estado') == 'RECHAZADO':
                self.estado = 'rechazado'
            self.message_post(
                body=f'SRI respuesta: {self.mensaje_sri}')

    def action_proceso_completo(self):
        """Ejecuta el flujo completo: Generar → Firmar → Enviar → Autorizar."""
        self.ensure_one()
        self.action_generar_xml()
        self.action_firmar_xml()
        self.action_enviar_sri()

    def action_descargar_ride(self):
        """Descarga el RIDE PDF del documento electrónico."""
        self.ensure_one()
        return self.env.ref('l10n_ec_sri_vet.action_report_ride').report_action(self)

    def action_enviar_ride_email(self):
        """Envía el RIDE PDF y el XML autorizado por email al cliente."""
        self.ensure_one()
        if self.estado != 'autorizado':
            raise UserError('Solo se puede enviar el RIDE de comprobantes autorizados.')

        factura = self.facturacion_id
        partner = factura.propietario_id
        if not partner.email:
            raise UserError(
                f'El cliente {partner.name} no tiene email configurado.')

        # Generar el PDF del RIDE
        report = self.env.ref('l10n_ec_sri_vet.action_report_ride')
        pdf_content, _ = report._render_qweb_pdf(report.report_name, self.ids)
        pdf_b64 = base64.b64encode(pdf_content)

        # Crear adjuntos
        attachments = []
        # RIDE PDF
        att_pdf = self.env['ir.attachment'].create({
            'name': f'RIDE_{self.clave_acceso}.pdf',
            'type': 'binary',
            'datas': pdf_b64,
            'mimetype': 'application/pdf',
        })
        attachments.append(att_pdf.id)

        # XML Autorizado
        if self.xml_autorizado:
            att_xml = self.env['ir.attachment'].create({
                'name': f'factura_{self.clave_acceso}.xml',
                'type': 'binary',
                'datas': self.xml_autorizado,
                'mimetype': 'application/xml',
            })
            attachments.append(att_xml.id)

        # Enviar email
        mail_values = {
            'subject': f'Factura Electrónica {self.name} - VitalPet',
            'body_html': f"""
                <p>Estimado/a <strong>{partner.name}</strong>,</p>
                <p>Adjunto encontrará su comprobante electrónico:</p>
                <ul>
                    <li><strong>Factura:</strong> {self.name}</li>
                    <li><strong>Clave de Acceso:</strong> {self.clave_acceso}</li>
                    <li><strong>Fecha de Autorización:</strong> {self.fecha_autorizacion or ''}</li>
                </ul>
                <p>Se adjunta el RIDE (PDF) y el XML autorizado.</p>
                <br/>
                <p>Atentamente,</p>
                <p><strong>VitalPet Clínica Veterinaria</strong></p>
                <hr/>
                <small><em>Este documento es una representación impresa de un comprobante electrónico.</em></small>
            """,
            'email_to': partner.email,
            'email_from': self.env.company.email or 'noreply@vitalpet.com',
            'attachment_ids': [(6, 0, attachments)],
        }
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        self.message_post(body=f'📧 RIDE y XML enviados por email a {partner.email}')
