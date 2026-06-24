import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validar que las variables de entorno estén configuradas
if not SUPABASE_URL:
    raise ValueError("La variable de entorno SUPABASE_URL no está configurada. Verifica tu archivo .env")

if not SUPABASE_KEY:
    raise ValueError("La variable de entorno SUPABASE_KEY no está configurada. Verifica tu archivo .env")

# Inicializar el cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
