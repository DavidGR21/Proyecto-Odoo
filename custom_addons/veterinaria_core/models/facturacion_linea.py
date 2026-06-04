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
        domain=[('estado', '=', 'completada'), ('facturada', '=', False)]
    )

    inventario_id = fields.Many2one(
        'veterinaria.inventario',
        string='Item de Inventario',
        domain="[('tipo_inventario', '=', tipo_linea), ('activo', '=', True), '|', ('tipo_inventario', '=', 'servicio'), ('cantidad_stock', '>', 0)]"
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

    impuesto_ids = fields.Many2many(
        'account.tax',
        string='Impuestos',
        domain=[('type_tax_use', '=', 'sale')]
    )
    impuesto_linea = fields.Float('Monto Impuesto', compute='_compute_linea_totales', store=True)
    total_linea = fields.Float('Total Línea', compute='_compute_linea_totales', store=True)

    @api.depends('subtotal', 'impuesto_ids', 'cantidad', 'precio_unitario')
    def _compute_linea_totales(self):
        for rec in self:
            subtotal = rec.cantidad * rec.precio_unitario
            impuesto_total = 0.0
            if rec.impuesto_ids:
                # Usar la función estándar de Odoo para calcular impuestos de forma robusta
                currency = rec.env.company.currency_id
                taxes_res = rec.impuesto_ids.compute_all(
                    rec.precio_unitario,
                    quantity=rec.cantidad,
                    currency=currency,
                    product=None,
                    partner=rec.facturacion_id.propietario_id if rec.facturacion_id else None
                )
                impuesto_total = sum(t['amount'] for t in taxes_res['taxes'])
            rec.impuesto_linea = impuesto_total
            rec.total_linea = subtotal + impuesto_total

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
                self.impuesto_ids = [(6, 0, self.item_ref.impuesto_id.ids)]
            elif self.item_ref._name == 'veterinaria.cita':
                self.cita_id = self.item_ref.id
                self.tipo_linea = 'cita'
                if self.item_ref.servicio_id:
                    self.precio_unitario = self.item_ref.servicio_id.precio or 0.0
                if self.item_ref.impuesto_ids:
                    self.impuesto_ids = [(6, 0, self.item_ref.impuesto_ids.ids)]
                elif self.item_ref.servicio_id and self.item_ref.servicio_id.impuesto_ids:
                    self.impuesto_ids = [(6, 0, self.item_ref.servicio_id.impuesto_ids.ids)]
                else:
                    tax_15 = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', 15.0)], limit=1)
                    self.impuesto_ids = [(6, 0, tax_15.ids)] if tax_15 else [(5, 0, 0)]

    @api.onchange('tipo_linea')
    def _onchange_tipo_linea(self):
        self.cita_id = False
        self.inventario_id = False
        self.precio_unitario = 0.0
        self.cantidad = 1.0
        self.impuesto_ids = [(5, 0, 0)]

    @api.onchange('cita_id')
    def _onchange_cita_id(self):
        if self.tipo_linea == 'cita' and self.cita_id:
            servicio = self.cita_id.servicio_id
            self.precio_unitario = servicio.precio if servicio else 0.0
            self.cantidad = 1.0
            if self.cita_id.impuesto_ids:
                self.impuesto_ids = [(6, 0, self.cita_id.impuesto_ids.ids)]
            elif servicio and servicio.impuesto_ids:
                self.impuesto_ids = [(6, 0, servicio.impuesto_ids.ids)]
            else:
                tax_15 = self.env['account.tax'].search([('type_tax_use', '=', 'sale'), ('amount', '=', 15.0)], limit=1)
                self.impuesto_ids = [(6, 0, tax_15.ids)] if tax_15 else [(5, 0, 0)]

    @api.onchange('inventario_id')
    def _onchange_inventario_id(self):
        if self.tipo_linea in ('medicamento', 'producto', 'servicio') and self.inventario_id:
            self.precio_unitario = self.inventario_id.precio_venta or 0.0
            self.cantidad = 1.0
            self.impuesto_ids = [(6, 0, self.inventario_id.impuesto_id.ids)]

    @api.onchange('precio_unitario')
    def _onchange_precio_unitario(self):
        if self.tipo_linea in ('medicamento', 'producto', 'servicio') and self.inventario_id:
            self.precio_unitario = self.inventario_id.precio_venta or 0.0

    @api.onchange('cantidad', 'inventario_id', 'tipo_linea')
    def _onchange_cantidad(self):
        if self.tipo_linea in ('medicamento', 'producto') and self.inventario_id:
            if self.inventario_id.cantidad_stock < self.cantidad:
                raise ValidationError(
                    f"Stock insuficiente para '{self.inventario_id.name}': "
                    f"disponible {self.inventario_id.cantidad_stock}, solicitado {self.cantidad}\n"
                    "Actualice el stock en inventario para continuar en la factura."
                )

    # ── Constraints ───────────────────────────────────────────────────────────

    def _validate_stock_vals(self, vals):
        tipo_linea = vals.get('tipo_linea', self.tipo_linea)
        inventario_id = vals.get('inventario_id', self.inventario_id.id if self.inventario_id else False)
        cantidad = vals.get('cantidad', self.cantidad)
        if tipo_linea in ('medicamento', 'producto') and inventario_id:
            inventario = self.env['veterinaria.inventario'].browse(inventario_id)
            if inventario and inventario.cantidad_stock < cantidad:
                raise ValidationError(
                    f"Stock insuficiente para '{inventario.name}': "
                    f"disponible {inventario.cantidad_stock}, solicitado {cantidad}\n"
                    "Actualice el stock en inventario antes de importar a factura."
                )

    def _check_stock_disponible(self):
        for rec in self:
            if rec.tipo_linea in ('medicamento', 'producto') and rec.inventario_id:
                if rec.inventario_id.cantidad_stock < rec.cantidad:
                    raise ValidationError(
                        f"Stock insuficiente para '{rec.inventario_id.name}': "
                        f"disponible {rec.inventario_id.cantidad_stock}, solicitado {rec.cantidad}\n"
                        "Actualice el stock en inventario antes de importar a factura."
                    )

    @api.constrains('tipo_linea', 'cita_id', 'inventario_id', 'cantidad', 'precio_unitario')
    def _check_linea(self):
        for rec in self:
            if rec.cantidad <= 0:
                raise ValidationError("La cantidad debe ser mayor a 0")
            rec._check_stock_disponible()
            if rec.tipo_linea in ('medicamento', 'producto', 'servicio') and rec.inventario_id:
                expected_price = rec.inventario_id.precio_venta or 0.0
                if abs((rec.precio_unitario or 0.0) - expected_price) > 0.000001:
                    raise ValidationError("El precio unitario debe coincidir con el precio de inventario")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._validate_stock_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            rec._validate_stock_vals(vals)
        return super().write(vals)