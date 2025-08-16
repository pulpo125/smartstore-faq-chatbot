from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Union
from enum import Enum


# =====================
# chat
# =====================


class ChatRequest(BaseModel):
    input: str = Field(..., description="사용자 입력값")
    session_id: str = Field(..., description="세션 id")
    chat_id: str = Field(..., description="채팅 id")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "string",
                "chat_id": "string",
                "input": "string",
            }
        }


class StreamingType(str, Enum):
    """스트리밍 응답 타입"""

    AI = "ai"
    NEXT_QUESTION = "next_question"
    COMPLETE = "complete"
    ERROR = "error"


class ChatResponse(BaseModel):
    """chat 응답 청크"""

    type: Literal["chat"] = "chat"
    content: str = Field(..., description="chat 응답 청크 내용")

    class Config:
        json_schema_extra = {"example": {"type": "chat", "content": "string"}}


class ChatEndResponse(BaseModel):
    """chat_end 응답 청크: chat 답변 전체 내용을 응답합니다."""

    type: Literal["chat_end"] = "chat_end"
    content: str = Field(..., description="chat 답변 전체 내용")

    class Config:
        json_schema_extra = {"example": {"type": "chat_end", "content": "string"}}


class CompleteResponse(BaseModel):
    """최종 완성된 응답: chat 답변 + next_question"""

    type: Literal["complete"] = "complete"
    response: str = Field(..., description="전체 응답")
    next_questions: List[str] = Field(..., description="추천 질문들")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "complete",
                "response": "string",
                "next_questions": ["string"],
            }
        }


class ErrorResponse(BaseModel):
    """에러 응답"""

    type: Literal["error"] = "error"
    content: str = Field(..., description="에러 메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "error",
                "content": "죄송합니다. 응답 생성 중 오류가 발생했습니다.",
            }
        }


# 스트리밍 응답의 Union 타입
StreamingResponse = Union[
    ChatResponse, ChatEndResponse, CompleteResponse, ErrorResponse
]


# =====================
# db
# =====================


class InsertBatchRequest(BaseModel):
    """배치 단위로 ChromaDB에 데이터를 삽입하기 위한 요청 모델"""

    filepath: Optional[str] = Field(
        None, description="삽입할 데이터 파일 경로, 지정하지 않으면 기본 경로 사용"
    )
    batch_size: Optional[int] = Field(
        None, description="한 번에 삽입할 데이터 개수, 지정하지 않으면 기본값 사용"
    )

    class Config:
        schema_extra = {"example": {"filepath": None, "batch_size": None}}


class InsertResponse(BaseModel):
    """DB API 성공/실패 응답 모델"""

    status: str = Field(..., description="응답 상태")
    message: str = Field(..., description="상세 메시지")

    class Config:
        schema_extra = {
            "example": {"status": "success", "message": "데이터가 삽입되었습니다."}
        }
