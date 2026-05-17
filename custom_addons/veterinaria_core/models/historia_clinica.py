# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class HistoriaClinica(models.Model):
    _name = 'veterinaria.historia_clinica'
    _description = 'Historia Clínica'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_apertura DESC'

    TIPO_SANGRE = [
        ('a_pos', 'A+'),
        ('a_neg', 'A-'),
        ('b_pos', 'B+'),
        ('b_neg', 'B-'),
        ('ab_pos', 'AB+'),
        ('ab_neg', 'AB-'),
        ('o_pos', 'O+'),
        ('o_neg', 'O-'),
        ('desconocido', 'Desconocido'),
    ]

    paciente_id = fields.Many2one('veterinaria.paciente', string='Paciente', required=True,
                                   ondelete='cascade', tracking=True)
    cita_ids = fields.One2many('veterinaria.cita', 'historia_clinica_id', string='Citas')
    receta_ids = fields.One2many('veterinaria.receta', 'historia_clinica_id', string='Recetas')
    # Relación inversa para record rules del portal
    propietario_id = fields.Many2one(related='paciente_id.propietario_id',
                                      store=True, readonly=True)
    fecha_apertura = fields.Datetime('Fecha de Apertura', default=fields.Datetime.now, required=True, tracking=True)
    activa = fields.Boolean('Activa', default=True, tracking=True)
    alergias = fields.Text('Alergias')
    tipo_sangre = fields.Selection(TIPO_SANGRE, string='Tipo de Sangre', default='desconocido')
    peso = fields.Float('Peso (kg)')
    condiciones_cronicas = fields.Text('Condiciones Crónicas')
    observaciones = fields.Text('Observaciones Generales')
    cita_count = fields.Integer(string='Total de Citas', compute='_compute_cita_count')

    _sql_constraints = [
        ('historia_clinica_paciente_unique', 'UNIQUE(paciente_id)', 'Cada paciente solo puede tener una historia clínica.'),
    ]

    @api.depends('cita_ids')
    def _compute_cita_count(self):
        for record in self:
            record.cita_count = len(record.cita_ids)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('from_cita_create'):
            raise UserError('La historia clínica se genera automáticamente al crear una cita.')
        return super().create(vals_list)
