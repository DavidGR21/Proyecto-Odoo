# -*- coding: utf-8 -*-
from odoo import models, fields, api


class VentaProductos(models.Model):
    _name = 'veterinaria.venta'
    _description = 'Venta de Productos y Medicamentos'

    name = fields.Char('Nombre de la Venta', compute='_compute_name', store=True)
    
    # Link a sale.order
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        required=False,
        ondelete='cascade',
        readonly=True
    )
    
    propietario_id = fields.Many2one(
        'res.partner',
        string='Cliente (Propietario)',
        domain=[('es_propietario', '=', True)],
        required=True,
        ondelete='restrict'
    )
    
    paciente_id = fields.Many2one(
        'veterinaria.paciente',
        string='Mascota (Opcional)',
        ondelete='set null'
    )
    
    fecha_venta = fields.Date('Fecha de Venta', default=fields.Date.today)
    
    # Líneas de venta (productos/medicamentos)
    linea_venta_ids = fields.One2many(
        'veterinaria.venta.linea',
        'venta_id',
        string='Productos/Medicamentos'
    )
    
    total_sin_impuesto = fields.Float('Total sin Impuesto', compute='_compute_totales', store=True)
    impuesto_total = fields.Float('Total Impuesto', compute='_compute_totales', store=True)
    total = fields.Float('Total', compute='_compute_totales', store=True)
    
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('validado', 'Validado'),
        ('cancelado', 'Cancelado'),
    ], string='Estado', default='borrador')
    
    observaciones = fields.Text('Observaciones')
    
    @api.depends('linea_venta_ids.subtotal', 'linea_venta_ids.impuesto')
    def _compute_totales(self):
        for record in self:
            record.total_sin_impuesto = sum(line.subtotal for line in record.linea_venta_ids)
            record.impuesto_total = sum(line.impuesto for line in record.linea_venta_ids)
            record.total = record.total_sin_impuesto + record.impuesto_total
    
    @api.depends('propietario_id', 'fecha_venta')
    def _compute_name(self):
        for record in self:
            if record.propietario_id and record.fecha_venta:
                record.name = f"VTA-{record.propietario_id.name[:10]}-{record.fecha_venta.strftime('%Y%m%d')}"
            else:
                record.name = "Venta"
    
    def action_validar_venta(self):
        """Valida la venta y crea una orden de venta en Odoo"""
        for record in self:
            if record.estado != 'borrador':
                raise ValueError('Solo se pueden validar ventas en borrador')
            
            if not record.linea_venta_ids:
                raise ValueError('Debe agregar al menos un producto')
            
            # Crear líneas para sale.order
            order_lines = []
            for line in record.linea_venta_ids:
                product_id = None
                item_name = None
                
                # Determinar qué tipo de item es
                if line.producto_id:
                    item = line.producto_id
                    item_name = item.name
                    product_id = item.product_id
                elif line.medicamento_id:
                    item = line.medicamento_id
                    item_name = item.name
                
                # Si no tiene producto Odoo asociado, crear uno
                if not product_id:
                    # Obtener o crear categoría de producto por defecto
                    categ_id = self.env['product.category'].search([], limit=1)
                    if not categ_id:
                        categ_id = self.env['product.category'].create({'name': 'General'})
                    
                    # Crear el product.template primero
                    template = self.env['product.template'].create({
                        'name': item_name,
                        'categ_id': categ_id.id,
                    })
                    # El product.product se crea automáticamente
                    product_id = template.product_variant_ids[0]
                
                order_lines.append((0, 0, {
                    'product_id': product_id.id,
                    'product_uom_qty': line.cantidad,
                    'price_unit': line.precio_unitario,
                    'tax_id': [(6, 0, line.impuesto_id.ids)],
                }))
            
            # Crear sale.order
            sale_order = self.env['sale.order'].create({
                'partner_id': record.propietario_id.id,
                'order_line': order_lines,
                'date_order': record.fecha_venta,
            })
            
            record.sale_order_id = sale_order
            record.estado = 'validado'
    
    def action_cancelar_venta(self):
        """Cancela la venta"""
        for record in self:
            if record.sale_order_id:
                record.sale_order_id.action_cancel()
            record.estado = 'cancelado'


class VentaLinea(models.Model):
    _name = 'veterinaria.venta.linea'
    _description = 'Línea de Venta'

    venta_id = fields.Many2one('veterinaria.venta', string='Venta', ondelete='cascade', required=True)
    
    # Campos separados para producto y medicamento
    producto_id = fields.Many2one(
        'veterinaria.producto',
        string='Producto',
        ondelete='restrict'
    )
    
    medicamento_id = fields.Many2one(
        'veterinaria.medicamento',
        string='Medicamento',
        ondelete='restrict'
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
    
    @api.depends('cantidad', 'precio_unitario')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.cantidad * record.precio_unitario
    
    @api.depends('subtotal', 'impuesto_id')
    def _compute_impuesto(self):
        for record in self:
            # Calcular impuesto basado en tasas
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
    
    @api.constrains('producto_id', 'medicamento_id')
    def _check_item_selected(self):
        """Valida que solo uno de los dos campos esté seleccionado"""
        for record in self:
            if not record.producto_id and not record.medicamento_id:
                raise ValueError('Debe seleccionar un producto o medicamento')
            if record.producto_id and record.medicamento_id:
                raise ValueError('Solo puede seleccionar uno: producto O medicamento')
    
    @api.onchange('producto_id', 'medicamento_id')
    def _onchange_item(self):
        """Al seleccionar un producto o medicamento, carga su precio"""
        if self.producto_id:
            self.medicamento_id = False
            self.precio_unitario = self.producto_id.precio_venta
        elif self.medicamento_id:
            self.producto_id = False
            self.precio_unitario = self.medicamento_id.precio_venta
