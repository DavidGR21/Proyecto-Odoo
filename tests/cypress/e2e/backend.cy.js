describe('VitalPet Backend Tests (Odoo)', { defaultCommandTimeout: 15000 }, () => {
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
      cy.wait(1000); // Wait for the autocomplete dropdown to fetch results
      cy.get(`div[name="${fieldName}"] input`).type('{downarrow}{enter}', {force: true});
    } else {
      cy.get(`div[name="${fieldName}"] input`).click({force: true});
      cy.wait(500);
      cy.get(`div[name="${fieldName}"] input`).type('{downarrow}{enter}', {force: true});
    }
    cy.wait(1000);
  };

  it('Navigates to the Veterinaria App', () => {
    goToApp();
    cy.contains('Gestión Clínica').should('exist');
  });

  it('Creates a Propietario', () => {
    goToApp();
    
    cy.contains('Gestión Clínica').should('be.visible').click();
    cy.contains('Dueños').should('be.visible').click();
    
    cy.wait(1500);
    cy.contains(/Nuevo|Crear|New/i).first().click({force: true});
    
    cy.get('div[name="name"] input').should('be.visible').clear().type('Dueño Cypress Automático');
    autoSave();
    cy.contains('Dueño Cypress Automático').should('exist');
  });

  it('Creates a new Paciente', () => {
    goToApp();
    
    cy.contains('Gestión Clínica').should('be.visible').click();
    cy.contains('Pacientes').should('be.visible').click();

    cy.wait(1500);
    cy.contains(/Nuevo|Crear|New/i).first().click({force: true});

    cy.get('div[name="name"] input').should('be.visible').clear().type('Firulais Cypress');
    cy.get('div[name="especie"] select').select('"perro"');

    fillMany2one('propietario_id', 'Dueño Cypress Automático');

    autoSave();
    cy.contains('Firulais Cypress').should('exist');
  });
});
