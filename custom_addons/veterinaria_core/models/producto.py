# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductoVeterinario(models.Model):
    _name = 'veterinaria.producto'
    _description = 'Producto Veterinario'

    name = fields.Char('Nombre del Producto', required=True)
    categoria = fields.Selection([
        ('medicamento', 'Medicamento'),
        ('alimento', 'Alimento'),
        ('accesorio', 'Accesorio'),
        ('equipo', 'Equipo Médico'),
        ('servicio', 'Servicio'),
    ], string='Categoría', required=True)
    
    descripcion = fields.Text('Descripción')
    precio_venta = fields.Float('Precio de Venta', required=True)
    precio_costo = fields.Float('Precio de Costo')
    
    # Inventario
    cantidad_stock = fields.Float('Stock Disponible', default=0.0)
    cantidad_minima = fields.Float('Stock Mínimo', default=5.0)
    unidad_medida = fields.Selection([
        ('unidad', 'Unidad'),
        ('kg', 'Kilogramo'),
        ('l', 'Litro'),
        ('ml', 'Mililitro'),
        ('caja', 'Caja'),
    ], string='Unidad de Medida', default='unidad')
    
    # Para medicamentos
    principio_activo = fields.Char('Principio Activo')
    dosis = fields.Char('Dosis')
    via_administracion = fields.Selection([
        ('oral', 'Oral'),
        ('intramuscular', 'Intramuscular'),
        ('intravenosa', 'Intravenosa'),
        ('topica', 'Tópica'),
        ('oftalmologica', 'Oftalmológica'),
    ], string='Vía de Administración')
    
    # Proveedor
    proveedor_id = fields.Many2one('res.partner', string='Proveedor',
                                    domain=[('supplier_rank', '>', 0)])
    product_id = fields.Many2one('product.product', string='Producto Odoo', help='Vincula con el producto del inventario')
    
    # Control
    activo = fields.Boolean('Activo', default=True)
    impuesto_id = fields.Many2many('account.tax', string='Impuestos')
    margen_ganancia = fields.Float('Margen de Ganancia (%)', compute='_compute_margen')

    def _compute_margen(self):
        for record in self:
            if record.precio_costo > 0:
                margen = ((record.precio_venta - record.precio_costo) / record.precio_costo) * 100
                record.margen_ganancia = margen
            else:
                record.margen_ganancia = 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            if record.product_id:
                # Sincronizar precios y stock básicos desde el producto Odoo si están disponibles
                try:
                    if record.product_id.lst_price:
                        record.precio_venta = record.product_id.lst_price
                except Exception:
                    pass
                try:
                    if record.product_id.standard_price:
                        record.precio_costo = record.product_id.standard_price
                except Exception:
                    pass
                try:
                    # qty_available está disponible cuando stock está instalado
                    qty = getattr(record.product_id, 'qty_available', None)
                    if qty is not None:
                        record.cantidad_stock = qty
                except Exception:
                    pass
