# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class Cita(models.Model):
    _name = 'veterinaria.cita'
    _description = 'Cita Veterinaria'
    _order = 'fecha_hora DESC'

    name = fields.Char('Referencia', compute='_compute_name')
    paciente_id = fields.Many2one('veterinaria.paciente', string='Paciente', required=True, 
                                   ondelete='cascade')
    propietario_id = fields.Many2one(
        'res.partner',
        string='Propietario',
        required=False,
        domain=[('es_propietario', '=', True)],
        store=True,
        index=True,
    )
    facturada = fields.Boolean('Facturada', default=False)
    veterinario_id = fields.Many2one('veterinaria.veterinario', string='Veterinario', ondelete='set null')
    servicio_id = fields.Many2one('veterinaria.servicio', string='Servicio', ondelete='set null')
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    fecha_hora = fields.Datetime('Fecha y Hora', required=True)
    duracion = fields.Selection([
        ('0.5', '30 minutos'),
        ('1.0', '1 hora'),
    ], string='Duración', default='1.0')
    duracion_horas = fields.Float('Duración (horas)', compute='_compute_duracion_horas', store=True)
    
    motivo = fields.Text('Motivo de la Cita', required=True)
    sintoma_ids = fields.Many2many('veterinaria.sintoma', string='Síntomas')
    sintomas_resumen = fields.Char(
        string='Síntomas',
        compute='_compute_sintomas_resumen',
        store=True,
        help='Primeros 3 síntomas de la cita'
    )
    
    # Estado
    estado = fields.Selection([
        ('programada', 'Programada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('no_asistio', 'No Asistió'),
    ], string='Estado', default='programada')
    
    # Relación con historia clínica
    historia_clinica_id = fields.Many2one('veterinaria.historia_clinica', string='Historia Clínica')
    receta_ids = fields.One2many('veterinaria.receta', 'cita_id', string='Recetas Médicas')
    receta_count = fields.Integer(compute='_compute_receta_count')

    @api.depends('receta_ids')
    def _compute_receta_count(self):
        for rec in self:
            rec.receta_count = len(rec.receta_ids)

    @api.depends('sintoma_ids')
    def _compute_sintomas_resumen(self):
        for rec in self:
            nombres = rec.sintoma_ids.mapped('name')
            if not nombres:
                rec.sintomas_resumen = False
            elif len(nombres) <= 3:
                rec.sintomas_resumen = ', '.join(nombres)
            else:
                rec.sintomas_resumen = ', '.join(nombres[:3]) + '...'

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

    @api.onchange('propietario_id')
    def _onchange_propietario_id(self):
        for record in self:
            if record.propietario_id and record.paciente_id:
                if record.paciente_id.propietario_id != record.propietario_id:
                    record.paciente_id = False
            elif not record.propietario_id:
                record.paciente_id = False

    @api.depends('paciente_id', 'fecha_hora')
    def _compute_name(self):
        for record in self:
            record.name = f"Cita {record.paciente_id.name} - {record.fecha_hora.strftime('%d/%m/%Y') if record.fecha_hora else ''}"

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
            # Las observaciones generales son independientes de los síntomas por cita
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
            # Los síntomas de cada cita NO se escriben en observaciones generales de la historia
            historia.write(update_vals)

    # ==================================================================
    # Métodos de envío de correo (#8)
    # ==================================================================
    def _send_confirmacion_email(self):
        """Envía email de confirmación al crear una cita"""
        template = self.env.ref('veterinaria_core.mail_template_cita_confirmacion', raise_if_not_found=False)
        if not template:
            return
        for record in self:
            if record.propietario_id and record.propietario_id.email:
                try:
                    template.send_mail(record.id, force_send=True)
                    _logger.info('Email de confirmación enviado para cita %s', record.name)
                except Exception as e:
                    _logger.warning('No se pudo enviar email de confirmación para cita %s: %s', record.name, e)

    def _send_completada_email(self):
        """Envía resumen post-consulta al completar la cita"""
        template = self.env.ref('veterinaria_core.mail_template_cita_completada', raise_if_not_found=False)
        if not template:
            return
        for record in self:
            if record.propietario_id and record.propietario_id.email:
                try:
                    template.send_mail(record.id, force_send=True)
                    _logger.info('Email de consulta completada enviado para cita %s', record.name)
                except Exception as e:
                    _logger.warning('No se pudo enviar email post-consulta para cita %s: %s', record.name, e)

    @api.model
    def _cron_enviar_recordatorios(self):
        """Cron: Envía recordatorio de citas en las próximas 24h"""
        template = self.env.ref('veterinaria_core.mail_template_cita_recordatorio', raise_if_not_found=False)
        if not template:
            _logger.warning('Plantilla de recordatorio no encontrada')
            return

        now = fields.Datetime.now()
        en_24h = now + timedelta(hours=24)

        citas = self.search([
            ('estado', '=', 'programada'),
            ('recordatorio_enviado', '=', False),
            ('fecha_hora', '>=', now),
            ('fecha_hora', '<=', en_24h),
        ])

        _logger.info('Cron recordatorios: %d citas encontradas', len(citas))

        for cita in citas:
            if cita.propietario_id and cita.propietario_id.email:
                try:
                    template.send_mail(cita.id, force_send=True)
                    cita.write({'recordatorio_enviado': True})
                    _logger.info('Recordatorio enviado para cita %s', cita.name)
                except Exception as e:
                    _logger.warning('Error enviando recordatorio para cita %s: %s', cita.name, e)

    # ==================================================================
    # CRUD overrides e Interceptores de Caché (Normalización de Duración)
    # ==================================================================
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'duracion' in res:
            val = res['duracion']
            try:
                fl_val = float(val)
                str_val = str(fl_val)
                if str_val in ['0.5', '1.0']:
                    res['duracion'] = str_val
            except Exception:
                pass
        return res

    def onchange(self, values, field_names, fields_spec):
        if values and 'duracion' in values:
            val = values['duracion']
            try:
                fl_val = float(val)
                str_val = str(fl_val)
                if str_val in ['0.5', '1.0']:
                    values['duracion'] = str_val
            except Exception:
                pass
        return super().onchange(values, field_names, fields_spec)

    @api.model_create_multi
    def create(self, vals_list):
        # validate overlaps before create and normalize duracion
        for vals in vals_list:
            if 'duracion' in vals:
                try:
                    fl_val = float(vals['duracion'])
                    str_val = str(fl_val)
                    if str_val in ['0.5', '1.0']:
                        vals['duracion'] = str_val
                except Exception:
                    pass
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
        # Enviar email de confirmación (#8)
        records._send_confirmacion_email()
        return records

    def write(self, vals):
        if 'duracion' in vals:
            try:
                fl_val = float(vals['duracion'])
                str_val = str(fl_val)
                if str_val in ['0.5', '1.0']:
                    vals['duracion'] = str_val
            except Exception:
                pass
        result = super().write(vals)
        campos_sincronizados = {
            'paciente_id',
            'veterinario_id',
            'fecha_hora',
            'motivo',
            'estado',
        }
        if campos_sincronizados.intersection(vals.keys()):
            self._sync_historia()
        return result

    def action_completar_cita(self):
        """Marcar cita como completada y enviar resumen (#8)"""
        self.write({'estado': 'completada'})
        self._send_completada_email()

    def action_cancelar_cita(self):
        """Cancelar cita"""
        self.write({'estado': 'cancelada'})

    def action_crear_receta(self):
        """Abre el formulario para crear una nueva receta vinculada a esta cita"""
        self.ensure_one()
        return {
            'name': 'Nueva Receta Médica',
            'type': 'ir.actions.act_window',
            'res_model': 'veterinaria.receta',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_cita_id': self.id,
            }
        }
