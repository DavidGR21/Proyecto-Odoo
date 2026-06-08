import sys
sys.path.append("/opt/odoo")
import odoo

def run():
    registry = odoo.registry('postgres')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        users = env['res.users'].search([('name', 'ilike', 'sadfsdfsdf')])
        if not users:
            print("No user found")
            return
        user = users[0]
        print(f"User ID: {user.id}")
        
        citas = env['veterinaria.cita'].search([])
        for c in citas:
            vet_user_id = c.veterinario_id.user_id.id if c.veterinario_id and c.veterinario_id.user_id else None
            print(f"Cita {c.id}: Vet User ID = {vet_user_id}, Vet Name = {c.veterinario_id.name}")

        # Check the rule explicitly
        rule = env.ref('veterinaria_core.rule_cita_veterinario')
        print(f"Rule Domain: {rule.domain_force}")
        
        # Check what compute_domain gives for this user
        env_user = odoo.api.Environment(cr, user.id, {})
        domain = env_user['ir.rule']._compute_domain('veterinaria.cita', 'read')
        print(f"Computed domain for user: {domain}")

if __name__ == '__main__':
    run()
