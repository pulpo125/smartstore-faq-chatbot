from typing import Any
import uuid
from tqdm import tqdm

from src.db.data import load_data, preprocess_data, chunk_text
from src.config import cfg_engine
from src.utils import logger, get_openai_embedding_func
from src.decorator import timer


from tqdm import tqdm
import uuid
from typing import Any


@timer
def insert_data(filepath: str, collection: Any) -> None:
    """
    ChromaDB 데이터 삽입 함수 (tqdm 진행률 표시만 추가)

    Args:
        filepath: 데이터 파일 경로
        collection: ChromaDB 컬렉션 객체
    """

    logger.info("Start insert_data")

    # 데이터 로드
    data = load_data(filepath)

    # 데이터 전처리
    processed_data = preprocess_data(data)

    # 청킹 및 데이터 삽입
    for q, a in tqdm(list(processed_data.items())):
        try:
            parent_id = str(uuid.uuid4())
            chunks = chunk_text(
                text=a, max_chunk_size=cfg_engine.chroma_db.max_chunk_size
            )

            for idx, chunk in enumerate(chunks):
                id = str(uuid.uuid4())  # 고유 ID
                document = f"Question: {q}\nAnswer: {chunk}"

                collection.add(
                    ids=[id],
                    metadatas=[
                        {
                            "parent_id": parent_id,
                            "chunk_id": idx,
                            "question": q,
                            "answer": chunk,
                            "document": document,
                        }
                    ],
                    documents=[document],
                )

        except Exception as e:
            logger.error(f"[insert_data] 데이터 삽입 중 에러 발생: {e}", exc_info=True)
            continue

    logger.info("Finished insert_data")

    return None


import uuid
import logging
from typing import Any

logger = logging.getLogger(__name__)


@timer
def insert_data_batch(filepath: str, collection: Any, batch_size: int = 100) -> None:
    """
    ChromaDB 데이터 삽입 함수 (배치 처리 최적화 버전)

    Args:
        filepath: 데이터 파일 경로
        collection: ChromaDB 컬렉션 객체
        batch_size: 한 번에 삽입할 청크 수
    """
    logger.info("Start insert_data_batch")

    # 데이터 로드
    data = load_data(filepath)

    # 데이터 전처리
    processed_data = preprocess_data(data)

    # 배치 저장용 리스트
    batch_ids = []
    batch_metadatas = []
    batch_documents = []

    total_chunks = 0

    for q, a in list(processed_data.items()):
        try:
            parent_id = str(uuid.uuid4())
            chunks = chunk_text(
                text=a, max_chunk_size=cfg_engine.chroma_db.max_chunk_size
            )

            for idx, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                document = f"Question: {q}\nAnswer: {chunk}"

                batch_ids.append(chunk_id)
                batch_metadatas.append(
                    {
                        "parent_id": parent_id,
                        "chunk_id": idx,
                        "question": q,
                        "answer": chunk,
                        "document": document,
                    }
                )
                batch_documents.append(document)
                total_chunks += 1

                # 배치 사이즈 도달 시 insert
                if len(batch_ids) >= batch_size:
                    collection.add(
                        ids=batch_ids,
                        metadatas=batch_metadatas,
                        documents=batch_documents,
                    )
                    logger.info(f"Inserted batch of {len(batch_ids)} chunks")
                    batch_ids = []
                    batch_metadatas = []
                    batch_documents = []

        except Exception as e:
            logger.error(
                f"[insert_data_batch] 데이터 삽입 중 에러 발생: {e}", exc_info=True
            )
            continue

    # 전체 루프 종료 후 남은 청크 삽입
    if batch_ids:
        collection.add(
            ids=batch_ids,
            metadatas=batch_metadatas,
            documents=batch_documents,
        )
        logger.info(f"Inserted final batch of {len(batch_ids)} chunks")

    logger.info(f"Finished insert_data_batch, total chunks inserted: {total_chunks}")


def get_or_create_collection(db_client: Any, collection_name: str) -> Any:
    """
    ChromaDB에서 컬렉션을 가져오거나 생성하는 함수
    **컬렉션이 없는 경우 데이터를 삽입합니다.**

    Args:
        db_client (Any): ChromaDB 클라이언트 객체
    Returns:
        collection: ChromaDB 컬렉션 객체
    """

    def _check_collection_exists(db_client: Any, collection_name: str) -> bool:
        """ChromaDB에 컬렉션이 존재하는지 확인하는 함수"""
        return collection_name in [col.name for col in db_client.list_collections()]

    is_collection = _check_collection_exists(db_client, collection_name)

    if is_collection:
        # 컬렉션이 이미 존재하는 경우
        logger.info(f"[ChromaDB] '{collection_name}' exists. Connect Collection")
        collection = db_client.get_collection(
            name=collection_name, embedding_function=get_openai_embedding_func()
        )
    else:
        # 컬렉션이 존재하지 않는 경우
        logger.info(
            f"[ChromaDB] '{collection_name}' does not exist. Create the collection and insert the data."
        )
        collection = db_client.create_collection(
            name=collection_name, embedding_function=get_openai_embedding_func()
        )

    return collection
