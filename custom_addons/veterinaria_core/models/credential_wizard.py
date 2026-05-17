# -*- coding: utf-8 -*-
from odoo import fields, models


class VeterinariaCredentialWizard(models.TransientModel):
    _name = 'veterinaria.credential.wizard'
    _description = 'Credenciales temporales de acceso al portal'

    partner_name = fields.Char(string='Cliente', readonly=True)
    login = fields.Char(string='Login (email)', readonly=True)
    password = fields.Char(string='Contraseña temporal', readonly=True)
