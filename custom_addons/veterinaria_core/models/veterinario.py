# -*- coding: utf-8 -*-
from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    es_veterinario = fields.Boolean(string='Es veterinario', default=False)
    especialidad = fields.Char(string='Especialidad')
    matricula_profesional = fields.Char(string='Matrícula profesional')
    cita_ids = fields.One2many('veterinaria.cita', 'veterinario_id', string='Citas')
    cantidad_citas = fields.Integer(string='Cantidad de Citas', compute='_compute_cantidad_citas')

    def _compute_cantidad_citas(self):
        for record in self:
            record.cantidad_citas = len(record.cita_ids)