# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Receta(models.Model):
    """Receta médica generada en el contexto de una historia clínica/cita.
    Permite que el cliente vea desde el portal qué medicamentos se le recetaron a su mascota."""
    _name = 'veterinaria.receta'
    _description = 'Receta médica'
    _order = 'fecha DESC'

    name = fields.Char('Referencia', compute='_compute_name', store=True)
    historia_clinica_id = fields.Many2one('veterinaria.historia_clinica',
                                           string='Historia clínica',
                                           required=True, ondelete='cascade')
    cita_id = fields.Many2one('veterinaria.cita', string='Cita asociada',
                              ondelete='set null')
    paciente_id = fields.Many2one(related='historia_clinica_id.paciente_id',
                                   store=True, readonly=True, string='Mascota')
    propietario_id = fields.Many2one(related='paciente_id.propietario_id',
                                      store=True, readonly=True)
    veterinario_id = fields.Many2one('veterinaria.veterinario', string='Veterinario')
    medicamento_id = fields.Many2one('veterinaria.medicamento', string='Medicamento',
                                      required=True)
    dosis = fields.Char('Dosis', help='Ej: 1 comprimido cada 8h')
    frecuencia = fields.Char('Frecuencia', help='Ej: Cada 8 horas')
    duracion_dias = fields.Integer('Duración (días)', default=7)
    fecha = fields.Date('Fecha de emisión', default=fields.Date.today, required=True)
    observaciones = fields.Text('Indicaciones adicionales')

    @api.depends('paciente_id', 'medicamento_id', 'fecha')
    def _compute_name(self):
        for r in self:
            partes = []
            if r.paciente_id:
                partes.append(r.paciente_id.name)
            if r.medicamento_id:
                partes.append(r.medicamento_id.name)
            if r.fecha:
                partes.append(r.fecha.strftime('%d/%m/%Y'))
            r.name = ' - '.join(partes) or 'Receta'
