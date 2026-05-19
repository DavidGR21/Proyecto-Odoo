# -*- coding: utf-8 -*-
{
    'name': 'Facturación Electrónica SRI Ecuador (Veterinaria)',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Integración con el SRI de Ecuador en modo pruebas para facturación electrónica',
    'description': """
        Módulo de facturación electrónica para el SRI de Ecuador.
        - Generación de XML según XSD 2.1.0
        - Clave de acceso con dígito verificador Módulo 11
        - Firma electrónica XAdES-BES con certificado .p12
        - Envío al Web Service SOAP del SRI (ambiente de pruebas)
        - Generación del RIDE (PDF) con código de barras Code128
        - Envío automático del RIDE por email al cliente
    """,
    'author': 'VitalPet Team',
    'website': 'https://www.vitalpet.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
        'veterinaria_core',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/sri_catalogo_data.xml',
        # Views
        'views/res_company_view.xml',
        'views/sri_documento_view.xml',
        'views/facturacion_view_inherit.xml',
        # Reports
        'report/ride_report.xml',
        'report/ride_template.xml',
    ],
    'external_dependencies': {
        'python': ['zeep', 'barcode', 'stdnum'],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
