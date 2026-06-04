# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ServicioVeterinario(models.Model):
    _name = 'veterinaria.servicio'
    _description = 'Servicio Veterinario'

    name = fields.Char('Nombre del Servicio', required=True)
    
    # Descripción del servicio
    descripcion = fields.Text('Descripción del Servicio')
   
    # Precio del servicio
    precio = fields.Float('Precio del Servicio', required=True)
    
    # Estado
    activo = fields.Boolean('Activo', default=True)

    # Impuestos
    impuesto_ids = fields.Many2many(
        'account.tax',
        'veterinaria_servicio_tax_rel',
        'servicio_id',
        'tax_id',
        string='Impuestos',
        domain=[('type_tax_use', '=', 'sale')]
    )
