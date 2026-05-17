# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Paciente(models.Model):
    _name = 'veterinaria.paciente'
    _description = 'Paciente (Mascota)'

    name = fields.Char('Nombre', required=True)
    especie = fields.Selection([
        ('perro', 'Perro'),
        ('gato', 'Gato'),
        ('conejo', 'Conejo'),
        ('pajaro', 'Pájaro'),
        ('reptil', 'Reptil'),
        ('otro', 'Otro'),
    ], string='Especie', required=True)
    raza = fields.Char('Raza')
    fecha_nacimiento = fields.Date('Fecha de Nacimiento')
    peso = fields.Float('Peso (kg)')
    foto = fields.Image('Foto', max_width=200, max_height=200)
    propietario_id = fields.Many2one(
        'res.partner',
        string='Propietario',
        required=True,
        domain=[('es_propietario', '=', True)],
    )
    alergias = fields.Text('Alergias Conocidas')
    estado_vacunacion = fields.Selection([
        ('al_dia', 'Al día'),
        ('atrasado', 'Atrasado'),
        ('sin_vacunas', 'Sin vacunas'),
    ], string='Estado de Vacunación', default='sin_vacunas')
    
    # Relación con historia clínica
    historia_clinica_ids = fields.One2many('veterinaria.historia_clinica', 'paciente_id', string='Historia Clínica')
    historia_clinica_count = fields.Integer(string='Consultas', compute='_compute_historia_clinica_count')
    cita_count = fields.Integer(string='Citas', compute='_compute_cita_count')

    # Vacunas aplicadas (carnet de vacunación) y recetas asociadas
    vacuna_aplicada_ids = fields.One2many('veterinaria.vacuna.aplicada', 'paciente_id',
                                           string='Vacunas aplicadas')
    receta_ids = fields.One2many('veterinaria.receta', 'paciente_id', string='Recetas')
    
    # Información adicional
    microchip = fields.Char('Número Microchip')
    fecha_registro = fields.Date('Fecha de Registro', default=fields.Date.today, readonly=True)
    
    # Estados
    estado = fields.Selection([
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
        ('fallecido', 'Fallecido'),
    ], string='Estado', default='activo')

    _sql_constraints = [
        ('microchip_unique', 'UNIQUE(microchip)', 'El número de microchip ya existe'),
    ]

    @api.depends('historia_clinica_ids')
    def _compute_historia_clinica_count(self):
        for record in self:
            record.historia_clinica_count = len(record.historia_clinica_ids)

    def _compute_cita_count(self):
        cita_model = self.env['veterinaria.cita']
        for record in self:
            record.cita_count = cita_model.search_count([('paciente_id', '=', record.id)])

    def action_view_historia_clinica(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Historia Clínica',
            'res_model': 'veterinaria.historia_clinica',
            'view_mode': 'list,form',
            'domain': [('paciente_id', '=', self.id)],
            'context': {'default_paciente_id': self.id},
        }

    def action_view_citas(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Citas',
            'res_model': 'veterinaria.cita',
            'view_mode': 'list,calendar,form',
            'domain': [('paciente_id', '=', self.id)],
            'context': {'default_paciente_id': self.id},
        }

    def action_agendar_cita(self):
        """Abrir formulario para agendar cita con paciente pre-seleccionado"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agendar Cita',
            'res_model': 'veterinaria.cita',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_paciente_id': self.id,
            },
        }

