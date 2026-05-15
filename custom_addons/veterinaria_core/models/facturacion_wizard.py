# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FacturacionLineaWizard(models.TransientModel):
    _name = 'veterinaria.facturacion.linea.wizard'
    _description = 'Asistente para Agregar Línea de Facturación'

    facturacion_id = fields.Many2one(
        'veterinaria.facturacion',
        string='Facturación',
        required=True
    )
    
    tipo_linea = fields.Selection([
        ('cita', 'Cita Veterinaria'),
        ('medicamento', 'Medicamento'),
        ('producto', 'Producto'),
        ('servicio', 'Servicio'),
    ], string='Tipo de Documento', required=True)
    
    # Campos específicos
    cita_id = fields.Many2one(
        'veterinaria.cita',
        string='Seleccionar Cita',
        domain=[('estado', '=', 'completada')]
    )
    
    medicamento_id = fields.Many2one(
        'veterinaria.medicamento',
        string='Seleccionar Medicamento',
        domain=[('activo', '=', True)]
    )
    
    producto_id = fields.Many2one(
        'veterinaria.producto',
        string='Seleccionar Producto',
        domain=[('activo', '=', True)]
    )
    
    servicio_id = fields.Many2one(
        'veterinaria.servicio',
        string='Seleccionar Servicio',
        domain=[('activo', '=', True)]
    )
    
    cantidad = fields.Float('Cantidad', required=True, default=1.0)
    precio_unitario = fields.Float('Precio Unitario', compute='_compute_precio', store=False)
    
    impuesto_id = fields.Many2many(
        'account.tax',
        string='Impuestos',
        domain=[('type_tax_use', '=', 'sale')]
    )
    
    observaciones_linea = fields.Text('Observaciones')
    
    @api.depends('tipo_linea', 'cita_id', 'medicamento_id', 'producto_id', 'servicio_id')
    def _compute_precio(self):
        for record in self:
            if record.tipo_linea == 'cita' and record.cita_id:
                if record.cita_id.servicio_id:
                    record.precio_unitario = record.cita_id.servicio_id.precio
                else:
                    record.precio_unitario = 0.0
            elif record.tipo_linea == 'medicamento' and record.medicamento_id:
                record.precio_unitario = record.medicamento_id.precio_venta
            elif record.tipo_linea == 'producto' and record.producto_id:
                record.precio_unitario = record.producto_id.precio_venta
            elif record.tipo_linea == 'servicio' and record.servicio_id:
                record.precio_unitario = record.servicio_id.precio
            else:
                record.precio_unitario = 0.0
    
    @api.onchange('tipo_linea')
    def _onchange_tipo_linea(self):
        """Limpia campos cuando cambia el tipo"""
        self.cita_id = False
        self.medicamento_id = False
        self.producto_id = False
        self.servicio_id = False
        self.cantidad = 1.0
    
    @api.onchange('cita_id', 'medicamento_id', 'producto_id', 'servicio_id')
    def _onchange_documento(self):
        """Valida que solo un documento sea seleccionado"""
        selected_count = sum([
            bool(self.cita_id),
            bool(self.medicamento_id),
            bool(self.producto_id),
            bool(self.servicio_id),
        ])
        
        if selected_count > 1:
            raise ValidationError('Solo puede seleccionar un documento')
    
    def action_agregar_linea(self):
        """Agrega la línea de facturación"""
        self.ensure_one()
        
        if not self.precio_unitario:
            raise ValidationError('El precio unitario debe ser mayor a 0')
        
        # Crear la línea de facturación
        linea_vals = {
            'facturacion_id': self.facturacion_id.id,
            'tipo_linea': self.tipo_linea,
            'cita_id': self.cita_id.id if self.cita_id else False,
            'medicamento_id': self.medicamento_id.id if self.medicamento_id else False,
            'producto_id': self.producto_id.id if self.producto_id else False,
            'servicio_id': self.servicio_id.id if self.servicio_id else False,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'impuesto_id': [(6, 0, self.impuesto_id.ids)],
            'observaciones_linea': self.observaciones_linea,
        }
        
        self.env['veterinaria.facturacion.linea'].create(linea_vals)
        
        # Retornar acción para cerrar el wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'veterinaria.facturacion',
            'res_id': self.facturacion_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class FacturacionMultilineaWizard(models.TransientModel):
    _name = 'veterinaria.facturacion.multilinea.wizard'
    _description = 'Asistente para Agregar Múltiples Líneas'

    facturacion_id = fields.Many2one(
        'veterinaria.facturacion',
        string='Facturación',
        required=True
    )
    
    tipo_documento = fields.Selection([
        ('cita', 'Citas'),
        ('medicamento', 'Medicamentos'),
        ('producto', 'Productos'),
        ('servicio', 'Servicios'),
    ], string='Tipo de Documento', required=True)
    
    # Campos multi-selección
    cita_ids = fields.Many2many(
        'veterinaria.cita',
        'facturacion_wizard_cita_rel',
        string='Seleccionar Citas',
        domain=[('estado', '=', 'completada')]
    )
    
    medicamento_ids = fields.Many2many(
        'veterinaria.medicamento',
        'facturacion_wizard_medicamento_rel',
        string='Seleccionar Medicamentos',
        domain=[('activo', '=', True)]
    )
    
    producto_ids = fields.Many2many(
        'veterinaria.producto',
        'facturacion_wizard_producto_rel',
        string='Seleccionar Productos',
        domain=[('activo', '=', True)]
    )
    
    servicio_ids = fields.Many2many(
        'veterinaria.servicio',
        'facturacion_wizard_servicio_rel',
        string='Seleccionar Servicios',
        domain=[('activo', '=', True)]
    )
    
    cantidad_default = fields.Float('Cantidad por Defecto', default=1.0)
    
    def action_agregar_multiples_lineas(self):
        """Agrega múltiples líneas de facturación"""
        self.ensure_one()
        
        lineas_creadas = 0
        
        if self.tipo_documento == 'cita':
            for cita in self.cita_ids:
                if cita.servicio_id:
                    self.env['veterinaria.facturacion.linea'].create({
                        'facturacion_id': self.facturacion_id.id,
                        'tipo_linea': 'cita',
                        'cita_id': cita.id,
                        'cantidad': self.cantidad_default,
                        'precio_unitario': cita.servicio_id.precio,
                    })
                    lineas_creadas += 1
        
        elif self.tipo_documento == 'medicamento':
            for medicamento in self.medicamento_ids:
                self.env['veterinaria.facturacion.linea'].create({
                    'facturacion_id': self.facturacion_id.id,
                    'tipo_linea': 'medicamento',
                    'medicamento_id': medicamento.id,
                    'cantidad': self.cantidad_default,
                    'precio_unitario': medicamento.precio_venta,
                })
                lineas_creadas += 1
        
        elif self.tipo_documento == 'producto':
            for producto in self.producto_ids:
                self.env['veterinaria.facturacion.linea'].create({
                    'facturacion_id': self.facturacion_id.id,
                    'tipo_linea': 'producto',
                    'producto_id': producto.id,
                    'cantidad': self.cantidad_default,
                    'precio_unitario': producto.precio_venta,
                })
                lineas_creadas += 1
        
        elif self.tipo_documento == 'servicio':
            for servicio in self.servicio_ids:
                self.env['veterinaria.facturacion.linea'].create({
                    'facturacion_id': self.facturacion_id.id,
                    'tipo_linea': 'servicio',
                    'servicio_id': servicio.id,
                    'cantidad': self.cantidad_default,
                    'precio_unitario': servicio.precio,
                })
                lineas_creadas += 1
        
        # Retornar acción para cerrar el wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'veterinaria.facturacion',
            'res_id': self.facturacion_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
