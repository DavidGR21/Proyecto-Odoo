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


class ImportarRecetaWizard(models.TransientModel):
    """Wizard para importar medicamentos de una receta a la factura."""
    _name = 'veterinaria.importar.receta.wizard'
    _description = 'Asistente para Importar Receta'

    facturacion_id = fields.Many2one(
        'veterinaria.facturacion',
        string='Facturacion',
        required=True
    )

    propietario_id = fields.Many2one(
        'res.partner',
        string='Propietario',
        readonly=True
    )

    cita_id = fields.Many2one(
        'veterinaria.cita',
        string='Seleccionar Cita/Receta',
        required=True,
    )

    @api.onchange('facturacion_id')
    def _onchange_facturacion_id(self):
        """Filtra cita_id para mostrar solo las citas ya presentes en la factura."""
        if self.facturacion_id:
            citas_ya_en_factura = self.facturacion_id.linea_ids.filtered(lambda l: l.tipo_linea == 'cita' and l.cita_id).mapped('cita_id')
            return {'domain': {'cita_id': [('id', 'in', citas_ya_en_factura.ids)]}}

    linea_ids = fields.One2many(
        'veterinaria.importar.receta.wizard.linea',
        'wizard_id',
        string='Medicamentos a Importar'
    )

    @api.onchange('cita_id')
    def _onchange_cita_id(self):
        """Carga las lineas de la receta filtrando solo las de inventario."""
        # Limpiar lineas anteriores
        self.linea_ids = [(5, 0, 0)]
        if self.cita_id:
            lineas_wizard = []
            # Recorrer todas las recetas vinculadas a la cita
            for receta in self.cita_id.receta_ids:
                for linea in receta.linea_ids:
                    # Filtro estricto: Solo medicamentos del inventario
                    if linea.tipo_origen == 'inventario' and linea.medicamento_id:
                        lineas_wizard.append((0, 0, {
                            'medicamento_id': linea.medicamento_id.id, # ID explícito
                            'cantidad_a_facturar': linea.cantidad_total,
                        }))
            self.linea_ids = lineas_wizard

    def action_confirmar_importacion(self):
        """Crea las lineas en la factura usando item_ref y precio unitario."""
        self.ensure_one()
        if not self.linea_ids:
            raise ValidationError("No hay medicamentos seleccionados para importar. Verifique que la cita tenga una receta con medicamentos de inventario.")
        
        lineas_creadas = 0
        for linea in self.linea_ids:
            if linea.cantidad_a_facturar > 0 and linea.medicamento_id:
                # Obtenemos el item de inventario para sacar el precio
                item = linea.medicamento_id
                self.env['veterinaria.facturacion.linea'].create({
                    'facturacion_id': self.facturacion_id.id,
                    'tipo_linea': 'medicamento',
                    'item_ref': f'veterinaria.inventario,{item.id}',
                    'inventario_id': item.id,
                    'cantidad': linea.cantidad_a_facturar,
                    'precio_unitario': item.precio_venta or 0.0,
                })
                lineas_creadas += 1
        
        if lineas_creadas == 0:
            raise ValidationError("No se pudo importar ninguna línea. Asegúrese de que las cantidades sean mayores a cero.")
            
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class ImportarRecetaWizardLinea(models.TransientModel):
    _name = 'veterinaria.importar.receta.wizard.linea'
    _description = 'Linea de Asistente para Importar Receta'

    wizard_id = fields.Many2one('veterinaria.importar.receta.wizard', string='Wizard')
    medicamento_id = fields.Many2one('veterinaria.inventario', string='Medicamento')
    cantidad_a_facturar = fields.Float('Cantidad a Facturar')
