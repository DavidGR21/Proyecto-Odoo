# -*- coding: utf-8 -*-
{
    'name': 'Veterinaria Core',
    'version': '18.0.1.0.0',
    'category': 'Veterinary',
    'summary': 'Módulo base para la gestión de veterinaria',
    'description': """
        Módulo principal para VitalPet
        - Gestión de mascotas (pacientes)
        - Gestión de historia clínica
        - Gestión de medicamentos
        - Integración con Calendario, Inventario, Ventas, Contabilidad y CRM
    """,
    'author': 'VitalPet Team',
    'website': 'https://www.vitalpet.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',      # Agregado: Necesario para el chatter (mail.thread y mail.activity.mixin)
        'sale',
        'account',
        'calendar',
        'stock',
        'crm',
    ],
    'data': [
        # Security (groups must load before ACL)
        'security/veterinaria_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/mail_templates.xml',
        'data/cron_recordatorio.xml',
        # Views
        'views/propietario_view.xml',
        'views/especialidad_view.xml',
        'views/veterinario_view.xml',
        'views/paciente_view.xml',
        'views/historia_clinica_view.xml',
        'views/medicamento_view.xml',
        'views/cita_view.xml',
        'views/producto_view.xml',
        'views/servicio_view.xml',
        'views/inventario_view.xml',
        'views/venta_view.xml',
        'views/facturacion_view.xml',
        'views/facturacion_linea_view.xml',
        'views/facturacion_wizard_view.xml',
        'views/documento_venta_view.xml',
        'views/receta_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}