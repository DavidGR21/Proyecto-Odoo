# VitalPet - Sistema de Gestión Veterinaria en Odoo

Proyecto Odoo 18 para la gestión de clínicas veterinarias.

## 📋 Estructura del Proyecto

```
PROYECTO ODOO/
├── docker-compose.yml          # Configuración de contenedores
├── odoo.conf                   # Configuración de Odoo
├── .env.example                # Variables de entorno (ejemplo)
├── .gitignore                  # Exclusiones de git
├── README.md                   # Este archivo
├── custom_addons/              # Módulos personalizados
│   └── veterinaria_core/       # Módulo base de veterinaria
│       ├── __init__.py
│       ├── __manifest__.py     # Definición del módulo
│       ├── models/             # Modelos de datos
│       ├── views/              # Vistas XML
│       ├── security/           # Control de acceso
│       └── static/             # Recursos estáticos
└── .devcontainer/              # Configuración de dev container
    └── devcontainer.json
```

## 🚀 Inicio Rápido

### Requisitos
- Docker
- Docker Compose

### Levantar el proyecto

```bash
docker-compose up -d
```

Accede a Odoo en: **http://localhost:8070**

Credenciales por defecto:
- Usuario: `admin`
- Contraseña: `admin`

### Detener el proyecto

```bash
docker-compose down
```

## 📝 Configuración

### Variables de Entorno

Copia `.env.example` a `.env` (opcional):
```bash
cp .env.example .env
```

### Configuración de Odoo

Edita `odoo.conf` para ajustar parámetros como:
- Nivel de logging
- Número de workers
- Puertos
- Configuración SMTP

## 📦 Módulos Instalados

- **veterinaria_core**: Módulo base para la gestión veterinaria

Para instalar un módulo:
1. Accede a Odoo
2. Ve a **Aplicaciones**
3. Busca y haz clic en **Instalar**

## 🔧 Desarrollo

### Estructura de un Modelo

En `custom_addons/veterinaria_core/models/`:

```python
from odoo import models, fields

class MasModel(models.Model):
    _name = 'veterinaria.modelo'
    _description = 'Descripción'

    name = fields.Char('Nombre', required=True)
    description = fields.Text('Descripción')
```

### Vistas XML

En `custom_addons/veterinaria_core/views/`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>
        <record id="view_model_list" model="ir.ui.view">
            <field name="name">veterinaria.modelo.list</field>
            <field name="model">veterinaria.modelo</field>
            <field name="arch" type="xml">
                <tree>
                    <field name="name"/>
                </tree>
            </field>
        </record>
    </data>
</odoo>
```

## 🐛 Solución de Problemas

### Los contenedores no inician
```bash
docker-compose logs -f
```

### Necesito reinstalar el módulo
```bash
# Eliminar contenedores y volúmenes
docker-compose down -v

# Levantar nuevamente
docker-compose up -d
```

### Cambios en el código no se reflejan
- Reinicia el servicio de Odoo: `docker-compose restart odoo`
- O actualiza el módulo desde la interfaz de Odoo

## 📚 Recursos

- [Documentación oficial de Odoo 18](https://www.odoo.com/documentation/18.0/)
- [Guía de desarrollo de módulos](https://www.odoo.com/documentation/18.0/developer/tutorials.html)

## 👥 Equipo

VitalPet Team

## 📄 Licencia

LGPL-3
