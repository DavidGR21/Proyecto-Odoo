# Documentacion de API y servicios internos
## 1) Estructura general del proyecto
### Módulos Desarrollados

| Módulo                  | Descripción |
|-------------------------|-----------|
| `veterinaria_core`      | Módulo principal del sistema. Contiene la lógica de negocio, modelos, controladores y reportes. |
| `veterinaria_web`       | Módulo para funcionalidades web y portal. |
| `l10n_ec_sri_vet`       | Módulo de localización ecuatoriana y facturación electrónica SRI adaptado al rubro veterinario. |

- Raiz
  - Dockerfile
  - docker-compose.yml
  - odoo.conf
  - README.md
  - logs.txt
  - custom_addons/
    - l10n_ec_sri_vet/
      - __manifest__.py
      - data/
      - models/
      - report/
      - security/
      - views/
    - veterinaria_core/
      - __manifest__.py
      - controllers/
      - data/
      - models/
      - reports/
      - security/
      - static/
      - views/
    - veterinaria_web/
      - __manifest__.py
      - controllers/
      - demo/
      - models/
      - security/
      - static/
      - views/

## 2) Modulos (addons) y carpetas principales

### 2.1) veterinaria_core
El módulo **`veterinaria_core`** es el núcleo principal del sistema. Contiene toda la lógica de negocio específica para la clínica veterinaria. 

Este módulo está organizado de la siguiente manera:
- controllers/
  - portal.py: rutas del portal del cliente (mis mascotas, citas, facturas, etc.).
- data/
  - cron_recordatorio.xml: cron para recordatorios de citas.
  - mail_server.xml: configuracion de correo.
  - mail_templates.xml: plantillas email.
  - sequences.xml: secuencias (recetas, etc.).
- models/
  - cita.py
  - credential_wizard.py
  - documento_venta.py
  - especialidad.py
  - facturacion.py
  - facturacion_linea.py
  - facturacion_wizard.py
  - historia_clinica.py
  - inventario.py
  - medicamento.py
  - paciente.py
  - producto.py
  - propietario.py (extension de res.partner)
  - receta.py
  - servicio.py
  - vacuna.py
  - venta.py
  - veterinario.py
- reports/
  - carnet_vacunas_report.xml
  - factura_veterinaria_report.xml
- security/
  - ir.model.access.csv
  - portal_security.xml
  - veterinaria_security.xml
- views/
  - vistas y menus para los modelos anteriores
  - portal_templates.xml (portal del cliente)

### 2.2) l10n_ec_sri_vet

- models/
  - facturacion_inherit.py (hereda veterinaria.facturacion para SRI)
  - res_company.py (campos SRI en compania)
  - sri_documento.py (flujo de documento electronico)
  - sri_firma.py (firma XAdES-BES)
  - sri_ws_client.py (cliente SOAP SRI)
  - sri_xml_generator.py (XML factura SRI)
- data/
  - sri_catalogo_data.xml
- report/
  - ride_report.xml
  - ride_template.xml
- views/
  - res_company_view.xml
  - sri_documento_view.xml
  - facturacion_view_inherit.xml

### 2.3) veterinaria_web

- controllers/
  - main.py: rutas publicas del sitio web.
- models/
  - models.py: ejemplo comentado (sin modelo activo).
- views/
  - assets.xml
  - layout.xml
  - pages/ (inicio, servicios, nosotros, contacto)
  - snippets/ (navbar, footer)

## 3) Endpoints HTTP (rutas web)

No existe una API REST formal directamente para este sistema es decir únicamente se  exponen rutas web (HTML/PDF) con controladores Odoo. A continuacion se muestran las rutas y su comportamiento dentro del sistema.

### 3.1) Portal del cliente (veterinaria_core)

Base: controlador `VeterinariaPortal`.

| Ruta | Metodo | Autenticacion | Parametros | Respuesta | Codigos | Observaciones |
| --- | --- | --- | --- | --- | --- | --- |
| /my/account | GET, POST | user | POST: image_1920 (archivo) | HTML | 200 | Actualiza foto de perfil. |
| /my/security | GET, POST | user | POST: old, new1, new2 | HTML | 200 | Vista simplificada para grupo cliente. |
| /my/pets | GET | user | - | HTML | 200 | Lista mascotas del propietario. |
| /my/pets/<int:pet_id> | GET | user | pet_id | HTML | 200, 302 | Redirige si no pertenece al usuario. |
| /my/appointments | GET | user | - | HTML | 200 | Lista citas pasadas y futuras. |
| /my/medical_records | GET | user | - | HTML | 200 | Lista historias clinicas. |
| /my/invoices_vet | GET | user | - | HTML | 200 | Lista facturas veterinarias. |
| /my/invoices_vet/<int:factura_id> | GET | user | factura_id | HTML | 200, 302 | Redirige si no pertenece al usuario. |
| /my/invoices_vet/<int:factura_id>/pdf | GET | user | factura_id | PDF | 200, 302 | Descarga PDF de factura. |
| /my/prescriptions | GET | user | - | HTML | 200 | Lista recetas del propietario. |
| /my/vaccination_card/<int:pet_id> | GET | user | pet_id | PDF | 200, 302 | Descarga carnet de vacunas. |

Ejemplo request:

```http
GET /my/appointments HTTP/1.1
Host: <odoo-host>
Cookie: session_id=<token>
```

Ejemplo response:

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
```

### 3.2) Sitio web publico (veterinaria_web)

| Ruta | Metodo | Autenticacion | Parametros | Respuesta | Codigos | Observaciones |
| --- | --- | --- | --- | --- | --- | --- |
| / | GET | public | - | HTML | 200 | Landing page. |
| /servicios | GET | public | - | HTML | 200 | Servicios. |
| /nosotros | GET | public | - | HTML | 200 | Equipo. |
| /contacto | GET | public | - | HTML | 200 | Formulario de contacto. |
| /contacto/enviar | POST | public + CSRF | nombre, email, telefono, asunto, mensaje | HTML | 200 | Envió de datos a la empresa en caso de requerir contratación |

Ejemplo request:

```http
POST /contacto/enviar HTTP/1.1
Host: <odoo-host>
Content-Type: application/x-www-form-urlencoded

nombre=Ana&email=ana@example.com&telefono=099999999&asunto=Consulta&mensaje=Hola
```

Ejemplo response:

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
```

## 4) Integraciones y servicios internos 
El sistema **Veterinaria** cuenta con varias integraciones y servicios internos clave para su correcto funcionamiento:
### 4.1) SRI Ecuador (SOAP)
Se implementó una integración completa con el **Servicio de Rentas Internas (SRI)** de Ecuador mediante protocolo **SOAP**.
- Cliente SOAP: `sri.ws.client`
  - Servicio recepcion: https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl
  - Servicio autorizacion: https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl
- Librerias externas: zeep, requests, cryptography, lxml, stdnum, barcode.
- Flujo:
  1) Generar XML (XSD 2.1.0) en `sri.xml.generator`.
  2) Firmar XML (XAdES-BES) en `sri.firma.electronica`.
  3) Enviar comprobante al SRI (recepcion) en `sri.ws.client`.
  4) Consultar autorizacion en `sri.ws.client`.
  5) Generar/descargar RIDE PDF y enviar por email.

### 4.2) Correo electronico (Odoo mail)

- Plantillas en data/mail_templates.xml
- Uso en citas (confirmacion, recordatorios) y envio de RIDE.

### 4.3) Reportes PDF (QWeb)

- Factura veterinaria (veterinaria_core)
- Carnet de vacunas (veterinaria_core)
- RIDE SRI (l10n_ec_sri_vet)

## 5) Modelos y métodos 
A continuación se presenta un resumen de los modelos más importantes y sus métodos principales dentro del proyecto:
### 5.1) veterinaria_core/models/cita.py

- _compute_receta_count: cuenta recetas asociadas.
- _compute_duracion_horas: convierte seleccion a float.
- _onchange_fecha_hora_disponibilidad: filtra veterinarios disponibles.
- _onchange_propietario_id: sincroniza mascota con propietario.
- _compute_name: referencia legible de la cita.
- _check_required_fields: valida veterinario, motivo, fecha.
- _map_estado_historia: mapea estado para historia clinica.
- _prepare_historia_vals: prepara valores de historia.
- _onchange_paciente_id: carga datos clinicos del paciente.
- _sync_historia: crea o actualiza historia clinica.
- _send_confirmacion_email: envia email al crear cita.
- _send_completada_email: envia resumen post-consulta.
- _cron_enviar_recordatorios: cron de recordatorios 24h.
- default_get: normaliza duracion.
- onchange: normaliza duracion en cache.
- create: valida solapamientos, crea y sincroniza historia.
- write: sincroniza historia si cambia info clinica.
- action_completar_cita: marca completada y envia email.
- action_cancelar_cita: cancela.
- action_crear_receta: abre wizard de receta.

### 5.2) veterinaria_core/models/facturacion.py

- _compute_totales: calcula subtotal, impuesto y total.
- action_validar_factura: valida, descuenta stock y marca citas facturadas.
- action_cancelar_factura: cancela y libera citas.
- action_importar_receta: abre wizard de importacion.
- _get_allowed_fields_validado: campos editables en validado.
- write: bloquea cambios si no esta en borrador.
- create: asigna numero FAC-.

### 5.3) veterinaria_core/models/facturacion_linea.py

- _compute_nombre_item: nombre unificado del item.
- _compute_subtotal: cantidad * precio.
- _compute_descripcion: descripcion legible.
- _onchange_item_ref: carga item y precio.
- _onchange_tipo_linea: limpia campos.
- _onchange_cita_id: carga precio del servicio.
- _onchange_inventario_id: carga precio de inventario.
- _onchange_precio_unitario: fuerza precio desde inventario.
- _onchange_cantidad: valida stock en UI.
- _validate_stock_vals: valida stock en create/write.
- _check_stock_disponible: valida stock en registro.
- _check_linea: valida cantidad y precio correcto.
- create: valida stock.
- write: valida stock.

### 5.4) veterinaria_core/models/facturacion_wizard.py

- FacturacionLineaWizard
  - _onchange_tipo_linea: limpia campos.
  - _onchange_cita_id: carga precio.
  - _onchange_inventario_id: carga precio.
  - _onchange_precio_unitario: fuerza precio.
  - _onchange_cantidad: valida stock.
  - action_agregar_linea: crea linea en factura.
- FacturacionMultilineaWizard
  - action_agregar_multiples_lineas: crea multiples lineas segun tipo.
- ImportarRecetaWizard
  - _onchange_propietario_id: filtra citas.
  - _onchange_cita_id: carga medicamentos desde recetas.
  - action_confirmar_importacion: crea lineas y marca receta facturada.

### 5.5) veterinaria_core/models/venta.py

- VentaProductos
  - _compute_totales: suma subtotal e impuestos.
  - _compute_name: genera nombre VTA-.
  - action_validar_venta: crea sale.order con lineas.
  - action_cancelar_venta: cancela orden.
- VentaLinea
  - _compute_subtotal: cantidad * precio.
  - _compute_impuesto: suma impuestos.
  - _compute_total_linea: subtotal + impuesto.
  - _check_item_selected: valida que solo uno (producto/medicamento).
  - _onchange_item: carga precio desde item.

### 5.6) veterinaria_core/models/documento_venta.py

- _compute_name: nombre segun tipo.
- _compute_propietario_id: propietario desde cita.
- _compute_paciente_id: paciente desde cita.
- _compute_veterinario_id: veterinario desde cita.
- _compute_fecha_cita: fecha de cita.
- _compute_motivo_cita: motivo de cita.
- _compute_totales: totales segun tipo.
- _onchange_tipo_documento: limpia campos.
- _check_required_fields: valida segun tipo.
- _onchange_propietario_id_mascota: valida pertenencia.
- action_validar_factura: cambia estado.
- action_cancelar_factura: cambia estado.

### 5.7) veterinaria_core/models/inventario.py

- _compute_margen: calcula margen.
- _onchange_precios: actualiza margen.
- _check_categoria_servicio: valida categoria en servicio.
- _check_no_negative_values: valida no negativos.

### 5.8) veterinaria_core/models/producto.py

- _compute_margen: calcula margen.
- _onchange_product_id: sincroniza datos desde product.product.

### 5.9) veterinaria_core/models/servicio.py

- Sin metodos personalizados.

### 5.10) veterinaria_core/models/medicamento.py

- Sin metodos personalizados.

### 5.11) veterinaria_core/models/paciente.py

- _compute_historia_clinica_count: cuenta historias.
- _compute_cita_count: cuenta citas.
- action_view_historia_clinica: abre historial.
- action_view_citas: abre citas.
- action_agendar_cita: abre formulario de cita.

### 5.12) veterinaria_core/models/propietario.py (res.partner)

- _compute_cantidad_mascotas: cuenta mascotas.
- _compute_cita_count: cuenta citas.
- _compute_tiene_acceso_portal: valida si tiene grupo portal.
- _send_credentials_email: envia credenciales.
- _create_portal_user: crea o actualiza usuario portal.
- action_crear_acceso_portal: wizard con credenciales.
- create: auto-crea acceso portal si aplica.
- write: auto-crea acceso portal si aplica.
- action_view_mascotas: abre mascotas.
- action_view_citas: abre citas.
- action_agendar_cita: abre formulario de cita.

### 5.13) veterinaria_core/models/veterinario.py

- _compute_cantidad_citas: cuenta citas.

### 5.14) veterinaria_core/models/especialidad.py

- Sin metodos personalizados.

### 5.15) veterinaria_core/models/historia_clinica.py

- _compute_cita_count: cuenta citas.
- create: bloquea creacion manual (solo desde cita).

### 5.16) veterinaria_core/models/vacuna.py

- Vacuna
  - Sin metodos personalizados.
- VacunaAplicada
  - _compute_proxima_dosis: calcula proxima dosis.

### 5.17) veterinaria_core/models/receta.py

- Receta
  - _compute_display_name: referencia legible.
  - _check_cita_unica: valida receta unica.
  - _check_cita_tiene_historia: valida historia clinica.
  - write: bloquea cambios si facturada.
  - unlink: bloquea borrado si facturada.
- RecetaLinea
  - _compute_nombre_medicamento_display: unifica nombre.
  - _compute_cantidad_total: calcula cantidad total.
  - _check_medicamento_identificado: valida origen.
  - create: bloquea si receta facturada.
  - write: bloquea si receta facturada.
  - unlink: bloquea si receta facturada.

### 5.18) veterinaria_core/models/credential_wizard.py

- Sin metodos personalizados (solo campos).

### 5.19) l10n_ec_sri_vet/models/res_company.py

- sri_get_next_secuencial: incrementa secuencial.
- _check_vat_sri: valida RUC de 13 digitos.
- _check_sri_establecimiento: valida codigos de 3 digitos.

### 5.20) l10n_ec_sri_vet/models/facturacion_inherit.py

- _onchange_propietario_sri: llena identificacion cliente.
- _get_allowed_fields_validado: habilita campos SRI.
- action_enviar_sri: flujo completo SRI.
- action_consultar_sri: reconsulta autorizacion.
- action_descargar_ride: descarga PDF RIDE.
- action_enviar_ride_email: envia RIDE y XML por email.

### 5.21) l10n_ec_sri_vet/models/sri_documento.py

- _compute_name: numero compuesto.
- action_generar_xml: genera XML sin firma.
- action_firmar_xml: firma XML con certificado.
- action_enviar_sri: envia a recepcion.
- action_consultar_autorizacion: consulta autorizacion.
- action_proceso_completo: flujo completo.
- action_descargar_ride: descarga PDF.
- action_enviar_ride_email: envia RIDE y XML.

### 5.22) l10n_ec_sri_vet/models/sri_ws_client.py

- _get_client: crea cliente SOAP.
- enviar_comprobante: envia XML firmado.
- consultar_autorizacion: consulta autorizacion.

### 5.23) l10n_ec_sri_vet/models/sri_firma.py

- firmar_xml: firma XAdES-BES con certificado .p12.

### 5.24) l10n_ec_sri_vet/models/sri_xml_generator.py

- _calcular_digito_modulo11: calcula verificador.
- _generar_clave_acceso: genera clave de acceso.
- generar_factura_xml: arma XML de factura.
- _add_element: helper XML.

### 5.25) veterinaria_web/controllers/main.py

- pagina_inicio: renderiza inicio.
- pagina_servicios: renderiza servicios.
- pagina_nosotros: renderiza nosotros.
- pagina_contacto: renderiza contacto.
- contacto_enviar: procesa formulario y registra en log.
## 6) Autenticación y Seguridad

El sistema cuenta con un esquema de autenticación y seguridad robusto, adaptado tanto para usuarios internos como para clientes del portal:

- **Rutas del Portal (`/my/*`)**: Protegidas con `auth="user"`, requiriendo que el usuario esté autenticado. Además, se aplican **Record Rules** específicas para garantizar que cada cliente solo pueda visualizar su propia información (mascotas, citas, facturas, etc.).
  
- **Grupo de Portal**: Se creó el grupo de seguridad `veterinaria_core.group_veterinaria_cliente`, el cual otorga acceso a vistas y funcionalidades especiales del portal del cliente.

- **Formulario de Contacto (`/contacto/enviar`)**: Configurado con `auth="public"` para permitir el acceso sin login, pero protegido mediante **CSRF** para prevenir ataques de falsificación de peticiones.

Esta configuración asegura un equilibrio adecuado entre usabilidad para los clientes y protección de los datos sensibles de la clínica.

## 7) Observaciones Técnicas

- El proyecto **no expone una API REST JSON** formal. La mayoría de las interacciones se realizan a través de rutas HTML (vistas y portal) y generación de reportes PDF. Toda la lógica de negocio se basa en el **ORM interno de Odoo**.

- La **única integración externa** relevante es la **facturación electrónica con el SRI de Ecuador** mediante protocolo **SOAP**.

- El envío de correos electrónicos depende completamente de la configuración del servidor de mail en Odoo (no se utiliza servicio externo como SendGrid o SMTP propio).

- Todos los reportes en PDF se generan utilizando el motor **QWeb** de Odoo.

- El sistema está completamente dockerizado y sigue las mejores prácticas de desarrollo en módulos personalizados de Odoo.
