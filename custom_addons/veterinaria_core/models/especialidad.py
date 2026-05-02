# -*- coding: utf-8 -*-
from odoo import fields, models


class VeterinariaEspecialidad(models.Model):
    _name = 'veterinaria.especialidad'
    _description = 'Especialidad Veterinaria'

    name = fields.Char(string='Especialidad', required=True)
    descripcion = fields.Text(string='Descripción')
