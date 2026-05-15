# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta


class Cita(models.Model):
    _name = 'veterinaria.cita'
    _description = 'Cita Veterinaria'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_hora DESC'

    name = fields.Char('Referencia', compute='_compute_name')
    paciente_id = fields.Many2one('veterinaria.paciente', string='Paciente', required=True, 
                                   ondelete='cascade', tracking=True)
    propietario_id = fields.Many2one('res.partner', string='Propietario', compute='_compute_propietario', store=False)
    veterinario_id = fields.Many2one('veterinaria.veterinario', string='Veterinario', ondelete='set null')
    servicio_id = fields.Many2one('veterinaria.servicio', string='Servicio', ondelete='set null')
    fecha_hora = fields.Datetime('Fecha y Hora', required=True, tracking=True)
    duracion = fields.Selection([
        ('0.5', '30 minutos'),
        ('1.0', '1 hora'),
    ], string='Duración', default='1.0')
    duracion_horas = fields.Float('Duración (horas)', compute='_compute_duracion_horas', store=True)
    
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

    @api.depends('duracion')
    def _compute_duracion_horas(self):
        for record in self:
            record.duracion_horas = float(record.duracion or 0.0)

    @api.onchange('fecha_hora', 'duracion')
    def _onchange_fecha_hora_disponibilidad(self):
        """Limitar veterinarios disponibles según su horario y citas existentes."""
        for record in self:
            if not record.fecha_hora:
                return {'domain': {'veterinario_id': []}}
            start = record.fecha_hora
            duration = float(record.duracion or 0.0)
            end = start + timedelta(hours=duration)
            weekday = start.weekday()  # 0=Mon .. 6=Sun

            vets = self.env['veterinaria.veterinario'].search([])
            available_ids = []
            for vet in vets:
                # dias_disponibles mapping
                ok_day = False
                if vet.dias_disponibles == 'todos':
                    ok_day = True
                elif vet.dias_disponibles == 'lun_vie' and weekday in range(0,5):
                    ok_day = True
                elif vet.dias_disponibles == 'lun_sab' and weekday in range(0,6):
                    ok_day = True
                elif vet.dias_disponibles == 'sab_dom' and weekday in (5,6):
                    ok_day = True
                if not ok_day:
                    continue

                # horario strings like '08:00'
                try:
                    h_start = float(vet.horario_inicio.split(':')[0]) + float(vet.horario_inicio.split(':')[1]) / 60.0
                    h_end = float(vet.horario_fin.split(':')[0]) + float(vet.horario_fin.split(':')[1]) / 60.0
                except Exception:
                    continue
                start_hour = start.hour + start.minute/60.0
                if not (start_hour >= h_start and (start_hour + duration) <= h_end):
                    continue

                # check for overlapping existing citas
                conflict = False
                existing = self.env['veterinaria.cita'].search([
                    ('veterinario_id', '=', vet.id),
                    ('id', '!=', record.id),
                    ('estado', '!=', 'cancelada'),
                ])
                for ex in existing:
                    if not ex.fecha_hora:
                        continue
                    ex_start = ex.fecha_hora
                    ex_end = ex_start + timedelta(hours=ex.duracion_horas or 0.0)
                    if ex_start < end and ex_end > start:
                        conflict = True
                        break
                if conflict:
                    continue

                available_ids.append(vet.id)

            # Si el veterinario actualmente seleccionado no está disponible, lo limpiamos
            if record.veterinario_id and record.veterinario_id.id not in available_ids:
                record.veterinario_id = False

            return {'domain': {'veterinario_id': [('id', 'in', available_ids)]}}

    @api.depends('paciente_id', 'fecha_hora')
    def _compute_name(self):
        for record in self:
            record.name = f"Cita {record.paciente_id.name} - {record.fecha_hora.strftime('%d/%m/%Y') if record.fecha_hora else ''}"

    @api.depends('paciente_id')
    def _compute_propietario(self):
        for record in self:
            record.propietario_id = record.paciente_id.propietario_id if record.paciente_id else False

    @api.constrains('veterinario_id', 'motivo', 'fecha_hora')
    def _check_required_fields(self):
        for record in self:
            if not record.veterinario_id:
                raise ValidationError('Debe seleccionar un Veterinario para la cita')
            if not record.motivo:
                raise ValidationError('Debe ingresar el Motivo de la cita')
            if not record.fecha_hora:
                raise ValidationError('Debe seleccionar la Fecha y Hora de la cita')

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
        # validate overlaps before create
        for vals in vals_list:
            if vals.get('veterinario_id') and vals.get('fecha_hora'):
                start = fields.Datetime.to_datetime(vals['fecha_hora']) if isinstance(vals['fecha_hora'], str) else vals['fecha_hora']
                duration = float(vals.get('duracion') or 1.0)
                end = start + timedelta(hours=duration)
                conflicts = self.env['veterinaria.cita'].search([
                    ('veterinario_id', '=', vals['veterinario_id']),
                    ('estado', '!=', 'cancelada'),
                    ('fecha_hora', '<', end),
                ])
                for ex in conflicts:
                    ex_end = ex.fecha_hora + timedelta(hours=ex.duracion_horas or 0.0)
                    if ex_end > start:
                        raise ValidationError('El veterinario no está disponible en ese horario (conflicto con otra cita).')
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
