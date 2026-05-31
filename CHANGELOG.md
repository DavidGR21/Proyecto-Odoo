# Changelog — VitalPet

Todos los cambios notables de este proyecto están documentados en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.0.0/) y el proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [18.0.1.6.0] — 2025-05-31

### Añadido
- Control de ingreso de valores negativos en inventario de productos, medicamentos y servicios.
- Validación de stock al seleccionar productos/medicamentos en la factura: solo se muestran ítems con stock mayor a 0.
- Control de stock frente al total del pedido al momento de facturar.
- Extensión del control de stock para importación desde recetas (medicamentos asignados desde la cita).

### Corregido
- Error al intentar facturar productos sin stock suficiente.
- Visualización incorrecta de cantidades disponibles en el wizard de importación de receta.

---

## [18.0.1.5.0] — 2025-05-20

### Añadido
- Módulo `l10n_ec_sri_vet`: integración completa de facturación electrónica con el SRI de Ecuador.
  - Generación de XML según XSD 2.1.0 del SRI.
  - Firma digital XAdES-BES con certificado .p12 usando `cryptography`.
  - Envío SOAP al Web Service de Recepción del SRI (ambiente pruebas).
  - Consulta de autorización al WS del SRI.
  - Generación de RIDE (PDF) con código de barras Code128.
  - Envío automático de RIDE y XML autorizado al cliente por email.
- Vistas de configuración SRI en la empresa (`res.company`).
- Catálogos del SRI (tipos de identificación, formas de pago, códigos de impuesto).
- Reportes QWeb para el RIDE.

### Cambiado
- `veterinaria.facturacion` extendida con campos SRI: forma de pago, tipo de identificación, estado del documento electrónico.

---

## [18.0.1.4.0] — 2025-05-10

### Añadido
- Gestión completa de facturas veterinarias en el portal del cliente (`/my/invoices_vet`).
  - Listado de facturas del propietario.
  - Detalle de factura con líneas, subtotal, impuestos y total.
  - Descarga de PDF de factura desde el portal.
- Contador de facturas en el dashboard del portal (`/my`).

### Corregido
- Record rules del portal para facturas: el cliente solo ve sus propias facturas.

---

## [18.0.1.3.0] — 2025-04-25

### Añadido
- Módulo `veterinaria_web`: sitio web público de la clínica VitalPet.
  - Página de inicio (landing page).
  - Página de servicios con 7 servicios listados.
  - Página "Nosotros" con 4 miembros del equipo.
  - Página de contacto con formulario.
  - CSS personalizado, animaciones y diseño responsivo.
- Envío de emails a usuarios del portal (credenciales de acceso).
- Icono SVG de pata para la interfaz del módulo.

### Cambiado
- Se eliminó la sección de planes de precios de la página web.
- Se eliminó la sección de app store de la página web.

---

## [18.0.1.2.0] — 2025-04-10

### Añadido
- Portal del cliente (`veterinaria_core/controllers/portal.py`):
  - `/my/pets` — Listado de mascotas del propietario.
  - `/my/pets/<id>` — Detalle de mascota.
  - `/my/appointments` — Citas próximas y pasadas.
  - `/my/medical_records` — Historias clínicas.
  - `/my/prescriptions` — Recetas médicas.
  - `/my/vaccination_carnet` — Carnet de vacunación.
  - `/my/vaccination_carnet/<pet_id>/pdf` — Descarga PDF del carnet.
  - `/my/account` — Perfil con carga de foto.
  - `/my/security` — Cambio de contraseña simplificado.
- Reportes QWeb-PDF: carnet de vacunación y factura veterinaria.
- Plantillas de email (5): credenciales portal, confirmación cita, recordatorio 24h, cita completada.
- Cron job: recordatorio automático de citas 24 horas antes.
- Foto de perfil del paciente en el reporte del carnet de vacunas.

### Cambiado
- Historia clínica creada automáticamente al crear una cita (método `_sync_historia`).

---

## [18.0.1.1.0] — 2025-03-20

### Añadido
- Modelo `veterinaria.inventario`: inventario unificado para productos, servicios y medicamentos.
- Modelo `veterinaria.receta` y `veterinaria.receta.linea`: recetas médicas con cálculo automático de cantidad total.
- Modelo `veterinaria.vacuna.aplicada`: carnet de vacunación con cálculo de próxima dosis.
- Modelo `veterinaria.facturacion` y `veterinaria.facturacion.linea`: facturación multiservicio.
- Wizards de facturación: agregar línea, múltiples líneas, importar desde receta.
- Modelo `veterinaria.venta` y `veterinaria.documento_venta`.
- Sistema de seguridad con 4 grupos jerárquicos: Recepcionista, Veterinario, Administrador, Cliente Portal.
- 11 record rules de aislamiento de datos para el portal cliente.
- Secuencias automáticas para recetas (REC-XXXX) y facturas (FAC-XXXX).
- Creación automática de usuarios portal al registrar propietarios con email.
- Wizard `veterinaria.credential.wizard` para mostrar credenciales generadas.

### Cambiado
- `res.partner` extendido con campos `es_propietario`, `paciente_ids`, `tiene_acceso_portal`.
- Validación de disponibilidad de veterinario mejorada (conflictos de horario).

---

## [18.0.1.0.0] — 2025-03-01

### Añadido
- Inicio del proyecto **VitalPet** sobre Odoo 18.
- Módulo `veterinaria_core` versión inicial:
  - Modelo `veterinaria.paciente` (mascotas): especie, raza, peso, microchip, propietario.
  - Modelo `veterinaria.propietario` (herencia `res.partner`).
  - Modelo `veterinaria.veterinario`: especialidad, horarios, disponibilidad.
  - Modelo `veterinaria.especialidad`: catálogo de especialidades.
  - Modelo `veterinaria.cita`: agendamiento con validación de disponibilidad y conflictos.
  - Modelo `veterinaria.historia_clinica`: alergias, tipo de sangre, condiciones crónicas.
  - Modelo `veterinaria.medicamento`: catálogo de medicamentos.
  - Modelo `veterinaria.producto`: productos veterinarios.
  - Modelo `veterinaria.servicio`: servicios de la clínica.
  - Modelo `veterinaria.vacuna`: catálogo de vacunas.
  - Vistas de lista, formulario y calendario para todos los modelos.
  - Menú principal del módulo.
- Contenerización con Docker (Docker Compose: Odoo 18 + PostgreSQL 15).
- Archivo `odoo.conf` y `.env.example`.
- README.md inicial.

---

## Formato de Versiones

El proyecto sigue el esquema `<odoo_version>.<major>.<minor>.<patch>`:

- `18.0` — Versión de Odoo base.
- `major` — Cambios incompatibles en la estructura de datos o módulos.
- `minor` — Nuevas funcionalidades compatibles hacia atrás.
- `patch` — Correcciones de bugs y ajustes menores.

---

*Para ver el historial completo de commits, consulta el [repositorio en GitHub](https://github.com/DavidGR21/Proyecto-Odoo/commits/main).*
