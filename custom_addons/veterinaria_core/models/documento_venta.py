# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DocumentoVenta(models.Model):
    _name = 'veterinaria.documento_venta'
    _description = 'Documento de Venta Unificado (Facturas y Ventas)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Número de Documento', compute='_compute_name', store=True, readonly=True)
    
    # Tipo de documento
    tipo_documento = fields.Selection([
        ('cita', 'Factura por Cita'),
        ('venta', 'Venta de Productos/Servicios/Medicamentos'),
    ], string='Tipo de Documento', required=True, default='cita')
    
    # Para Citas
    cita_id = fields.Many2one(
        'veterinaria.cita',
        string='Cita',
        ondelete='cascade',
        domain=[('estado', '=', 'completada')],
        help='Requerido si es Factura por Cita'
    )
    
    servicio_id = fields.Many2one(
        'veterinaria.servicio',
        string='Servicio Prestado',
        ondelete='set null',
        help='Servicio asociado a esta facturación'
    )
    
    # Para Ventas
    tipo_venta = fields.Selection([
        ('producto', 'Producto'),
        ('servicio', 'Servicio'),
        ('medicamento', 'Medicamento'),
    ], string='Tipo de Venta', help='Aplica solo si Tipo de Documento es "Venta de Productos"')
    
    # Líneas de venta
    linea_venta_ids = fields.One2many(
        'veterinaria.venta.linea',
        'venta_id',
        string='Líneas de Venta'
    )
    
    propietario_id = fields.Many2one(
        'res.partner', string='Cliente', required=True, 
        domain=[('es_propietario', '=', True)], compute='_compute_propietario_id', 
        store=True, readonly=False
    )
    paciente_id = fields.Many2one(
        'veterinaria.paciente', string='Mascota', 
        compute='_compute_paciente_id', store=True, readonly=False
    )
    
    # Veterinario (para citas)
    veterinario_id = fields.Many2one(
        'veterinaria.veterinario',
        string='Veterinario',
        compute='_compute_veterinario_id',
        store=False
    )
    
    # Fechas
    fecha_documento = fields.Date('Fecha del Documento', default=fields.Date.today, required=True)
    fecha_cita = fields.Datetime(
        'Fecha de la Cita',
        compute='_compute_fecha_cita',
        store=False
    )
    
    # Motivo de cita
    motivo_cita = fields.Text(
        'Motivo de la Cita',
        compute='_compute_motivo_cita',
        store=False
    )
    
    # Precios
    precio_unitario = fields.Float('Precio Unitario')
    total_sin_impuesto = fields.Float('Total sin Impuesto', compute='_compute_totales', store=True)
    impuesto_total = fields.Float('Total Impuesto', compute='_compute_totales', store=True)
    total = fields.Float('Total', compute='_compute_totales', store=True)
    
    # Impuestos
    impuesto_id = fields.Many2many(
        'account.tax',
        string='Impuestos',
        domain=[('type_tax_use', '=', 'sale')]
    )
    
    # Estado
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('validado', 'Validado'),
        ('cancelado', 'Cancelado'),
    ], string='Estado', default='borrador')
    
    # Invoice relacionada
    move_id = fields.Many2one(
        'account.move',
        string='Factura Contable',
        ondelete='cascade',
        readonly=True
    )
    
    # Observaciones
    observaciones = fields.Text('Observaciones')
    
    @api.depends('tipo_documento', 'cita_id', 'propietario_id', 'fecha_documento')
    def _compute_name(self):
        for record in self:
            if record.tipo_documento == 'cita' and record.cita_id:
                record.name = f"FAC-{record.cita_id.id:05d}"
            elif record.tipo_documento == 'venta' and record.propietario_id:
                record.name = f"VTA-{record.propietario_id.name[:10]}-{record.fecha_documento.strftime('%Y%m%d')}"
            else:
                record.name = "Documento"
    
    @api.depends('tipo_documento', 'cita_id')
    def _compute_propietario_id(self):
        for record in self:
            if record.tipo_documento == 'cita' and record.cita_id:
                record.propietario_id = record.cita_id.propietario_id
    
    @api.depends('cita_id')
    def _compute_paciente_id(self):
        for record in self:
            if record.cita_id:
                record.paciente_id = record.cita_id.paciente_id
    
    @api.depends('cita_id')
    def _compute_veterinario_id(self):
        for record in self:
            record.veterinario_id = record.cita_id.veterinario_id if record.cita_id else False
    
    @api.depends('cita_id')
    def _compute_fecha_cita(self):
        for record in self:
            # Cambiamos .fecha por .fecha_hora
            record.fecha_cita = record.cita_id.fecha_hora if record.cita_id else False
        
    @api.depends('cita_id')
    def _compute_motivo_cita(self):
        for record in self:
            record.motivo_cita = record.cita_id.motivo if record.cita_id else ""
    
    @api.depends('precio_unitario', 'linea_venta_ids.subtotal', 'linea_venta_ids.impuesto')
    def _compute_totales(self):
        for record in self:
            if record.tipo_documento == 'cita':
                record.total_sin_impuesto = record.precio_unitario
                record.impuesto_total = 0
                record.total = record.precio_unitario
            else:
                record.total_sin_impuesto = sum(line.subtotal for line in record.linea_venta_ids)
                record.impuesto_total = sum(line.impuesto for line in record.linea_venta_ids)
                record.total = record.total_sin_impuesto + record.impuesto_total
    
    @api.onchange('tipo_documento')
    def _onchange_tipo_documento(self):
        """Limpia campos cuando cambia el tipo de documento"""
        if self.tipo_documento == 'cita':
            self.linea_venta_ids = [(5, 0, 0)]  # Limpia líneas de venta
            self.tipo_venta = False
        else:
            self.cita_id = False
            self.servicio_id = False
    
    @api.constrains('tipo_documento', 'cita_id', 'propietario_id')
    def _check_required_fields(self):
        """Valida que los campos requeridos estén presentes según el tipo"""
        for record in self:
            if record.tipo_documento == 'cita' and not record.cita_id:
                raise ValidationError('Debe seleccionar una Cita para facturas por cita.')
            if record.tipo_documento == 'venta' and not record.propietario_id:
                raise ValidationError('Debe seleccionar un Cliente para ventas.')
            
    @api.onchange('propietario_id')
    def _onchange_propietario_id_mascota(self):
        """Si cambia el dueño, verificamos que la mascota actual le pertenezca. 
        Si no le pertenece, limpiamos el campo de la mascota."""
        if self.propietario_id and self.paciente_id:
            if self.paciente_id.propietario_id != self.propietario_id:
                self.paciente_id = False  # Borra la mascota de la vista
        elif not self.propietario_id:
            self.paciente_id = False # Si quita al dueño, también quitamos la mascota
            

    def action_validar_factura(self):
        for record in self:
            if record.estado != 'borrador':
                raise ValidationError('Solo se pueden validar borradores.')
            record.estado = 'validado'

    def action_cancelar_factura(self):
        for record in self:
            record.estado = 'cancelado'

