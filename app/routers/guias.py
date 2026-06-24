from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.database import supabase

router = APIRouter(prefix="/api/guias", tags=["guias"])


# ============================================================================
# ESQUEMAS DE PYDANTIC V2
# ============================================================================

class ContenedorCreate(BaseModel):
    """Esquema para crear un contenedor"""
    numerocontenedor: str = Field(..., min_length=1, description="Número único del contenedor")
    precinto: str = Field(..., min_length=1, description="Número de precinto")
    tamanioid: int = Field(..., gt=0, description="ID del tamaño del contenedor")
    pesokg: float = Field(..., gt=0, description="Peso del contenedor en kilogramos")
    terminalid: int = Field(..., gt=0, description="ID de la terminal")
    estadocontenedorid: int = Field(..., gt=0, description="ID del estado del contenedor")

    class Config:
        """Configuración del esquema"""
        json_schema_extra = {
            "example": {
                "numerocontenedor": "CONT001",
                "precinto": "PREC12345",
                "tamanioid": 1,
                "pesokg": 5000.50,
                "terminalid": 1,
                "estadocontenedorid": 1
            }
        }


class GuiaCreateRequest(BaseModel):
    """Esquema para crear una guía de remisión con contenedor asociado"""
    numeroguia: str = Field(..., min_length=1, description="Número de la guía de remisión")
    conductorid: int = Field(..., gt=0, description="ID del conductor")
    vehiculoid: int = Field(..., gt=0, description="ID del vehículo")
    empresaid: int = Field(..., gt=0, description="ID de la empresa")
    tiposervicioid: int = Field(..., gt=0, description="ID del tipo de servicio")
    origenid: int = Field(..., gt=0, description="ID del origen")
    destinoid: int = Field(..., gt=0, description="ID del destino")
    pesotoneladas: float = Field(..., gt=0, description="Peso en toneladas")
    estadoid: int = Field(..., gt=0, description="ID del estado de la guía")
    fechaservicio: str = Field(..., description="Fecha del servicio (YYYY-MM-DD)")
    registradopor: int = Field(..., gt=0, description="ID del usuario que registra la guía")
    contenedor: ContenedorCreate = Field(..., description="Datos del contenedor asociado")

    class Config:
        """Configuración del esquema"""
        json_schema_extra = {
            "example": {
                "numeroguia": "GUIA001",
                "conductorid": 1,
                "vehiculoid": 1,
                "empresaid": 1,
                "tiposervicioid": 1,
                "origenid": 1,
                "destinoid": 2,
                "pesotoneladas": 5.5,
                "estadoid": 1,
                "fechaservicio": "2026-06-23",
                "registradopor": 1,
                "contenedor": {
                    "numerocontenedor": "CONT001",
                    "precinto": "PREC12345",
                    "tamanioid": 1,
                    "pesokg": 5000.50,
                    "terminalid": 1,
                    "estadocontenedorid": 1
                }
            }
        }


class GuiaVerificacionRequest(BaseModel):
    """Esquema para verificar una guía de remisión"""
    usuarioverificador: int = Field(..., gt=0, description="ID del usuario que verifica la guía")

    class Config:
        """Configuración del esquema"""
        json_schema_extra = {
            "example": {
                "usuarioverificador": 1
            }
        }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/")
async def crear_guia(data: GuiaCreateRequest):
    """
    Crear una nueva guía de remisión con su contenedor asociado.
    
    Args:
        data: GuiaCreateRequest con información de la guía y contenedor
    
    Returns:
        JSON con la guía creada y su contenedor
    
    Raises:
        HTTPException 400: Si los datos están vacíos o inválidos
        HTTPException 500: Si hay error en la base de datos
    """
    try:
        # Validar que los datos obligatorios no estén vacíos
        if not data.numeroguia or not data.numeroguia.strip():
            raise HTTPException(
                status_code=400,
                detail="El número de guía es requerido y no puede estar vacío"
            )
        
        # Validar contenedor
        if not data.contenedor.numerocontenedor or not data.contenedor.numerocontenedor.strip():
            raise HTTPException(
                status_code=400,
                detail="El número de contenedor es requerido"
            )
        
        if not data.contenedor.precinto or not data.contenedor.precinto.strip():
            raise HTTPException(
                status_code=400,
                detail="El precinto es requerido"
            )
        
        # Preparar datos de la guía para inserción
        guia_data = {
            "numeroguia": data.numeroguia,
            "conductorid": data.conductorid,
            "vehiculoid": data.vehiculoid,
            "empresaid": data.empresaid,
            "tiposervicioid": data.tiposervicioid,
            "origenid": data.origenid,
            "destinoid": data.destinoid,
            "pesotoneladas": data.pesotoneladas,
            "estadoid": data.estadoid,
            "fechaservicio": data.fechaservicio,
            "registradopor": data.registradopor
        }
        
        # Insertar en la tabla guia_remision
        guia_response = supabase.table("guia_remision").insert(guia_data).execute()
        
        if not guia_response.data or len(guia_response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Error al crear la guía de remisión"
            )
        
        # Obtener el guiaid de la guía creada
        guiaid = guia_response.data[0]["guiaid"]
        
        # Preparar datos del contenedor para inserción
        contenedor_data = {
            "guiaid": guiaid,
            "numerocontenedor": data.contenedor.numerocontenedor,
            "precinto": data.contenedor.precinto,
            "tamanioid": data.contenedor.tamanioid,
            "pesokg": data.contenedor.pesokg,
            "terminalid": data.contenedor.terminalid,
            "estadocontenedorid": data.contenedor.estadocontenedorid
        }
        
        # Insertar el contenedor en la tabla contenedor
        contenedor_response = supabase.table("contenedor").insert(contenedor_data).execute()
        
        if not contenedor_response.data:
            raise HTTPException(
                status_code=500,
                detail="Error al crear el contenedor"
            )
        
        # Retornar respuesta exitosa
        return {
            "success": True,
            "message": "Guía de remisión y contenedor creados exitosamente",
            "guiaid": guiaid,
            "guia": guia_response.data[0],
            "contenedor": contenedor_response.data[0]
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la guía: {str(e)}"
        )


@router.get("/")
async def listar_guias(
    conductorid: Optional[int] = Query(None, description="Filtrar por ID de conductor"),
    empresaid: Optional[int] = Query(None, description="Filtrar por ID de empresa"),
    vehiculoid: Optional[int] = Query(None, description="Filtrar por ID de vehículo"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    rolid: Optional[int] = Query(None, description="ID del rol del usuario (1=Administrador, 2=Cajero)")
):
    """
    Listar guías de remisión registradas con filtros opcionales.
    
    Si no hay filtros, retorna las últimas 50 guías ordenadas por fecharegistro descendente.
    Permite listar guías filtrando por conductorid, empresaid, vehiculoid y rango de fechas.
    Disponible para roles de Administrador (rolid=1) y Cajero (rolid=2).
    
    Args:
        conductorid: ID del conductor (opcional)
        empresaid: ID de la empresa (opcional)
        vehiculoid: ID del vehículo (opcional)
        fecha_inicio: Fecha de inicio (YYYY-MM-DD) (opcional)
        fecha_fin: Fecha de fin (YYYY-MM-DD) (opcional)
        rolid: ID del rol del usuario (1=Administrador, 2=Cajero)
    
    Returns:
        Lista de guías con sus contenedores asociados
    
    Raises:
        HTTPException 403: Si el usuario no tiene permisos
        HTTPException 500: Si hay error en la base de datos
    """
    try:
        # Validar que el usuario tenga permisos (Administrador o Cajero)
        if rolid and rolid not in [1, 2]:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para acceder a este recurso. Solo Administrador y Cajero pueden listar guías"
            )
        
        # Construir la consulta base
        query = supabase.table("guia_remision").select("*")
        
        # Aplicar filtros
        if conductorid:
            query = query.eq("conductorid", conductorid)
        
        if empresaid:
            query = query.eq("empresaid", empresaid)
        
        if vehiculoid:
            query = query.eq("vehiculoid", vehiculoid)
        
        if fecha_inicio:
            query = query.gte("fechaservicio", fecha_inicio)
        
        if fecha_fin:
            query = query.lte("fechaservicio", fecha_fin)
        
        # Ordenar por fecharegistro descendente
        query = query.order("fecharegistro", desc=True)
        
        # Limitar a 50 resultados si no hay filtros específicos
        has_filters = conductorid or empresaid or vehiculoid or fecha_inicio or fecha_fin
        if not has_filters:
            query = query.limit(50)
        
        # Ejecutar la consulta
        guias_response = query.execute()
        
        if not guias_response.data:
            return {
                "success": True,
                "message": "No se encontraron guías con los filtros especificados",
                "total": 0,
                "guias": []
            }
        
        # Para cada guía, obtener sus contenedores asociados
        guias_con_contenedores = []
        for guia in guias_response.data:
            guiaid = guia.get("guiaid")
            
            # Consultar contenedores de la guía
            contenedores_response = supabase.table("contenedor").select("*").eq("guiaid", guiaid).execute()
            
            guia["contenedores"] = contenedores_response.data if contenedores_response.data else []
            guias_con_contenedores.append(guia)
        
        return {
            "success": True,
            "message": f"Se encontraron {len(guias_con_contenedores)} guía(s)",
            "total": len(guias_con_contenedores),
            "guias": guias_con_contenedores
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar guías: {str(e)}"
        )


@router.patch("/{guiaid}/verificar")
async def verificar_guia(guiaid: int, data: GuiaVerificacionRequest, rolid: Optional[int] = Query(None)):
    """
    Verificar una guía de remisión (solo para Administrador).
    
    Actualiza las columnas vehiculoverificado y contenedorverificado a true,
    registra el usuarioverificador y la fechaverificacion.
    
    Args:
        guiaid: ID de la guía de remisión a verificar
        data: GuiaVerificacionRequest con usuarioverificador
        rolid: ID del rol del usuario (1=Administrador)
    
    Returns:
        JSON con la guía actualizada
    
    Raises:
        HTTPException 403: Si el usuario no es Administrador
        HTTPException 404: Si la guía no existe
        HTTPException 500: Si hay error en la base de datos
    """
    try:
        # Validar que solo Administrador (rolid=1) pueda verificar
        if rolid != 1:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para verificar guías. Solo el Administrador puede hacer esto"
            )
        
        # Validar que el guiaid sea válido
        if not guiaid or guiaid <= 0:
            raise HTTPException(
                status_code=400,
                detail="El ID de la guía debe ser un número válido"
            )
        
        # Validar que el usuarioverificador sea válido
        if not data.usuarioverificador or data.usuarioverificador <= 0:
            raise HTTPException(
                status_code=400,
                detail="El ID del usuario verificador debe ser válido"
            )
        
        # Obtener la guía para verificar que existe
        guia_check = supabase.table("guia_remision").select("*").eq("guiaid", guiaid).single().execute()
        
        if not guia_check.data:
            raise HTTPException(
                status_code=404,
                detail=f"La guía con ID {guiaid} no existe"
            )
        
        # Obtener la marca de tiempo actual del servidor
        fecha_verificacion = datetime.now().isoformat()
        
        # Preparar datos para actualización
        update_data = {
            "vehiculoverificado": True,
            "contenedorverificado": True,
            "usuarioverificador": data.usuarioverificador,
            "fechaverificacion": fecha_verificacion
        }
        
        # Actualizar la guía
        update_response = supabase.table("guia_remision").update(update_data).eq("guiaid", guiaid).execute()
        
        if not update_response.data:
            raise HTTPException(
                status_code=500,
                detail="Error al actualizar la guía de remisión"
            )
        
        # Retornar respuesta exitosa
        return {
            "success": True,
            "message": "Guía de remisión verificada exitosamente",
            "guiaid": guiaid,
            "guia": update_response.data[0]
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al verificar la guía: {str(e)}"
        )
