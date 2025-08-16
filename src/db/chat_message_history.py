from typing import Any, List, Dict
from datetime import datetime
import uuid
import chromadb

from src.utils import logger


class ChatMessageHistory:
    """
    ChromaDB에 채팅 히스토리를 저장하는 클래스 입니다.
    """

    def __init__(
        self,
        session_id: str,
        chat_id: str,
        db_client: chromadb.Client,
        collection_name: str,
    ):
        self.session_id = session_id
        self.chat_id = chat_id
        self.db_client = db_client
        self.collection_name = collection_name

        # Connect ChromaDB Collection
        self.collection = self.db_client.get_or_create_collection(self.collection_name)
        logger.info(f"[ChatHistory] Connect collection: {collection_name}")

    def messages(self) -> List[Dict[str, str]]:
        """session_id, chat_id 를 기준으로 채팅 히스토리 메시지 목록을 조회합니다."""
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"session_id": {"$eq": self.session_id}},
                        {"chat_id": {"$eq": self.chat_id}},
                    ]
                }
            )

            if not results["metadatas"]:
                return []

            # created_at 으로 정렬
            messages_with_created_at = [
                (
                    metadata.get("created_at", ""),
                    {
                        "role": metadata.get("role", ""),
                        "content": metadata.get("content", ""),
                    },
                )
                for metadata in results["metadatas"]
            ]

            messages_with_created_at.sort(key=lambda x: x[0])  # created_at 오름차순
            messages = [msg[1] for msg in messages_with_created_at]

            logger.info(f"[ChatHistory] Retrieved {len(messages)} messages")
            return messages

        except Exception as e:
            logger.error(f"[ChatHistory] Error retrieving messages: {e}", exc_info=True)
            return []

    def add_messages(self, messages: List[Dict[str, str]]) -> None:
        """session_id, chat_id 를 기준으로 채팅 히스토리 메시지 목록을 추가합니다."""
        if not messages:
            return

        ids = []
        documents = []
        metadatas = []

        for message in messages:
            message_id = str(uuid.uuid4())  # 각 메시지마다 고유 ID
            message_data = {
                "session_id": self.session_id,
                "chat_id": self.chat_id,
                "role": message.get("role", ""),
                "content": message.get("content", ""),
                "created_at": datetime.now().isoformat(),
            }

            ids.append(message_id)
            documents.append("")  # 빈 문자열로 임베딩 생성 방지
            metadatas.append(message_data)

        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

        logger.info(f"[ChatHistory] Added {len(messages)} messages")

    def clear(self):
        """session_id, chat_id를 기준으로 해당 데이터를 삭제합니다."""
        try:
            self.collection.delete(
                where={
                    "$and": [
                        {"session_id": self.session_id},
                        {"chat_id": self.chat_id},
                    ]
                }
            )
            logger.info(
                f"[ChatHistory] Cleared messages for session_id={self.session_id}, chat_id={self.chat_id} from ChromaDB"
            )

        except Exception as e:
            logger.error(f"[ChatHistory] Error clearing messages: {e}", exc_info=True)
