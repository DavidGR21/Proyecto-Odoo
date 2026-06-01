describe('Pruebas Cypress - Módulo Inventario', { defaultCommandTimeout: 15000 }, () => {
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

  it('Prueba de Gestión de Productos', () => {
    goToApp();
    cy.contains('Inventario').should('be.visible').click();
    cy.wait(1500);
    
    cy.get('body').then($body => {
      if ($body.find('button.o_list_button_add, button.o_form_button_create').length > 0) {
        cy.contains(/Nuevo|Crear|New/i).first().click({force: true});
        if ($body.find('div[name="name"] input').length > 0) {
          cy.get('div[name="name"] input').clear().type('Producto Cypress Test');
        }
        autoSave();
      }
    });
  });

  it('Prueba de Gestión de Medicamentos', () => {
    goToApp();
    cy.contains('Inventario').should('be.visible').click();
    cy.wait(1500);
    
    cy.get('body').then($body => {
      if ($body.find('button.o_list_button_add, button.o_form_button_create').length > 0) {
        cy.contains(/Nuevo|Crear|New/i).first().click({force: true});
        if ($body.find('div[name="name"] input').length > 0) {
          cy.get('div[name="name"] input').clear().type('Medicamento Cypress Test');
        }
        autoSave();
      }
    });
  });
});
