# -*- coding: utf-8 -*-
import logging
import secrets
import string
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def _generar_password_temporal(longitud=12):
    """Genera una contraseña aleatoria legible (sin caracteres confusos)."""
    alfabeto = string.ascii_letters + string.digits + '!@#$%&*'
    # Evita caracteres ambiguos
    alfabeto = alfabeto.replace('l', '').replace('I', '').replace('1', '') \
                       .replace('O', '').replace('0', '')
    return ''.join(secrets.choice(alfabeto) for _ in range(longitud))


class ResPartner(models.Model):
    _inherit = 'res.partner'

    es_propietario = fields.Boolean(string='Es propietario de mascota', default=False)
    observaciones_veterinaria = fields.Text(string='Observaciones veterinarias')
    paciente_ids = fields.One2many('veterinaria.paciente', 'propietario_id', string='Mascotas')
    cantidad_mascotas = fields.Integer(string='Cantidad de Mascotas', compute='_compute_cantidad_mascotas')
    cita_count = fields.Integer(string='Citas', compute='_compute_cita_count')

    # Flag visible para saber si ya tiene acceso portal creado
    tiene_acceso_portal = fields.Boolean(
        string='Tiene acceso al portal',
        compute='_compute_tiene_acceso_portal',
    )

    def _compute_cantidad_mascotas(self):
        for record in self:
            record.cantidad_mascotas = len(record.paciente_ids)

    def _compute_cita_count(self):
        cita_model = self.env['veterinaria.cita']
        for record in self:
            paciente_ids = record.paciente_ids.ids
            if paciente_ids:
                record.cita_count = cita_model.search_count([
                    ('paciente_id', 'in', paciente_ids)
                ])
            else:
                record.cita_count = 0

    @api.depends('user_ids')
    def _compute_tiene_acceso_portal(self):
        cliente_group = self.env.ref(
            'veterinaria_core.group_veterinaria_cliente', raise_if_not_found=False
        )
        for record in self:
            record.tiene_acceso_portal = bool(
                cliente_group and any(cliente_group in u.groups_id for u in record.user_ids)
            )

    # ==================================================================
    # Creación automática del usuario portal
    # ==================================================================
    def _send_credentials_email(self, user, password):
        self.ensure_one()
        template = self.env.ref('veterinaria_core.mail_template_credenciales_portal', raise_if_not_found=False)
        if template:
            try:
                template.with_context(portal_password=password).send_mail(self.id, force_send=True)
                _logger.info('Email de credenciales enviado a %s', self.email)
            except Exception as e:
                _logger.warning('Error al enviar email de credenciales a %s: %s', self.email, e)

    def _create_portal_user(self):
        """Crea un res.users vinculado al partner con el grupo Cliente Veterinaria (Portal).
        Si el usuario ya existe, le añade los grupos y le resetea la contraseña.
        Devuelve una tupla (user, password_temporal) — password_temporal es None
        si solo se actualizó un usuario existente sin regenerar la clave."""
        self.ensure_one()

        if not self.email:
            raise UserError(_(
                "El propietario '%s' debe tener un email para crearle un acceso al portal."
            ) % self.name)

        group_portal = self.env.ref('base.group_portal')
        group_cliente = self.env.ref('veterinaria_core.group_veterinaria_cliente')

        # Si el partner ya tiene un user, generamos nueva password temporal
        existing_user = self.user_ids[:1]
        if existing_user:
            nueva_clave = _generar_password_temporal()
            existing_user.sudo().write({
                'groups_id': [(4, group_portal.id), (4, group_cliente.id)],
                'password': nueva_clave,
            })
            return existing_user, nueva_clave

        # Comprobar si ya existe un user con ese login (email)
        same_login = self.env['res.users'].sudo().search(
            [('login', '=', self.email)], limit=1
        )
        if same_login:
            nueva_clave = _generar_password_temporal()
            same_login.sudo().write({
                'partner_id': self.id,
                'groups_id': [(4, group_portal.id), (4, group_cliente.id)],
                'password': nueva_clave,
            })
            return same_login, nueva_clave

        # Crear user nuevo con password temporal
        password_temporal = _generar_password_temporal()
        user_vals = {
            'name': self.name,
            'login': self.email,
            'email': self.email,
            'password': password_temporal,
            'partner_id': self.id,
            'groups_id': [(6, 0, [group_portal.id, group_cliente.id])],
        }
        # no_reset_password=True para evitar el correo automático que dispara
        # auth_signup cuando se crea un user sin password. Como SÍ asignamos
        # password, no queremos que Odoo además mande el reset.
        new_user = self.env['res.users'].with_context(
            no_reset_password=True
        ).sudo().create(user_vals)

        _logger.info("Usuario portal creado para propietario %s (login=%s)",
                     self.name, self.email)
        return new_user, password_temporal

    def action_crear_acceso_portal(self):
        """Botón en la vista del partner: crea/refresca el acceso al portal.
        Abre un diálogo modal con las credenciales (no las expone en la pantalla
        principal). Las credenciales también quedan en el log del servidor con
        el prefijo [PORTAL] para recuperarlas desde consola."""
        self.ensure_one()
        user, password = self._create_portal_user()
        _logger.info(
            "[PORTAL] Credenciales generadas para '%s': login=%s | password=%s",
            self.name, user.login, password,
        )
        wizard = self.env['veterinaria.credential.wizard'].sudo().create({
            'partner_name': self.name,
            'login': user.login,
            'password': password,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Credenciales de acceso al portal'),
            'res_model': 'veterinaria.credential.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.es_propietario and record.email and not record.user_ids:
                try:
                    user, password = record._create_portal_user()
                    if password:
                        record._send_credentials_email(user, password)
                    # Dejamos la pass en el log del servidor para que el admin
                    # pueda recuperarla si no la copió a tiempo (entorno dev).
                    _logger.info(
                        "[PORTAL] Acceso creado para '%s': login=%s | password=%s",
                        record.name, user.login, password,
                    )
                except Exception as e:
                    _logger.warning(
                        "No se pudo crear automáticamente el usuario portal "
                        "para %s: %s", record.name, e
                    )
        return records

    def write(self, vals):
        res = super().write(vals)
        if vals.get('es_propietario'):
            for record in self:
                if record.es_propietario and record.email and not record.user_ids:
                    try:
                        user, password = record._create_portal_user()
                        if password:
                            record._send_credentials_email(user, password)
                        _logger.info(
                            "[PORTAL] Acceso creado para '%s': login=%s | password=%s",
                            record.name, user.login, password,
                        )
                    except Exception as e:
                        _logger.warning(
                            "No se pudo crear automáticamente el usuario portal "
                            "para %s: %s", record.name, e
                        )
        return res

    # ==================================================================
    # Acciones existentes (sin cambios)
    # ==================================================================
    def action_view_mascotas(self):
        """Navegar a la lista de mascotas del propietario"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Mascotas de {self.name}',
            'res_model': 'veterinaria.paciente',
            'view_mode': 'list,form',
            'domain': [('propietario_id', '=', self.id)],
            'context': {
                'default_propietario_id': self.id,
            },
        }

    def action_view_citas(self):
        """Navegar a las citas de todas las mascotas del propietario"""
        self.ensure_one()
        paciente_ids = self.paciente_ids.ids
        return {
            'type': 'ir.actions.act_window',
            'name': f'Citas de {self.name}',
            'res_model': 'veterinaria.cita',
            'view_mode': 'list,calendar,form',
            'domain': [('paciente_id', 'in', paciente_ids)],
            'context': {
                'default_paciente_id': paciente_ids[0] if paciente_ids else False,
            },
        }

    def action_agendar_cita(self):
        """Abrir formulario de nueva cita con propietario pre-seleccionado"""
        self.ensure_one()
        paciente_ids = self.paciente_ids.ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agendar Cita',
            'res_model': 'veterinaria.cita',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_paciente_id': paciente_ids[0] if len(paciente_ids) == 1 else False,
            },
        }
