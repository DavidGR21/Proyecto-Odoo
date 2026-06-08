describe('VitalPet Frontend Tests', { defaultCommandTimeout: 15000 }, () => {
  Cypress.on('uncaught:exception', (err, runnable) => {
    return false;
  });
  Cypress.on('unhandledRejection', (err, promise) => {
    return false;
  });

  it('Visits the Home Page', () => {
    cy.visit('/');
    cy.title().should('include', 'VitalPet');
    // Verify main header or welcome text exists
    cy.contains('VitalPet').should('be.visible');
  });

  it('Visits the Servicios Page', () => {
    cy.visit('/servicios');
    cy.title().should('include', 'Servicios');
    cy.contains('Consulta General').should('be.visible');
    cy.contains('Vacunación').should('be.visible');
  });

  it('Visits the Nosotros Page', () => {
    cy.visit('/nosotros');
    cy.title().should('include', 'Nosotros');
    cy.contains('Dra. María López').should('be.visible');
  });

  it('Submits the Contacto Form', () => {
    cy.visit('/contacto');
    cy.title().should('include', 'Contacto');
    
    // Fill the form
    cy.get('input[name="nombre"]').type('Test User');
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('input[name="telefono"]').type('0999999999');
    cy.get('select[name="asunto"]').select('informacion');
    cy.get('textarea[name="mensaje"]').type('Este es un mensaje de prueba desde Cypress.');
    
    // Submit
    cy.get('button.vp-form-btn').click({force: true});
    
    // Check success message or redirected state
    // We expect "enviado": True in the controller, so we can verify if the name appears or a success message
    cy.contains('Test User').should('exist');
  });
});
