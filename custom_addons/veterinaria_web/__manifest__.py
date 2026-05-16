# -*- coding: utf-8 -*-
{
    'name': 'VitalPet - Sitio Web Veterinaria',
    'summary': 'Sitio web profesional para la clínica veterinaria VitalPet',
    'description': '''
        Módulo completo para el sitio web de VitalPet.
        Incluye páginas de inicio, servicios, nosotros y contacto.
        Desarrollado con QWeb, Bootstrap y buenas prácticas de Odoo 18.
    ''',
    'author': 'VitalPet Dev Team',
    'website': 'https://www.vitalpet.com',
    'category': 'Website',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',

    'depends': [
        'website',
    ],

    'data': [
        'views/assets.xml',
        'views/layout.xml',
        'views/snippets/navbar.xml',
        'views/snippets/footer.xml',
        'views/pages/inicio.xml',
        'views/pages/servicios.xml',
        'views/pages/nosotros.xml',
        'views/pages/contacto.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'veterinaria_web/static/src/css/variables.css',
            'veterinaria_web/static/src/css/layout.css',
            'veterinaria_web/static/src/css/inicio.css',
            'veterinaria_web/static/src/css/servicios.css',
            'veterinaria_web/static/src/css/nosotros.css',
            'veterinaria_web/static/src/css/contacto.css',
            'veterinaria_web/static/src/css/animations.css',
            'veterinaria_web/static/src/js/main.js',
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
