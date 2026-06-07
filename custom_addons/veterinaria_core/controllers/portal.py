# -*- coding: utf-8 -*-
import base64
import logging
from werkzeug.utils import redirect as werkzeug_redirect
from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

try:
    from odoo.addons.portal.controllers.portal import get_error
except ImportError:
    # get_error fue removido en Odoo 18; definimos un fallback minimal
    def get_error(e='', msg=''):
        if isinstance(e, dict):
            return e.get(msg, '')
        return str(msg or e)

_logger = logging.getLogger(__name__)


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

    @http.route(['/my/pets/<int:pet_id>'], type='http', auth='user',
                website=True, methods=['GET', 'POST'])
    def portal_my_pet_detail(self, pet_id, **kw):
        """Detalle de mascota. POST procesa el cambio de foto del cliente."""
        pet = self._check_pet_access(pet_id)
        if not pet:
            return request.redirect('/my/pets')
        if request.httprequest.method == 'POST':
            # En Odoo 18 los archivos van a request.httprequest.files, NO a **kw
            foto_file = request.httprequest.files.get('foto')
            if foto_file and foto_file.filename:
                content = foto_file.read()
                if content:
                    try:
                        pet.sudo().write({'foto': base64.b64encode(content)})
                    except Exception as e:
                        _logger.error('Error al guardar foto mascota %s: %s', pet_id, e)
            return request.redirect(f'/my/pets/{pet_id}')
        values = {
            'pet': pet,
            'page_name': 'pet_detail',
            'default_url': '/my/pets',
        }
        return request.render('veterinaria_core.portal_my_pet_detail', values)

    # ------------------------------------------------------------------
    # /my/appointments/<id>/observations — guardar obs. del propietario
    # ------------------------------------------------------------------
    @http.route(['/my/appointments/<int:cita_id>/observations'], type='http',
                auth='user', website=True, methods=['POST'])
    def portal_appointment_observations(self, cita_id, **kw):
        """Guarda las observaciones del propietario en una cita programada."""
        partner = request.env.user.partner_id
        # Validación estricta: solo citas propias en estado programada
        cita = request.env['veterinaria.cita'].search([
            ('id', '=', int(cita_id)),
            ('paciente_id.propietario_id', '=', partner.id),
            ('estado', '=', 'programada'),
        ], limit=1)
        if not cita:
            return request.redirect('/my/appointments')
        texto = (kw.get('observaciones_cliente') or '').strip()
        cita.sudo().write({'observaciones_cliente': texto or False})
        return request.redirect('/my/appointments')

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

        # Acceso seguro a observaciones_cliente.
        # La columna puede no existir si el módulo aún no fue actualizado (-u).
        # El try/except permite que la página cargue de todas formas.
        obs_upcoming, obs_past = {}, {}
        try:
            obs_upcoming = {c.id: c.observaciones_cliente or '' for c in upcoming}
            obs_past = {c.id: c.observaciones_cliente or '' for c in past}
        except Exception:
            _logger.warning(
                'observaciones_cliente no disponible en BD. '
                'Ejecute: ./odoo-bin -u veterinaria_core'
            )

        values = {
            'upcoming': upcoming,
            'past': past,
            'page_name': 'appointments',
            'obs_upcoming': obs_upcoming,
            'obs_past': obs_past,
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
    def portal_my_vet_invoice_detail(self, factura_id, payment_status=None, **kw):
        factura = self._check_invoice_access(factura_id)
        if not factura:
            return request.redirect('/my/invoices_vet')
        values = {
            'factura': factura,
            'page_name': 'invoices_vet_detail',
            'payment_status': payment_status,  # 'success', 'cancel', 'error'
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
    # PayPal — helpers internos (usan la infraestructura nativa de Odoo 18)
    # ------------------------------------------------------------------
    def _get_paypal_provider(self):
        """Retorna el proveedor PayPal activo configurado en Odoo, o None."""
        provider = request.env['payment.provider'].sudo().search([
            ('code', '=', 'paypal'),
            ('state', 'in', ('enabled', 'test')),
        ], limit=1)
        return provider or None

    def _create_paypal_order(self, provider, factura, return_url, cancel_url):
        """Crea una orden PayPal usando el método nativo de Odoo.

        Devuelve (order_id, approval_url) o lanza excepción.
        El proveedor ya maneja internamente el token (caché + renovación).
        """
        company_currency = request.env.company.currency_id
        currency_code = company_currency.name if company_currency else 'USD'
        amount_str = '%.2f' % factura.total

        payload = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'reference_id': factura.name or str(factura.id),
                'description': f'Factura Veterinaria {factura.name} - VitalPet',
                'amount': {
                    'currency_code': currency_code,
                    'value': amount_str,
                },
            }],
            'payment_source': {
                'paypal': {
                    'experience_context': {
                        'brand_name': 'VitalPet',
                        'locale': 'es-EC',
                        'landing_page': 'LOGIN',
                        'user_action': 'PAY_NOW',
                        'return_url': return_url,
                        'cancel_url': cancel_url,
                    }
                }
            },
        }
        # _paypal_make_request gestiona el Bearer token automáticamente
        data = provider._paypal_make_request('/v2/checkout/orders', json_payload=payload)
        order_id = data.get('id')
        if not order_id:
            raise ValueError('PayPal no devolvió un order ID válido.')

        # Construimos la URL de checkout directamente desde el order_id.
        # Esto es más confiable que extraer el href de los links, ya que
        # el header PayPal-Partner-Attribution-Id de Odoo puede devolver
        # hrefs relativos que rompen el redirect.
        # Patrón: https://api-m.sandbox.paypal.com → https://www.sandbox.paypal.com
        checkout_base = provider._paypal_get_api_url().replace('api-m.', 'www.')
        approval_url = f'{checkout_base}/checkoutnow?token={order_id}'
        return order_id, approval_url

    def _capture_paypal_order(self, provider, order_id):
        """Captura (cobra) una orden PayPal aprobada. Devuelve True si completada."""
        try:
            data = provider._paypal_make_request(
                f'/v2/checkout/orders/{order_id}/capture',
                json_payload={},
            )
            return data.get('status') == 'COMPLETED'
        except Exception:
            _logger.exception('Error al capturar orden PayPal %s', order_id)
            return False

    # ------------------------------------------------------------------
    # /my/invoices_vet/<id>/pay — Iniciar pago PayPal
    # ------------------------------------------------------------------
    @http.route(['/my/invoices_vet/<int:factura_id>/pay'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_vet_invoice_pay(self, factura_id, **kw):
        """Inicia el flujo de pago PayPal para una factura veterinaria."""
        factura = self._check_invoice_access(factura_id)
        if not factura:
            return request.redirect('/my/invoices_vet')

        # Solo facturas validadas y no pagadas
        if factura.estado != 'validado' or factura.pagado:
            return request.redirect(
                f'/my/invoices_vet/{factura_id}?payment_status=error'
            )

        if factura.total <= 0:
            return request.redirect(
                f'/my/invoices_vet/{factura_id}?payment_status=error'
            )

        provider = self._get_paypal_provider()
        if not provider:
            _logger.error('No hay proveedor PayPal activo configurado en Odoo.')
            return request.redirect(
                f'/my/invoices_vet/{factura_id}?payment_status=error'
            )

        try:
            base_site = request.httprequest.host_url.rstrip('/')
            return_url = f'{base_site}/my/invoices_vet/{factura_id}/payment/return'
            cancel_url = f'{base_site}/my/invoices_vet/{factura_id}/payment/cancel'

            order_id, approval_url = self._create_paypal_order(
                provider, factura, return_url, cancel_url
            )

            if not approval_url:
                raise ValueError('No se obtuvo approval_url de PayPal.')

            # Guardar referencia de la orden PayPal en la factura
            factura.sudo().write({'payment_reference': order_id})

            _logger.info(
                'Factura %s: orden PayPal %s creada. Redirigiendo a: %s',
                factura.name, order_id, approval_url,
            )
            # Usamos werkzeug_redirect para garantizar un 302 limpio
            # hacia la URL externa de PayPal sin que Odoo modifique la URL.
            return werkzeug_redirect(approval_url, code=302)

        except Exception as e:
            _logger.exception('Error al crear orden PayPal para factura %s: %s', factura_id, e)
            return request.redirect(
                f'/my/invoices_vet/{factura_id}?payment_status=error'
            )

    # ------------------------------------------------------------------
    # /my/invoices_vet/<id>/payment/return — Retorno de PayPal (éxito)
    # ------------------------------------------------------------------
    @http.route(['/my/invoices_vet/<int:factura_id>/payment/return'],
                type='http', auth='user', website=True, methods=['GET'])
    def portal_vet_invoice_payment_return(self, factura_id, token=None, PayerID=None, **kw):
        """Callback de retorno de PayPal. Captura la orden y marca la factura como pagada."""
        factura = self._check_invoice_access(factura_id)
        if not factura:
            return request.redirect('/my/invoices_vet')

        # Verificar que no esté ya pagada
        if factura.pagado:
            return request.redirect(
                f'/my/invoices_vet/{factura_id}?payment_status=success'
            )

        order_id = factura.payment_reference
        if not order_id:
            _logger.error('No hay order_id PayPal registrado para factura %s', factura_id)
            return request.redirect(
                f'/my/invoices_vet/{factura_id}?payment_status=error'
            )

        provider = self._get_paypal_provider()
        if not provider:
            return request.redirect(
                f'/my/invoices_vet/{factura_id}?payment_status=error'
            )

        try:
            captured = self._capture_paypal_order(provider, order_id)

            if captured:
                # Marcar factura como pagada
                factura.sudo().write({
                    'pagado': True,
                    'fecha_pago': fields.Datetime.now(),
                })
                # Registrar en el chatter
                factura.sudo().message_post(
                    body=f'✅ Pago recibido via PayPal. Orden: {order_id}',
                    message_type='notification',
                )
                _logger.info('Factura %s pagada exitosamente via PayPal (orden %s).', factura.name, order_id)
                return request.redirect(
                    f'/my/invoices_vet/{factura_id}?payment_status=success'
                )
            else:
                _logger.warning('Captura PayPal fallida para factura %s, orden %s.', factura_id, order_id)
                return request.redirect(
                    f'/my/invoices_vet/{factura_id}?payment_status=error'
                )

        except Exception as e:
            _logger.exception('Error al capturar pago PayPal para factura %s: %s', factura_id, e)
            return request.redirect(
                f'/my/invoices_vet/{factura_id}?payment_status=error'
            )

    # ------------------------------------------------------------------
    # /my/invoices_vet/<id>/payment/cancel — Pago cancelado por el usuario
    # ------------------------------------------------------------------
    @http.route(['/my/invoices_vet/<int:factura_id>/payment/cancel'],
                type='http', auth='user', website=True, methods=['GET'])
    def portal_vet_invoice_payment_cancel(self, factura_id, **kw):
        """El usuario canceló el pago desde la página de PayPal."""
        factura = self._check_invoice_access(factura_id)
        if not factura:
            return request.redirect('/my/invoices_vet')
        _logger.info('Pago cancelado por usuario para factura %s.', factura_id)
        return request.redirect(
            f'/my/invoices_vet/{factura_id}?payment_status=cancel'
        )

    # ------------------------------------------------------------------
    # /my/prescriptions — recetas
    # ------------------------------------------------------------------
    @http.route(['/my/prescriptions'], type='http', auth='user', website=True)
    def portal_my_prescriptions(self, **kw):
        from datetime import timedelta
        partner = request.env.user.partner_id
        recetas = request.env['veterinaria.receta'].search([
            ('propietario_id', '=', partner.id),
        ], order='fecha_emision DESC')

        today = fields.Date.today()
        receta_status = {}
        for r in recetas:
            if r.state == 'finalizada':
                receta_status[r.id] = 'facturada'
            elif r.linea_ids:
                max_dias = max((l.duracion_dias for l in r.linea_ids), default=0)
                if r.fecha_emision and max_dias > 0:
                    fecha_fin = r.fecha_emision.date() + timedelta(days=max_dias)
                    receta_status[r.id] = 'activa' if fecha_fin >= today else 'terminada'
                else:
                    receta_status[r.id] = 'activa'
            else:
                receta_status[r.id] = 'activa'

        values = {
            'recetas': recetas,
            'receta_status': receta_status,
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

