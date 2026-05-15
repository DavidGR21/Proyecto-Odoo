# -*- coding: utf-8 -*-
from odoo import fields, models


class VeterinarioVeterinario(models.Model):
    _name = 'veterinaria.veterinario'
    _description = 'Veterinario'

    name = fields.Char(string='Nombre', required=True)
    especialidad_id = fields.Many2one('veterinaria.especialidad', string='Especialidad', required=True)
    matricula_profesional = fields.Char(string='Matrícula profesional')
    horario_inicio = fields.Selection([
        ('07:00', '07:00'),
        ('08:00', '08:00'),
        ('09:00', '09:00'),
        ('10:00', '10:00'),
        ('11:00', '11:00'),
        ('12:00', '12:00'),
        ('13:00', '13:00'),
        ('14:00', '14:00'),
        ('15:00', '15:00'),
        ('16:00', '16:00'),
        ('17:00', '17:00'),
        ('18:00', '18:00'),
        ('19:00', '19:00'),
    ], string='Hora de inicio')
    horario_fin = fields.Selection([
        ('07:00', '07:00'),
        ('08:00', '08:00'),
        ('09:00', '09:00'),
        ('10:00', '10:00'),
        ('11:00', '11:00'),
        ('12:00', '12:00'),
        ('13:00', '13:00'),
        ('14:00', '14:00'),
        ('15:00', '15:00'),
        ('16:00', '16:00'),
        ('17:00', '17:00'),
        ('18:00', '18:00'),
        ('19:00', '19:00'),
    ], string='Hora de fin')
    dias_disponibles = fields.Selection([
        ('lun_vie', 'Lunes a Viernes'),
        ('lun_sab', 'Lunes a Sabado'),
        ('sab_dom', 'Sabado y Domingo'),
        ('todos', 'Todos los dias'),
    ], string='Dias disponibles')
    observaciones_horario = fields.Text(string='Observaciones de horario')
    cita_ids = fields.One2many('veterinaria.cita', 'veterinario_id', string='Citas')
    cantidad_citas = fields.Integer(string='Cantidad de Citas', compute='_compute_cantidad_citas')

    def _compute_cantidad_citas(self):
        for record in self:
            record.cantidad_citas = len(record.cita_ids)