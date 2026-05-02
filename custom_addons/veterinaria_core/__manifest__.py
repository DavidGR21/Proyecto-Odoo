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
        'sale',
        'account',
        'calendar',
        'stock',
        'crm',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/propietario_view.xml',
        'views/veterinario_view.xml',
        'views/menu.xml',
        'views/paciente_view.xml',
        'views/historia_clinica_view.xml',
        'views/medicamento_view.xml',
        'views/cita_view.xml',
        'views/producto_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
