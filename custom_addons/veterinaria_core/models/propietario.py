# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    es_propietario = fields.Boolean(string='Es propietario de mascota', default=False)
    observaciones_veterinaria = fields.Text(string='Observaciones veterinarias')
    paciente_ids = fields.One2many('veterinaria.paciente', 'propietario_id', string='Mascotas')
    cantidad_mascotas = fields.Integer(string='Cantidad de Mascotas', compute='_compute_cantidad_mascotas')
    cita_count = fields.Integer(string='Citas', compute='_compute_cita_count')

    def _compute_cantidad_mascotas(self):
        for record in self:
            record.cantidad_mascotas = len(record.paciente_ids)

    def _compute_cita_count(self):
        cita_model = self.env['veterinaria.cita']
        for record in self:
            paciente_ids = record.paciente_ids.ids
            if paciente_ids:
                record.cita_count = cita_model.search_count([
                    ('paciente_id', 'in', paciente_ids)
                ])
            else:
                record.cita_count = 0

    def action_view_mascotas(self):
        """Navegar a la lista de mascotas del propietario"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Mascotas de {self.name}',
            'res_model': 'veterinaria.paciente',
            'view_mode': 'list,form',
            'domain': [('propietario_id', '=', self.id)],
            'context': {
                'default_propietario_id': self.id,
            },
        }

    def action_view_citas(self):
        """Navegar a las citas de todas las mascotas del propietario"""
        self.ensure_one()
        paciente_ids = self.paciente_ids.ids
        return {
            'type': 'ir.actions.act_window',
            'name': f'Citas de {self.name}',
            'res_model': 'veterinaria.cita',
            'view_mode': 'list,calendar,form',
            'domain': [('paciente_id', 'in', paciente_ids)],
            'context': {
                'default_paciente_id': paciente_ids[0] if paciente_ids else False,
            },
        }

    def action_agendar_cita(self):
        """Abrir formulario de nueva cita con propietario pre-seleccionado"""
        self.ensure_one()
        paciente_ids = self.paciente_ids.ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agendar Cita',
            'res_model': 'veterinaria.cita',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_paciente_id': paciente_ids[0] if len(paciente_ids) == 1 else False,
            },
        }