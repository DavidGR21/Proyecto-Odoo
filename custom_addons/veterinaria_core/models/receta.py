# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


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

    # Propietario (related) — necesario para las record rules del portal del cliente
    propietario_id = fields.Many2one(
        'res.partner',
        string='Propietario',
        related='paciente_id.propietario_id',
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

    # ── Estado de Facturación ────────────────────────────────────────────────
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('finalizada', 'Finalizada'),
    ], string='Estado', default='borrador', copy=False, tracking=True)

    # ── Validación ────────────────────────────────────────────────────────────
    _sql_constraints = [
        ('unique_cita_id', 'unique(cita_id)', '¡Ya existe una receta médica creada para esta cita!'),
    ]

    @api.constrains('cita_id')
    def _check_cita_unica(self):
        for rec in self:
            recetas = self.search([('cita_id', '=', rec.cita_id.id), ('id', '!=', rec.id)])
            if recetas:
                raise ValidationError(f'¡Ya existe una receta médica creada para la cita "{rec.cita_id.name}"!')

    @api.constrains('cita_id')
    def _check_cita_tiene_historia(self):
        for rec in self:
            if not rec.cita_id.historia_clinica_id:
                raise ValidationError(
                    f'La cita "{rec.cita_id.name}" no tiene una Historia Clínica asociada. '
                    'Por favor, genere la historia clínica primero.'
                )

    def write(self, vals):
        for rec in self:
            if rec.state == 'finalizada' and any(f not in ['state'] for f in vals):
                raise UserError("No se puede modificar una receta médica que ya ha sido finalizada.")
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state == 'finalizada':
                raise UserError("No se puede eliminar una receta médica que ya ha sido finalizada.")
        return super().unlink()


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

    # Propietario (related) — para record rules del portal
    propietario_id = fields.Many2one(
        'res.partner',
        related='receta_id.propietario_id',
        store=True,
        readonly=True,
    )

    paciente_id = fields.Many2one(
        'veterinaria.paciente',
        related='receta_id.paciente_id',
        store=True,
        readonly=True,
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

    # ── Detalles estructurados (Refactores para Cálculo) ──────────────────────
    dosis = fields.Float(
        'Dosis (unidades/ml)',
        required=True,
        default=1.0,
        help='Cantidad de medicamento por toma (ej: 1.5, 2, 0.5)',
    )

    frecuencia_horas = fields.Integer(
        'Cada (horas)',
        required=True,
        default=24,
        help='Intervalo de horas entre tomas (ej: 24, 12, 8, 6)',
    )

    duracion_dias = fields.Integer(
        'Duración (días)',
        required=True,
        default=1,
        help='Cantidad de días que durará el tratamiento',
    )

    cantidad_total = fields.Float(
        'Cantidad Total a Entregar',
        compute='_compute_cantidad_total',
        store=True,
        help='Dosis * (24 / Frecuencia) * Duración',
    )

    @api.depends('dosis', 'frecuencia_horas', 'duracion_dias')
    def _compute_cantidad_total(self):
        for rec in self:
            if rec.frecuencia_horas > 0:
                tomas_por_dia = 24.0 / rec.frecuencia_horas
                rec.cantidad_total = rec.dosis * tomas_por_dia * rec.duracion_dias
            else:
                rec.cantidad_total = 0.0

    # ── Validaciones ──────────────────────────────────────────────────────────
    @api.constrains('tipo_origen', 'medicamento_id', 'medicamento_texto')
    def _check_medicamento_identificado(self):
        for rec in self:
            if rec.tipo_origen == 'inventario' and not rec.medicamento_id:
                raise ValidationError('Debe seleccionar un medicamento del inventario.')
            if rec.tipo_origen == 'exterior' and not rec.medicamento_texto:
                raise ValidationError('Debe escribir el nombre del medicamento exterior.')

    # ── Restricciones tras facturación ───────────────────────────────────────
    @api.model
    def create(self, vals):
        if vals.get('receta_id'):
            receta = self.env['veterinaria.receta'].browse(vals['receta_id'])
            if receta.state == 'finalizada':
                raise UserError("No se pueden añadir nuevas líneas a una receta que ya ha sido finalizada.")
        return super().create(vals)

    def write(self, vals):
        for rec in self:
            if rec.receta_id.state == 'finalizada':
                raise UserError("No se puede modificar una línea de receta que ya ha sido finalizada.")
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.receta_id.state == 'finalizada':
                raise UserError("No se puede eliminar una línea de receta que ya ha sido finalizada.")
        return super().unlink()