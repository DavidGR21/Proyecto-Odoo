# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class FacturacionSRI(models.Model):
    """
    Herencia sobre veterinaria.facturacion para agregar campos y
    funcionalidad de facturación electrónica SRI.
    NO modifica ningún campo ni método existente del modelo original.
    """
    _inherit = 'veterinaria.facturacion'

    # ── Campos SRI agregados por herencia ─────────────────────────────────────

    sri_documento_id = fields.Many2one(
        'sri.documento.electronico',
        string='Documento Electrónico SRI',
        readonly=True, copy=False,
        help='Documento electrónico vinculado en el SRI'
    )

    sri_forma_pago = fields.Selection([
        ('01', 'Sin utilización del sistema financiero'),
        ('15', 'Compensación de deudas'),
        ('16', 'Tarjeta de débito'),
        ('17', 'Dinero electrónico'),
        ('18', 'Tarjeta prepago'),
        ('19', 'Tarjeta de crédito'),
        ('20', 'Otros con utilización del sistema financiero'),
        ('21', 'Endoso de títulos'),
    ], string='Forma de Pago SRI', default='01',
       help='Forma de pago según catálogo del SRI')

    tipo_identificacion_cliente = fields.Selection([
        ('04', 'RUC'),
        ('05', 'Cédula'),
        ('06', 'Pasaporte'),
        ('07', 'Consumidor Final'),
        ('08', 'Identificación del Exterior'),
    ], string='Tipo de Identificación', default='05',
       help='Tipo de documento de identidad del cliente según el SRI')

    identificacion_cliente = fields.Char(
        string='Nro. Identificación',
        help='Número de cédula, RUC o pasaporte del cliente'
    )

    # Campos related para mostrar info SRI en las vistas
    sri_estado = fields.Selection(
        related='sri_documento_id.estado',
        string='Estado SRI', store=True, readonly=True)
    sri_clave_acceso = fields.Char(
        related='sri_documento_id.clave_acceso',
        string='Clave de Acceso', readonly=True)
    sri_numero_autorizacion = fields.Char(
        related='sri_documento_id.numero_autorizacion',
        string='Nro. Autorización SRI', readonly=True)
    sri_fecha_autorizacion = fields.Datetime(
        related='sri_documento_id.fecha_autorizacion',
        string='Fecha Autorización', readonly=True)

    # ── Onchange: auto-llenar identificación del cliente ──────────────────────

    @api.onchange('propietario_id')
    def _onchange_propietario_sri(self):
        """Auto-llena la identificación del cliente desde el partner."""
        if self.propietario_id:
            partner = self.propietario_id
            if partner.vat:
                self.identificacion_cliente = partner.vat
                # Determinar tipo por longitud
                if len(partner.vat) == 13:
                    self.tipo_identificacion_cliente = '04'  # RUC
                elif len(partner.vat) == 10:
                    self.tipo_identificacion_cliente = '05'  # Cédula
                else:
                    self.tipo_identificacion_cliente = '06'  # Pasaporte

    # ── Override Core ─────────────────────────────────────────────────────────

    def _get_allowed_fields_validado(self):
        """Permite que los campos del SRI sean editados cuando la factura está validada."""
        fields = super()._get_allowed_fields_validado()
        fields.update({
            'sri_documento_id',
            'sri_estado',
            'sri_forma_pago',
            'tipo_identificacion_cliente',
            'identificacion_cliente',
            'message_follower_ids',
            'message_ids',
            'activity_ids',
        })
        return fields

    # ── Acciones SRI ──────────────────────────────────────────────────────────

    def action_enviar_sri(self):
        """
        Crea el documento electrónico SRI y ejecuta el flujo completo:
        Generar XML → Firmar → Enviar al SRI → Consultar Autorización.
        """
        self.ensure_one()
        if self.estado != 'validado':
            raise UserError(
                'Solo se pueden enviar al SRI facturas en estado "Validado".')

        if not self.identificacion_cliente:
            raise UserError(
                'Debe ingresar el número de identificación del cliente '
                'antes de enviar al SRI.')

        company = self.env.company
        if not company.vat:
            alt_company = self.env['res.company'].search([('vat', '!=', False)], limit=1)
            if alt_company:
                raise UserError(
                    f'Actualmente estás operando bajo la compañía "{company.name}", '
                    f'pero configuraste el RUC en la compañía "{alt_company.name}". '
                    'Por favor, cambia a la compañía correcta en el menú superior derecho de Odoo.'
                )
            raise UserError(
                'Debe configurar el RUC de la compañía en '
                'Ajustes → Compañía → pestaña SRI.')
        if not company.sri_certificado_p12:
            raise UserError(
                'Debe cargar el certificado de firma electrónica (.p12) en '
                'Ajustes → Compañía → pestaña SRI.')

        # Crear o reutilizar documento electrónico
        if not self.sri_documento_id or self.sri_documento_id.estado in ('rechazado', 'error'):
            doc = self.env['sri.documento.electronico'].create({
                'facturacion_id': self.id,
                'tipo_comprobante': '01',
                'ambiente': company.sri_ambiente or '1',
            })
            self.sri_documento_id = doc
        else:
            doc = self.sri_documento_id

        # Ejecutar flujo completo
        doc.action_proceso_completo()

    def action_consultar_sri(self):
        """Re-consulta la autorización del comprobante en el SRI."""
        self.ensure_one()
        if not self.sri_documento_id:
            raise UserError('No hay documento electrónico asociado.')
        self.sri_documento_id.action_consultar_autorizacion()

    def action_descargar_ride(self):
        """Descarga el RIDE PDF."""
        self.ensure_one()
        if not self.sri_documento_id:
            raise UserError('No hay documento electrónico asociado.')
        return self.sri_documento_id.action_descargar_ride()

    def action_enviar_ride_email(self):
        """Envía el RIDE y XML por email al cliente."""
        self.ensure_one()
        if not self.sri_documento_id:
            raise UserError('No hay documento electrónico asociado.')
        return self.sri_documento_id.action_enviar_ride_email()
