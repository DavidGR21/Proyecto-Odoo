import sys
sys.path.append("/opt/odoo")
import odoo

def run():
    registry = odoo.registry('postgres')
    with registry.cursor() as cr:
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        # check action 524
        try:
            act_window = env['ir.actions.act_window'].browse(524)
            print(f"Action 524: type={act_window.type}, name={act_window.name}, res_model={act_window.res_model}")
        except Exception as e:
            print(f"Error reading 524 as act_window: {e}")
            
        # check the menu item
        menu = env.ref('veterinaria_core.menu_veterinaria_citas')
        print(f"Menu action points to: {menu.action}")
        
        # check the server action XML ID
        server_act = env.ref('veterinaria_core.action_veterinaria_cita')
        print(f"XML ID action_veterinaria_cita points to: {server_act} (type: {type(server_act)})")
        
if __name__ == '__main__':
    run()
