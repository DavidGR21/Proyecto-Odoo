# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Facturacion(models.Model):
    _name = 'veterinaria.facturacion'
    _description = 'Facturacion Multiservicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Numero de Factura', readonly=True)

    propietario_id = fields.Many2one(
        'res.partner',
        string='Cliente (Propietario)',
        required=True,
        domain=[('es_propietario', '=', True)]
    )

    # paciente_id eliminado del encabezado:
    # un cliente puede pagar items de varias mascotas en una sola factura.
    # La mascota queda referenciada en cada linea de la factura (via item_ref -> cita).

    linea_ids = fields.One2many(
        'veterinaria.facturacion.linea',
        'facturacion_id',
        string='Lineas de Facturacion',
        copy=True
    )

    subtotal = fields.Float('Subtotal', compute='_compute_totales', store=True)
    impuesto_total = fields.Float('Total Impuestos', compute='_compute_totales', store=True)
    total = fields.Float('Total', compute='_compute_totales', store=True)

    detalles_impuestos_html = fields.Html(
        string='Detalle de Impuestos',
        compute='_compute_detalles_impuestos_html'
    )

    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('validado', 'Validado'),
        ('cancelado', 'Cancelado'),
    ], string='Estado', default='borrador', tracking=True)

    # ── Pago PayPal ──────────────────────────────────────────────────────
    pagado = fields.Boolean(
        'Pagado',
        default=False,
        tracking=True,
        help='Marcado automáticamente cuando el pago por PayPal es confirmado.',
    )
    fecha_pago = fields.Datetime(
        'Fecha de Pago',
        readonly=True,
        help='Fecha y hora en que se confirmó el pago.',
    )
    payment_transaction_id = fields.Many2one(
        'payment.transaction',
        string='Transacción de Pago',
        readonly=True,
        copy=False,
        help='Transacción de pago de Odoo vinculada a este cobro.',
    )
    payment_reference = fields.Char(
        'Referencia de Pago',
        readonly=True,
        copy=False,
        help='ID de orden/captura generado por PayPal.',
    )
    # ─────────────────────────────────────────────────────────────────────

    observaciones = fields.Text('Observaciones')
    fecha_factura = fields.Date(
        'Fecha de Factura',
        default=fields.Date.today,
        states={'validado': [('readonly', True)], 'cancelado': [('readonly', True)]}
    )

    @api.depends('linea_ids.subtotal', 'linea_ids.impuesto_linea')
    def _compute_totales(self):
        for record in self:
            subtotal = sum(line.subtotal for line in record.linea_ids)
            impuesto_total = sum(line.impuesto_linea for line in record.linea_ids)
            record.subtotal = subtotal
            record.impuesto_total = impuesto_total
            record.total = subtotal + impuesto_total

    @api.depends('linea_ids.subtotal', 'linea_ids.impuesto_ids', 'linea_ids.impuesto_linea')
    def _compute_detalles_impuestos_html(self):
        for record in self:
            impuestos = record._get_impuestos_agrupados()
            if not impuestos:
                record.detalles_impuestos_html = ""
                continue
            
            html = '<div style="width: 100%; display: flex; justify-content: flex-end; margin-top: 5px; margin-bottom: 5px;">'
            html += '<table style="width: 100%; max-width: 300px; font-size: 13px; color: #4b5563;">'
            for name, data in impuestos.items():
                html += f'<tr>' \
                        f'<td style="text-align: right; padding: 2px 10px 2px 0; font-weight: bold;">Subtotal {name}:</td>' \
                        f'<td style="text-align: right; padding: 2px 0; width: 120px;">${data["base"]:.2f}</td>' \
                        f'</tr>' \
                        f'<tr>' \
                        f'<td style="text-align: right; padding: 2px 10px 2px 0; font-weight: normal; color: #9ca3af;">{name}:</td>' \
                        f'<td style="text-align: right; padding: 2px 0; font-weight: normal; color: #9ca3af; width: 120px;">${data["monto"]:.2f}</td>' \
                        f'</tr>'
            html += '</table></div>'
            record.detalles_impuestos_html = html

    def _get_impuestos_agrupados(self):
        """
        Retorna un diccionario agrupado por impuesto (su porcentaje/nombre)
        con la base imponible y el monto del impuesto.
        """
        res = {}
        for line in self.linea_ids:
            taxes = line.impuesto_ids
            if not taxes:
                tax_name = "IVA 0%"
                tax_amount = 0.0
                codigo_porcentaje = '0'
            else:
                tax = taxes[0]
                tax_name = tax.name or f"IVA {tax.amount:.0f}%"
                tax_amount = tax.amount
                if tax_amount == 15:
                    codigo_porcentaje = '4'
                elif tax_amount == 12:
                    codigo_porcentaje = '2'
                elif tax_amount == 14:
                    codigo_porcentaje = '3'
                else:
                    codigo_porcentaje = '0' if tax_amount == 0 else '4'
            
            if tax_name not in res:
                res[tax_name] = {
                    'name': tax_name,
                    'base': 0.0,
                    'monto': 0.0,
                    'tax_amount': tax_amount,
                    'codigo_porcentaje': codigo_porcentaje
                }
            res[tax_name]['base'] += line.subtotal
            res[tax_name]['monto'] += line.impuesto_linea
            
        return res

    def action_validar_factura(self):
        """Valida la factura y descuenta stock donde aplica."""
        for record in self:
            if record.estado != 'borrador':
                raise ValidationError('Solo se pueden validar facturas en borrador')
            if not record.propietario_id:
                raise ValidationError('Falta el cliente (propietario)')
            lineas_con_item = record.linea_ids.filtered(lambda l: l.tipo_linea)
            if not lineas_con_item:
                raise ValidationError('Debe agregar al menos una linea con un item seleccionado')

            # Validar stock para medicamentos y productos
            for line in lineas_con_item:
                if line.tipo_linea in ('medicamento', 'producto') and line.inventario_id:
                    inv = line.inventario_id
                    if inv.cantidad_stock < line.cantidad:
                        raise ValidationError(
                            f"Stock insuficiente para '{inv.name}': "
                            f"disponible {inv.cantidad_stock}, solicitado {line.cantidad}"
                        )
            # Descontar stock y marcar citas/recetas como facturadas
            for line in lineas_con_item:
                if line.tipo_linea in ('medicamento', 'producto') and line.inventario_id:
                    inv = line.inventario_id
                    inv.cantidad_stock -= line.cantidad
                if line.cita_id:
                    line.cita_id.facturada = True
                    if line.cita_id.receta_ids:
                        line.cita_id.receta_ids.write({'state': 'finalizada'})

            record.estado = 'validado'

    def action_cancelar_factura(self):
        """Cancela la factura y libera citas y recetas."""
        for record in self:
            # Liberar citas y recetas
            for line in record.linea_ids:
                if line.cita_id:
                    line.cita_id.facturada = False
                    if line.cita_id.receta_ids:
                        line.cita_id.receta_ids.write({'state': 'borrador'})
            record.estado = 'cancelado'

    def action_importar_receta(self):
        """Abre el wizard para importar medicamentos de una receta."""
        self.ensure_one()
        return {
            'name': 'Importar desde Receta',
            'type': 'ir.actions.act_window',
            'res_model': 'veterinaria.importar.receta.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_facturacion_id': self.id,
                'default_propietario_id': self.propietario_id.id,
            }
        }

    def _get_allowed_fields_validado(self):
        return {
            'estado',
            'pagado',
            'fecha_pago',
            'payment_transaction_id',
            'payment_reference',
        }

    def write(self, vals):
        for record in self:
            if record.estado != 'borrador':
                allowed_fields = self._get_allowed_fields_validado()
                if set(vals.keys()) - allowed_fields:
                    raise ValidationError('No se puede editar una factura validada o cancelada')
        return super().write(vals)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if not record.name or record.name == 'Factura':
            record.name = f"FAC-{record.id:05d}"
        return record