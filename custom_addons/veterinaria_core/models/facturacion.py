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
    
    impuesto_id = fields.Many2one(
        'account.tax',
        string='Impuesto',
        domain=[('type_tax_use', '=', 'sale')],
        tracking=True
    )
    
    impuesto_total = fields.Float('Total Impuestos', compute='_compute_totales', store=True)
    total = fields.Float('Total', compute='_compute_totales', store=True)

    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('validado', 'Validado'),
        ('cancelado', 'Cancelado'),
    ], string='Estado', default='borrador', tracking=True)

    observaciones = fields.Text('Observaciones')
    fecha_factura = fields.Date(
        'Fecha de Factura',
        default=fields.Date.today,
        states={'validado': [('readonly', True)], 'cancelado': [('readonly', True)]}
    )

    @api.depends('linea_ids.subtotal', 'impuesto_id')
    def _compute_totales(self):
        for record in self:
            subtotal = sum(line.subtotal for line in record.linea_ids)
            record.subtotal = subtotal
            
            if record.impuesto_id:
                if record.impuesto_id.amount_type == 'percent':
                    record.impuesto_total = subtotal * (record.impuesto_id.amount / 100.0)
                elif record.impuesto_id.amount_type == 'fixed':
                    record.impuesto_total = record.impuesto_id.amount
                else:
                    record.impuesto_total = 0.0
            else:
                record.impuesto_total = 0.0
                
            record.total = subtotal + record.impuesto_total

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
            # Descontar stock y marcar citas como facturadas
            for line in lineas_con_item:
                if line.tipo_linea in ('medicamento', 'producto') and line.inventario_id:
                    inv = line.inventario_id
                    inv.cantidad_stock -= line.cantidad
                if line.tipo_linea == 'cita' and line.cita_id:
                    line.cita_id.facturada = True

            record.estado = 'validado'

    def action_cancelar_factura(self):
        """Cancela la factura y libera citas."""
        for record in self:
            # Liberar citas
            for line in record.linea_ids:
                if line.tipo_linea == 'cita' and line.cita_id:
                    line.cita_id.facturada = False
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

    def write(self, vals):
        for record in self:
            if record.estado != 'borrador':
                allowed_fields = {'estado'}
                if set(vals.keys()) - allowed_fields:
                    raise ValidationError('No se puede editar una factura validada o cancelada')
        return super().write(vals)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if not record.name or record.name == 'Factura':
            record.name = f"FAC-{record.id:05d}"
        return record