import sys
sys.path.append("/opt/odoo")
import odoo
odoo.tools.config.parse_config(['-d', 'postgres'])
registry = odoo.registry('postgres')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, 1, {})
    rules = env['ir.rule'].search([('model_id.model', '=', 'veterinaria.cita')])
    for r in rules:
        print(f"Rule: {r.name}, Domain: {r.domain_force}, Groups: {r.groups.mapped('name')}")
    users = env['res.users'].search([])
    for u in users:
        print(f"User: {u.name}, Groups: {u.groups_id.mapped('name')}")
