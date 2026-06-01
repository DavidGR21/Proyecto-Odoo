# 📡 Documentación de API — VitalPet

> **Nota:** VitalPet es un sistema basado en Odoo 18 y no expone una API REST formal independiente.
> Sin embargo, utiliza **controladores HTTP** (endpoints) para el portal del cliente y el sitio web público,
> y se integra con **servicios externos** (SRI de Ecuador) a través de SOAP.
>
> Este documento describe detalladamente todas las rutas, modelos internos, métodos de servicio e integraciones del sistema.

---

## 📑 Tabla de Contenidos

1. [Controladores HTTP — Portal del Cliente](#1-controladores-http--portal-del-cliente)
2. [Controladores HTTP — Sitio Web Público](#2-controladores-http--sitio-web-público)
3. [Integración Externa — SRI de Ecuador (SOAP)](#3-integración-externa--sri-de-ecuador-soap)
4. [Modelos ORM Internos — veterinaria_core](#4-modelos-orm-internos--veterinaria_core)
5. [Modelos ORM Internos — l10n_ec_sri_vet](#5-modelos-orm-internos--l10n_ec_sri_vet)
6. [Servicios Internos y Automatizaciones](#6-servicios-internos-y-automatizaciones)
7. [Sistema de Autenticación y Seguridad](#7-sistema-de-autenticación-y-seguridad)
8. [Plantillas de Email](#8-plantillas-de-email)

---

## 1. Controladores HTTP — Portal del Cliente

**Archivo:** `custom_addons/veterinaria_core/controllers/portal.py`
**Clase:** `VeterinariaPortal` (hereda de `CustomerPortal`)
**Autenticación:** `auth='user'` (requiere sesión de usuario autenticado)

Estos endpoints extienden el portal estándar de Odoo para ofrecer al cliente (propietario de mascotas) acceso a su información veterinaria.

---

### 1.1 `GET /my/account` — Perfil del Cliente

| Atributo          | Valor                         |
| ----------------- | ----------------------------- |
| **Ruta**          | `/my/account`                 |
| **Método HTTP**   | `GET`, `POST`                 |
| **Autenticación** | `user` (sesión requerida)     |
| **Controlador**   | `VeterinariaPortal.account()` |

**Descripción:** Override de la página estándar `/my/account` de Odoo. Procesa la foto de perfil del usuario (`image_1920`) si se envía en el formulario POST.

**Parámetros de Entrada (POST):**

| Parámetro                         | Tipo          | Requerido   | Descripción                              |
| --------------------------------- | ------------- | ----------- | ---------------------------------------- |
| `image_1920`                      | `FileStorage` | No          | Archivo de imagen para la foto de perfil |
| _(otros campos estándar de Odoo)_ | Varios        | Según campo | Nombre, email, teléfono, dirección, etc. |

**Respuesta:**

- `200 OK` — Renderiza template `portal.portal_my_details`
- Redirige a `/my/account` tras POST exitoso

**Observaciones:** La imagen se codifica en base64 y se escribe directamente en `partner.image_1920` con `sudo()`.

---

### 1.2 `GET/POST /my/security` — Cambio de Contraseña

| Atributo          | Valor                          |
| ----------------- | ------------------------------ |
| **Ruta**          | `/my/security`                 |
| **Método HTTP**   | `GET`, `POST`                  |
| **Autenticación** | `user`                         |
| **Controlador**   | `VeterinariaPortal.security()` |

**Descripción:** Versión simplificada de la página de seguridad para clientes del portal veterinario. Solo permite cambiar contraseña y eliminar cuenta. Si el usuario no pertenece al grupo `group_veterinaria_cliente`, se delega al comportamiento estándar de Odoo.

**Parámetros de Entrada (POST):**

| Parámetro | Tipo     | Requerido | Descripción                      |
| --------- | -------- | --------- | -------------------------------- |
| `old`     | `string` | Sí        | Contraseña actual                |
| `new1`    | `string` | Sí        | Nueva contraseña                 |
| `new2`    | `string` | Sí        | Confirmación de nueva contraseña |

**Respuesta:**

- `200 OK` — Renderiza template `veterinaria_core.portal_my_security_simple`

**Headers de Seguridad:**

```
X-Frame-Options: SAMEORIGIN
Content-Security-Policy: frame-ancestors 'self'
```

---

### 1.3 `GET /my/pets` — Listado de Mascotas

| Atributo          | Valor                                |
| ----------------- | ------------------------------------ |
| **Ruta**          | `/my/pets`                           |
| **Método HTTP**   | `GET`                                |
| **Autenticación** | `user`                               |
| **Controlador**   | `VeterinariaPortal.portal_my_pets()` |

**Descripción:** Lista todas las mascotas del usuario autenticado (filtradas por `propietario_id = partner_id`).

**Parámetros de Entrada:** Ninguno

**Estructura de Respuesta:**

```python
{
    'pets': recordset[veterinaria.paciente],  # Mascotas del usuario
    'page_name': 'pets',
    'default_url': '/my/pets'
}
```

**Códigos de Estado:**
| Código | Descripción |
|---|---|
| `200` | Renderiza la lista de mascotas |
| `303` | Redirige a `/web/login` si no está autenticado |

---

### 1.4 `GET /my/pets/<int:pet_id>` — Detalle de Mascota

| Atributo          | Valor                                      |
| ----------------- | ------------------------------------------ |
| **Ruta**          | `/my/pets/<int:pet_id>`                    |
| **Método HTTP**   | `GET`                                      |
| **Autenticación** | `user`                                     |
| **Controlador**   | `VeterinariaPortal.portal_my_pet_detail()` |

**Parámetros de Entrada:**

| Parámetro | Tipo        | Requerido | Descripción      |
| --------- | ----------- | --------- | ---------------- |
| `pet_id`  | `int` (URL) | Sí        | ID de la mascota |

**Códigos de Estado:**
| Código | Descripción |
|---|---|
| `200` | Renderiza detalle de la mascota (especie, raza, peso, vacunas, historial) |
| `302` | Redirige a `/my/pets` si la mascota no pertenece al usuario |

**Seguridad:** Se verifica que `paciente.propietario_id == user.partner_id` antes de mostrar los datos.

---

### 1.5 `GET /my/appointments` — Citas del Cliente

| Atributo          | Valor                                        |
| ----------------- | -------------------------------------------- |
| **Ruta**          | `/my/appointments`                           |
| **Método HTTP**   | `GET`                                        |
| **Autenticación** | `user`                                       |
| **Controlador**   | `VeterinariaPortal.portal_my_appointments()` |

**Descripción:** Muestra citas futuras y pasadas del cliente, separadas en dos secciones.

**Estructura de Respuesta:**

```python
{
    'upcoming': recordset[veterinaria.cita],   # Citas futuras (ASC por fecha)
    'past': recordset[veterinaria.cita],       # Últimas 50 citas pasadas (DESC)
    'page_name': 'appointments'
}
```

---

### 1.6 `GET /my/medical_records` — Historial Médico

| Atributo          | Valor                                           |
| ----------------- | ----------------------------------------------- |
| **Ruta**          | `/my/medical_records`                           |
| **Método HTTP**   | `GET`                                           |
| **Autenticación** | `user`                                          |
| **Controlador**   | `VeterinariaPortal.portal_my_medical_records()` |

**Descripción:** Lista las historias clínicas de todas las mascotas del usuario.

**Estructura de Respuesta:**

```python
{
    'historias': recordset[veterinaria.historia_clinica],  # Ordenadas por fecha DESC
    'page_name': 'medical_records'
}
```

---

### 1.7 `GET /my/invoices_vet` — Facturas Veterinarias

| Atributo          | Valor                                        |
| ----------------- | -------------------------------------------- |
| **Ruta**          | `/my/invoices_vet`                           |
| **Método HTTP**   | `GET`                                        |
| **Autenticación** | `user`                                       |
| **Controlador**   | `VeterinariaPortal.portal_my_vet_invoices()` |

**Estructura de Respuesta:**

```python
{
    'facturas': recordset[veterinaria.facturacion],  # Ordenadas por fecha DESC
    'page_name': 'invoices_vet'
}
```

---

### 1.8 `GET /my/invoices_vet/<int:factura_id>` — Detalle de Factura

| Atributo          | Valor                               |
| ----------------- | ----------------------------------- |
| **Ruta**          | `/my/invoices_vet/<int:factura_id>` |
| **Método HTTP**   | `GET`                               |
| **Autenticación** | `user`                              |

**Parámetros de Entrada:**

| Parámetro    | Tipo        | Requerido | Descripción      |
| ------------ | ----------- | --------- | ---------------- |
| `factura_id` | `int` (URL) | Sí        | ID de la factura |

**Códigos de Estado:**
| Código | Descripción |
|---|---|
| `200` | Renderiza detalle de factura con líneas, subtotal, impuestos y total |
| `302` | Redirige a `/my/invoices_vet` si la factura no pertenece al usuario |

---

### 1.9 `GET /my/invoices_vet/<int:factura_id>/pdf` — Descargar PDF de Factura

| Atributo          | Valor                                   |
| ----------------- | --------------------------------------- |
| **Ruta**          | `/my/invoices_vet/<int:factura_id>/pdf` |
| **Método HTTP**   | `GET`                                   |
| **Autenticación** | `user`                                  |

**Descripción:** Genera y descarga el PDF de la factura veterinaria usando el reporte QWeb `action_report_factura_veterinaria`.

**Respuesta:**

```
Content-Type: application/pdf
Content-Disposition: attachment; filename="Factura_FAC-00001.pdf"
```

**Códigos de Estado:**
| Código | Descripción |
|---|---|
| `200` | Descarga el archivo PDF |
| `302` | Redirige si la factura no pertenece al usuario |

---

### 1.10 `GET /my/prescriptions` — Recetas Médicas

| Atributo          | Valor               |
| ----------------- | ------------------- |
| **Ruta**          | `/my/prescriptions` |
| **Método HTTP**   | `GET`               |
| **Autenticación** | `user`              |

**Estructura de Respuesta:**

```python
{
    'recetas': recordset[veterinaria.receta],  # Ordenadas por fecha emisión DESC
    'page_name': 'prescriptions'
}
```

---

### 1.11 `GET /my/vaccination_card/<int:pet_id>` — Carnet de Vacunación PDF

| Atributo          | Valor                               |
| ----------------- | ----------------------------------- |
| **Ruta**          | `/my/vaccination_card/<int:pet_id>` |
| **Método HTTP**   | `GET`                               |
| **Autenticación** | `user`                              |

**Descripción:** Genera y descarga el carnet de vacunación de la mascota como PDF.

**Parámetros de Entrada:**

| Parámetro | Tipo        | Requerido | Descripción      |
| --------- | ----------- | --------- | ---------------- |
| `pet_id`  | `int` (URL) | Sí        | ID de la mascota |

**Respuesta:**

```
Content-Type: application/pdf
Content-Disposition: attachment; filename="carnet_vacunas_Luna.pdf"
```

**Códigos de Estado:**
| Código | Descripción |
|---|---|
| `200` | Descarga el PDF del carnet |
| `302` | Redirige a `/my/pets` si la mascota no pertenece al usuario |

---

### 1.12 Contadores del Portal Home (`/my`)

**Método:** `_prepare_home_portal_values(counters)`

Agrega contadores al dashboard del portal:

| Contador             | Modelo                    | Filtro                                    |
| -------------------- | ------------------------- | ----------------------------------------- |
| `pet_count`          | `veterinaria.paciente`    | `propietario_id = partner_id`             |
| `appointment_count`  | `veterinaria.cita`        | Citas programadas futuras del propietario |
| `invoice_count_vet`  | `veterinaria.facturacion` | `propietario_id = partner_id`             |
| `prescription_count` | `veterinaria.receta`      | `propietario_id = partner_id`             |

---

## 2. Controladores HTTP — Sitio Web Público

**Archivo:** `custom_addons/veterinaria_web/controllers/main.py`
**Clase:** `VitalPetWebsite` (hereda de `http.Controller`)
**Autenticación:** `auth='public'` (acceso sin login)

---

### 2.1 `GET /` — Página de Inicio

| Atributo          | Valor                           |
| ----------------- | ------------------------------- |
| **Ruta**          | `/`                             |
| **Método HTTP**   | `GET`                           |
| **Autenticación** | `public`                        |
| **Sitemap**       | Sí                              |
| **Template**      | `veterinaria_web.pagina_inicio` |

**Descripción:** Landing page de la clínica veterinaria VitalPet.

---

### 2.2 `GET /servicios` — Servicios de la Clínica

| Atributo          | Valor                              |
| ----------------- | ---------------------------------- |
| **Ruta**          | `/servicios`                       |
| **Método HTTP**   | `GET`                              |
| **Autenticación** | `public`                           |
| **Sitemap**       | Sí                                 |
| **Template**      | `veterinaria_web.pagina_servicios` |

**Descripción:** Muestra los servicios ofrecidos: Consulta General, Vacunación, Cirugía, Laboratorio Clínico, Farmacia Veterinaria, Agenda de Citas e Historial Clínico.

**Estructura de Datos:**

```python
servicios = [
    {'icono': 'fa-heartbeat', 'titulo': 'Consulta General', 'descripcion': '...', 'color': '#40C2D6'},
    {'icono': 'fa-plus-square', 'titulo': 'Vacunación', 'descripcion': '...', 'color': '#9B7EBD'},
    # ... 7 servicios en total
]
```

---

### 2.3 `GET /nosotros` — Sobre Nosotros

| Atributo          | Valor                             |
| ----------------- | --------------------------------- |
| **Ruta**          | `/nosotros`                       |
| **Método HTTP**   | `GET`                             |
| **Autenticación** | `public`                          |
| **Sitemap**       | Sí                                |
| **Template**      | `veterinaria_web.pagina_nosotros` |

**Descripción:** Presenta el equipo veterinario con fotos, cargos y descripciones.

---

### 2.4 `GET /contacto` — Formulario de Contacto

| Atributo          | Valor                             |
| ----------------- | --------------------------------- |
| **Ruta**          | `/contacto`                       |
| **Método HTTP**   | `GET`                             |
| **Autenticación** | `public`                          |
| **Sitemap**       | Sí                                |
| **Template**      | `veterinaria_web.pagina_contacto` |

---

### 2.5 `POST /contacto/enviar` — Enviar Formulario de Contacto

| Atributo          | Valor                |
| ----------------- | -------------------- |
| **Ruta**          | `/contacto/enviar`   |
| **Método HTTP**   | `POST`               |
| **Autenticación** | `public`             |
| **CSRF**          | Sí (token requerido) |

**Parámetros de Entrada:**

| Parámetro    | Tipo     | Requerido | Descripción          |
| ------------ | -------- | --------- | -------------------- |
| `nombre`     | `string` | No        | Nombre del contacto  |
| `email`      | `string` | No        | Email del contacto   |
| `telefono`   | `string` | No        | Teléfono de contacto |
| `asunto`     | `string` | No        | Asunto del mensaje   |
| `mensaje`    | `string` | No        | Cuerpo del mensaje   |
| `csrf_token` | `string` | Sí        | Token CSRF de Odoo   |

**Respuesta:** Renderiza la misma página de contacto con `enviado=True` y `nombre_enviado`.

**Observaciones:** Los datos se registran en el log del servidor (`_logger.info`). En producción se puede extender para crear registros en un modelo o enviar correos.

---

## 3. Integración Externa — SRI de Ecuador (SOAP)

### 3.1 Descripción General

El módulo `l10n_ec_sri_vet` integra la facturación electrónica del SRI (Servicio de Rentas Internas) de Ecuador. La comunicación se realiza mediante **Web Services SOAP** usando la librería `zeep`.

### 3.2 Web Services del SRI

| Servicio         | URL (Pruebas)                                                                                 | Método SOAP                             |
| ---------------- | --------------------------------------------------------------------------------------------- | --------------------------------------- |
| **Recepción**    | `https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl`    | `validarComprobante(xml_b64)`           |
| **Autorización** | `https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl` | `autorizacionComprobante(clave_acceso)` |

### 3.3 Flujo de Facturación Electrónica

```
┌─────────────┐     ┌─────────────┐     ┌────────────┐     ┌─────────────┐     ┌──────────────┐
│  1. Generar │────▶│  2. Firmar  │────▶│ 3. Enviar  │────▶│ 4. Consultar│────▶│ 5. RIDE/Email│
│    XML      │     │   XAdES-BES │     │  al SRI    │     │ Autorización│     │              │
└─────────────┘     └─────────────┘     └────────────┘     └─────────────┘     └──────────────┘
```

### 3.4 Servicio `sri.ws.client` — Cliente SOAP

**Archivo:** `custom_addons/l10n_ec_sri_vet/models/sri_ws_client.py`
**Tipo:** `models.AbstractModel` (no persistente)

#### `enviar_comprobante(xml_firmado_bytes, ambiente='1')`

| Atributo        | Valor                                                                 |
| --------------- | --------------------------------------------------------------------- |
| **Descripción** | Envía el XML firmado al WS de Recepción del SRI                       |
| **Parámetros**  | `xml_firmado_bytes` (bytes), `ambiente` ('1'=Pruebas, '2'=Producción) |
| **Retorno**     | `dict` con claves `estado` y `mensaje`                                |

**Ejemplo de Petición:**

```python
ws_client = self.env['sri.ws.client']
resultado = ws_client.enviar_comprobante(xml_firmado_bytes, ambiente='1')
```

**Ejemplo de Respuesta:**

```python
{
    'estado': 'RECIBIDA',          # o 'DEVUELTA', 'ERROR'
    'mensaje': 'Comprobante recibido correctamente'
}
```

#### `consultar_autorizacion(clave_acceso, ambiente='1')`

| Atributo        | Valor                                                                                         |
| --------------- | --------------------------------------------------------------------------------------------- |
| **Descripción** | Consulta si el comprobante fue autorizado por el SRI                                          |
| **Parámetros**  | `clave_acceso` (string 49 dígitos), `ambiente`                                                |
| **Retorno**     | `dict` con `estado`, `numero_autorizacion`, `fecha_autorizacion`, `xml_autorizado`, `mensaje` |

**Ejemplo de Respuesta:**

```python
{
    'estado': 'AUTORIZADO',
    'numero_autorizacion': '3105202601010300000100010010000000011234567810',
    'fecha_autorizacion': datetime(2026, 5, 31, 14, 30, 0),
    'xml_autorizado': '<autorizacion>...</autorizacion>',
    'mensaje': 'AUTORIZADO'
}
```

### 3.5 Servicio `sri.xml.generator` — Generador XML

**Archivo:** `custom_addons/l10n_ec_sri_vet/models/sri_xml_generator.py`
**Tipo:** `models.AbstractModel`

#### `generar_factura_xml(documento)`

| Atributo        | Valor                                               |
| --------------- | --------------------------------------------------- |
| **Descripción** | Genera XML de factura según XSD 2.1.0 del SRI       |
| **Parámetro**   | `documento` — record de `sri.documento.electronico` |
| **Retorno**     | `bytes` del XML generado                            |

**Estructura del XML generado:**

```xml
<factura id="comprobante" version="2.1.0">
    <infoTributaria>
        <ambiente>1</ambiente>
        <tipoEmision>1</tipoEmision>
        <razonSocial>VitalPet Clínica Veterinaria</razonSocial>
        <ruc>1234567890001</ruc>
        <claveAcceso>3105202601...</claveAcceso>
        <codDoc>01</codDoc>
        <estab>001</estab>
        <ptoEmi>001</ptoEmi>
        <secuencial>000000001</secuencial>
        <dirMatriz>Dirección...</dirMatriz>
    </infoTributaria>
    <infoFactura>
        <fechaEmision>31/05/2026</fechaEmision>
        <tipoIdentificacionComprador>05</tipoIdentificacionComprador>
        <razonSocialComprador>Juan Pérez</razonSocialComprador>
        <identificacionComprador>1712345678</identificacionComprador>
        <totalSinImpuestos>100.00</totalSinImpuestos>
        <totalConImpuestos>...</totalConImpuestos>
        <importeTotal>115.00</importeTotal>
        <moneda>DOLAR</moneda>
        <pagos>...</pagos>
    </infoFactura>
    <detalles>
        <detalle>
            <codigoPrincipal>CITA-1</codigoPrincipal>
            <descripcion>Consulta General</descripcion>
            <cantidad>1.00</cantidad>
            <precioUnitario>100.00</precioUnitario>
            <precioTotalSinImpuesto>100.00</precioTotalSinImpuesto>
            <impuestos>...</impuestos>
        </detalle>
    </detalles>
</factura>
```

#### `_generar_clave_acceso(...)`

Genera la clave de acceso de 49 dígitos:

| Posición | Longitud | Contenido                        |
| -------- | -------- | -------------------------------- |
| 1-8      | 8        | Fecha de emisión (ddmmaaaa)      |
| 9-10     | 2        | Tipo de comprobante (01=Factura) |
| 11-23    | 13       | RUC del emisor                   |
| 24       | 1        | Tipo de ambiente (1=Pruebas)     |
| 25-27    | 3        | Establecimiento                  |
| 28-30    | 3        | Punto de emisión                 |
| 31-39    | 9        | Secuencial                       |
| 40-47    | 8        | Código numérico aleatorio        |
| 48       | 1        | Tipo de emisión (1=Normal)       |
| 49       | 1        | Dígito verificador (Módulo 11)   |

### 3.6 Servicio `sri.firma.electronica` — Firma XAdES-BES

**Archivo:** `custom_addons/l10n_ec_sri_vet/models/sri_firma.py`
**Tipo:** `models.AbstractModel`

#### `firmar_xml(xml_bytes, p12_bytes, password)`

| Atributo             | Valor                                              |
| -------------------- | -------------------------------------------------- |
| **Descripción**      | Firma un XML con XAdES-BES usando certificado .p12 |
| **Parámetros**       | `xml_bytes`, `p12_bytes`, `password` (string)      |
| **Retorno**          | `bytes` del XML firmado                            |
| **Algoritmo Firma**  | RSA-SHA1 (requerido por el SRI)                    |
| **Canonicalización** | C14N 1.0 inclusiva                                 |

**Dependencias:** `cryptography` (hazmat.primitives)

**Pasos del Flujo de Firma:**

1. Extraer clave privada y certificado del PKCS#12
2. Calcular digest del certificado (SHA-1)
3. Parsear XML y calcular digest del comprobante (antes de insertar firma)
4. Construir la estructura `ds:Signature` completa con placeholders
5. Insertar Signature en el documento
6. Calcular digests en contexto (SignedProperties, KeyInfo)
7. Canonicalizar SignedInfo en contexto → firma RSA
8. Serializar XML firmado

---

## 4. Modelos ORM Internos — veterinaria_core

### 4.1 `res.partner` (Propietario) — Herencia

**Archivo:** `models/propietario.py`
**Modelo base:** `res.partner` (herencia `_inherit`)

#### Campos Agregados

| Campo                       | Tipo                              | Descripción                                   |
| --------------------------- | --------------------------------- | --------------------------------------------- |
| `es_propietario`            | `Boolean`                         | Marca si el partner es propietario de mascota |
| `observaciones_veterinaria` | `Text`                            | Notas veterinarias del propietario            |
| `paciente_ids`              | `One2many → veterinaria.paciente` | Mascotas del propietario                      |
| `cantidad_mascotas`         | `Integer` (computed)              | Conteo de mascotas                            |
| `cita_count`                | `Integer` (computed)              | Conteo de citas de sus mascotas               |
| `tiene_acceso_portal`       | `Boolean` (computed)              | Si tiene usuario portal activo                |

#### Métodos Principales

| Método                                    | Tipo          | Descripción                                                                                              |
| ----------------------------------------- | ------------- | -------------------------------------------------------------------------------------------------------- |
| `_create_portal_user()`                   | Instancia     | Crea/actualiza usuario portal con grupo `group_veterinaria_cliente`. Retorna `(user, password_temporal)` |
| `_send_credentials_email(user, password)` | Instancia     | Envía email con credenciales usando template `mail_template_credenciales_portal`                         |
| `action_crear_acceso_portal()`            | Acción        | Botón: crea acceso portal y abre wizard con credenciales                                                 |
| `action_view_mascotas()`                  | Acción        | Navega a lista de mascotas del propietario                                                               |
| `action_view_citas()`                     | Acción        | Navega a citas de las mascotas del propietario                                                           |
| `action_agendar_cita()`                   | Acción        | Abre formulario de nueva cita                                                                            |
| `create(vals_list)`                       | Override CRUD | Auto-crea usuario portal si `es_propietario=True` y tiene email                                          |
| `write(vals)`                             | Override CRUD | Auto-crea usuario portal al marcar como propietario                                                      |

---

### 4.2 `veterinaria.paciente` — Mascotas

**Archivo:** `models/paciente.py`

#### Campos

| Campo                  | Tipo                     | Requerido | Descripción                                      |
| ---------------------- | ------------------------ | --------- | ------------------------------------------------ |
| `name`                 | `Char`                   | Sí        | Nombre de la mascota                             |
| `especie`              | `Selection`              | Sí        | perro, gato, conejo, pajaro, reptil, otro        |
| `raza`                 | `Char`                   | No        | Raza de la mascota                               |
| `fecha_nacimiento`     | `Date`                   | No        | Fecha de nacimiento                              |
| `peso`                 | `Float`                  | No        | Peso en kg                                       |
| `foto`                 | `Image`                  | No        | Foto (max 200x200)                               |
| `propietario_id`       | `Many2one → res.partner` | Sí        | Propietario (filtrado por `es_propietario=True`) |
| `alergias`             | `Text`                   | No        | Alergias conocidas                               |
| `estado_vacunacion`    | `Selection`              | No        | al_dia, atrasado, sin_vacunas                    |
| `microchip`            | `Char`                   | No        | Número de microchip (UNIQUE)                     |
| `fecha_registro`       | `Date`                   | Auto      | Fecha de registro en el sistema                  |
| `estado`               | `Selection`              | No        | activo, inactivo, fallecido                      |
| `historia_clinica_ids` | `One2many`               | —         | Relación con historias clínicas                  |
| `vacuna_aplicada_ids`  | `One2many`               | —         | Vacunas aplicadas (carnet)                       |
| `receta_ids`           | `One2many`               | —         | Recetas asociadas                                |

#### Restricciones SQL

- `microchip_unique`: El número de microchip debe ser único

---

### 4.3 `veterinaria.veterinario` — Veterinarios

**Archivo:** `models/veterinario.py`

#### Campos

| Campo                   | Tipo                                  | Descripción                      |
| ----------------------- | ------------------------------------- | -------------------------------- |
| `name`                  | `Char`                                | Nombre del veterinario           |
| `especialidad_id`       | `Many2one → veterinaria.especialidad` | Especialidad                     |
| `matricula_profesional` | `Char`                                | Matrícula profesional            |
| `horario_inicio`        | `Selection`                           | Hora de inicio (07:00 a 19:00)   |
| `horario_fin`           | `Selection`                           | Hora de fin (07:00 a 19:00)      |
| `dias_disponibles`      | `Selection`                           | lun_vie, lun_sab, sab_dom, todos |
| `cita_ids`              | `One2many → veterinaria.cita`         | Citas asignadas                  |
| `cantidad_citas`        | `Integer` (computed)                  | Total de citas                   |

---

### 4.4 `veterinaria.cita` — Citas

**Archivo:** `models/cita.py`

#### Campos Principales

| Campo                                                     | Tipo        | Descripción                                   |
| --------------------------------------------------------- | ----------- | --------------------------------------------- |
| `paciente_id`                                             | `Many2one`  | Mascota a atender                             |
| `propietario_id`                                          | `Many2one`  | Propietario (auto-poblado)                    |
| `veterinario_id`                                          | `Many2one`  | Veterinario asignado                          |
| `servicio_id`                                             | `Many2one`  | Servicio veterinario                          |
| `fecha_hora`                                              | `Datetime`  | Fecha y hora de la cita                       |
| `duracion`                                                | `Selection` | 30 min o 1 hora                               |
| `motivo`                                                  | `Text`      | Motivo de la cita                             |
| `estado`                                                  | `Selection` | programada, completada, cancelada, no_asistio |
| `historia_clinica_id`                                     | `Many2one`  | Historia clínica vinculada                    |
| `receta_ids`                                              | `One2many`  | Recetas de la cita                            |
| `alergias`, `tipo_sangre`, `peso`, `condiciones_cronicas` | Varios      | Datos clínicos al momento de la cita          |
| `recordatorio_enviado`                                    | `Boolean`   | Control de envío de recordatorio              |
| `facturada`                                               | `Boolean`   | Si la cita ya fue facturada                   |

#### Métodos Principales

| Método                                  | Descripción                                                  |
| --------------------------------------- | ------------------------------------------------------------ |
| `_onchange_fecha_hora_disponibilidad()` | Filtra veterinarios disponibles según horario y conflictos   |
| `_sync_historia()`                      | Crea o actualiza la historia clínica al crear/modificar cita |
| `_send_confirmacion_email()`            | Envía email de confirmación al crear cita                    |
| `_send_completada_email()`              | Envía resumen post-consulta                                  |
| `_cron_enviar_recordatorios()`          | Cron job: envía recordatorios 24h antes                      |
| `action_completar_cita()`               | Marca como completada y envía email                          |
| `action_cancelar_cita()`                | Cancela la cita                                              |
| `action_crear_receta()`                 | Abre formulario para crear receta                            |

---

### 4.5 `veterinaria.historia_clinica` — Historia Clínica

**Archivo:** `models/historia_clinica.py`
**Herencia Mixin:** `mail.thread`, `mail.activity.mixin`

#### Campos

| Campo                  | Tipo        | Descripción                                   |
| ---------------------- | ----------- | --------------------------------------------- |
| `paciente_id`          | `Many2one`  | Paciente (UNIQUE — una historia por mascota)  |
| `cita_ids`             | `One2many`  | Citas asociadas                               |
| `receta_ids`           | `One2many`  | Recetas asociadas                             |
| `fecha_apertura`       | `Datetime`  | Fecha de apertura                             |
| `activa`               | `Boolean`   | Estado de la historia                         |
| `alergias`             | `Text`      | Alergias del paciente                         |
| `tipo_sangre`          | `Selection` | A+, A-, B+, B-, AB+, AB-, O+, O-, Desconocido |
| `peso`                 | `Float`     | Peso actual (kg)                              |
| `condiciones_cronicas` | `Text`      | Condiciones crónicas                          |
| `observaciones`        | `Text`      | Observaciones generales                       |

**Restricción:** Solo se puede crear a través del flujo de citas (`from_cita_create` en context).

---

### 4.6 `veterinaria.facturacion` — Facturación

**Archivo:** `models/facturacion.py`
**Herencia Mixin:** `mail.thread`, `mail.activity.mixin`

#### Campos

| Campo            | Tipo                     | Descripción                         |
| ---------------- | ------------------------ | ----------------------------------- |
| `name`           | `Char`                   | Número de factura (auto: FAC-00001) |
| `propietario_id` | `Many2one`               | Cliente propietario                 |
| `linea_ids`      | `One2many`               | Líneas de facturación               |
| `subtotal`       | `Float` (computed)       | Subtotal calculado                  |
| `impuesto_id`    | `Many2one → account.tax` | Impuesto aplicable                  |
| `impuesto_total` | `Float` (computed)       | Total de impuestos                  |
| `total`          | `Float` (computed)       | Total general                       |
| `estado`         | `Selection`              | borrador, validado, cancelado       |
| `fecha_factura`  | `Date`                   | Fecha de la factura                 |

#### Métodos

| Método                      | Descripción                                           |
| --------------------------- | ----------------------------------------------------- |
| `action_validar_factura()`  | Valida, descuenta stock y marca citas como facturadas |
| `action_cancelar_factura()` | Cancela y libera citas                                |
| `action_importar_receta()`  | Abre wizard para importar medicamentos de receta      |

---

### 4.7 `veterinaria.receta` — Recetas Médicas

**Archivo:** `models/receta.py`

#### Campos

| Campo                     | Tipo                 | Descripción                           |
| ------------------------- | -------------------- | ------------------------------------- |
| `name`                    | `Char`               | Referencia (secuencia REC-XXXX)       |
| `cita_id`                 | `Many2one`           | Cita médica (UNIQUE)                  |
| `veterinario_id`          | `Many2one` (related) | Veterinario                           |
| `paciente_id`             | `Many2one` (related) | Paciente                              |
| `diagnostico`             | `Text`               | Diagnóstico clínico                   |
| `instrucciones_generales` | `Text`               | Indicaciones generales                |
| `linea_ids`               | `One2many`           | Medicamentos recetados                |
| `facturada`               | `Boolean`            | Si ya fue facturada (bloquea edición) |

#### Modelo `veterinaria.receta.linea`

| Campo               | Tipo                                | Descripción                       |
| ------------------- | ----------------------------------- | --------------------------------- |
| `tipo_origen`       | `Selection`                         | inventario / exterior             |
| `medicamento_id`    | `Many2one → veterinaria.inventario` | Medicamento del inventario        |
| `medicamento_texto` | `Char`                              | Medicamento externo (texto libre) |
| `dosis`             | `Float`                             | Cantidad por toma                 |
| `frecuencia_horas`  | `Integer`                           | Cada cuántas horas                |
| `duracion_dias`     | `Integer`                           | Duración del tratamiento          |
| `cantidad_total`    | `Float` (computed)                  | Dosis × (24/Frecuencia) × Días    |

---

### 4.8 `veterinaria.vacuna` / `veterinaria.vacuna.aplicada`

**Archivo:** `models/vacuna.py`

#### Catálogo de Vacunas

| Campo              | Tipo        | Descripción                       |
| ------------------ | ----------- | --------------------------------- |
| `name`             | `Char`      | Nombre de la vacuna               |
| `especie_sugerida` | `Selection` | Especie para la que se recomienda |
| `frecuencia_meses` | `Integer`   | Frecuencia de revacunación        |

#### Vacunas Aplicadas (Carnet)

| Campo              | Tipo              | Descripción            |
| ------------------ | ----------------- | ---------------------- |
| `paciente_id`      | `Many2one`        | Mascota                |
| `vacuna_id`        | `Many2one`        | Vacuna aplicada        |
| `fecha_aplicacion` | `Date`            | Fecha de aplicación    |
| `veterinario_id`   | `Many2one`        | Veterinario que aplicó |
| `lote`             | `Char`            | Número de lote         |
| `proxima_dosis`    | `Date` (computed) | Próxima dosis sugerida |

---

### 4.9 `veterinaria.inventario` — Inventario Unificado

**Archivo:** `models/inventario.py`

Modelo unificado para productos, servicios y medicamentos.

| Campo             | Tipo               | Descripción                     |
| ----------------- | ------------------ | ------------------------------- |
| `tipo_inventario` | `Selection`        | producto, servicio, medicamento |
| `name`            | `Char`             | Nombre del item                 |
| `precio_venta`    | `Float`            | Precio de venta                 |
| `precio_costo`    | `Float`            | Precio de costo                 |
| `cantidad_stock`  | `Float`            | Stock disponible                |
| `cantidad_minima` | `Float`            | Stock mínimo de alerta          |
| `margen_ganancia` | `Float` (computed) | Margen de ganancia %            |

---

## 5. Modelos ORM Internos — l10n_ec_sri_vet

### 5.1 `sri.documento.electronico`

**Archivo:** `models/sri_documento.py`
**Herencia Mixin:** `mail.thread`, `mail.activity.mixin`

#### Campos

| Campo                 | Tipo                                 | Descripción                                          |
| --------------------- | ------------------------------------ | ---------------------------------------------------- |
| `facturacion_id`      | `Many2one → veterinaria.facturacion` | Factura vinculada                                    |
| `tipo_comprobante`    | `Selection`                          | 01=Factura, 04=NC, 05=ND                             |
| `clave_acceso`        | `Char(49)`                           | Clave de acceso SRI                                  |
| `numero_autorizacion` | `Char`                               | Número de autorización                               |
| `estado`              | `Selection`                          | borrador → generado → firmado → enviado → autorizado |
| `xml_sin_firma`       | `Binary`                             | XML sin firmar                                       |
| `xml_firmado`         | `Binary`                             | XML firmado con XAdES-BES                            |
| `xml_autorizado`      | `Binary`                             | XML con autorización SRI                             |
| `mensaje_sri`         | `Text`                               | Mensajes de respuesta del SRI                        |

#### Métodos (Flujo)

| Método                            | Paso | Descripción                |
| --------------------------------- | ---- | -------------------------- |
| `action_generar_xml()`            | 1    | Genera XML según XSD 2.1.0 |
| `action_firmar_xml()`             | 2    | Firma con certificado .p12 |
| `action_enviar_sri()`             | 3    | Envía al WS de Recepción   |
| `action_consultar_autorizacion()` | 4    | Consulta autorización      |
| `action_proceso_completo()`       | 1→4  | Ejecuta todo el flujo      |
| `action_descargar_ride()`         | —    | Descarga RIDE PDF          |
| `action_enviar_ride_email()`      | —    | Envía RIDE + XML por email |

### 5.2 `res.company` — Configuración SRI (Herencia)

**Archivo:** `models/res_company.py`

| Campo                       | Tipo        | Descripción                         |
| --------------------------- | ----------- | ----------------------------------- |
| `sri_ambiente`              | `Selection` | 1=Pruebas, 2=Producción             |
| `sri_certificado_p12`       | `Binary`    | Certificado de firma electrónica    |
| `sri_certificado_password`  | `Char`      | Contraseña del .p12                 |
| `sri_establecimiento`       | `Char(3)`   | Código de establecimiento           |
| `sri_punto_emision`         | `Char(3)`   | Código de punto de emisión          |
| `sri_secuencial`            | `Integer`   | Último secuencial (auto-incremento) |
| `sri_razon_social`          | `Char`      | Razón social para el SRI            |
| `sri_obligado_contabilidad` | `Boolean`   | Obligado a llevar contabilidad      |

### 5.3 `veterinaria.facturacion` — Herencia SRI

**Archivo:** `models/facturacion_inherit.py`

Campos agregados por herencia:

| Campo                         | Tipo                  | Descripción                     |
| ----------------------------- | --------------------- | ------------------------------- |
| `sri_documento_id`            | `Many2one`            | Documento electrónico vinculado |
| `sri_forma_pago`              | `Selection`           | Forma de pago SRI (01, 15-21)   |
| `tipo_identificacion_cliente` | `Selection`           | RUC, Cédula, Pasaporte, etc.    |
| `identificacion_cliente`      | `Char`                | Número de identificación        |
| `sri_estado`                  | `Selection` (related) | Estado del documento SRI        |
| `sri_clave_acceso`            | `Char` (related)      | Clave de acceso                 |

---

## 6. Servicios Internos y Automatizaciones

### 6.1 Cron Job — Recordatorios de Cita

| Atributo        | Valor                                                                                   |
| --------------- | --------------------------------------------------------------------------------------- |
| **ID XML**      | `ir_cron_recordatorio_cita`                                                             |
| **Modelo**      | `veterinaria.cita`                                                                      |
| **Método**      | `_cron_enviar_recordatorios()`                                                          |
| **Frecuencia**  | Cada 1 hora                                                                             |
| **Descripción** | Busca citas programadas en las próximas 24 horas sin recordatorio enviado y envía email |

### 6.2 Creación Automática de Usuario Portal

Al crear un `res.partner` con `es_propietario=True` y email:

1. Se crea un `res.users` con login = email
2. Se asignan grupos: `base.group_portal` + `group_veterinaria_cliente`
3. Se genera contraseña temporal aleatoria (12 caracteres)
4. Se envía email con credenciales usando template `mail_template_credenciales_portal`

### 6.3 Sincronización de Historia Clínica

Al crear o modificar una cita, se ejecuta `_sync_historia()`:

1. Busca historia clínica existente del paciente
2. Si no existe, la crea automáticamente
3. Actualiza campos clínicos (alergias, peso, tipo de sangre, condiciones)

### 6.4 Control de Stock en Facturación

Al validar una factura (`action_validar_factura`):

1. Valida que haya stock suficiente para cada línea de tipo `medicamento` o `producto`
2. Descuenta `cantidad_stock` del inventario
3. Marca las citas incluidas como `facturada=True`

---

## 7. Sistema de Autenticación y Seguridad

### 7.1 Autenticación

| Tipo                  | Mecanismo                                                  | Rutas                                       |
| --------------------- | ---------------------------------------------------------- | ------------------------------------------- |
| **Backend (Interno)** | Login estándar de Odoo (`/web/login`)                      | `/web/*`                                    |
| **Portal (Clientes)** | Login de portal Odoo con grupo `group_veterinaria_cliente` | `/my/*`                                     |
| **Público**           | Sin autenticación (`auth='public'`)                        | `/`, `/servicios`, `/nosotros`, `/contacto` |

### 7.2 Protección CSRF

Todos los formularios POST del sitio web incluyen protección CSRF automática de Odoo (`csrf=True`).

### 7.3 Grupos de Seguridad

| XML ID                            | Nombre         | Permisos Clave                                 |
| --------------------------------- | -------------- | ---------------------------------------------- |
| `group_veterinaria_recepcionista` | Recepcionista  | CRUD citas y pacientes, lectura medicamentos   |
| `group_veterinaria_veterinario`   | Veterinario    | + Historia clínica, recetas                    |
| `group_veterinaria_admin`         | Administrador  | + Facturación, ventas, inventario, eliminación |
| `group_veterinaria_cliente`       | Cliente Portal | Solo sus propios registros (record rules)      |

### 7.4 Record Rules (Aislamiento de Datos)

Los clientes del portal solo ven registros donde `propietario_id = user.partner_id`. Esto aplica a:

- `veterinaria.paciente`
- `veterinaria.cita`
- `veterinaria.historia_clinica`
- `veterinaria.facturacion`
- `veterinaria.receta`
- `veterinaria.vacuna.aplicada`

---

## 8. Plantillas de Email

| Template XML ID                     | Evento                     | Destinatario                |
| ----------------------------------- | -------------------------- | --------------------------- |
| `mail_template_credenciales_portal` | Creación de usuario portal | Propietario (nuevo usuario) |
| `mail_template_cita_confirmacion`   | Creación de cita           | Propietario del paciente    |
| `mail_template_cita_recordatorio`   | Cron (24h antes)           | Propietario del paciente    |
| `mail_template_cita_completada`     | Cita completada            | Propietario del paciente    |

### Configuración SMTP

El servidor SMTP se configura en:

1. **Datos XML:** `data/mail_server.xml` (servidor por defecto)
2. **Variables de entorno:** `.env` → `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
3. **Odoo UI:** Ajustes → Servidores de correo saliente
