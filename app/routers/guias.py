from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.database import supabase

router = APIRouter(prefix="/api/guias", tags=["guias"])

# ============================================================================
# ESQUEMAS DE PYDANTIC V2 (Mantenidos intactos de tu código original)
# ============================================================================

class ContenedorCreate(BaseModel):
    numerocontenedor: str = Field(..., min_length=1, description="Número único del contenedor")
    precinto: str = Field(..., min_length=1, description="Número de precinto")
    tamanioid: int = Field(..., gt=0, description="ID del tamaño del contenedor")
    pesokg: float = Field(..., gt=0, description="Peso del contenedor en kilogramos")
    terminalid: int = Field(..., gt=0, description="ID de la terminal")
    estadocontenedorid: int = Field(..., gt=0, description="ID del estado del contenedor")

    class Config:
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
    usuarioverificador: int = Field(..., gt=0, description="ID del usuario que verifica la guía")

    class Config:
        json_schema_extra = {
            "example": {"usuarioverificador": 1}
        }

# ============================================================================
# ENDPOINTS ACTUALIZADOS PARA EL PROTOTIPO
# ============================================================================

@router.post("/")
async def crear_guia(data: GuiaCreateRequest):
    try:
        if not data.numeroguia or not data.numeroguia.strip():
            raise HTTPException(status_code=400, detail="El número de guía es requerido")
        if not data.contenedor.numerocontenedor or not data.contenedor.numerocontenedor.strip():
            raise HTTPException(status_code=400, detail="El número de contenedor es requerido")
        if not data.contenedor.precinto or not data.contenedor.precinto.strip():
            raise HTTPException(status_code=400, detail="El precinto es requerido")
        
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
        
        guia_response = supabase.table("guia_remision").insert(guia_data).execute()
        if not guia_response.data:
            raise HTTPException(status_code=500, detail="Error al crear la guía de remisión")
        
        guiaid = guia_response.data[0]["guiaid"]
        
        contenedor_data = {
            "guiaid": guiaid,
            "numerocontenedor": data.contenedor.numerocontenedor,
            "precinto": data.contenedor.precinto,
            "tamanioid": data.contenedor.tamanioid,
            "pesokg": data.contenedor.pesokg,
            "terminalid": data.contenedor.terminalid,
            "estadocontenedorid": data.contenedor.estadocontenedorid
        }
        
        contenedor_response = supabase.table("contenedor").insert(contenedor_data).execute()
        if not contenedor_response.data:
            raise HTTPException(status_code=500, detail="Error al crear el contenedor")
        
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
        raise HTTPException(status_code=500, detail=f"Error al procesar la guía: {str(e)}")


@router.get("/")
async def listar_guias(
    conductorid: Optional[int] = Query(None, description="Filtrar por ID de conductor"),
    empresaid: Optional[int] = Query(None, description="Filtrar por ID de empresa"),
    vehiculoid: Optional[int] = Query(None, description="Filtrar por ID de vehículo"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    rolid: Optional[int] = Query(None, description="ID del rol (1=Admin, 2=Cajero, 3=Chofer)")
):
    try:
        # Enriquecemos la consulta haciendo JOIN relacional con tus tablas reales
        query = supabase.table("guia_remision").select("""
            guiaid, numeroguia, fechaservicio, fecharegistro, pesotoneladas, estadoid,
            conductor:conductorid(nombres, apellidos),
            vehiculo:vehiculoid(placa),
            empresa:empresaid(nombre),
            tipo_servicio:tiposervicioid(descripcion),
            origen:origenid(nombre),
            destino:destinoid(nombre),
            estado:estadoid(nombre)
        """)
        
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
        
        query = query.order("fecharegistro", desc=True)
        
        has_filters = conductorid or empresaid or vehiculoid or fecha_inicio or fecha_fin
        if not has_filters:
            query = query.limit(50)
        
        guias_response = query.execute()
        if not guias_response.data:
            return {"success": True, "message": "No se encontraron guías", "total": 0, "guias": []}
        
        guias_formateadas = []
        for g in guias_response.data:
            guiaid = g.get("guiaid")
            # Jalamos los datos del contenedor hijo
            cont_res = supabase.table("contenedor").select("numerocontenedor, precinto").eq("guiaid", guiaid).execute()
            contenedor = cont_res.data[0] if cont_res.data else {"numerocontenedor": "S/N", "precinto": "S/P"}
            
            # Construimos la estructura idéntica a lo que espera tu prototipo visual
            guias_formateadas.append({
                "guiaid": g["guiaid"],
                "numeroguia": g["numeroguia"],
                "fecha": g["fechaservicio"],
                "conductor": f"{g['conductor']['nombres']} {g['conductor']['apellidos']}" if g.get("conductor") else "No asignado",
                "placa": g["vehiculo"]["placa"] if g.get("vehiculo") else "S/P",
                "contenedor": contenedor["numerocontenedor"],
                "precinto": contenedor["precinto"],
                "ruta": f"{g['origen']['nombre']} → {g['destino']['nombre']}" if g.get("origen") and g.get("destino") else "Sin Ruta",
                "empresa": g["empresa"]["nombre"] if g.get("empresa") else "S/E",
                "tipo": g["tipo_servicio"]["descripcion"] if g.get("tipo_servicio") else "S/T",
                "estado": g["estado"]["nombre"] if g.get("estado") else "REGISTRADA",
                "peso": float(g["pesotoneladas"])
            })
        
        return {
            "success": True,
            "message": f"Se encontraron {len(guias_formateadas)} guía(s)",
            "total": len(guias_formateadas),
            "guias": guias_formateadas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar guías: {str(e)}")


@router.patch("/{guiaid}/verificar")
async def verificar_guia(guiaid: int, data: GuiaVerificacionRequest, rolid: Optional[int] = Query(None)):
    try:
        if rolid != 1:
            raise HTTPException(status_code=403, detail="Solo el Administrador puede verificar guías")
        if not guiaid or guiaid <= 0:
            raise HTTPException(status_code=400, detail="ID de guía inválido")
        
        fecha_verificacion = datetime.now().isoformat()
        update_data = {
            "vehiculoverificado": True,
            "contenedorverificado": True,
            "usuarioverificador": data.usuarioverificador,
            "fechaverificacion": fecha_verificacion,
            "estadoid": 2  # Pasa automáticamente a VALIDADA al verificar
        }
        
        update_response = supabase.table("guia_remision").update(update_data).eq("guiaid", guiaid).execute()
        if not update_response.data:
            raise HTTPException(status_code=500, detail="Error al verificar la guía")
            
        return {
            "success": True,
            "message": "Guía de remisión verificada exitosamente",
            "guiaid": guiaid,
            "guia": update_response.data[0]
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar la guía: {str(e)}")