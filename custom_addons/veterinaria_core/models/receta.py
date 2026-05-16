# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Receta(models.Model):
    """
    Prescripción médica emitida por el veterinario al finalizar una cita.
    Ámbito clínico: no contiene información financiera.
    """
    _name = 'veterinaria.receta'
    _description = 'Receta Médica Veterinaria'
    _order = 'fecha_emision DESC'
    _rec_name = 'display_name'

    # ── Secuencia ─────────────────────────────────────────────────────────────
    name = fields.Char(
        'Referencia',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('veterinaria.receta') or 'REC-NUEVO'
    )

    # ── Relaciones obligatorias ────────────────────────────────────────────────
    cita_id = fields.Many2one(
        'veterinaria.cita',
        string='Cita Médica',
        required=True,
        ondelete='cascade',
        tracking=True,
    )

    historia_clinica_id = fields.Many2one(
        'veterinaria.historia_clinica',
        string='Historia Clínica',
        related='cita_id.historia_clinica_id',
        store=True,
        readonly=True,
    )

    # ── Campos clínicos ───────────────────────────────────────────────────────
    veterinario_id = fields.Many2one(
        'veterinaria.veterinario',
        string='Veterinario',
        related='cita_id.veterinario_id',
        store=True,
        readonly=True,
    )

    paciente_id = fields.Many2one(
        'veterinaria.paciente',
        string='Paciente',
        related='cita_id.paciente_id',
        store=True,
        readonly=True,
    )

    fecha_emision = fields.Datetime(
        'Fecha de Emisión',
        default=fields.Datetime.now,
        required=True,
    )

    diagnostico = fields.Text(
        'Diagnóstico / Observaciones Clínicas',
        help='Resumen del diagnóstico del veterinario en esta consulta',
    )

    instrucciones_generales = fields.Text(
        'Instrucciones Generales',
        help='Indicaciones generales de cuidado que debe seguir el propietario',
    )

    observaciones_adicionales = fields.Text(
        'Observaciones o Instrucciones Adicionales',
        help='Indicaciones de cuidado general (ej: reposo, collar isabelino, etc.)',
    )

    # ── Líneas de medicamentos ─────────────────────────────────────────────────
    linea_ids = fields.One2many(
        'veterinaria.receta.linea',
        'receta_id',
        string='Medicamentos Recetados',
    )

    # ── Compute display_name ──────────────────────────────────────────────────
    @api.depends('name', 'paciente_id', 'cita_id.fecha_hora')
    def _compute_display_name(self):
        for rec in self:
            fecha = ''
            if rec.cita_id and rec.cita_id.fecha_hora:
                fecha = rec.cita_id.fecha_hora.strftime('%d/%m/%Y')
            paciente = rec.paciente_id.name if rec.paciente_id else ''
            rec.display_name = f"{rec.name} - {fecha} (Paciente: {paciente})"

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    # ── Validación ────────────────────────────────────────────────────────────
    @api.constrains('cita_id')
    def _check_cita_tiene_historia(self):
        for rec in self:
            if not rec.cita_id.historia_clinica_id:
                raise ValidationError(
                    f'La cita "{rec.cita_id.name}" no tiene una Historia Clínica asociada. '
                    'Por favor, genere la historia clínica primero.'
                )


class RecetaLinea(models.Model):
    """
    Línea de la receta: un medicamento individual con su dosis, frecuencia y duración.
    REGLA ESTRICTA: Sin ningún campo financiero.
    """
    _name = 'veterinaria.receta.linea'
    _description = 'Línea de Receta Médica'

    receta_id = fields.Many2one(
        'veterinaria.receta',
        string='Receta',
        required=True,
        ondelete='cascade',
    )

    # ── Origen del Medicamento ─────────────────────────────────────────────────
    tipo_origen = fields.Selection([
        ('inventario', 'De Inventario'),
        ('exterior', 'Exterior/Manual'),
    ], string='Origen', required=True, default='inventario')

    # ── Campos de Datos del Medicamento ────────────────────────────────────────
    medicamento_id = fields.Many2one(
        'veterinaria.inventario',
        string='Medicamento (Inventario)',
        domain=[('tipo_inventario', '=', 'medicamento'), ('activo', '=', True)],
        help='Seleccione un medicamento del catálogo de la clínica',
    )

    medicamento_texto = fields.Char(
        'Medicamento (Exterior)',
        help='Escriba el nombre del medicamento si es externo a la clínica',
    )

    # ── Campo Computado para Visualización Única (Solución #2) ──────────────────
    nombre_medicamento_display = fields.Char(
        'Medicamento',
        compute='_compute_nombre_medicamento_display',
        store=True
    )

    @api.depends('tipo_origen', 'medicamento_id', 'medicamento_texto')
    def _compute_nombre_medicamento_display(self):
        for rec in self:
            if rec.tipo_origen == 'inventario' and rec.medicamento_id:
                rec.nombre_medicamento_display = rec.medicamento_id.name
            elif rec.tipo_origen == 'exterior' and rec.medicamento_texto:
                rec.nombre_medicamento_display = rec.medicamento_texto
            else:
                rec.nombre_medicamento_display = 'No definido'

    # ── Detalles estructurados ───────────────────────────────────────────────
    dosis = fields.Char(
        'Dosis',
        required=True,
        help='Ej: 1 pastilla, 2.5 ml',
    )

    frecuencia = fields.Char(
        'Frecuencia',
        required=True,
        help='Ej: Cada 8 horas, Cada 12 horas',
    )

    duracion = fields.Char(
        'Duración',
        required=True,
        help='Ej: Por 7 días, Por 3 semanas',
    )

    # ── Validaciones ──────────────────────────────────────────────────────────
    @api.constrains('tipo_origen', 'medicamento_id', 'medicamento_texto')
    def _check_medicamento_identificado(self):
        for rec in self:
            if rec.tipo_origen == 'inventario' and not rec.medicamento_id:
                raise ValidationError('Debe seleccionar un medicamento del inventario.')
            if rec.tipo_origen == 'exterior' and not rec.medicamento_texto:
                raise ValidationError('Debe escribir el nombre del medicamento exterior.')
