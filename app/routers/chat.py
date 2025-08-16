import traceback
import json
from typing import Generator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse as FastAPIStreamingResponse

from src.agents.faq_agent import FAQAgent
from src.utils import logger

from app import llm, db
from app.models import ChatRequest, StreamingResponse as PydanticStreamingResponse

# ==================================================
router = APIRouter()
# ==================================================


@router.post("/v1", response_model=PydanticStreamingResponse)
async def chat_stream(params: ChatRequest):
    """FAQ 채팅 스트리밍 엔드포인트"""

    # session_id, chat_id
    session_id = params.session_id
    chat_id = params.chat_id

    try:
        # 에이전트
        agent = FAQAgent(llm=llm, db=db)
        agent.initialize(session_id, chat_id)

        # 스트리밍 응답 반환
        return FastAPIStreamingResponse(
            stream_response(agent, params.input),
            media_type="application/json",  # JSON 스트리밍으로 변경
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Session-ID": session_id,
                "X-Chat-ID": chat_id,
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json; charset=utf-8",  # JSON으로 변경
            },
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="채팅 처리 중 오류가 발생했습니다.")


def stream_response(agent: FAQAgent, input: str) -> Generator[str, None, None]:
    """스트리밍 응답을 생성합니다."""
    try:
        full_response = ""

        # chat
        for chunk in agent.stream(input):

            full_response += chunk

            # 응답 청크 스트리밍
            chunk_data = {"type": "chat", "content": chunk}
            yield json.dumps(chunk_data, ensure_ascii=False) + "\n"

        # chat end
        chat_end = {"type": "chat_end", "content": full_response}
        yield json.dumps(chat_end, ensure_ascii=False) + "\n"

        # next_question
        next_questions = agent.generate_next_question()
        if not next_questions:
            # next_question 이 비어있는 경우(에러인 경우) 디폴트 질문으로 설정
            next_questions = [
                "어떤 카테고리로 등록해야할지 모르겠어요.",
                "스토어 가입 승인 완료 후 '현재 운용되고 있지 않습니다.'라고 노출됩니다.",
            ]

        # Complete
        final_data = {
            "type": "complete",
            "response": full_response,
            "next_questions": next_questions,
        }
        logger.info(f"Complete Data:\n{final_data}")

        yield json.dumps(final_data, ensure_ascii=False) + "\n"
        logger.info("Stream completed successfully")

    except Exception as e:
        logger.error(f"Error in streaming response: {e}")
        error_data = {
            "type": "error",
            "content": "죄송합니다. 응답 생성 중 오류가 발생했습니다.",
        }
        yield json.dumps(error_data, ensure_ascii=False) + "\n"
