# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FacturacionLinea(models.Model):
    _name = 'veterinaria.facturacion.linea'
    _description = 'Línea de Facturación Multiservicio'

    facturacion_id = fields.Many2one(
        'veterinaria.facturacion',
        string='Facturación',
        ondelete='cascade',
        required=True
    )
    
    # Tipo de documento de la línea
    tipo_linea = fields.Selection([
        ('cita', 'Cita Veterinaria'),
        ('medicamento', 'Medicamento'),
        ('producto', 'Producto'),
        ('servicio', 'Servicio'),
    ], string='Tipo de Documento', required=True, tracking=True)
    
    # Campos para cada tipo de documento
    cita_id = fields.Many2one(
        'veterinaria.cita',
        string='Cita',
        ondelete='restrict',
        domain=[('estado', '=', 'completada')]
    )
    
    servicio_id = fields.Many2one(
        'veterinaria.inventario',
        string='Servicio',
        ondelete='restrict',
        domain=[('tipo_inventario', '=', 'servicio'), ('activo', '!=', False)]
    )

    producto_id = fields.Many2one(
        'veterinaria.inventario',
        string='Producto',
        ondelete='restrict',
        domain=[('tipo_inventario', '=', 'producto'), ('activo', '!=', False), ('cantidad_stock', '>', 0)]
    )
    
    medicamento_id = fields.Many2one(
        'veterinaria.inventario',
        string='Medicamento',
        ondelete='restrict',
        domain=[('tipo_inventario', '=', 'medicamento'), ('activo', '!=', False), ('cantidad_stock', '>', 0)]
    )
    
    cantidad = fields.Float('Cantidad', required=True, default=1.0)
    precio_unitario = fields.Float('Precio Unitario', required=True)
    
    impuesto_id = fields.Many2many(
        'account.tax',
        string='Impuestos',
        domain=[('type_tax_use', '=', 'sale')]
    )
    
    subtotal = fields.Float('Subtotal', compute='_compute_subtotal', store=True)
    impuesto = fields.Float('Impuesto', compute='_compute_impuesto', store=True)
    total_linea = fields.Float('Total Línea', compute='_compute_total_linea', store=True)
    
    # Descripción para la factura
    descripcion = fields.Char('Descripción', compute='_compute_descripcion', store=True)
    
    # Información adicional según el tipo
    observaciones_linea = fields.Text('Observaciones de la Línea')
    
    @api.depends('cantidad', 'precio_unitario')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.cantidad * record.precio_unitario
    
    @api.depends('subtotal', 'impuesto_id')
    def _compute_impuesto(self):
        for record in self:
            impuesto_total = 0
            for tax in record.impuesto_id:
                if tax.amount_type == 'percent':
                    impuesto_total += (record.subtotal * tax.amount) / 100
                elif tax.amount_type == 'fixed':
                    impuesto_total += tax.amount
            record.impuesto = impuesto_total
    
    @api.depends('subtotal', 'impuesto')
    def _compute_total_linea(self):
        for record in self:
            record.total_linea = record.subtotal + record.impuesto
    
    @api.depends('cita_id', 'servicio_id', 'producto_id', 'medicamento_id', 'cantidad', 'tipo_linea')
    def _compute_descripcion(self):
        for record in self:
            if record.tipo_linea == 'cita' and record.cita_id:
                record.descripcion = f"Cita - {record.cita_id.motivo} (x{record.cantidad})"
            elif record.tipo_linea == 'servicio' and record.servicio_id:
                record.descripcion = f"Servicio - {record.servicio_id.name} (x{record.cantidad})"
            elif record.tipo_linea == 'producto' and record.producto_id:
                record.descripcion = f"Producto - {record.producto_id.name} (x{record.cantidad})"
            elif record.tipo_linea == 'medicamento' and record.medicamento_id:
                record.descripcion = f"Medicamento - {record.medicamento_id.name} (x{record.cantidad})"
            else:
                record.descripcion = f"Artículo (x{record.cantidad})"
    
    @api.constrains('tipo_linea', 'cita_id', 'servicio_id', 'producto_id', 'medicamento_id')
    def _check_tipo_documento_consistency(self):
        """Valida que solo un tipo de documento esté seleccionado"""
        for record in self:
            selected_count = sum([
                bool(record.cita_id),
                bool(record.servicio_id),
                bool(record.producto_id),
                bool(record.medicamento_id),
            ])
            
            if selected_count == 0:
                raise ValidationError('Debe seleccionar un documento según el tipo de línea')
            elif selected_count > 1:
                raise ValidationError('Solo puede seleccionar un documento por línea')
            
            # Validar que coincida con el tipo_linea
            if record.tipo_linea == 'cita' and not record.cita_id:
                raise ValidationError('Debe seleccionar una Cita')
            elif record.tipo_linea == 'servicio' and not record.servicio_id:
                raise ValidationError('Debe seleccionar un Servicio')
            elif record.tipo_linea == 'producto' and not record.producto_id:
                raise ValidationError('Debe seleccionar un Producto')
            elif record.tipo_linea == 'medicamento' and not record.medicamento_id:
                raise ValidationError('Debe seleccionar un Medicamento')
    
    @api.onchange('tipo_linea')
    def _onchange_tipo_linea(self):
        """Limpia campos cuando cambia el tipo de línea"""
        self.cita_id = False
        self.servicio_id = False
        self.producto_id = False
        self.medicamento_id = False
        self.precio_unitario = 0.0
        self.cantidad = 1.0
    
    @api.onchange('cita_id')
    def _onchange_cita_id(self):
        if self.cita_id:
            self.tipo_linea = 'cita'
            # Limpiar otros campos
            self.servicio_id = False
            self.producto_id = False
            self.medicamento_id = False
            # Obtener precio del servicio principal de la cita
            if self.cita_id.servicio_id:
                self.precio_unitario = self.cita_id.servicio_id.precio
            self.cantidad = 1.0
    
    @api.onchange('servicio_id')
    def _onchange_servicio_id(self):
        if self.servicio_id:
            self.tipo_linea = 'servicio'
            self.cita_id = False
            self.producto_id = False
            self.medicamento_id = False
            self.precio_unitario = self.servicio_id.precio_venta
            self.cantidad = 1.0
    
    @api.onchange('producto_id')
    def _onchange_producto_id(self):
        if self.producto_id:
            self.tipo_linea = 'producto'
            self.cita_id = False
            self.servicio_id = False
            self.medicamento_id = False
            self.precio_unitario = self.producto_id.precio_venta
            # Usar stock disponible como cantidad por defecto (máximo 1)
            self.cantidad = 1.0
    
    @api.onchange('medicamento_id')
    def _onchange_medicamento_id(self):
        if self.medicamento_id:
            self.tipo_linea = 'medicamento'
            self.cita_id = False
            self.servicio_id = False
            self.producto_id = False
            self.precio_unitario = self.medicamento_id.precio_venta
            self.cantidad = 1.0
    
    def _get_detail_fields(self):
        """Retorna los campos de detalle según el tipo de línea"""
        return {
            'cita': ['cita_id', 'cantidad'],
            'medicamento': ['medicamento_id', 'cantidad', 'observaciones_linea'],
            'producto': ['producto_id', 'cantidad', 'observaciones_linea'],
            'servicio': ['servicio_id', 'cantidad', 'observaciones_linea'],
        }