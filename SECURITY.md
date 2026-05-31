# Política de Seguridad — VitalPet

## Versiones Soportadas

| Versión | Soporte de seguridad |
|---|---|
| 18.0.1.6.x (actual) | Activo |
| 18.0.1.x anteriores | Solo bugs críticos |
| < 18.0.1.0 | Sin soporte |

---

## Reporte de Vulnerabilidades

Si descubres una vulnerabilidad de seguridad en VitalPet, **no abras un Issue público**. En su lugar:

1. **Contacta al equipo de forma privada** enviando un correo a: `andru7478@gmail.com`
2. **Asunto del correo:** `[SECURITY] VitalPet - Descripción breve del problema`
3. Incluye en tu reporte:
   - Descripción detallada de la vulnerabilidad.
   - Pasos para reproducirla.
   - Impacto potencial (qué datos o funcionalidades se ven afectados).
   - Si es posible, una propuesta de solución o parche.

Nos comprometemos a responder en un plazo máximo de **72 horas** y a trabajar contigo para resolver el problema antes de cualquier divulgación pública.

---

## Modelo de Seguridad del Sistema

### Autenticación

VitalPet delega la autenticación completamente en **Odoo 18**, que provee:

- Autenticación por sesión con cookies seguras (`HttpOnly`, `SameSite=Lax`).
- Hashing de contraseñas con **bcrypt** (no MD5 ni SHA1 plano).
- Protección contra fuerza bruta (bloqueo de cuenta tras intentos fallidos).
- Soporte para 2FA (Two-Factor Authentication) mediante la funcionalidad estándar de Odoo.

### Autorización — Grupos Jerárquicos

El sistema implementa **4 grupos de seguridad** jerárquicos:

| Grupo | Acceso |
|---|---|
| `group_veterinaria_recepcionista` | Citas, pacientes, propietarios (sin eliminación) |
| `group_veterinaria_veterinario` | + Historia clínica, recetas, vacunas |
| `group_veterinaria_admin` | Acceso total incluyendo facturación y eliminación |
| `group_veterinaria_cliente` | Solo sus propios registros vía record rules |

### Aislamiento de Datos del Portal

Todas las rutas del portal (`/my/*`) aplican **record rules** que garantizan que cada cliente solo acceda a sus propios datos:

```python
# Ejemplo: record rule para mascotas del portal
domain = [('propietario_id.user_ids', 'in', [user.id])]
```

Adicionalmente, los controladores del portal verifican explícitamente la pertenencia del registro antes de mostrarlo (doble validación).

### Protección CSRF

Todos los formularios POST del sitio web y portal incluyen protección **CSRF** automática proporcionada por Odoo.

### Certificado SRI (.p12)

El certificado de firma electrónica `.p12` utilizado para la facturación con el SRI:

- **Nunca** debe commitearse en el repositorio Git.
- Se almacena en la base de datos de Odoo (campo `Binary` en `res.company`), cifrado en reposo por PostgreSQL.
- La contraseña del certificado se gestiona como campo de contraseña en Odoo (no se muestra en texto plano en la UI).

---

## Buenas Prácticas para Desarrolladores

### Variables de Entorno

- **Nunca** versionar el archivo `.env` con credenciales reales. Solo versionar `.env.example` con valores de ejemplo.
- Rotar contraseñas regularmente: `POSTGRES_PASSWORD`, `ODOO_ADMIN_PASSWD`, `SMTP_PASSWORD`.
- En producción, usar un gestor de secretos (HashiCorp Vault, AWS Secrets Manager, etc.).

### Uso de `sudo()` en el código

El uso de `sudo()` en modelos y controladores debe ser mínimo y justificado:

```python
# Correcto: uso justificado con comentario
partner.sudo().write({'image_1920': image_data})  # El usuario portal no tiene write en res.partner directamente

# Incorrecto: sudo sin justificación en un controlador público
records = request.env['veterinaria.facturacion'].sudo().search([])  # Expone TODOS los registros
```

### Validación de Entradas

- Nunca construir queries SQL con interpolación directa de cadenas. Usar el ORM de Odoo.
- Validar `pet_id`, `factura_id` y otros parámetros de URL en los controladores del portal antes de devolver datos.
- Los parámetros de usuario deben escaparse automáticamente por los templates QWeb de Odoo (protección XSS).

### Dependencias Externas

Las dependencias Python externas del proyecto son:

| Librería | Versión | Propósito | Última revisión de seguridad |
|---|---|---|---|
| `zeep` | Última estable | Cliente SOAP para SRI | Al instalar |
| `python-barcode` | Última estable | Generación de códigos de barras | Al instalar |
| `python-stdnum` | Última estable | Validación RUC/Cédula | Al instalar |

Mantener estas dependencias actualizadas para recibir parches de seguridad.

---

## Configuración Segura para Producción

Al desplegar en producción, asegurarse de:

1. **Cambiar `ODOO_ADMIN_PASSWD`** a una contraseña fuerte (mínimo 16 caracteres, aleatorio).
2. **Deshabilitar el modo debug** (`?debug=1`) en producción. Configurar en `odoo.conf`:
   ```ini
   without_demo = all
   ```
3. **Usar HTTPS** con un certificado TLS válido (Let's Encrypt o similar) frente al contenedor Odoo.
4. **Configurar `workers`** en `odoo.conf` para entornos multiworker (mínimo 2):
   ```ini
   workers = 4
   limit_memory_hard = 2684354560
   limit_time_cpu = 60
   limit_time_real = 120
   ```
5. **Exponer solo el puerto 443/80**, no el 8069 directamente a internet.
6. **Backups cifrados** de la base de datos PostgreSQL y el filestore de Odoo.
7. **Actualizar la imagen Docker** de Odoo regularmente:
   ```bash
   docker pull odoo:18
   docker-compose up -d --build
   ```

---

## Divulgación Responsable

Seguimos el principio de **Responsible Disclosure**:

1. El equipo recibe el reporte de forma privada.
2. Se confirma la vulnerabilidad y se desarrolla un parche.
3. Se lanza una versión corregida.
4. Se agradece públicamente al reportador (con su permiso) en el CHANGELOG.

Agradecemos a todas las personas que contribuyen a mejorar la seguridad del proyecto de forma responsable.
