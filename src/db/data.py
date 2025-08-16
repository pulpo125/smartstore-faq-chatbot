import pickle
import re

from src.utils import logger


def load_data(filepath: str) -> dict:
    """pickle 데이터 로드 함수"""
    try:
        with open(filepath, "rb") as file:
            data = pickle.load(file)
        return data
    except Exception as e:
        logger.error(f"데이터 로드 실패: {e}", exc_info=True)


def preprocess_data(data: dict) -> dict:
    """
    데이터 전처리 함수
    - \xa0 -> 공백
    - 연속 줄바꿈, 공백 정리
    - 불필요한 공통 텍스트 제거
    """

    def _normalize_text(x: str) -> str:
        """
        텍스트 정규화 함수
        - \xa0 -> 공백
        - 연속 줄바꿈, 공백 정리
        - 불필요한 공통 텍스트 제거
        """

        # 1. Non-breaking space → 공백
        x = x.replace("\xa0", " ")

        # 2. 불필요한 안내문/버튼/평점/의견 제거
        patterns_to_remove = [
            r"위 도움말이 도움이 되었나요\?",
            r"별점\d점",
            r"보내기",
            r"관련 도움말/키워드.*",
            r"도움말 닫기",
            r"소중한 의견을 남겨주시면 보완하도록 노력하겠습니다\.",
        ]
        for pat in patterns_to_remove:
            x = re.sub(pat, "", x)

        # 3. 연속 공백/탭을 단일 공백으로
        x = re.sub(r"[ \t]+", " ", x)

        # 4. 연속 줄바꿈 2줄로 통일
        x = re.sub(r"\n\s*\n+", "\n\n", x)

        # 5. 앞뒤 공백 제거
        return x.strip()

    # 전체 데이터 전처리
    processed_data = {k: _normalize_text(v) for k, v in data.items()}

    return processed_data


def chunk_text(text: str, max_chunk_size=1000) -> list:
    """텍스트를 길이에 따라 자연스럽게 문장 단위로 분할하는 청킹 함수"""
    sentences = text.split(". ")
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:  # 남아 있는 텍스트 추가
        chunks.append(current_chunk.strip())

    return chunks
