const { Stagehand } = require("@browserbasehq/stagehand");
const { expect } = require("playwright/test");
require("dotenv").config();

async function runStagehandTests() {
  // Initialize Stagehand
  const stagehand = new Stagehand({
    env: "LOCAL",
    apiKey: process.env.OPENAI_API_KEY, // Make sure this is in your .env
    modelName: "gpt-4o",
  });

  try {
    await stagehand.init();
    const page = stagehand.page;
    await page.goto("http://localhost:8070/web/login");

    console.log("=== Iniciando Flujo 1: Login y Crear Propietario/Paciente ===");
    // Login
    await page.fill('input[name="login"]', "admin");
    await page.fill('input[name="password"]', "admin");
    await page.click('form.oe_login_form button[type="submit"]');

    // Navegar a Veterinaria usando IA para encontrar los botones
    await page.act({ action: "Navegar a la aplicación 'Veterinaria' desde el menú principal de Odoo" });
    
    // Crear propietario
    await page.act({ action: "Hacer clic en el menú 'Dueños' y luego en 'Nuevo'" });
    await page.act({ action: "Llenar el formulario de propietario con el nombre 'Prueba', email 'prueba@gmail.com' y phone '0999999999' y guardar" });

    // Crear paciente asociado a ese propietario
    await page.act({ action: "Ir al menú 'Pacientes' y hacer clic en 'Nuevo'" });
    await page.act({ action: "Llenar el nombre del paciente como 'Rex', seleccionar a 'Juan Perez' como propietario, especie 'Perro' y guardar" });

    console.log("=== Iniciando Flujo 2: Agendar Cita Médica ===");
    await page.act({ action: "Ir al menú 'Agenda / Citas' y hacer clic en 'Nuevo'" });
    await page.act({ action: "Crear una nueva cita para el paciente 'Rex', seleccionando un veterinario disponible y una fecha en el futuro, luego guardar" });

    console.log("=== Iniciando Flujo 3: Facturación Básica ===");
    await page.act({ action: "Ir al menú 'Facturación y Ventas'" });
    await page.act({ action: "Crear una nueva factura para el propietario 'Juan Perez' y guardar" });

    console.log("Todas las pruebas de Stagehand completadas con éxito.");

  } catch (error) {
    console.error("Error durante las pruebas de Stagehand:", error);
  } finally {
    await stagehand.close();
  }
}

// Ejecutar si se llama directamente
if (require.main === module) {
  runStagehandTests();
}

module.exports = { runStagehandTests };
