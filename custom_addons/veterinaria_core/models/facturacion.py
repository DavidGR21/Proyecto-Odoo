# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class Facturacion(models.Model):
    _name = 'veterinaria.facturacion'
    _description = 'Facturación Multiservicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Número de Factura', readonly=True)
    
    
    propietario_id = fields.Many2one(
        'res.partner',
        string='Cliente (Propietario)',
        readonly=False,
        domain=[('es_propietario', '=', True)]
    )
    
    paciente_id = fields.Many2one(
        'veterinaria.paciente',
        string='Paciente (Mascota)',
        readonly=False,
        domain="[('propietario_id', '=', propietario_id)]"
    )
    
    fecha_cita = fields.Datetime('Fecha de la Cita')
    
    motivo_cita = fields.Text('Motivo de la Cita')
    
    # Líneas de facturación (multiservicio)
    linea_ids = fields.One2many(
        'veterinaria.facturacion.linea',
        'facturacion_id',
        string='Líneas de Facturación',
        copy=True
    )
    
    # Totales
    subtotal = fields.Float('Subtotal', compute='_compute_totales', store=True)
    impuesto_total = fields.Float('Total Impuestos', compute='_compute_totales', store=True)
    total = fields.Float('Total', compute='_compute_totales', store=True)
    
    # Invoice relacionada
    move_id = fields.Many2one(
        'account.move',
        string='Factura Contable',
        ondelete='cascade',
        readonly=True
    )
    
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('validado', 'Validado'),
        ('cancelado', 'Cancelado'),
    ], string='Estado', default='borrador', tracking=True)
    
    impuesto_id = fields.Many2many(
        'account.tax',
        string='Impuestos por Defecto',
        domain=[('type_tax_use', '=', 'sale')]
    )
    
    observaciones = fields.Text('Observaciones')
    fecha_factura = fields.Date('Fecha de Factura', default=fields.Date.today,
                               states={'validado': [('readonly', True)], 'cancelado': [('readonly', True)]})
    
    
    @api.depends('linea_ids.subtotal', 'linea_ids.impuesto', 'linea_ids.total_linea')
    def _compute_totales(self):
        for record in self:
            record.subtotal = sum(line.subtotal for line in record.linea_ids)
            record.impuesto_total = sum(line.impuesto for line in record.linea_ids)
            record.total = sum(line.total_linea for line in record.linea_ids)

    @api.constrains('linea_ids')
    def _check_lineas(self):
        for record in self:
            if not record.linea_ids:
                raise ValidationError('Debe agregar al menos una línea de facturación')
    
    def action_validar_factura(self):
        """Genera la factura contable desde la facturación multiservicio"""
        for record in self:
            if record.estado != 'borrador':
                raise ValidationError('Solo se pueden validar facturas en borrador')
            
            if not record.propietario_id:
                raise ValidationError('Falta el cliente (propietario) para generar la factura')
            
            if not record.linea_ids:
                raise ValidationError('Debe agregar al menos una línea de facturación')

            # Validar y descontar stock para productos/medicamentos
            for line in record.linea_ids:
                if line.tipo_linea in ('producto', 'medicamento'):
                    inventario = line.producto_id if line.tipo_linea == 'producto' else line.medicamento_id
                    if not inventario:
                        raise ValidationError('Debe seleccionar un producto o medicamento válido')
                    if inventario.cantidad_stock < line.cantidad:
                        raise ValidationError(
                            f"Stock insuficiente para {inventario.name}: disponible {inventario.cantidad_stock}"
                        )
            for line in record.linea_ids:
                if line.tipo_linea in ('producto', 'medicamento'):
                    inventario = line.producto_id if line.tipo_linea == 'producto' else line.medicamento_id
                    inventario.cantidad_stock -= line.cantidad
            
            # Construir líneas de la factura contable
            invoice_lines = []
            for line in record.linea_ids:
                invoice_lines.append((0, 0, {
                    'name': line.descripcion,
                    'quantity': line.cantidad,
                    'price_unit': line.precio_unitario,
                    'tax_ids': [(6, 0, line.impuesto_id.ids)],
                }))
            
            # Crear factura contable (account.move)
            move_vals = {
                'move_type': 'out_invoice',
                'partner_id': record.propietario_id.id,
                'invoice_date': record.fecha_factura,
                'ref': f"{record.name} - {record.paciente_id.name if record.paciente_id else 'General'}",
                'invoice_line_ids': invoice_lines,
            }
            
            move = self.env['account.move'].create(move_vals)
            record.move_id = move
            record.estado = 'validado'
    
    def action_cancelar_factura(self):
        """Cancela la facturación"""
        for record in self:
            if record.move_id:
                record.move_id.button_cancel()
            record.estado = 'cancelado'

    def write(self, vals):
        """Bloquea ediciones cuando la factura esta validada o cancelada."""
        for record in self:
            if record.estado != 'borrador':
                allowed_fields = {'estado'}
                if set(vals.keys()) - allowed_fields:
                    raise ValidationError('No se puede editar una factura validada o cancelada')
        return super().write(vals)
    
    @api.model
    def create(self, vals):
        """Override create para validaciones y generar nombre"""
        record = super().create(vals)
        if not record.name or record.name == 'Factura':
            record.name = f"FAC-{record.id:05d}"
        return record