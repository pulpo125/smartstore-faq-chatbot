# src/api/db.py
import os
import uuid
import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.db.chroma_db import insert_data_batch
from src.utils import logger
from src.config import cfg_engine

from app import db
from app.models import (
    InsertBatchRequest,
    InsertResponse,
)

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# ==================================================
router = APIRouter()
# ==================================================


@router.post("/insert_batch", response_model=InsertResponse)
async def insert_batch(params: InsertBatchRequest):
    """ChromaDB에 데이터 배치 삽입"""
    try:
        filepath = params.filepath or cfg_engine.data.path
        batch_size = params.batch_size or cfg_engine.chroma_db.batch_size

        insert_data_batch(filepath=filepath, collection=db, batch_size=batch_size)

        return InsertResponse(
            status="success", message=f"{filepath} 데이터가 삽입되었습니다."
        )

    except Exception as e:
        logger.error(f"[DB API] insert_batch error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="데이터 삽입 중 오류 발생")
