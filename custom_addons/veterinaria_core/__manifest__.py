# -*- coding: utf-8 -*-
{
    'name': 'Veterinaria Core',
    'version': '18.0.1.0.0',
    'category': 'Veterinary',
    'summary': 'Módulo base para la gestión de veterinaria',
    'description': """
        Módulo principal para VitalPet
        - Gestión de mascotas
        - Gestión de propietarios
        - Gestión de citas
    """,
    'author': 'VitalPet Team',
    'website': 'https://www.vitalpet.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'account',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
