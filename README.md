# smartstore-faq-chatbot

네이버 스마트스토어의 자주 묻는 질문(FAQ)을 기반으로 질의응답하는 챗봇입니다.
랭체인 없이 개발한 프로젝트 입니다.

## 프로젝트 구조

```
.
├── app                       # FastAPI 디렉토리
├── conf                      # 설정 파일 디렉토리
│   ├── service.dev.yaml      
│   └── service.yaml            
├── data                     
│   └── final_result.pkl      # 스마트스토어 faq 데이터 파일
├── README.md
├── requirements.txt
└── src                       # 소스 코드 디렉토리
```

## 설정 및 실행 방법

### 1. 환경 설정

```bash
# Conda 환경 생성 및 활성화
conda create -n faq python=3.11
conda activate faq

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 2. OpenAI API Key 설정

1. 먼저 conf/service.dev.yaml을 복사하여 conf/service.yaml 파일을 생성합니다.
2. conf/service.yaml에서 openai.api\_key 값을 본인의 API 키로 설정합니다.

```yaml
# conf/service.yaml 예시
openai:
  api_key: your-openai-api-key-here
```

### 3. data 파일 추가

* data/final\_result.pkl 경로에 네이버 스마트스토어 FAQ 데이터를 추가합니다.
* 아래 예시를 참고해주세요.

  ```
  .
  ├── data                     
  │   └── final_result.pkl      # 스마트스토어 faq 데이터 파일
  ```

### 4. FastAPI 실행

```bash
uvicorn app:application --host 0.0.0.0 --port 8000 --reload
```

### 5. Swagger UI에서 데이터 Insert 하기

FastAPI 실행 후 아래 URL에 접속하세요.

👉 [http://localhost:8000/docs](http://localhost:8000/docs)

* `POST /db/insert_batch` API를 선택합니다.
* **Request body** 부분에 빈 JSON `{}` 만 넣고 **Execute** 버튼을 누르면,
  `data/final_result.pkl` 파일을 자동으로 읽어 ChromaDB에 데이터가 삽입됩니다.

예시:

```json
{}
```

성공적으로 실행되면 ChromaDB에 FAQ 데이터가 삽입되어 챗봇에서 활용할 수 있습니다. 🚀

---

### 6. 챗봇 질의 요청하기

데이터 삽입이 완료되면, `/chat/v1` API를 호출하여 FAQ 기반 질의응답을 수행할 수 있습니다.

예시 요청:

```json
{
  "chat_id": "test1",
  "input": "빠른 정산은 어떻게 신청해?",
  "session_id": "test1"
}
```

## API Reference — Chat

### POST `/chat/v1`

FAQ 기반 답변을 **스트리밍**으로 반환합니다. 응답은 여러 줄의 **NDJSON(Newline Delimited JSON)** 청크로 전송됩니다.

### Headers

* `Content-Type: application/json`
* `Accept: application/json`

### Request Body

```json
{
  "chat_id": "string",
  "input": "string",
  "session_id": "string"
}
```

#### 필드 설명

| 필드           | 타입     | 필수 | 설명                                                                    |
| ------------ | ------ | -- | --------------------------------------------------------------------- |
| `chat_id`    | string | O  | 대화(채팅)의 고유 ID. 같은 `chat_id`로 여러 번 호출하면 같은 대화 컨텍스트로 후속 질의를 이어갈 수 있습니다. |
| `input`      | string | O  | 사용자가 질의하는 실제 질문 텍스트. 예) `"빠른 정산은 어떻게 신청해?"`                           |
| `session_id` | string | O  | 사용자 세션 식별자. 동시 접속/여러 디바이스를 구분하는 데 사용됩니다.                              |

### Streaming Response (NDJSON)

요청이 성공하면 HTTP 200으로 연결이 유지되고, 아래 타입의 JSON 객체들이 **한 줄씩** 순서대로 전송됩니다.

#### 공통 타입

| 타입(`type`) | 페이로드                                                 | 설명                                                                                    |
| ---------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `chat`     | `{ "content": string }`                              | 모델이 생성 중인 답변을 **조각(chunk)** 단위로 전달합니다. 여러 번 반복됩니다.                                    |
| `chat_end` | `{ "content": string }`                              | 지금까지의 `chat` 조각들을 합친 **최종 답변 전체 텍스트**입니다.                                             |
| `complete` | `{ "response": string, "next_questions": string[] }` | **최종 메타 이벤트**. 완성된 답변(`response`)과 **후속 추천 질문** 배열을 함께 제공합니다. 스트림의 **마지막**에 1회 전송됩니다. |
| `error`    | `{ "content": string }`                              | 오류 발생 시 전송됩니다.                                                                        |

> **보장 사항**
>
> * `chat` → `chat_end` → `complete` 순서로 전송됩니다.
> * `complete.response` 는 `chat_end.content` 와 내용이 동일합니다.
> * `next_questions` 는 2개 내외의 자연어 추천 질문 목록입니다.

### 예시: 스트리밍 출력 (일부)

```ndjson
{"type":"chat","content":"정"}
{"type":"chat","content":"산"}
{"type":"chat","content":"은"}
{"type":"chat","content":" 주문"}
...
{"type":"chat_end","content":"정산은 주문이 종료된 시점(구매확정·반품완료·교환완료)으로부터 1영업일째에 진행됩니다.\n\n주요사항\n- ..."}
{"type":"complete","response":"정산은 주문이 종료된 시점(구매확정·반품완료·교환완료)으로부터 1영업일째에 진행됩니다.\n\n주요사항\n- ...","next_questions":["정산 예정일은 어디에서 확인할 수 있나요?","정산 금액에서 수수료는 어떻게 계산되나요?"]}
```

---

#### `complete` 이벤트 상세

```json
{
  "type": "complete",
  "response": "string",
  "next_questions": ["string", "..."]
}
```

| 필드               | 타입           | 설명                                                                                |
| ---------------- | ------------ | --------------------------------------------------------------------------------- |
| `type`           | `"complete"` | 이벤트 고정값. 스트림의 **마지막 청크**입니다.                                                      |
| `response`       | string       | 모델이 생성한 **최종 답변 전체 텍스트**. `chat_end.content` 와 동일합니다. |
| `next_questions` | list    | 사용자가 이어서 물어볼 수 있는 **후속 추천 질문** 리스트입니다. |
