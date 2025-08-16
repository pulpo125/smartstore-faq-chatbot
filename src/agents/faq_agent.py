# FAQAgent 는 네이버 스마트스토어 FAQ 에 대해 답변하는 챗봇 입니다.

from typing import Any, List, Dict
from pydantic import BaseModel, Field
import json

from src.utils import logger, get_chroma_db_client
from src.config import cfg, cfg_engine
from src.agents.prompts import AGENT_SYSTEM_PROMPT, ERROR_RESULT_PROMPT
from src.agents.tools import retrieve
from src.db.chat_message_history import ChatMessageHistory
from src.decorator import timer


class FAQAgent(BaseModel):
    # clinent
    llm: Any = Field(..., description="OpneAI Client")
    db: Any = Field(..., description="ChromaDB Client collection for RAG")
    chat_message_history: ChatMessageHistory = Field(
        None, description="Chat message history Manager"
    )

    # Agent States
    available_functions: dict = Field(None, description="이용가능한 도구 함수 목록")

    class Config:
        arbitrary_types_allowed = True

    def initialize(self, session_id: str, chat_id: str) -> None:
        db_client = get_chroma_db_client()
        self.chat_message_history = ChatMessageHistory(
            session_id,
            chat_id,
            db_client,
            cfg_engine.chat_message_history.collection_name,
        )

    def delete_state(self) -> None:
        """모든 Agent 상태를 삭제합니다."""
        self.available_functions = None
        self.chat_message_history.clear()
        self.chat_message_history = None

    def _select_history(self) -> List[Dict[str, str]]:
        """last_n_turn 만큼 히스토리를 선택합니다."""
        history_messages = self.chat_message_history.messages()
        last_n_turn = cfg_engine.faq_agent.last_n_turn
        return history_messages[-last_n_turn:]

    def _update_history(self, input: str, result: str) -> None:
        "chat history 를 업데이트 합니다."
        update_history = [
            {"role": "user", "content": input},
            {"role": "assistant", "content": result},
        ]
        self.chat_message_history.add_messages(update_history)

    @timer
    def invoke(self, input: str) -> str:
        """
        Agent Invoke 함수 입니다.
        사용자 입력 시 알맞은 도구를 사용하여 답변을 생성합니다.
        예외 발생 시 에러 메시지를 반환 합니다.
        """
        logger.info(f"[Agent] Invoking...")
        logger.info(f"[Agent] User: {input}")

        try:
            # chat history 로드
            history_messages = self._select_history()

            # Create Prompt
            messages = [
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            ]
            messages.extend(history_messages)
            messages.append({"role": "user", "content": input})

            # Create tool
            tools = self.get_tools()

            # Calling LLM in the loop
            while True:
                logger.info(f"[Agent] Calling LLM...")
                response = self.create_chat_completion(
                    messages, stream=False, tools=tools
                )
                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                # Tool 이 호출된 경우
                if tool_calls:
                    messages.append(response_message)  # assistant의 tool call 기록

                    for tool_call in tool_calls:

                        # Tool 검증
                        function_name = tool_call.function.name
                        if function_name not in self.available_functions:
                            logger.error(
                                f"[Agent] Undefined tool call: {function_name}",
                                exc_info=True,
                            )
                            raise ValueError(
                                f"정의되지 않은 함수 호출: {function_name}"
                            )
                        function_args = json.loads(tool_call.function.arguments)

                        # Tool 실행
                        logger.info(
                            f"[Agent] Action: Call tool '{function_name}' with args {function_args}"
                        )
                        try:
                            function_response = self.available_functions[function_name](
                                **function_args
                            )
                            logger.info(
                                f"[Tool] {function_name} returned:\n{function_response}"
                            )
                        except Exception as e:
                            logger.error(
                                f"[Tool] Error executing '{function_name}': {e}",
                                exc_info=True,
                            )
                            raise e

                        # Tool 실행 결과 추가
                        messages.append(
                            {
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps(
                                    function_response, ensure_ascii=False
                                ),
                            }
                        )

                    continue  # Tool 호출 시 다시 루프

                # Tool 이 호출되지 않은 경우
                else:
                    result = response_message.content
                    logger.info(f"[Agent] Assistant:\n{result}")

                    # 히스토리 저장
                    self._update_history(input, result)
                    return result

        except Exception as e:
            logger.error(f"[Agent] Exception occurred: {e}", exc_info=True)
            result = ERROR_RESULT_PROMPT
            return result

    def ainvoke(self, input: str):
        pass

    def stream(self, input: str):
        pass

    def astream(self, input: str):
        pass

    def create_chat_completion(
        self,
        messages: list[dict],
        stream: bool = False,
        tools: list = [],
        tool_choice: str = "auto",
    ) -> Any:
        """
        OpenAI 챗봇 API를 호출하여 답변을 생성합니다.

        Args:
            messages (list[dict]): 대화 메시지 목록 (role, content 포함).
            stream (bool, optional): 스트리밍 응답 여부. 기본값은 False.

        Returns:
            response: OpenAI API의 응답 객체.
        """
        response = self.llm.chat.completions.create(
            model=cfg.openai.llm_model,
            max_completion_tokens=cfg.openai.llm_max_tokens,
            messages=messages,
            stream=stream,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response

    def get_tools(self) -> list:
        """
        도구 목록을 얻습니다.
        사용가능한 도구를 등록합니다.
        """
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "retrieve_faq",
                    "description": "사용자 쿼리와 유사한 FAQ 문서를 검색하는 도구 입니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "사용자 쿼리입니다.",
                            }
                        },
                        "required": ["query"],
                    },
                },
            }
        ]
        self.available_functions = {"retrieve_faq": self.retrieve_faq}

        return tools

    def retrieve_faq(self, query: str) -> list:
        """FAQ 문서를 검색하는 도구 입니다."""
        return retrieve(query, self.db)
