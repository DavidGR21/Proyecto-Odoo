# -*- coding: utf-8 -*-
from odoo import models, fields

class VeterinariaSintoma(models.Model):
    _name = 'veterinaria.sintoma'
    _description = 'Síntomas para la Cita'

    name = fields.Char(string='Nombre', required=True)
