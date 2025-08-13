# smartstore-faq-chatbot
네이버 스마트스토어의 자주 묻는 질문(FAQ)을 기반으로 질의응답하는 챗봇입니다.

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

## Settings
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
2. conf/service.yaml에서 openai.api_key 값을 본인의 API 키로 설정합니다.
```yaml
# conf/service.yaml 예시
openai:
  api_key: your-openai-api-key-here
```

### 3. data 파일 추가
- data/final_result.pkl 경로에 네이버 스마트스토어 FAQ 데이터를 추가합니다.
- 아래 예시를 참고해주세요.
  ```
  .
  ├── data                     
  │   └── final_result.pkl      # 스마트스토어 faq 데이터 파일
  ```