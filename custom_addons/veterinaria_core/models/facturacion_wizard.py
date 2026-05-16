# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FacturacionLineaWizard(models.TransientModel):
    """Wizard simplificado: agrega una linea rapida a la factura usando item_ref."""
    _name = 'veterinaria.facturacion.linea.wizard'
    _description = 'Asistente para Agregar Linea de Facturacion'

    facturacion_id = fields.Many2one(
        'veterinaria.facturacion',
        string='Facturacion',
        required=True
    )

    tipo_linea = fields.Selection([
        ('cita', 'Cita Veterinaria'),
        ('medicamento', 'Medicamento'),
        ('producto', 'Producto'),
        ('servicio', 'Servicio'),
    ], string='Tipo', required=True, default='cita')

    cita_id = fields.Many2one(
        'veterinaria.cita',
        string='Cita Veterinaria',
        domain=[('estado', '=', 'completada')]
    )

    inventario_id = fields.Many2one(
        'veterinaria.inventario',
        string='Item de Inventario',
        domain="[('tipo_inventario', '=', tipo_linea), ('activo', '=', True)]"
    )

    cantidad = fields.Float('Cantidad', required=True, default=1.0)
    precio_unitario = fields.Float('Precio Unitario', required=True, default=0.0)

    @api.onchange('tipo_linea')
    def _onchange_tipo_linea(self):
        self.cita_id = False
        self.inventario_id = False
        self.precio_unitario = 0.0
        self.cantidad = 1.0

    @api.onchange('cita_id')
    def _onchange_cita_id(self):
        if self.tipo_linea == 'cita' and self.cita_id:
            servicio = self.cita_id.servicio_id
            self.precio_unitario = getattr(servicio, 'precio', 0.0) if servicio else 0.0
            self.cantidad = 1.0

    @api.onchange('inventario_id')
    def _onchange_inventario_id(self):
        if self.tipo_linea in ('medicamento', 'producto', 'servicio') and self.inventario_id:
            self.precio_unitario = self.inventario_id.precio_venta or 0.0
            self.cantidad = 1.0

    def action_agregar_linea(self):
        self.ensure_one()
        self.env['veterinaria.facturacion.linea'].create({
            'facturacion_id': self.facturacion_id.id,
            'tipo_linea': self.tipo_linea,
            'cita_id': self.cita_id.id if self.tipo_linea == 'cita' else False,
            'inventario_id': self.inventario_id.id if self.tipo_linea != 'cita' else False,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'veterinaria.facturacion',
            'res_id': self.facturacion_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class FacturacionMultilineaWizard(models.TransientModel):
    """Wizard para importar multiples citas o items a la factura."""
    _name = 'veterinaria.facturacion.multilinea.wizard'
    _description = 'Asistente para Agregar Multiples Lineas'

    facturacion_id = fields.Many2one(
        'veterinaria.facturacion',
        string='Facturacion',
        required=True
    )

    tipo_documento = fields.Selection([
        ('cita', 'Citas'),
        ('medicamento', 'Medicamentos'),
        ('producto', 'Productos'),
        ('servicio', 'Servicios'),
    ], string='Tipo de Documento', required=True)

    cita_ids = fields.Many2many(
        'veterinaria.cita',
        'facturacion_wiz_multi_cita_rel',
        string='Seleccionar Citas',
        domain=[('estado', '=', 'completada')]
    )

    inventario_ids = fields.Many2many(
        'veterinaria.inventario',
        'facturacion_wiz_multi_inv_rel',
        string='Seleccionar Items',
        domain="[('tipo_inventario', '=', tipo_documento), ('activo', '=', True)]"
    )

    cantidad_default = fields.Float('Cantidad por Defecto', default=1.0)

    def action_agregar_multiples_lineas(self):
        self.ensure_one()

        if self.tipo_documento == 'cita':
            if not self.cita_ids:
                raise ValidationError('Debe seleccionar al menos una cita.')
            for cita in self.cita_ids:
                precio = getattr(cita.servicio_id, 'precio', 0.0) if cita.servicio_id else 0.0
                self.env['veterinaria.facturacion.linea'].create({
                    'facturacion_id': self.facturacion_id.id,
                    'tipo_linea': 'cita',
                    'cita_id': cita.id,
                    'cantidad': self.cantidad_default,
                    'precio_unitario': precio,
                })
        else:
            if not self.inventario_ids:
                raise ValidationError('Debe seleccionar al menos un item.')
            for item in self.inventario_ids:
                self.env['veterinaria.facturacion.linea'].create({
                    'facturacion_id': self.facturacion_id.id,
                    'tipo_linea': self.tipo_documento,
                    'inventario_id': item.id,
                    'cantidad': self.cantidad_default,
                    'precio_unitario': item.precio_venta or 0.0,
                })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'veterinaria.facturacion',
            'res_id': self.facturacion_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
