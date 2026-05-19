# -*- coding: utf-8 -*-
import base64
from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, get_error


class VeterinariaPortal(CustomerPortal):
    """Portal para clientes (propietarios) de la veterinaria.

    Reutiliza el layout estándar de Odoo (portal.portal_layout) y agrega
    secciones para mascotas, citas, historia clínica, recetas, facturas y
    el carnet de vacunación (PDF descargable).
    """

    # ------------------------------------------------------------------
    # Permitir actualizar la foto de perfil desde /my/account
    # ------------------------------------------------------------------
    def details_form_validate(self, data, partner_creation=False):
        """No validamos el campo image_1920 — solo lo dejamos pasar."""
        error, error_message = super().details_form_validate(data, partner_creation)
        # image_1920 viene como FileStorage; lo manejamos en account_update
        return error, error_message

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        """Override de la página /my/account para procesar la foto de perfil."""
        if post and request.httprequest.method == 'POST':
            # Procesar foto si viene en el form
            image_file = post.get('image_1920')
            # FileStorage de werkzeug expone .filename y .read()
            if image_file and hasattr(image_file, 'read'):
                content = image_file.read()
                if content:
                    request.env.user.partner_id.sudo().write({
                        'image_1920': base64.b64encode(content),
                    })
            # Eliminar la clave para no romper la validación estándar
            post.pop('image_1920', None)
        return super().account(redirect=redirect, **post)

    # ------------------------------------------------------------------
    # /my/security simplificado para Cliente Veterinaria
    # ------------------------------------------------------------------
    @http.route('/my/security', type='http', auth='user', website=True,
                methods=['GET', 'POST'])
    def security(self, **post):
        """Si el user es Cliente Vet, renderiza nuestra versión simplificada
        del template (solo cambio password + eliminar cuenta).
        Para todos los demás, usa la página estándar de Odoo."""
        if not request.env.user.has_group('veterinaria_core.group_veterinaria_cliente'):
            return super().security(**post)

        values = self._prepare_portal_layout_values()
        values['get_error'] = get_error
        values['errors'] = {}
        values['success'] = {}
        values['open_deactivate_modal'] = False

        if request.httprequest.method == 'POST':
            values.update(self._update_password(
                (post.get('old') or '').strip(),
                (post.get('new1') or '').strip(),
                (post.get('new2') or '').strip(),
            ))

        return request.render(
            'veterinaria_core.portal_my_security_simple',
            values,
            headers={
                'X-Frame-Options': 'SAMEORIGIN',
                'Content-Security-Policy': "frame-ancestors 'self'",
            },
        )

    # ------------------------------------------------------------------
    # Home portal: contadores en /my
    # ------------------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        Paciente = request.env['veterinaria.paciente']
        Cita = request.env['veterinaria.cita']
        Facturacion = request.env['veterinaria.facturacion']
        Receta = request.env['veterinaria.receta']

        if 'pet_count' in counters:
            values['pet_count'] = Paciente.search_count([
                ('propietario_id', '=', partner.id)
            ])
        if 'appointment_count' in counters:
            values['appointment_count'] = Cita.search_count([
                ('paciente_id.propietario_id', '=', partner.id),
                ('estado', '=', 'programada'),
                ('fecha_hora', '>=', fields.Datetime.now()),
            ])
        if 'invoice_count_vet' in counters:
            values['invoice_count_vet'] = Facturacion.search_count([
                ('propietario_id', '=', partner.id),
            ])
        if 'prescription_count' in counters:
            values['prescription_count'] = Receta.search_count([
                ('propietario_id', '=', partner.id),
            ])
        return values

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_my_pets_domain(self):
        return [('propietario_id', '=', request.env.user.partner_id.id)]

    def _check_pet_access(self, pet_id):
        """Asegura que la mascota pertenezca al usuario logueado.
        Las record rules ya filtran a nivel de ORM; este chequeo extra
        bloquea explícitamente cualquier acceso cruzado."""
        partner = request.env.user.partner_id
        pet = request.env['veterinaria.paciente'].search([
            ('id', '=', int(pet_id)),
            ('propietario_id', '=', partner.id),
        ], limit=1)
        return pet or None

    # ------------------------------------------------------------------
    # /my/pets — listado y detalle
    # ------------------------------------------------------------------
    @http.route(['/my/pets'], type='http', auth='user', website=True)
    def portal_my_pets(self, **kw):
        pets = request.env['veterinaria.paciente'].search(self._get_my_pets_domain())
        values = {
            'pets': pets,
            'page_name': 'pets',
            'default_url': '/my/pets',
        }
        return request.render('veterinaria_core.portal_my_pets', values)

    @http.route(['/my/pets/<int:pet_id>'], type='http', auth='user', website=True)
    def portal_my_pet_detail(self, pet_id, **kw):
        pet = self._check_pet_access(pet_id)
        if not pet:
            return request.redirect('/my/pets')
        values = {
            'pet': pet,
            'page_name': 'pet_detail',
            'default_url': '/my/pets',
        }
        return request.render('veterinaria_core.portal_my_pet_detail', values)

    # ------------------------------------------------------------------
    # /my/appointments — citas pasadas y futuras
    # ------------------------------------------------------------------
    @http.route(['/my/appointments'], type='http', auth='user', website=True)
    def portal_my_appointments(self, **kw):
        Cita = request.env['veterinaria.cita']
        partner = request.env.user.partner_id
        now = fields.Datetime.now()

        upcoming = Cita.search([
            ('paciente_id.propietario_id', '=', partner.id),
            ('fecha_hora', '>=', now),
        ], order='fecha_hora ASC')
        past = Cita.search([
            ('paciente_id.propietario_id', '=', partner.id),
            ('fecha_hora', '<', now),
        ], order='fecha_hora DESC', limit=50)

        values = {
            'upcoming': upcoming,
            'past': past,
            'page_name': 'appointments',
        }
        return request.render('veterinaria_core.portal_my_appointments', values)

    # ------------------------------------------------------------------
    # /my/medical_records — historia clínica
    # ------------------------------------------------------------------
    @http.route(['/my/medical_records'], type='http', auth='user', website=True)
    def portal_my_medical_records(self, **kw):
        partner = request.env.user.partner_id
        historias = request.env['veterinaria.historia_clinica'].search([
            ('paciente_id.propietario_id', '=', partner.id),
        ], order='fecha_apertura DESC')
        values = {
            'historias': historias,
            'page_name': 'medical_records',
        }
        return request.render('veterinaria_core.portal_my_medical_records', values)

    # ------------------------------------------------------------------
    # /my/invoices_vet — facturas veterinarias
    # ------------------------------------------------------------------
    @http.route(['/my/invoices_vet'], type='http', auth='user', website=True)
    def portal_my_vet_invoices(self, **kw):
        partner = request.env.user.partner_id
        facturas = request.env['veterinaria.facturacion'].search([
            ('propietario_id', '=', partner.id),
        ], order='fecha_factura DESC')
        values = {
            'facturas': facturas,
            'page_name': 'invoices_vet',
        }
        return request.render('veterinaria_core.portal_my_vet_invoices', values)

    def _check_invoice_access(self, factura_id):
        """Devuelve la factura si pertenece al usuario, sino None."""
        partner = request.env.user.partner_id
        factura = request.env['veterinaria.facturacion'].search([
            ('id', '=', int(factura_id)),
            ('propietario_id', '=', partner.id),
        ], limit=1)
        return factura or None

    @http.route(['/my/invoices_vet/<int:factura_id>'],
                type='http', auth='user', website=True)
    def portal_my_vet_invoice_detail(self, factura_id, **kw):
        factura = self._check_invoice_access(factura_id)
        if not factura:
            return request.redirect('/my/invoices_vet')
        values = {
            'factura': factura,
            'page_name': 'invoices_vet_detail',
        }
        return request.render(
            'veterinaria_core.portal_my_vet_invoice_detail', values
        )

    @http.route(['/my/invoices_vet/<int:factura_id>/pdf'],
                type='http', auth='user', website=True)
    def portal_my_vet_invoice_pdf(self, factura_id, **kw):
        """Descarga el PDF de la factura veterinaria."""
        factura = self._check_invoice_access(factura_id)
        if not factura:
            return request.redirect('/my/invoices_vet')
        pdf, _ct = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'veterinaria_core.action_report_factura_veterinaria',
            [factura.id],
        )
        return request.make_response(pdf, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition',
             'attachment; filename="Factura_%s.pdf"' % (factura.name or factura.id)),
        ])

    # ------------------------------------------------------------------
    # /my/prescriptions — recetas
    # ------------------------------------------------------------------
    @http.route(['/my/prescriptions'], type='http', auth='user', website=True)
    def portal_my_prescriptions(self, **kw):
        partner = request.env.user.partner_id
        recetas = request.env['veterinaria.receta'].search([
            ('propietario_id', '=', partner.id),
        ], order='fecha_emision DESC')
        values = {
            'recetas': recetas,
            'page_name': 'prescriptions',
        }
        return request.render('veterinaria_core.portal_my_prescriptions', values)

    # ------------------------------------------------------------------
    # /my/vaccination_card/<pet_id> — descarga PDF del carnet de vacunas
    # ------------------------------------------------------------------
    @http.route(['/my/vaccination_card/<int:pet_id>'], type='http', auth='user', website=True)
    def portal_my_vaccination_card(self, pet_id, **kw):
        pet = self._check_pet_access(pet_id)
        if not pet:
            return request.redirect('/my/pets')
        # Renderiza el reporte QWeb-PDF definido en reports/carnet_vacunas_report.xml
        report_ref = 'veterinaria_core.action_report_carnet_vacunas'
        pdf, _content_type = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            report_ref, [pet.id]
        )
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition',
             'attachment; filename="carnet_vacunas_%s.pdf"' % (pet.name or pet.id)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
