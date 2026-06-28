# 🚛 Sistema Logístico Perene Transport - API REST Backend

Este repositorio contiene la API REST para el sistema de control de guías de remisión y liquidaciones quincenales de **Perene Transport**. El backend está construido con **FastAPI (Python)** y utiliza **Supabase** como base de datos relacional nativa[cite: 1, 2, 3]. 

El sistema implementa una arquitectura modular adaptada para tres roles operativos principales: Administrador, Cajero y Conductor.

---

## 🛠️ Tecnologías Utilizadas

*   **FastAPI:** Framework de alto rendimiento para la construcción de los endpoints[cite: 2, 3].
*   **Pydantic V2:** Validación de estructuras de datos y esquemas lógicos rigurosos[cite: 2, 3].
*   **Supabase Python Client:** Integración directa con PostgreSQL y ejecución de consultas relacionales enriquecidas[cite: 1, 2].
*   **Uvicorn:** Servidor ASGI para el despliegue local y en la nube.

---

## 📁 Estructura del Proyecto

```text
API_PERENE/
├── app/
│   ├── routers/            # Módulos de la API divididos por contextos
│   │   ├── auth.py         # Control de autenticación y tokens
│   │   ├── auxiliares.py   # Catálogos estáticos/mock del prototipo
│   │   ├── conductores.py  # Gestión del personal y tarjetas del dashboard
│   │   ├── guias.py        # Inserción relacional y KPIs operativos[cite: 2]
│   │   └── liquidaciones.py# Lógica y cálculos de cierre financiero[cite: 3]
│   ├── database.py         # Inicialización del cliente Supabase
│   └── main.py             # Configuración central e inclusión de rutas
├── .env                    # Variables de entorno locales (Excluido de Git)
├── .gitignore              # Archivos ignorados por Git
└── requirements.txt        # Dependencias del proyecto para la nube



⚙️ Configuración e Instalación Local (Para el equipo de desarrollo)
Si se desea levantar o continuar editando este backend de forma local, se deben seguir estos pasos:

1. Clonar el repositorio
git clone [https://github.com/Dennills/Api-Rest--Sistema-Logistico.git](https://github.com/Dennills/Api-Rest--Sistema-Logistico.git)
cd Api-Rest--Sistema-Logistico

2. Configurar el Entorno Virtual
# Crear entorno virtual
python -m venv .venv

# Activar en Windows (PowerShell)
.venv\Scripts\Activate.ps1

3. Instalar Dependencias
pip install -r requirements.txt


4. Variables de Entorno (.env)
Crear un archivo .env en la raíz del proyecto y configurar las credenciales del cluster de Supabase correspondiente:

SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_anon_public_key

5. Levantar el Servidor Local
uvicorn app.main:app --reload
La API estará disponible en http://127.0.0.1:8000. Puedes acceder a la documentación interactiva y hacer pruebas en vivo desde http://127.0.0.1:8000/docs