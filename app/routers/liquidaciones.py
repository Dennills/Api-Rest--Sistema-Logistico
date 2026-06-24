from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from app.database import supabase

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])


# ============================================================================
# ESQUEMAS DE PYDANTIC V2
# ============================================================================

class LiquidacionProcesarRequest(BaseModel):
    """Esquema para procesar una liquidación de conductor"""
    conductorid: int = Field(..., gt=0, description="ID del conductor")
    empresaid: int = Field(..., gt=0, description="ID de la empresa")
    periodoinicio: str = Field(..., description="Fecha de inicio del periodo (YYYY-MM-DD)")
    periodofin: str = Field(..., description="Fecha de fin del periodo (YYYY-MM-DD)")
    cerradopor: int = Field(..., gt=0, description="ID del usuario que cierra la liquidación")
    guias_ids: List[int] = Field(..., min_items=1, description="Lista de IDs de guías a incluir en la liquidación")

    class Config:
        """Configuración del esquema"""
        json_schema_extra = {
            "example": {
                "conductorid": 1,
                "empresaid": 1,
                "periodoinicio": "2026-06-01",
                "periodofin": "2026-06-30",
                "cerradopor": 1,
                "guias_ids": [1, 2, 3, 4, 5]
            }
        }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/previsualizar")
async def previsualizar_liquidacion(
    conductorid: int = Query(..., gt=0, description="ID del conductor"),
    fecha_inicio: str = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    fecha_fin: str = Query(..., description="Fecha de fin (YYYY-MM-DD)")
):
    """
    Previsualizar guías de un conductor para liquidación.
    
    Busca todas las guías registradas de un conductor en un rango de fechas
    con estado REGISTRADA (estadoid=1) para que el Cajero previsualice
    antes de procesar la liquidación.
    
    Args:
        conductorid: ID del conductor
        fecha_inicio: Fecha de inicio del rango (YYYY-MM-DD)
        fecha_fin: Fecha de fin del rango (YYYY-MM-DD)
    
    Returns:
        JSON con lista de guías y total encontradas
    
    Raises:
        HTTPException 400: Si faltan parámetros o son inválidos
        HTTPException 500: Si hay error en la base de datos
    """
    try:
        # Validar parámetros obligatorios
        if not conductorid or conductorid <= 0:
            raise HTTPException(
                status_code=400,
                detail="El ID del conductor debe ser un número válido"
            )
        
        if not fecha_inicio or not fecha_fin:
            raise HTTPException(
                status_code=400,
                detail="Las fechas de inicio y fin son requeridas"
            )
        
        # Consultar guías del conductor en el rango de fechas con estado REGISTRADA (estadoid=1)
        guias_response = supabase.table("guia_remision").select("*").eq(
            "conductorid", conductorid
        ).eq(
            "estadoid", 1
        ).gte(
            "fechaservicio", fecha_inicio
        ).lte(
            "fechaservicio", fecha_fin
        ).execute()
        
        guias = guias_response.data if guias_response.data else []
        
        return {
            "success": True,
            "message": f"Se encontraron {len(guias)} guía(s) para previsualizar",
            "total_guias": len(guias),
            "guias": guias
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al previsualizar liquidación: {str(e)}"
        )


@router.post("/procesar")
async def procesar_liquidacion(data: LiquidacionProcesarRequest):
    """
    Procesar liquidación de un conductor.
    
    Crea un registro de liquidación y vincula las guías seleccionadas,
    luego actualiza el estado de esas guías a VALIDADA para congelarlas.
    
    Args:
        data: LiquidacionProcesarRequest con información de la liquidación
    
    Returns:
        JSON con la liquidación creada y sus detalles
    
    Raises:
        HTTPException 400: Si los datos están vacíos o inválidos
        HTTPException 500: Si hay error en la base de datos
    """
    try:
        # Validar que los datos obligatorios no estén vacíos
        if not data.conductorid or data.conductorid <= 0:
            raise HTTPException(
                status_code=400,
                detail="El ID del conductor es requerido y debe ser válido"
            )
        
        if not data.empresaid or data.empresaid <= 0:
            raise HTTPException(
                status_code=400,
                detail="El ID de la empresa es requerido y debe ser válido"
            )
        
        if not data.periodoinicio or not data.periodofin:
            raise HTTPException(
                status_code=400,
                detail="Las fechas del periodo (inicio y fin) son requeridas"
            )
        
        if not data.cerradopor or data.cerradopor <= 0:
            raise HTTPException(
                status_code=400,
                detail="El ID del usuario que cierra es requerido y debe ser válido"
            )
        
        if not data.guias_ids or len(data.guias_ids) == 0:
            raise HTTPException(
                status_code=400,
                detail="Se requiere al menos una guía para procesar la liquidación"
            )
        
        # Validar que todas las guías IDs sean válidas
        for guia_id in data.guias_ids:
            if not isinstance(guia_id, int) or guia_id <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"ID de guía inválido: {guia_id}"
                )
        
        # PASO 1: Insertar en la tabla liquidacion
        liquidacion_data = {
            "conductorid": data.conductorid,
            "empresaid": data.empresaid,
            "periodoinicio": data.periodoinicio,
            "periodofin": data.periodofin,
            "totalguias": len(data.guias_ids),
            "estadoid": 1,  # ABIERTA
            "cerradopor": data.cerradopor
        }
        
        liquidacion_response = supabase.table("liquidacion").insert(liquidacion_data).execute()
        
        if not liquidacion_response.data or len(liquidacion_response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Error al crear el registro de liquidación"
            )
        
        # PASO 2: Recuperar el liquidacionid generado
        liquidacionid = liquidacion_response.data[0]["liquidacionid"]
        
        # PASO 3: Insertar en la tabla intermedia liquidacion_detalle
        detalle_records = []
        for guia_id in data.guias_ids:
            detalle_data = {
                "liquidacionid": liquidacionid,
                "guiaid": guia_id,
                "incluida": True
            }
            detalle_records.append(detalle_data)
        
        if detalle_records:
            detalle_response = supabase.table("liquidacion_detalle").insert(detalle_records).execute()
            
            if not detalle_response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Error al crear los detalles de la liquidación"
                )
        
        # PASO 4: Update masivo en guia_remision - cambiar estadoid a 2 (VALIDADA)
        # Usamos una consulta RPC o actualizamos cada guía
        # Para actualizar múltiples registros, iteramos sobre ellos o usamos una consulta
        update_count = 0
        for guia_id in data.guias_ids:
            update_response = supabase.table("guia_remision").update(
                {"estadoid": 2}  # VALIDADA
            ).eq("guiaid", guia_id).execute()
            
            if update_response.data:
                update_count += 1
        
        if update_count != len(data.guias_ids):
            raise HTTPException(
                status_code=500,
                detail=f"Error al actualizar el estado de algunas guías. Se actualizaron {update_count} de {len(data.guias_ids)}"
            )
        
        # Retornar respuesta exitosa
        return {
            "success": True,
            "message": "Liquidación procesada exitosamente",
            "liquidacionid": liquidacionid,
            "liquidacion": liquidacion_response.data[0],
            "detalles": detalle_response.data if detalle_records else [],
            "guias_actualizadas": update_count
        }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la liquidación: {str(e)}"
        )
