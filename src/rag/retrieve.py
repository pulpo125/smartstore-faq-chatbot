# rag 기본 함수
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
        검색 결과(메타데이터) 리스트 목록
        - chunk_id
        - parent_id
        - question
        - query
        - document
    """
    # 검색
    try:
        docs = collection.query(
            query_texts=[query],
            n_results=cfg_engine.chroma_db.n_results,
            include=["metadatas"],
        )
        metadatas = docs["metadatas"][0]
        logger.info(f"[retrieve] 검색 결과 {len(metadatas)}개의 문서가 있습니다.")
    except Exception as e:
        logger.error(f"[retrieve] 검색 실패: {e}")
        metadatas = []

    return metadatas


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
