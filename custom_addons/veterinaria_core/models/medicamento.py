# -*- coding: utf-8 -*-
from odoo import models, fields


class Medicamento(models.Model):
    _name = 'veterinaria.medicamento'
    _description = 'Medicamento'

    name = fields.Char('Nombre del Medicamento', required=True)
    principio_activo = fields.Char('Principio Activo')
    tipo = fields.Selection([
        ('comprimido', 'Comprimido'),
        ('jarabe', 'Jarabe'),
        ('inyectable', 'Inyectable'),
        ('crema', 'Crema'),
        ('polvo', 'Polvo'),
        ('otro', 'Otro'),
    ], string='Tipo', required=True)
    dosis_recomendada = fields.Char('Dosis Recomendada')
    via_administracion = fields.Selection([
        ('oral', 'Oral'),
        ('intramuscular', 'Intramuscular'),
        ('intravenosa', 'Intravenosa'),
        ('topica', 'Tópica'),
        ('oftalmologica', 'Oftalmológica'),
    ], string='Vía de Administración')
    
    # Información del medicamento
    descripcion = fields.Text('Descripción')
    contraindicaciones = fields.Text('Contraindicaciones')
    efectos_secundarios = fields.Text('Efectos Secundarios')
    
    # Proveedor
    proveedor_id = fields.Many2one('res.partner', string='Proveedor',
                                    domain=[('supplier_rank', '>', 0)])
    
    # Control
    activo = fields.Boolean('Activo', default=True)
    fecha_registro = fields.Date('Fecha de Registro', default=fields.Date.today, readonly=True)
