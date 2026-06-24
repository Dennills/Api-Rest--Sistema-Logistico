from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import supabase

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Esquema para la solicitud de login"""
    email: str
    password: str


@router.post("/login")
async def login(data: LoginRequest):
    """
    Endpoint para autenticar usuarios con Supabase Auth.
    
    Args:
        data: Credenciales del usuario (email y password)
    
    Returns:
        JSON con access_token, email, username y rolid
    
    Raises:
        HTTPException: Si las credenciales son inválidas
    """
    try:
        # Autenticar con Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })
        
        # Extraer el UUID del usuario autenticado
        user_id = auth_response.user.id
        access_token = auth_response.session.access_token
        
        # Consultar la tabla public.usuario para obtener rolid y username
        user_data = supabase.table("usuario").select("username, rolid").eq("supabase_uid", user_id).single().execute()
        
        if not user_data.data:
            raise HTTPException(status_code=401, detail="Usuario no encontrado en la base de datos")
        
        # Extraer los datos del usuario
        username = user_data.data.get("username")
        rolid = user_data.data.get("rolid")
        
        # Retornar los datos de autenticación
        return {
            "access_token": access_token,
            "email": data.email,
            "username": username,
            "rolid": rolid
        }
    
    except Exception as e:
        # Si las credenciales son inválidas o hay otro error
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
