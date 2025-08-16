# 도구 관련 함수 모음입니다.
from typing import Any
import json

from src.config import cfg_engine
from src.utils import logger
from src.decorator import timer
from src.agents.prompts import RERANK_PROMPT, NO_FAQ_CONTEXT_MSG
from src.config import cfg


@timer
def retrieve(query: str, collection: Any) -> str:
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


def get_contexts(metadatas: list, return_list: bool = False):
    """
    컨텍스트를 추출하는 함수
    - return_list=True: 리스트 반환
    - return_list=False: 문자열 반환
    """
    if not metadatas:
        return [] if return_list else ""

    contexts = []
    context_list = []
    for idx, item in enumerate(metadatas):
        document = item.get("document", "").strip()
        question = item.get("question", "").strip()
        answer = item.get("answer", "").strip()
        if document:
            context = f"[문서 {idx}]\n{document}\n"
            contexts.append(context)

        if question and answer:
            context_list.append({"question": question, "answer": answer})

    if return_list:
        return context_list
    else:
        return "\n".join(contexts)


@timer
def retrieve_advanced(query: str, collection: Any, llm: Any) -> str:
    """
    RAG Advanced 검색 함수.
    - retrieve 후 reranking 진행
    - relevance 기준으로 상위 문서 반환 (0~1 점수 문서 제거)
    - cfg_engine.chroma_db.n_results 기준으로 개수 제한

    Args:
        query: 쿼리 텍스트
        collection: ChromaDB 컬렉션 객체
        llm: OpenAI 클라이언트 객체

    Returns:
        contexts_str: 최종 컨텍스트 문자열, 문서 없을 경우 안내 메시지 반환
    """
    # 1. 기본 검색
    try:
        docs = collection.query(
            query_texts=[query],
            n_results=cfg_engine.chroma_db.n_results * 2,  # 여유롭게 가져오기
            # n_results=cfg_engine.chroma_db.n_results,
            include=["metadatas"],
        )
        metadatas = docs["metadatas"][0]
        logger.info(f"[RetrieveFAQ] Retrieved {len(metadatas)} documents")
    except Exception as e:
        logger.error(f"[RetrieveFAQ] Retrieve Failed: {e}", exc_info=True)
        return NO_FAQ_CONTEXT_MSG

    if not metadatas:
        return NO_FAQ_CONTEXT_MSG

    # 2. 컨텍스트 추출 (리스트)
    contexts_list = get_contexts(metadatas, return_list=True)

    if cfg_engine.faq_agent.verbose:
        logger.info(f"[RetrieveFAQ] 기본 검색 결과:\n{contexts_list}")
        # pass

    # 3. reranking LLM 호출
    try:
        prompt = RERANK_PROMPT.format(query=query, contexts=contexts_list)
        messages = [
            {
                "role": "system",
                "content": "당신은 네이버 스마트스토어 FAQ 리랭킹 전문가입니다.",
            },
            {"role": "user", "content": prompt},
        ]

        response = llm.chat.completions.create(
            model=cfg.openai.llm_model,
            # max_completion_tokens=cfg.openai.llm_max_tokens,
            messages=messages,
        )
        llm_result = response.choices[0].message.content.strip()
        logger.info(f"[RetrieveFAQ] - ReRanking Result:\n{llm_result}")
        scores = json.loads(llm_result)

    except Exception as e:
        logger.error(f"[RetrieveFAQ] Reranking Failed: {e}", exc_info=True)
        scores = [{"index": i, "relevance": 0} for i in range(len(contexts_list))]

    # 4. 0~1점 문서 제거, relevance 기준 정렬
    filtered_scores = [s for s in scores if s["relevance"] > 1]
    filtered_scores.sort(key=lambda x: x["relevance"], reverse=True)
    top_scores = filtered_scores[: cfg_engine.chroma_db.n_results]

    if not top_scores:
        return NO_FAQ_CONTEXT_MSG

    # 5. 최종 컨텍스트 문자열로 변환 (get_contexts return_list=False 사용)
    selected_metadatas = [metadatas[s["index"]] for s in top_scores]
    contexts_str = get_contexts(selected_metadatas, return_list=False)

    logger.info(
        f"[RetrieveAdvanced] {len(top_scores)} documents selected after reranking"
    )
    return contexts_str
