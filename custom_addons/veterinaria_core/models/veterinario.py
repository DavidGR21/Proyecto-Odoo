# -*- coding: utf-8 -*-
from odoo import fields, models


class VeterinarioVeterinario(models.Model):
    _name = 'veterinaria.veterinario'
    _description = 'Veterinario'

    name = fields.Char(string='Nombre', required=True)
    especialidad_id = fields.Many2one('veterinaria.especialidad', string='Especialidad', required=True)
    matricula_profesional = fields.Char(string='Matrícula profesional')
    cita_ids = fields.One2many('veterinaria.cita', 'veterinario_id', string='Citas')
    cantidad_citas = fields.Integer(string='Cantidad de Citas', compute='_compute_cantidad_citas')

    def _compute_cantidad_citas(self):
        for record in self:
            record.cantidad_citas = len(record.cita_ids)