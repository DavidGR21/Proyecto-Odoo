# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class InventarioVeterinario(models.Model):
    _name = 'veterinaria.inventario'
    _description = 'Inventario Veterinario (Productos, Servicios y Medicamentos)'

    # Campo tipo para seleccionar entre producto, servicio o medicamento
    tipo_inventario = fields.Selection([
        ('producto', 'Producto'),
        ('servicio', 'Servicio'),
        ('medicamento', 'Medicamento'),
    ], string='Tipo de Inventario', required=True)

    # Campos comunes
    name = fields.Char('Nombre', required=True)
    descripcion = fields.Text('Descripción')
    activo = fields.Boolean('Activo', default=True)

    # Campos de precios (comunes para todos)
    precio_venta = fields.Float('Precio de Venta', required=True)
    precio_costo = fields.Float('Precio de Costo')
    proveedor_id = fields.Many2one('res.partner', string='Proveedor',
                                    domain=[('supplier_rank', '>', 0)])
    veterinario_servicio_id = fields.Many2one('veterinaria.veterinario', 
                                              string='Veterinario Responsable')

    # Campos específicos para Producto
    categoria = fields.Selection([
        ('comida', 'Comida'),
        ('accesorios', 'Accesorios'),
        ('ropa', 'Ropa'),
        ('juguetes', 'Juguetes'),
        ('higiene', 'Higiene y Cuidado'),
    ], string='Categoría del Producto')
    
    # Campos específicos para Servicio
    categoria_servicio = fields.Selection([
        ('peluqueria', 'Peluquería/Grooming'),
        ('operaciones', 'Operaciones/Cirugía'),
        ('consulta', 'Consulta General'),
        ('vacunacion', 'Vacunación'),
        ('laboratorio', 'Laboratorio/Análisis'),
        ('radiologia', 'Radiología/Imagenología'),
        ('odontologia', 'Odontología'),
        ('bano', 'Baño y Aseo'),
        ('otros', 'Otros Servicios'),
    ], string='Categoría del Servicio')
    
    cantidad_stock = fields.Float('Stock Disponible', default=0.0)
    cantidad_minima = fields.Float('Stock Mínimo', default=5.0)
    unidad_medida = fields.Selection([
        ('unidad', 'Unidad'),
        ('kg', 'Kilogramo'),
        ('l', 'Litro'),
        ('ml', 'Mililitro'),
        ('caja', 'Caja'),
    ], string='Unidad de Medida', default='unidad')
    
    impuesto_id = fields.Many2many('account.tax', string='Impuestos')
    margen_ganancia = fields.Float('Margen de Ganancia (%)', compute='_compute_margen')

    # Campos específicos para Medicamento
    principio_activo = fields.Char('Principio Activo')
    tipo_medicamento = fields.Selection([
        ('comprimido', 'Comprimido'),
        ('jarabe', 'Jarabe'),
        ('inyectable', 'Inyectable'),
        ('crema', 'Crema'),
        ('polvo', 'Polvo'),
        ('otro', 'Otro'),
    ], string='Tipo de Medicamento')
    
    dosis = fields.Char('Dosis')
    dosis_recomendada = fields.Char('Dosis Recomendada')
    via_administracion = fields.Selection([
        ('oral', 'Oral'),
        ('intramuscular', 'Intramuscular'),
        ('intravenosa', 'Intravenosa'),
        ('topica', 'Tópica'),
        ('oftalmologica', 'Oftalmológica'),
    ], string='Vía de Administración')
    
    contraindicaciones = fields.Text('Contraindicaciones')
    efectos_secundarios = fields.Text('Efectos Secundarios')
    fecha_registro = fields.Date('Fecha de Registro', default=fields.Date.today, readonly=True)

    @api.depends('precio_venta', 'precio_costo')
    def _compute_margen(self):
        for record in self:
            if record.precio_costo > 0:
                margen = ((record.precio_venta - record.precio_costo) / record.precio_costo) * 100
                record.margen_ganancia = margen
            else:
                record.margen_ganancia = 0.0

    @api.onchange('precio_venta', 'precio_costo')
    def _onchange_precios(self):
        for record in self:
            if record.precio_costo > 0:
                margen = ((record.precio_venta - record.precio_costo) / record.precio_costo) * 100
                record.margen_ganancia = margen
            else:
                record.margen_ganancia = 0.0

    @api.constrains('tipo_inventario', 'categoria_servicio')
    def _check_categoria_servicio(self):
        for record in self:
            if record.tipo_inventario == 'servicio' and not record.categoria_servicio:
                raise ValidationError('Debe seleccionar una Categoría del Servicio')

    @api.constrains('precio_venta', 'precio_costo', 'cantidad_stock')
    def _check_no_negative_values(self):
        for record in self:
            if record.precio_venta is not False and record.precio_venta < 0:
                raise ValidationError('El precio de venta no puede ser menor a 0')
            if record.precio_costo is not False and record.precio_costo < 0:
                raise ValidationError('El precio de costo no puede ser menor a 0')
            if record.cantidad_stock is not False and record.cantidad_stock < 0:
                raise ValidationError('El stock no puede ser menor a 0')
