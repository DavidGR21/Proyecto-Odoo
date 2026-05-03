# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Facturacion(models.Model):
    _name = 'veterinaria.facturacion'
    _description = 'Facturación por Servicios (Citas)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Número de Factura', compute='_compute_name', store=True, readonly=True)
    
    cita_id = fields.Many2one(
        'veterinaria.cita',
        string='Cita',
        required=True,
        ondelete='cascade',
        domain=[('estado', '=', 'completada')]
    )
    
    propietario_id = fields.Many2one(
        'res.partner',
        string='Cliente (Propietario)',
        compute='_compute_propietario_id',
        store=False
    )
    
    paciente_id = fields.Many2one(
        'veterinaria.paciente',
        string='Paciente (Mascota)',
        compute='_compute_paciente_id',
        store=False
    )
    
    veterinario_id = fields.Many2one(
        'veterinaria.veterinario',
        string='Veterinario',
        compute='_compute_veterinario_id',
        store=False
    )
    
    fecha_cita = fields.Datetime(
        'Fecha de la Cita',
        compute='_compute_fecha_cita',
        store=False
    )
    
    motivo_cita = fields.Text(
        'Motivo de la Cita',
        compute='_compute_motivo_cita',
        store=False
    )
    
    # Precio del servicio (modificable)
    precio_unitario = fields.Float('Precio del Servicio', required=True)
    
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
    ], string='Estado', default='borrador')
    
    impuesto_id = fields.Many2many(
        'account.tax',
        string='Impuestos',
        domain=[('type_tax_use', '=', 'sale')]
    )
    
    observaciones = fields.Text('Observaciones')
    fecha_factura = fields.Date('Fecha de Factura', default=fields.Date.today)
    
    @api.depends('cita_id')
    def _compute_name(self):
        for record in self:
            if record.cita_id:
                record.name = f"FAC-{record.cita_id.id:05d}"
            else:
                record.name = "Factura"
    
    @api.depends('cita_id')
    def _compute_propietario_id(self):
        for record in self:
            record.propietario_id = record.cita_id.propietario_id if record.cita_id else False
    
    @api.depends('cita_id')
    def _compute_paciente_id(self):
        for record in self:
            record.paciente_id = record.cita_id.paciente_id if record.cita_id else False
    
    @api.depends('cita_id')
    def _compute_veterinario_id(self):
        for record in self:
            record.veterinario_id = record.cita_id.veterinario_id if record.cita_id else False
    
    @api.depends('cita_id')
    def _compute_fecha_cita(self):
        for record in self:
            record.fecha_cita = record.cita_id.fecha_hora if record.cita_id else False
    
    @api.depends('cita_id')
    def _compute_motivo_cita(self):
        for record in self:
            record.motivo_cita = record.cita_id.motivo if record.cita_id else False
    
    def action_validar_factura(self):
        """Genera la factura contable desde la facturación"""
        for record in self:
            if record.estado != 'borrador':
                raise ValidationError('Solo se pueden validar facturas en borrador')
            
            if not record.propietario_id:
                raise ValidationError('Falta el cliente (propietario) para generar la factura')
            
            # Crear factura contable (account.move)
            move_vals = {
                'move_type': 'out_invoice',
                'partner_id': record.propietario_id.id,
                'invoice_date': record.fecha_factura,
                'ref': f"{record.name} - {record.paciente_id.name}",
                'line_ids': [
                    (0, 0, {
                        'name': f"Servicio Veterinario - {record.motivo_cita}",
                        'quantity': 1,
                        'price_unit': record.precio_unitario,
                        'tax_ids': [(6, 0, record.impuesto_id.ids)],
                    })
                ],
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
