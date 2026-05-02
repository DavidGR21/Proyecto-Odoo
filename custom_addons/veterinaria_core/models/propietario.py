# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    es_propietario = fields.Boolean(string='Es propietario de mascota', default=False)
    observaciones_veterinaria = fields.Text(string='Observaciones veterinarias')
    paciente_ids = fields.One2many('veterinaria.paciente', 'propietario_id', string='Mascotas')
    cantidad_mascotas = fields.Integer(string='Cantidad de Mascotas', compute='_compute_cantidad_mascotas')

    def _compute_cantidad_mascotas(self):
        for record in self:
            record.cantidad_mascotas = len(record.paciente_ids)