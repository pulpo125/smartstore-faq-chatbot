# 도구 관련 함수 모음입니다.
from typing import Any
from src.config import cfg_engine
from src.utils import logger
from src.decorator import timer


@timer
def retrieve(query: str, collection: Any) -> list:
    """
    기본 검색 함수 입니다.

    Args:
        query: 쿼리 텍스트
        collection: ChromaDB 컬렉션 객체

    Returns:
        contexts: 검색 결과 컨텍스트 리스트
    """
    # 검색
    try:
        docs = collection.query(
            query_texts=[query],
            n_results=cfg_engine.chroma_db.n_results,
            include=["metadatas"],
        )
        metadatas = docs["metadatas"][0]
        logger.info(f"[RetrieveFAQ] Retrieved {len(metadatas)} documents")

    except Exception as e:
        logger.error(f"[RetrieveFAQ] Retrieve Failed: {e}", exc_info=True)
        contexts = []

    # 컨텍스트 추출
    contexts = get_contexts(metadatas)

    return contexts


def get_contexts(metadatas: list) -> list:
    """컨텍스트를 추출하는 함수 입니다."""
    if not metadatas:
        contexts = []
    else:
        context_list = []
        for idx, item in enumerate(metadatas):
            document = item.get("document", "").strip()
            if document:
                context = f"[문서 {idx}]\n{document}\n"
                context_list.append(context)

        contexts = "\n".join(context_list)

    return contexts
