# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class ResCompanySRI(models.Model):
    _inherit = 'res.company'

    # ── Ambiente SRI ──────────────────────────────────────────────────────────
    sri_ambiente = fields.Selection([
        ('1', 'Pruebas'),
        ('2', 'Producción'),
    ], string='Ambiente SRI', default='1',
       help='Ambiente del SRI. SOLO PRUEBAS en esta versión.')

    sri_tipo_emision = fields.Selection([
        ('1', 'Normal'),
    ], string='Tipo de Emisión', default='1')

    # ── Certificado de Firma Electrónica ──────────────────────────────────────
    sri_certificado_p12 = fields.Binary(
        string='Certificado Firma Electrónica (.p12)',
        help='Archivo .p12 de firma electrónica emitido por entidad certificadora'
    )
    sri_certificado_filename = fields.Char(string='Nombre del archivo .p12')
    sri_certificado_password = fields.Char(
        string='Contraseña del Certificado',
        help='Contraseña del archivo .p12'
    )

    # ── Datos del Establecimiento ─────────────────────────────────────────────
    sri_establecimiento = fields.Char(
        string='Establecimiento', size=3, default='001',
        help='Código del establecimiento (3 dígitos)')
    sri_punto_emision = fields.Char(
        string='Punto de Emisión', size=3, default='001',
        help='Código del punto de emisión (3 dígitos)')
    sri_secuencial = fields.Integer(
        string='Último Secuencial', default=0,
        help='Se auto-incrementa con cada factura enviada al SRI')

    # ── Datos Tributarios ─────────────────────────────────────────────────────
    sri_razon_social = fields.Char(
        string='Razón Social SRI',
        help='Si está vacío se usa el nombre de la compañía')
    sri_nombre_comercial = fields.Char(string='Nombre Comercial')
    sri_obligado_contabilidad = fields.Boolean(
        string='Obligado a llevar Contabilidad', default=False)
    sri_contribuyente_especial = fields.Char(
        string='Nro. Resolución Contribuyente Especial',
        help='Solo si aplica. Dejar vacío si no es contribuyente especial')
    sri_direccion_matriz = fields.Char(
        string='Dirección Matriz',
        help='Dirección fiscal del establecimiento matriz')
    sri_direccion_establecimiento = fields.Char(
        string='Dirección Establecimiento',
        help='Dirección del punto de emisión')

    # ── Métodos ───────────────────────────────────────────────────────────────

    def sri_get_next_secuencial(self):
        """Obtiene e incrementa el secuencial para la siguiente factura."""
        self.ensure_one()
        self.sri_secuencial += 1
        return str(self.sri_secuencial).zfill(9)

    @api.constrains('vat')
    def _check_vat_sri(self):
        """Valida que el RUC de la compañía tenga 13 dígitos."""
        for company in self:
            if company.vat and not re.match(r'^\d{13}$', company.vat):
                raise ValidationError(
                    'El RUC de la compañía debe tener exactamente 13 dígitos numéricos '
                    'para poder emitir comprobantes electrónicos al SRI.')

    @api.constrains('sri_establecimiento', 'sri_punto_emision')
    def _check_sri_establecimiento(self):
        for company in self:
            if company.sri_establecimiento and not re.match(r'^\d{3}$', company.sri_establecimiento):
                raise ValidationError('El establecimiento debe tener exactamente 3 dígitos.')
            if company.sri_punto_emision and not re.match(r'^\d{3}$', company.sri_punto_emision):
                raise ValidationError('El punto de emisión debe tener exactamente 3 dígitos.')
