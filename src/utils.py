import logging
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from src.config import cfg, cfg_engine

# ==============================
# Logger
# ==============================


logger = logging.getLogger()

logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# ==============================
# Clients
# ==============================


class ClientManager:
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(ClientManager, cls).__new__(cls)
        return cls.instance


client_manager = ClientManager()


def get_chroma_db_client():
    key = "chroma_db"
    if not hasattr(client_manager, key):
        client = chromadb.PersistentClient(path=cfg_engine.chroma_db.path)
        setattr(client_manager, key, client)
    return getattr(client_manager, key)


# ==============================
# Embedding
# ==============================


def get_openai_embedding_func():
    """OpenAI Embedding 함수"""
    return OpenAIEmbeddingFunction(
        api_key=cfg.openai.api_key,
        model_name=cfg.openai.embeddings_model,
        dimensions=cfg.openai.embeddings_dimensions,
    )


# ==============================
# General util
# ==============================
