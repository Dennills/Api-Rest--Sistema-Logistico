from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, guias, liquidaciones

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="API Perene",
    description="Sistema logístico de Perene Transport S.A.C.",
    version="1.0.0"
)

# Configurar CORS middleware para permitir peticiones desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos HTTP
    allow_headers=["*"]  # Permitir todos los headers
)

# Incluir el router de autenticación
app.include_router(auth.router)

# Incluir el router de guías
app.include_router(guias.router)

# Incluir el router de liquidaciones
app.include_router(liquidaciones.router)


@app.get("/")
async def root():
    """
    Endpoint básico para verificar que la API está funcionando
    """
    return {"status": "API Perene Activa"}
