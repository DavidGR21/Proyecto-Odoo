# -*- coding: utf-8 -*-

import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class VitalPetWebsite(http.Controller):
    """Controlador principal del sitio web VitalPet.

    Maneja todas las rutas públicas del sitio web de la clínica veterinaria.
    Cada método renderiza un template QWeb específico heredando del layout
    principal del website de Odoo.
    """

    # -------------------------------------------------------------------------
    # Página de Inicio
    # -------------------------------------------------------------------------
    @http.route('/', type='http', auth='public', website=True, sitemap=True)
    def pagina_inicio(self, **kwargs):
        """Renderiza la página de inicio / landing page."""
        valores = {
            'titulo_pagina': 'VitalPet - Clínica Veterinaria',
        }
        return request.render('veterinaria_web.pagina_inicio', valores)

    # -------------------------------------------------------------------------
    # Página de Servicios
    # -------------------------------------------------------------------------
    @http.route('/servicios', type='http', auth='public', website=True, sitemap=True)
    def pagina_servicios(self, **kwargs):
        """Renderiza la página de servicios de la clínica."""
        servicios = [
            {
                'icono': 'fa-heartbeat',
                'titulo': 'Consulta General',
                'descripcion': 'Examen clínico completo, diagnóstico y tratamiento '
                               'personalizado para tu mascota.',
                'color': '#40C2D6',
            },
            {
                'icono': 'fa-plus-square',
                'titulo': 'Vacunación',
                'descripcion': 'Programa completo de vacunación para perros y gatos, '
                               'con seguimiento y recordatorios.',
                'color': '#9B7EBD',
            },
            {
                'icono': 'fa-cut',
                'titulo': 'Cirugía',
                'descripcion': 'Procedimientos quirúrgicos con equipos de última '
                               'generación y monitoreo post-operatorio.',
                'color': '#F4A4C3',
            },
            {
                'icono': 'fa-flask',
                'titulo': 'Laboratorio Clínico',
                'descripcion': 'Análisis de sangre, orina, heces y más. Resultados '
                               'rápidos y confiables.',
                'color': '#FFD4B8',
            },
            {
                'icono': 'fa-medkit',
                'titulo': 'Farmacia Veterinaria',
                'descripcion': 'Medicamentos especializados, alimentos terapéuticos '
                               'y suplementos para mascotas.',
                'color': '#40C2D6',
            },
            {
                'icono': 'fa-mobile',
                'titulo': 'App Móvil',
                'descripcion': 'Agenda citas, revisa el historial clínico y recibe '
                               'notificaciones desde tu celular.',
                'color': '#9B7EBD',
            },
            {
                'icono': 'fa-calendar-check-o',
                'titulo': 'Agenda de Citas',
                'descripcion': 'Reserva en línea, confirmación inmediata y '
                               'recordatorios automáticos por correo.',
                'color': '#F4A4C3',
            },
            {
                'icono': 'fa-file-text-o',
                'titulo': 'Historial Clínico',
                'descripcion': 'Registro digital completo de cada consulta, '
                               'tratamiento y evolución de tu mascota.',
                'color': '#FFD4B8',
            },
        ]
        valores = {
            'titulo_pagina': 'Servicios - VitalPet',
            'servicios': servicios,
        }
        return request.render('veterinaria_web.pagina_servicios', valores)

    # -------------------------------------------------------------------------
    # Página Nosotros
    # -------------------------------------------------------------------------
    @http.route('/nosotros', type='http', auth='public', website=True, sitemap=True)
    def pagina_nosotros(self, **kwargs):
        """Renderiza la página 'Sobre Nosotros' de la clínica."""
        equipo = [
            {
                'nombre': 'Dra. María López',
                'cargo': 'Directora Médica',
                'descripcion': 'Especialista en medicina interna con más de '
                               '15 años de experiencia.',
                'iniciales': 'ML',
                'color': '#40C2D6',
                'foto': 'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&q=80',
            },
            {
                'nombre': 'Dr. Carlos Mendoza',
                'cargo': 'Cirujano Veterinario',
                'descripcion': 'Experto en cirugía ortopédica y de tejidos '
                               'blandos.',
                'iniciales': 'CM',
                'color': '#9B7EBD',
                'foto': 'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&q=80',
            },
            {
                'nombre': 'Dra. Ana Rodríguez',
                'cargo': 'Dermatología Veterinaria',
                'descripcion': 'Especializada en enfermedades de piel y '
                               'alergias en mascotas.',
                'iniciales': 'AR',
                'color': '#F4A4C3',
                'foto': 'https://images.unsplash.com/photo-1594824476967-48c8b964273f?w=400&q=80',
            },
            {
                'nombre': 'Dr. Luis Herrera',
                'cargo': 'Imagenología',
                'descripcion': 'Especialista en ecografía, radiología y '
                               'diagnóstico por imagen.',
                'iniciales': 'LH',
                'color': '#FFD4B8',
                'foto': 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&q=80',
            },
        ]
        valores = {
            'titulo_pagina': 'Nosotros - VitalPet',
            'equipo': equipo,
        }
        return request.render('veterinaria_web.pagina_nosotros', valores)

    # -------------------------------------------------------------------------
    # Página de Contacto
    # -------------------------------------------------------------------------
    @http.route('/contacto', type='http', auth='public', website=True, sitemap=True)
    def pagina_contacto(self, **kwargs):
        """Renderiza la página de contacto con formulario."""
        valores = {
            'titulo_pagina': 'Contacto - VitalPet',
        }
        return request.render('veterinaria_web.pagina_contacto', valores)

    @http.route('/contacto/enviar', type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def contacto_enviar(self, **kwargs):
        """Procesa el formulario de contacto.

        Recibe los datos del formulario y los registra en el log.
        En producción, se puede extender para enviar correos o crear
        registros en un modelo personalizado.
        """
        nombre = kwargs.get('nombre', '')
        email = kwargs.get('email', '')
        telefono = kwargs.get('telefono', '')
        asunto = kwargs.get('asunto', '')
        mensaje = kwargs.get('mensaje', '')

        _logger.info(
            'Formulario de contacto recibido - Nombre: %s, Email: %s, '
            'Teléfono: %s, Asunto: %s',
            nombre, email, telefono, asunto
        )

        valores = {
            'titulo_pagina': 'Contacto - VitalPet',
            'enviado': True,
            'nombre_enviado': nombre,
        }
        return request.render('veterinaria_web.pagina_contacto', valores)
