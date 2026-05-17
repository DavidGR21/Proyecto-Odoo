# -*- coding: utf-8 -*-
{
    'name': 'Veterinaria Core',
    'version': '18.0.1.5.1',
    'category': 'Veterinary',
    'summary': 'Módulo base para la gestión de veterinaria, incluyendo portal del cliente',
    'description': """
        Módulo principal para VitalPet
        - Gestión de mascotas (pacientes)
        - Gestión de historia clínica
        - Gestión de medicamentos
        - Integración con Calendario, Inventario, Ventas, Contabilidad y CRM
        - Portal del cliente: mascotas, citas, historia, facturas, recetas
          y carnet de vacunación descargable en PDF
    """,
    'author': 'VitalPet Team',
    'website': 'https://www.vitalpet.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
        'portal',
        'auth_signup',  # permite enviar invitación por email al crear el portal user
        'sale',
        'account',
        'calendar',
        'stock',
        'crm',
    ],
    'data': [
        # Security (groups must load before ACL)
        'security/veterinaria_security.xml',
        'security/portal_security.xml',
        'security/ir.model.access.csv',
        # Data (secuencias antes de cualquier modelo que las use)
        'data/sequences.xml',
        'data/mail_server.xml',
        'data/mail_templates.xml',
        'data/cron_recordatorio.xml',
        # Views (wizards y modelos base primero)
        'views/credential_wizard_view.xml',
        'views/propietario_view.xml',
        'views/especialidad_view.xml',
        'views/veterinario_view.xml',
        'views/paciente_view.xml',
        'views/historia_clinica_view.xml',
        'views/medicamento_view.xml',
        'views/producto_view.xml',
        'views/servicio_view.xml',
        'views/inventario_view.xml',
        'views/venta_view.xml',
        'views/facturacion_view.xml',
        'views/facturacion_linea_view.xml',
        'views/facturacion_wizard_view.xml',
        'views/documento_venta_view.xml',
        # Menús base (deben cargarse antes de submenus en vacunas/recetas)
        'views/menu.xml',
        # Cita debe cargarse antes de receta_view (receta extiende la vista de cita)
        'views/cita_view.xml',
        'views/vacuna_view.xml',
        'views/receta_view.xml',
        # Portal templates (deben cargarse tras los menús)
        'views/portal_templates.xml',
        # Reports
        'reports/carnet_vacunas_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
