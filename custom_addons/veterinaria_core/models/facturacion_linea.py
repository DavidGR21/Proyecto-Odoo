# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FacturacionLinea(models.Model):
    _name = 'veterinaria.facturacion.linea'
    _description = 'Linea de Facturacion Multiservicio'

    facturacion_id = fields.Many2one(
        'veterinaria.facturacion',
        string='Facturacion',
        ondelete='cascade',
        required=True
    )

    # ── Campos de Seleccion ───────────────────────────────────────────────────
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

    # Columna unificada para seleccion (Reference)
    item_ref = fields.Reference([
        ('veterinaria.cita', 'Cita Veterinaria'),
        ('veterinaria.inventario', 'Inventario'),
    ], string='Item (Ref)')

    # Campo calculado para mostrar en la lista de forma unificada
    nombre_item = fields.Char(
        string='Item',
        compute='_compute_nombre_item',
        store=True
    )

    cantidad = fields.Float('Cantidad', default=1.0, required=True)
    precio_unitario = fields.Float('Precio Unitario', required=True)

    subtotal = fields.Float('Subtotal', compute='_compute_subtotal', store=True)
    descripcion = fields.Char('Descripcion', compute='_compute_descripcion', store=True)

    # ── Computes ──────────────────────────────────────────────────────────────

    @api.depends('tipo_linea', 'cita_id', 'inventario_id', 'item_ref')
    def _compute_nombre_item(self):
        for rec in self:
            if rec.item_ref:
                rec.nombre_item = rec.item_ref.display_name
            elif rec.tipo_linea == 'cita' and rec.cita_id:
                rec.nombre_item = rec.cita_id.name
            elif rec.tipo_linea in ('medicamento', 'producto', 'servicio') and rec.inventario_id:
                rec.nombre_item = rec.inventario_id.name
            else:
                rec.nombre_item = ''

    @api.depends('cantidad', 'precio_unitario')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.cantidad * rec.precio_unitario

    @api.depends('tipo_linea', 'cita_id', 'inventario_id', 'cantidad', 'item_ref')
    def _compute_descripcion(self):
        for rec in self:
            if rec.item_ref:
                rec.descripcion = f"{rec.item_ref.display_name} (x{rec.cantidad})"
            elif rec.tipo_linea == 'cita' and rec.cita_id:
                motivo = rec.cita_id.motivo or ''
                rec.descripcion = f"Cita - {motivo} (x{rec.cantidad})"
            elif rec.tipo_linea in ('medicamento', 'producto', 'servicio') and rec.inventario_id:
                tipo_str = rec.tipo_linea.capitalize()
                rec.descripcion = f"{tipo_str} - {rec.inventario_id.name} (x{rec.cantidad})"
            else:
                rec.descripcion = ''

    # ── Onchanges ─────────────────────────────────────────────────────────────

    @api.onchange('item_ref')
    def _onchange_item_ref(self):
        if self.item_ref:
            # Si es inventario, intentar sacar el precio
            if self.item_ref._name == 'veterinaria.inventario':
                self.precio_unitario = self.item_ref.precio_venta or 0.0
                self.inventario_id = self.item_ref.id
                self.tipo_linea = self.item_ref.tipo_inventario
            elif self.item_ref._name == 'veterinaria.cita':
                self.cita_id = self.item_ref.id
                self.tipo_linea = 'cita'
                if self.item_ref.servicio_id:
                    self.precio_unitario = self.item_ref.servicio_id.precio or 0.0

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
            self.precio_unitario = servicio.precio if servicio else 0.0
            self.cantidad = 1.0

    @api.onchange('inventario_id')
    def _onchange_inventario_id(self):
        if self.tipo_linea in ('medicamento', 'producto') and self.inventario_id:
            self.precio_unitario = self.inventario_id.precio_venta or 0.0
            self.cantidad = 1.0
        elif self.tipo_linea == 'servicio' and self.inventario_id:
            self.precio_unitario = self.inventario_id.precio_venta or 0.0
            self.cantidad = 1.0

    # ── Constraints ───────────────────────────────────────────────────────────

    @api.constrains('tipo_linea', 'cita_id', 'inventario_id', 'cantidad', 'precio_unitario')
    def _check_linea(self):
        for rec in self:
            if rec.cantidad <= 0:
                raise ValidationError("La cantidad debe ser mayor a 0")