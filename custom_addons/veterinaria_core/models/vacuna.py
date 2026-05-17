# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Vacuna(models.Model):
    """Catálogo de vacunas disponibles en la clínica."""
    _name = 'veterinaria.vacuna'
    _description = 'Vacuna (Catálogo)'
    _order = 'name'

    name = fields.Char('Nombre', required=True)
    descripcion = fields.Text('Descripción')
    especie_sugerida = fields.Selection([
        ('perro', 'Perro'),
        ('gato', 'Gato'),
        ('conejo', 'Conejo'),
        ('pajaro', 'Pájaro'),
        ('reptil', 'Reptil'),
        ('todos', 'Todas'),
    ], string='Especie sugerida', default='todos')
    frecuencia_meses = fields.Integer('Frecuencia (meses)', default=12,
                                      help='Cada cuántos meses se recomienda revacunar.')
    activo = fields.Boolean('Activa', default=True)


class VacunaAplicada(models.Model):
    """Registro histórico de cada vacuna aplicada a una mascota.
    Es la fuente de datos del carnet de vacunación."""
    _name = 'veterinaria.vacuna.aplicada'
    _description = 'Vacuna aplicada a un paciente'
    _order = 'fecha_aplicacion DESC'

    paciente_id = fields.Many2one('veterinaria.paciente', string='Mascota',
                                   required=True, ondelete='cascade')
    vacuna_id = fields.Many2one('veterinaria.vacuna', string='Vacuna',
                                required=True, ondelete='restrict')
    fecha_aplicacion = fields.Date('Fecha de aplicación', required=True,
                                    default=fields.Date.today)
    veterinario_id = fields.Many2one('veterinaria.veterinario', string='Veterinario',
                                      ondelete='set null')
    lote = fields.Char('Lote')
    proxima_dosis = fields.Date('Próxima dosis sugerida',
                                 compute='_compute_proxima_dosis', store=True, readonly=False)
    observaciones = fields.Text('Observaciones')

    # Relación inversa hacia el propietario para escribir record rules sencillas.
    propietario_id = fields.Many2one(related='paciente_id.propietario_id',
                                      store=True, readonly=True)

    @api.depends('fecha_aplicacion', 'vacuna_id')
    def _compute_proxima_dosis(self):
        from dateutil.relativedelta import relativedelta
        for record in self:
            if record.fecha_aplicacion and record.vacuna_id and record.vacuna_id.frecuencia_meses:
                record.proxima_dosis = record.fecha_aplicacion + relativedelta(
                    months=record.vacuna_id.frecuencia_meses
                )
            else:
                record.proxima_dosis = False
