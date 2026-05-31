# 🐾 VitalPet — Sistema Integral de Gestión Veterinaria

<p align="center">
  <img src="custom_addons/veterinaria_core/static/description/icon.png" alt="VitalPet Logo" width="120"/>
</p>

<p align="center">
  <strong>Sistema profesional para la gestión integral de clínicas veterinarias</strong><br/>
  Desarrollado sobre <a href="https://www.odoo.com/">Odoo 18</a> · PostgreSQL 15 · Docker
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Odoo-18.0-875A7B?style=flat-square&logo=odoo" alt="Odoo 18"/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Licencia-LGPL--3-green?style=flat-square" alt="Licencia"/>
</p>

---

## 📖 Descripción General

**VitalPet** es un sistema ERP veterinario completo construido como un conjunto de módulos personalizados para Odoo 18. Permite a clínicas veterinarias gestionar de forma integral todos los procesos operativos: desde la recepción de pacientes y el agendamiento de citas, hasta la facturación electrónica con el SRI de Ecuador, pasando por la gestión de historial médico, inventario, recetas y un portal web para los clientes.

El sistema está completamente contenedorizado con Docker, lo que garantiza un despliegue rápido y reproducible en cualquier entorno.

---

## 🎯 Objetivo del Proyecto

Desarrollar una aplicación de gestión integral para clínicas veterinarias que:

- **Centralice** la información de pacientes (mascotas), propietarios, veterinarios y servicios en un solo sistema.
- **Automatice** procesos administrativos como facturación, control de inventario, recordatorios de citas y envío de credenciales de acceso.
- **Ofrezca** un portal web para que los clientes consulten sus mascotas, citas, historiales médicos, recetas y descarguen carnets de vacunación en PDF.
- **Integre** la facturación electrónica con el SRI (Servicio de Rentas Internas) de Ecuador, cumpliendo con los estándares de XML XSD 2.1.0 y firma electrónica XAdES-BES.
- **Facilite** la escalabilidad y el mantenimiento mediante buenas prácticas de desarrollo en Odoo, Docker y control de versiones.

---

## ✨ Funcionalidades Principales

### 🏥 Módulo Core (`veterinaria_core`)
| Funcionalidad | Descripción |
|---|---|
| **Gestión de Propietarios** | Registro de clientes (res.partner extendido), creación automática de usuario portal con credenciales por email |
| **Gestión de Pacientes** | Registro de mascotas con foto, especie, raza, peso, microchip, alergias y estado de vacunación |
| **Gestión de Veterinarios** | Catálogo de profesionales con especialidad, horarios y disponibilidad |
| **Agendamiento de Citas** | Citas con validación de disponibilidad, detección de conflictos horarios y vista calendario |
| **Historia Clínica** | Generada automáticamente al crear una cita, con seguimiento de alergias, peso, tipo de sangre y condiciones crónicas |
| **Carnet de Vacunación** | Registro de vacunas aplicadas con próxima dosis calculada automáticamente; descargable como PDF |
| **Recetas Médicas** | Prescripciones con medicamentos del inventario o externos, cálculo automático de cantidad total |
| **Inventario Unificado** | Gestión de productos, servicios y medicamentos con control de stock, precios y márgenes |
| **Facturación Multiservicio** | Facturación de citas, medicamentos, productos y servicios con importación desde recetas |
| **Ventas** | Integración con `sale.order` de Odoo para ventas directas de productos |
| **Notificaciones por Email** | Confirmación de citas, recordatorios 24h antes (cron), resumen post-consulta y credenciales de acceso |
| **Portal del Cliente** | Mis mascotas, citas, historial médico, facturas (con PDF), recetas y carnet de vacunas |

### 🌐 Módulo Web (`veterinaria_web`)
| Funcionalidad | Descripción |
|---|---|
| **Sitio Web Público** | Landing page profesional con páginas de Inicio, Servicios, Nosotros y Contacto |
| **Formulario de Contacto** | Recepción de consultas de potenciales clientes |
| **Diseño Responsivo** | CSS personalizado con animaciones, variables CSS y Bootstrap de Odoo |

### 🧾 Módulo SRI (`l10n_ec_sri_vet`)
| Funcionalidad | Descripción |
|---|---|
| **Generación XML** | XML según XSD 2.1.0 del SRI con clave de acceso Módulo 11 |
| **Firma Electrónica** | XAdES-BES con certificado .p12 usando `cryptography` nativo |
| **Envío SOAP** | Envío al Web Service de Recepción y consulta de Autorización del SRI |
| **RIDE** | Generación del RIDE (PDF) con código de barras Code128 |
| **Envío por Email** | Envío automático del RIDE y XML autorizado al cliente |

---

## 📋 Requisitos Previos

| Requisito | Versión Mínima | Descripción |
|---|---|---|
| **Docker** | 20.10+ | Motor de contenedores |
| **Docker Compose** | 2.0+ | Orquestación de servicios |
| **Git** | 2.30+ | Control de versiones |
| **Navegador Web** | Moderno | Chrome, Firefox, Edge (últimas versiones) |
| **Puerto 8069** | Disponible | Puerto por defecto de Odoo |

> **Nota:** No se requiere instalar Python, PostgreSQL ni Odoo localmente. Todo corre dentro de Docker.

---

## 🚀 Pasos de Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/DavidGR21/Proyecto-Odoo.git
cd Proyecto-Odoo
```

### 2. Configurar Variables de Entorno

```bash
cp .env.example .env
```

Editar el archivo `.env` con los valores deseados:

```env
# Base de Datos
POSTGRES_DB=postgres
POSTGRES_USER=odoo
POSTGRES_PASSWORD=odoo
DB_HOST=db
DB_PORT=5432

# Odoo
ODOO_PORT=8069
ODOO_LOG_LEVEL=info
ODOO_WORKERS=0
ODOO_ADMIN_PASSWD=admin

# SMTP (opcional — para notificaciones por email)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_app_password
```

### 3. Levantar los Contenedores

```bash
docker-compose up -d --build
```

Esto construye la imagen de Odoo con las dependencias adicionales (`zeep`, `python-barcode`, `python-stdnum`) y levanta:
- **vitalpet-db**: PostgreSQL 15
- **vitalpet-odoo**: Odoo 18 con los módulos personalizados

### 4. Verificar que los Servicios Están Corriendo

```bash
docker-compose ps
docker-compose logs -f odoo
```

### 5. Acceder a Odoo

- **URL:** `http://localhost:8069`
- **Usuario:** `admin`
- **Contraseña:** `admin`

### 6. Instalar los Módulos

1. Ir a **Aplicaciones** → **Actualizar lista de aplicaciones**
2. Buscar e instalar en este orden:
   - `Veterinaria Core` (instala dependencias base, mail, portal, sale, account, calendar, stock, crm)
   - `VitalPet - Sitio Web Veterinaria` (requiere módulo website)
   - `Facturación Electrónica SRI Ecuador` (requiere veterinaria_core + certificado .p12)

---

## ⚙️ Configuración del Entorno

### Archivo `odoo.conf`

```ini
[options]
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
db_name = postgres
http_port = 8069
workers = 0
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
admin_passwd = admin
smtp_server = mailhog
smtp_port = 1025
```

### Docker Compose

El archivo `docker-compose.yml` orquesta dos servicios:

| Servicio | Imagen | Puerto | Descripción |
|---|---|---|---|
| `db` | `postgres:15` | 5432 (interno) | Base de datos PostgreSQL |
| `odoo` | Build desde `Dockerfile` | 8069 → host | Servidor Odoo 18 |

### Volúmenes Persistentes

| Volumen | Ruta en contenedor | Descripción |
|---|---|---|
| `vitalpet-db-data` | `/var/lib/postgresql/data` | Datos de PostgreSQL |
| `vitalpet-web-data` | `/var/lib/odoo` | Datos de Odoo (filestore) |
| `./custom_addons` | `/mnt/extra-addons` | Módulos personalizados (bind mount) |

---

## 📂 Dependencias

### Dependencias de Odoo (módulos base)

| Módulo | Uso en VitalPet |
|---|---|
| `base` | Funcionalidades base de Odoo (res.partner, res.users) |
| `mail` | Sistema de mensajería, plantillas de email, chatter |
| `web` | Framework web de Odoo |
| `portal` | Portal de cliente autenticado |
| `auth_signup` | Invitaciones por email y registro de usuarios portal |
| `sale` | Órdenes de venta para integración de ventas |
| `account` | Facturación y contabilidad, impuestos |
| `calendar` | Vista calendario para citas |
| `stock` | Control de inventario y movimientos de stock |
| `crm` | Gestión de relaciones con clientes |
| `website` | Motor del sitio web público (para `veterinaria_web`) |

### Dependencias Python Externas (instaladas en Dockerfile)

| Librería | Versión | Uso |
|---|---|---|
| `zeep` | Última | Cliente SOAP para Web Services del SRI |
| `python-barcode[images]` | Última | Generación de códigos de barras Code128 para RIDE |
| `python-stdnum` | Última | Validación de números de identificación (RUC, cédula) |

---

## 🗂️ Estructura General del Repositorio

```
Proyecto-Odoo/
├── 📄 README.md                          # Documentación principal del proyecto
├── 📄 CONTRIBUTING.md                    # Guía de contribución al proyecto
├── 📄 CODE_OF_CONDUCT.md                # Código de conducta del equipo
├── 📄 LICENSE                            # Licencia LGPL-3
├── 📄 CHANGELOG.md                       # Historial de cambios
├── 📄 SECURITY.md                        # Política de seguridad
│
├── 🐳 docker-compose.yml                # Orquestación Docker (Odoo + PostgreSQL)
├── 🐳 Dockerfile                         # Imagen personalizada de Odoo 18
├── ⚙️ odoo.conf                          # Configuración del servidor Odoo
├── 📄 .env.example                       # Template de variables de entorno
├── 📄 .gitignore                         # Exclusiones de versionado
│
├── 📁 docs/                              # Documentación técnica extendida
│   └── API.md                            # Documentación de API, controladores y servicios
│
├── 📁 .devcontainer/                     # Configuración VS Code Dev Container
│
└── 📁 custom_addons/                     # Módulos personalizados de Odoo
    │
    ├── 📦 veterinaria_core/              # Módulo principal de gestión veterinaria
    │   ├── __init__.py
    │   ├── __manifest__.py               # v18.0.1.6.0 — metadatos y dependencias
    │   ├── controllers/                  # Controladores HTTP (portal del cliente)
    │   │   ├── __init__.py
    │   │   └── portal.py                 # Rutas /my/pets, /my/appointments, etc.
    │   ├── models/                       # 18 modelos ORM
    │   │   ├── propietario.py            # res.partner extendido (propietarios)
    │   │   ├── paciente.py               # Mascotas/Pacientes
    │   │   ├── veterinario.py            # Profesionales veterinarios
    │   │   ├── especialidad.py           # Especialidades veterinarias
    │   │   ├── cita.py                   # Citas con validación de disponibilidad
    │   │   ├── historia_clinica.py       # Historia clínica (auto-generada)
    │   │   ├── medicamento.py            # Catálogo de medicamentos
    │   │   ├── servicio.py               # Servicios veterinarios
    │   │   ├── producto.py               # Productos veterinarios
    │   │   ├── inventario.py             # Inventario unificado
    │   │   ├── vacuna.py                 # Catálogo + vacunas aplicadas
    │   │   ├── receta.py                 # Recetas médicas + líneas
    │   │   ├── facturacion.py            # Facturación multiservicio
    │   │   ├── facturacion_linea.py      # Líneas de facturación
    │   │   ├── facturacion_wizard.py     # Wizards de facturación
    │   │   ├── venta.py                  # Ventas + líneas de venta
    │   │   ├── documento_venta.py        # Documento de venta unificado
    │   │   └── credential_wizard.py      # Wizard de credenciales portal
    │   ├── views/                        # Vistas XML (formularios, listas, menús)
    │   ├── data/                         # Datos iniciales (secuencias, cron, templates email)
    │   ├── security/                     # Grupos, reglas de registro, ACLs
    │   ├── reports/                      # Reportes QWeb-PDF (carnet vacunas, factura)
    │   └── static/                       # Recursos estáticos
    │
    ├── 📦 veterinaria_web/               # Sitio web público de la clínica
    │   ├── __init__.py
    │   ├── __manifest__.py               # v18.0.1.0.0
    │   ├── controllers/
    │   │   ├── __init__.py
    │   │   ├── main.py                   # Rutas públicas (/, /servicios, /nosotros, /contacto)
    │   │   └── controllers.py            # Archivo placeholder (no activo)
    │   ├── models/
    │   ├── views/                        # Templates QWeb (layout, pages, snippets)
    │   ├── static/src/                   # CSS, JS e imágenes
    │   └── demo/                         # Datos demo
    │
    └── 📦 l10n_ec_sri_vet/               # Facturación electrónica SRI Ecuador
        ├── __init__.py
        ├── __manifest__.py               # v18.0.1.0.0
        ├── models/
        │   ├── facturacion_inherit.py     # Herencia sobre veterinaria.facturacion
        │   ├── res_company.py            # Configuración SRI en res.company
        │   ├── sri_documento.py          # Documento electrónico SRI
        │   ├── sri_xml_generator.py      # Generador XML XSD 2.1.0
        │   ├── sri_firma.py              # Firma XAdES-BES con certificado .p12
        │   └── sri_ws_client.py          # Cliente SOAP para Web Services del SRI
        ├── views/                        # Vistas de configuración SRI
        ├── data/                         # Catálogos del SRI
        ├── report/                       # RIDE template
        └── security/                     # ACLs del módulo SRI
```

---

## ▶️ Instrucciones para Ejecutar el Proyecto

### Desarrollo Local

```bash
# 1. Levantar contenedores
docker-compose up -d --build

# 2. Ver logs en tiempo real
docker-compose logs -f odoo

# 3. Acceder a http://localhost:8069

# 4. Tras cambios en el código, reiniciar Odoo
docker-compose restart odoo

# 5. Actualizar módulo desde la interfaz
#    Aplicaciones → Buscar módulo → ⚙️ Actualizar
```

### Comandos Útiles

```bash
# Ver estado de contenedores
docker-compose ps

# Acceder a la shell del contenedor Odoo
docker exec -it vitalpet-odoo bash

# Acceder a la consola PostgreSQL
docker exec -it vitalpet-db psql -U odoo -d postgres

# Parar servicios (mantiene datos)
docker-compose stop

# Parar y eliminar contenedores (mantiene volúmenes)
docker-compose down

# Parar y BORRAR TODO (base de datos, filestore)
docker-compose down -v
```

### Actualización de Módulos por Línea de Comandos

```bash
docker exec -it vitalpet-odoo odoo -c /etc/odoo/odoo.conf -u veterinaria_core --stop-after-init
docker-compose restart odoo
```

---

## 🔐 Sistema de Seguridad y Roles

El sistema implementa **4 grupos jerárquicos de seguridad**:

| Grupo | Hereda de | Permisos |
|---|---|---|
| **Recepcionista** | — | Gestión de citas, pacientes y propietarios. Lectura de medicamentos |
| **Veterinario** | Recepcionista | + Historia clínica, recetas, vacunas |
| **Administrador Veterinaria** | Veterinario | + Facturación, ventas, inventario completo, eliminación |
| **Cliente Veterinaria (Portal)** | Portal Odoo | Solo sus propias mascotas, citas, facturas, recetas, carnet |

Las **Record Rules** aseguran aislamiento de datos: cada cliente portal solo ve registros vinculados a su `partner_id`.

---

## 🐛 Solución de Problemas

| Problema | Solución |
|---|---|
| Contenedores no inician | `docker-compose logs -f` para ver errores |
| "Modelo no encontrado" | `docker-compose restart odoo` y actualizar módulo |
| "Permiso denegado" | Verificar `security/ir.model.access.csv` y grupos |
| Cambios no aparecen | Limpiar caché del navegador (Ctrl+Shift+Del) + `docker-compose restart odoo` |
| BD corrupta | `docker-compose down -v && docker-compose up -d --build` |
| Emails no se envían | Verificar configuración SMTP en `.env` y en Odoo → Ajustes → Correo |

---

## 🔧 Recomendaciones de Mantenimiento

1. **Backups regulares**: Realizar respaldos de la base de datos PostgreSQL (`pg_dump`) y del filestore de Odoo.
2. **Actualizar módulos**: Tras cada cambio de código, actualizar el módulo desde Aplicaciones o por CLI.
3. **Monitorear logs**: Revisar periódicamente `docker-compose logs odoo` para detectar errores.
4. **Variables de entorno**: Nunca versionar el archivo `.env` con credenciales reales.
5. **Certificado SRI**: Renovar el certificado de firma electrónica .p12 antes de su vencimiento.
6. **Actualizaciones de seguridad**: Mantener la imagen Docker de Odoo y PostgreSQL actualizadas.
7. **Pruebas antes de deploy**: Siempre probar cambios en ambiente local antes de pasar a producción.

---

## 📚 Documentación Adicional

| Documento | Descripción |
|---|---|
| [docs/API.md](docs/API.md) | Documentación completa de API: controladores, endpoints, modelos y servicios internos |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guía para contribuir al proyecto |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Código de conducta del equipo |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios del proyecto |
| [SECURITY.md](SECURITY.md) | Política de seguridad y reporte de vulnerabilidades |
| [LICENSE](LICENSE) | Licencia LGPL-3 |

---

## 👥 Equipo — VitalPet Team

Proyecto desarrollado como parte del curso de Desarrollo de Aplicaciones y Servicios (DAS), Octavo Semestre.

## 📄 Licencia

Este proyecto está licenciado bajo **LGPL-3** (GNU Lesser General Public License v3).
Consulta el archivo [LICENSE](LICENSE) para más detalles.
