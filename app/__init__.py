import traceback
from typing import Union
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

from src.utils import get_chroma_db_client, get_openai_client
from src.db.chroma_db import get_or_create_collection
from src.config import cfg_engine

# ==================================================

tags_metadata = [
    {"name": "chat", "description": "chat and answer"},
]
application = FastAPI(
    title="SmartStore FAQ Chat Service",
    version="0.0.1",
    openai_tags=tags_metadata,
    root_path=os.environ.get("FASTAPI_ROOT_PATH", None),
)
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# ===============================================================
# Config
# ===============================================================

#  ===============================================================
#  Client
#  ===============================================================

# llm client
llm = get_openai_client()

# DB client
db_client = get_chroma_db_client()
db = get_or_create_collection(
    db_client=db_client, collection_name=cfg_engine.chroma_db.collection_name
)

#  ===============================================================
#  Router
#  ===============================================================

from app.routers import healthcheck, chat, db

router_infos = [
    (healthcheck.router, "healthcheck"),
    (chat.router, "chat"),
    (db.router, "db"),
]

for router_info in router_infos:
    r = router_info[0]
    t = [router_info[1]]
    p = f"/{router_info[1]}"
    application.include_router(router=r, prefix=p)
