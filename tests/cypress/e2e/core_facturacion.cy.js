describe('Pruebas Cypress - Módulo Facturación y SRI', { defaultCommandTimeout: 15000 }, () => {
  Cypress.on('uncaught:exception', (err, runnable) => { return false; });
  Cypress.on('unhandledRejection', (err, promise) => { return false; });

  beforeEach(() => {
    cy.visit('/web/login');
    cy.wait(1000);
    cy.get('input[name="login"]').clear({force: true}).type('admin', {force: true});
    cy.get('input[name="password"]').clear({force: true}).type('admin{enter}', {force: true});
    cy.url().should('not.include', '/login');
    cy.wait(2000);
  });

  const goToApp = () => {
    cy.get('.o_navbar_apps_menu').click();
    cy.contains('Veterinaria').should('be.visible').click();
    cy.wait(1000);
  };

  const autoSave = () => {
    cy.get('body').then($body => {
      if ($body.find('.o_form_button_save').length > 0) {
        cy.get('.o_form_button_save').first().click({force: true});
      } else {
        cy.get('body').click(0,0);
      }
    });
    cy.wait(1500);
  };

  const fillMany2one = (fieldName, searchText = '') => {
    if (searchText) {
      cy.get(`div[name="${fieldName}"] input`).clear({force: true}).type(searchText, {force: true});
      cy.wait(1000); // Wait for autocomplete
      cy.get(`div[name="${fieldName}"] input`).type('{downarrow}{enter}', {force: true});
    } else {
      cy.get(`div[name="${fieldName}"] input`).click({force: true});
      cy.wait(500);
      cy.get(`div[name="${fieldName}"] input`).type('{downarrow}{enter}', {force: true});
    }
    cy.wait(1000);
  };

  it('1. Prueba de Acceso a Documentos Electrónicos SRI', () => {
    goToApp();
    // Accedemos al menú SRI que vemos en la barra superior
    cy.contains('Documentos Electrónicos SRI').click({force: true});
    cy.wait(1500);
    
    // Verificamos que la vista cargue correctamente (suele ser de solo lectura o sincronizada)
    cy.get('.o_list_view, .o_kanban_view').should('exist');
  });

  it('2. Prueba de Gestión de Facturación y Ventas', () => {
    goToApp();
    // Accedemos al menú principal de facturación
    cy.contains('Facturación y Ventas').click({force: true});
    cy.wait(1500);
    
    cy.get('body').then($body => {
      // Si hay botón de crear, creamos una factura/venta de prueba
      if ($body.find('button.o_list_button_add, button.o_form_button_create').length > 0) {
        cy.contains(/Nuevo|Crear|New/i).first().click({force: true});
        
        cy.get('body').then($body2 => {
          if ($body2.find('div[name="propietario_id"] input').length > 0) {
            fillMany2one('propietario_id', 'Dueño Base Cypress');
          }
        });
        autoSave();
      }
    });
  });
});
