from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.models.inference_result import InferenceResult
from app.models.model import Model
from app.schemas.inference_result import InferenceResultCreate, InferenceResultResponse
from app.services.yolo_service import YOLOService
from app.services.image_service import ImageService

router = APIRouter()
yolo_service = YOLOService()
image_service = ImageService()

@router.post("/", response_model=InferenceResultResponse)
async def perform_inference(
    file: UploadFile = File(...),
    model_id: int = None,
    confidence_threshold: float = 0.5,
    db: Session = Depends(get_db)
):
    """Realiza inferência em uma imagem."""
    # Validar modelo
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    
    # Validar tipo de arquivo
    if file.content_type not in ["image/jpeg", "image/png", "image/tiff"]:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não suportado")
    
    # Ler conteúdo do arquivo
    content = await file.read()
    
    # Salvar imagem temporariamente
    image_info = image_service.save_image(
        image_data=content,
        filename=file.filename,
        dataset_id=None
    )
    
    try:
        # Realizar inferência
        predictions, metrics = await yolo_service.predict(
            model_id=model_id,
            image_path=image_info["filepath"],
            confidence_threshold=confidence_threshold
        )
        
        # Criar resultado
        result = InferenceResult(
            predictions=predictions,
            metrics=metrics,
            image_id=image_info["id"],
            model_id=model_id
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        
        return result
        
    finally:
        # Limpar arquivo temporário
        image_service.delete_image(image_info["filename"])

@router.get("/", response_model=List[InferenceResultResponse])
def list_inference_results(
    image_id: int = None,
    model_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista todos os resultados de inferência."""
    query = db.query(InferenceResult)
    if image_id:
        query = query.filter(InferenceResult.image_id == image_id)
    if model_id:
        query = query.filter(InferenceResult.model_id == model_id)
    results = query.offset(skip).limit(limit).all()
    return results

@router.get("/{result_id}", response_model=InferenceResultResponse)
def get_inference_result(result_id: int, db: Session = Depends(get_db)):
    """Obtém um resultado de inferência específico."""
    result = db.query(InferenceResult).filter(InferenceResult.id == result_id).first()
    if result is None:
        raise HTTPException(status_code=404, detail="Resultado de inferência não encontrado")
    return result 