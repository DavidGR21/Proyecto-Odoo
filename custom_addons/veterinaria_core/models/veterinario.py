from odoo import fields, models, api


import logging
_logger = logging.getLogger(__name__)

class VeterinarioVeterinario(models.Model):
    _name = 'veterinaria.veterinario'
    _description = 'Veterinario'

    name = fields.Char(string='Nombre', required=True)
    email = fields.Char(string='Correo Electrónico')
    user_id = fields.Many2one('res.users', string='Usuario Odoo', help='Usuario de Odoo vinculado a este veterinario. Permite filtrar citas automáticamente.')
    especialidad_id = fields.Many2one('veterinaria.especialidad', string='Especialidad', required=True)
    matricula_profesional = fields.Char(string='Matrícula profesional')
    horario_inicio = fields.Selection([
        ('07:00', '07:00'),
        ('08:00', '08:00'),
        ('09:00', '09:00'),
        ('10:00', '10:00'),
        ('11:00', '11:00'),
        ('12:00', '12:00'),
        ('13:00', '13:00'),
        ('14:00', '14:00'),
        ('15:00', '15:00'),
        ('16:00', '16:00'),
        ('17:00', '17:00'),
        ('18:00', '18:00'),
        ('19:00', '19:00'),
    ], string='Hora de inicio')
    horario_fin = fields.Selection([
        ('07:00', '07:00'),
        ('08:00', '08:00'),
        ('09:00', '09:00'),
        ('10:00', '10:00'),
        ('11:00', '11:00'),
        ('12:00', '12:00'),
        ('13:00', '13:00'),
        ('14:00', '14:00'),
        ('15:00', '15:00'),
        ('16:00', '16:00'),
        ('17:00', '17:00'),
        ('18:00', '18:00'),
        ('19:00', '19:00'),
    ], string='Hora de fin')
    dias_disponibles = fields.Selection([
        ('lun_vie', 'Lunes a Viernes'),
        ('lun_sab', 'Lunes a Sabado'),
        ('sab_dom', 'Sabado y Domingo'),
        ('todos', 'Todos los dias'),
    ], string='Dias disponibles')
    observaciones_horario = fields.Text(string='Observaciones de horario')
    cita_ids = fields.One2many('veterinaria.cita', 'veterinario_id', string='Citas')
    cantidad_citas = fields.Integer(string='Cantidad de Citas', compute='_compute_cantidad_citas')
    can_edit_profile = fields.Boolean(compute='_compute_can_edit_profile')

    @api.depends('user_id')
    def _compute_can_edit_profile(self):
        is_admin = self.env.user.has_group('veterinaria_core.group_veterinaria_admin')
        for record in self:
            if is_admin:
                record.can_edit_profile = True
            elif not getattr(record, '_origin', record).id:
                # Si se está creando un nuevo registro (no guardado en BD aún)
                record.can_edit_profile = True
            elif record.user_id and record.user_id.id == self.env.uid:
                record.can_edit_profile = True
            else:
                record.can_edit_profile = False

    def _compute_cantidad_citas(self):
        for record in self:
            record.cantidad_citas = len(record.cita_ids)

    def _send_credentials_email(self, user, password):
        self.ensure_one()
        template = self.env.ref('veterinaria_core.mail_template_credenciales_veterinario', raise_if_not_found=False)
        if template:
            try:
                template.with_context(system_password=password).send_mail(self.id, force_send=True)
            except Exception as e:
                _logger.warning("No se pudo enviar el correo de credenciales: %s", e)

    def _create_system_user(self):
        self.ensure_one()
        if not self.email:
            return None, None

        # Generar contraseña más amigable basada en el nombre
        # Filtramos títulos comunes como Dr. o Dra.
        palabras = [p for p in self.name.replace('.', '').replace(',', '').split() 
                   if p.lower() not in ('dr', 'dra', 'vet', 'veterinario', 'medico', 'doc')]
        
        # Tomamos hasta las primeras dos palabras válidas (ej. Carlos Mendoza) y las capitalizamos
        base_password = "".join(p.capitalize() for p in palabras[:2])
        if not base_password:
            base_password = "VitalPet"
            
        password_temporal = f"{base_password}123"

        group_internal = self.env.ref('base.group_user')
        group_vet = self.env.ref('veterinaria_core.group_veterinaria_veterinario')

        same_login = self.env['res.users'].sudo().search([('login', '=', self.email)], limit=1)
        if same_login:
            same_login.sudo().write({
                'groups_id': [(6, 0, [group_internal.id, group_vet.id])],
                'password': password_temporal,
            })
            self.user_id = same_login.id
            return same_login, password_temporal

        user_vals = {
            'name': self.name,
            'login': self.email,
            'email': self.email,
            'password': password_temporal,
            'groups_id': [(6, 0, [group_internal.id, group_vet.id])],
        }
        new_user = self.env['res.users'].with_context(no_reset_password=True).sudo().create(user_vals)
        self.user_id = new_user.id
        return new_user, password_temporal

    from odoo import api
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.email and not record.user_id:
                try:
                    user, password = record._create_system_user()
                    if password:
                        record._send_credentials_email(user, password)
                except Exception as e:
                    _logger.error("Error creating system user for veterinario: %s", e)
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'email' in vals:
            for record in self:
                if record.email and not record.user_id:
                    try:
                        user, password = record._create_system_user()
                        if password:
                            record._send_credentials_email(user, password)
                    except Exception as e:
                        _logger.error("Error creating system user for veterinario (write): %s", e)
        return res

    def unlink(self):
        from odoo.exceptions import ValidationError
        for record in self:
            # Validar si tiene citas pendientes
            citas_pendientes = self.env['veterinaria.cita'].search([
                ('veterinario_id', '=', record.id),
                ('estado', '=', 'programada')
            ])
            if citas_pendientes:
                raise ValidationError(f"No se puede eliminar al veterinario '{record.name}' porque tiene {len(citas_pendientes)} cita(s) programada(s) pendiente(s). Por favor, reasigne o cancele las citas antes de eliminar.")
            
            # Intentar eliminar o archivar la cuenta de usuario de Odoo asociada
            if record.user_id:
                try:
                    record.user_id.unlink()
                except Exception as e:
                    # Si falla al eliminar (ej. por restricciones de claves foráneas), lo archivamos
                    record.user_id.write({'active': False})
                    _logger.warning("El usuario %s no pudo ser eliminado y fue archivado. Error: %s", record.user_id.login, e)
        return super().unlink()