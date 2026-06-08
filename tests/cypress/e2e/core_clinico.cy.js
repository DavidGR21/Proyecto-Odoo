describe('Pruebas Cypress - Módulo Clínico', { defaultCommandTimeout: 15000 }, () => {
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

  it('1. Crea Datos Base (Especialidad, Dueño, Paciente, Veterinario, Vacuna)', () => {
    goToApp();
    
    // Crear Especialidad
    cy.contains('Gestión Clínica').should('be.visible').click();
    cy.contains('Especialidades').should('be.visible').click();
    cy.wait(1500);
    cy.contains(/Nuevo|Crear|New/i).first().click({force: true});
    cy.get('div[name="name"] input').clear().type('Cirugía');
    autoSave();

    // Crear Veterinario
    cy.contains('Gestión Clínica').should('be.visible').click();
    cy.contains('Veterinarios').should('be.visible').click();
    cy.wait(1500);
    cy.contains(/Nuevo|Crear|New/i).first().click({force: true});
    cy.get('div[name="name"] input').clear().type('Dr. Base Cypress');
    fillMany2one('especialidad_id', 'Cirugía');
    autoSave();

    // Crear Dueño
    cy.contains('Gestión Clínica').should('be.visible').click();
    cy.contains('Dueños').should('be.visible').click();
    cy.wait(1500);
    cy.contains(/Nuevo|Crear|New/i).first().click({force: true});
    cy.get('div[name="name"] input').clear().type('Dueño Base Cypress');
    autoSave();

    // Crear Paciente
    cy.contains('Gestión Clínica').should('be.visible').click();
    cy.contains('Pacientes').should('be.visible').click();
    cy.wait(1500);
    cy.contains(/Nuevo|Crear|New/i).first().click({force: true});
    cy.get('div[name="name"] input').clear().type('Paciente Base Cypress');
    cy.get('div[name="especie"] select').select('"perro"');
    fillMany2one('propietario_id', 'Dueño Base Cypress');
    autoSave();

    // Crear Vacuna
    cy.contains('Gestión Clínica').should('be.visible').click();
    cy.contains('Vacunas').should('be.visible').click();
    cy.wait(1500);
    cy.contains(/Nuevo|Crear|New/i).first().click({force: true});
    cy.get('div[name="name"] input').clear().type('Vacuna Base Cypress');
    autoSave();
  });

  it('2. Prueba de Citas Médicas (Usa Paciente)', () => {
    goToApp();
    cy.contains('Agenda / Citas').should('be.visible').click();
    cy.wait(1500);
    cy.contains(/Nuevo|Crear|New/i).first().click({force: true});
    
    cy.get('body').then($body => {
      if ($body.find('div[name="name"] input').length > 0) {
        cy.get('div[name="name"] input').clear().type('Cita de Prueba Cypress');
      }
    });
    fillMany2one('paciente_id', 'Paciente Base Cypress');
    autoSave();
  });

  it('3. Verificación de Acceso a Historias Clínicas (Auto-generadas)', () => {
    goToApp();
    cy.contains('Gestión Clínica').should('be.visible').click();
    cy.contains('Historia Clínica').should('be.visible').click();
    cy.wait(1500);
    
    // Verificamos que la vista cargue sin errores
    cy.get('.o_list_view, .o_kanban_view').should('exist');
    
    // Validamos la regla de negocio: No debe haber botón de Nuevo porque Odoo las genera desde las Citas
    cy.contains(/Nuevo|Crear|New/i).should('not.exist');
  });

  it('4. Verificación de Acceso a Recetas Médicas', () => {
    goToApp();
    cy.contains('Gestión Clínica').should('be.visible').click();
    cy.contains('Recetas').should('be.visible').click();
    cy.wait(1500);
    
    // Verificamos que la vista cargue sin errores y esté lista
    cy.get('.o_list_view, .o_kanban_view').should('exist');
  });
});
