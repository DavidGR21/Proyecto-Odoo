# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Cita(models.Model):
    _name = 'veterinaria.cita'
    _description = 'Cita Veterinaria'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_hora DESC'

    name = fields.Char('Referencia', compute='_compute_name', store=True)
    paciente_id = fields.Many2one('veterinaria.paciente', string='Paciente', required=True, 
                                   ondelete='cascade', tracking=True)
    propietario_id = fields.Many2one('res.partner', string='Propietario',
                                      related='paciente_id.propietario_id', readonly=True, store=True)
    veterinario_id = fields.Many2one('veterinaria.veterinario', string='Veterinario', required=True, tracking=True)
    fecha_hora = fields.Datetime('Fecha y Hora', required=True, tracking=True)
    duracion = fields.Float('Duración (horas)', default=1.0)
    
    motivo = fields.Text('Motivo de la Cita', required=True, tracking=True)
    observaciones = fields.Text('Observaciones')
    
    # Estado
    estado = fields.Selection([
        ('programada', 'Programada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('no_asistio', 'No Asistió'),
    ], string='Estado', default='programada', tracking=True)
    
    # Relación con historia clínica
    historia_clinica_id = fields.Many2one('veterinaria.historia_clinica', string='Historia Clínica')
    alergias = fields.Text('Alergias de la Mascota')
    tipo_sangre = fields.Selection([
        ('a_pos', 'A+'),
        ('a_neg', 'A-'),
        ('b_pos', 'B+'),
        ('b_neg', 'B-'),
        ('ab_pos', 'AB+'),
        ('ab_neg', 'AB-'),
        ('o_pos', 'O+'),
        ('o_neg', 'O-'),
        ('desconocido', 'Desconocido'),
    ], string='Tipo de Sangre')
    condiciones_cronicas = fields.Text('Condiciones Crónicas')
    peso = fields.Float('Peso (kg)')
    
    # Recordatorio
    recordatorio_enviado = fields.Boolean('Recordatorio Enviado', default=False)

    @api.depends('paciente_id', 'fecha_hora')
    def _compute_name(self):
        for record in self:
            record.name = f"Cita {record.paciente_id.name} - {record.fecha_hora.strftime('%d/%m/%Y %H:%M') if record.fecha_hora else ''}"

    def _map_estado_historia(self):
        self.ensure_one()
        if self.estado == 'completada':
            return True
        if self.estado in ('cancelada', 'no_asistio'):
            return False
        return True

    def _prepare_historia_vals(self):
        self.ensure_one()
        return {
            'paciente_id': self.paciente_id.id,
            'fecha_apertura': self.fecha_hora,
            'activa': self._map_estado_historia(),
            'alergias': self.alergias or self.paciente_id.alergias,
            'tipo_sangre': self.tipo_sangre or 'desconocido',
            'peso': self.peso or self.paciente_id.peso,
            'condiciones_cronicas': self.condiciones_cronicas,
            'observaciones': self.observaciones,
        }

    @api.onchange('paciente_id')
    def _onchange_paciente_id(self):
        for record in self:
            if not record.paciente_id:
                continue
            historia = self.env['veterinaria.historia_clinica'].search([
                ('paciente_id', '=', record.paciente_id.id)
            ], limit=1)
            record.propietario_id = record.paciente_id.propietario_id
            record.alergias = historia.alergias or record.paciente_id.alergias
            record.tipo_sangre = historia.tipo_sangre if historia else 'desconocido'
            record.peso = historia.peso or record.paciente_id.peso
            record.condiciones_cronicas = historia.condiciones_cronicas if historia else False

    def _sync_historia(self):
        for record in self:
            historia = self.env['veterinaria.historia_clinica'].search([
                ('paciente_id', '=', record.paciente_id.id)
            ], limit=1)
            if not historia:
                historia = self.env['veterinaria.historia_clinica'].with_context(from_cita_create=True).create(
                    [record._prepare_historia_vals()]
                )
            record.historia_clinica_id = historia.id

            update_vals = {
                'paciente_id': record.paciente_id.id,
                'activa': record._map_estado_historia(),
            }
            if record.alergias:
                update_vals['alergias'] = record.alergias
            elif record.paciente_id.alergias and not historia.alergias:
                update_vals['alergias'] = record.paciente_id.alergias
            if record.tipo_sangre:
                update_vals['tipo_sangre'] = record.tipo_sangre
            if record.peso:
                update_vals['peso'] = record.peso
            elif record.paciente_id.peso and not historia.peso:
                update_vals['peso'] = record.paciente_id.peso
            if record.condiciones_cronicas:
                update_vals['condiciones_cronicas'] = record.condiciones_cronicas
            if record.observaciones:
                update_vals['observaciones'] = record.observaciones
            historia.write(update_vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_historia()
        return records

    def write(self, vals):
        result = super().write(vals)
        campos_sincronizados = {
            'paciente_id',
            'veterinario_id',
            'fecha_hora',
            'motivo',
            'observaciones',
            'estado',
        }
        if campos_sincronizados.intersection(vals.keys()):
            self._sync_historia()
        return result

    def action_completar_cita(self):
        """Marcar cita como completada"""
        self.write({'estado': 'completada'})

    def action_cancelar_cita(self):
        """Cancelar cita"""
        self.write({'estado': 'cancelada'})
