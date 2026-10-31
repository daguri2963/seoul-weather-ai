# 서울 기온 데이터 AI

기상청 서울 ASOS(108)의 **2024년 공식 일별 최고기온 366건**을 Firestore에 저장하고, 저장된 데이터에서 계산한 요약을 AI 대화에 반영하는 학습용 웹 서비스입니다. 기존 [시계열 분석 저장소](https://github.com/daguri2963/seoul-rain-temperature-analysis)의 `data/processed/temperature_daily_2024.csv`를 재사용했습니다. 원본 분석의 강수 유형별 결론은 이 서비스의 요약과 혼합하지 않았습니다. 이 앱이 다루는 `value`는 **일별 최고기온(°C)** 한 가지입니다.

## 기술과 구성

- 백엔드: Python 3.10+, FastAPI, Pydantic, Firebase Admin SDK, OpenAI SDK
- 저장소: Firestore `data`와 `conversations` 컬렉션
- 프론트엔드: HTML, CSS, 바닐라 JavaScript. `API_BASE_URL`을 빌드 때 `config.js`에 기록하는 작은 Node 스크립트만 사용합니다.
- 배포 대상: Render 웹 서비스, Vercel 정적 사이트

`backend/app/routers`는 HTTP 경로와 검증을, `backend/app/services`는 Firestore 작업과 요약 계산을 담당합니다. `data` 문서 ID는 `YYYY-MM-DD`이며 `{date, value, memo}`를 저장합니다. `conversations`에는 `{title, messages, created_at, updated_at}`를 저장합니다. 목록 조회에는 메시지가 빠지고 `GET /api/conversations/{id}`에서 전체 메시지를 불러옵니다.

## 로컬 실행

1. Firebase 프로젝트에서 Firestore Database를 만들고 서비스 계정 키를 발급합니다. 키 파일은 프로젝트 밖에 보관하거나 환경 변수에 넣습니다.
2. Codyssey 콘솔의 가상 키를 준비합니다. 호출 가능 횟수와 과금 여부는 해당 콘솔에서 확인합니다.
3. 백엔드를 시작합니다. Codyssey 콘솔의 가상 키는 `OPENAI_API_KEY`에만 입력합니다. 이 키를 채팅, Git, 프론트엔드 설정 파일에 넣지 마세요.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# .env에 OPENAI_API_KEY, FIREBASE_SERVICE_ACCOUNT_PATH 또는 FIREBASE_SERVICE_ACCOUNT_JSON 설정
uvicorn app.main:app --reload
```

4. 새 터미널에서 초기 데이터를 한 번 가져옵니다. 기존 날짜는 건너뛰므로 다시 실행해도 중복되지 않습니다.

```powershell
cd backend
python scripts/import_data.py
```

5. 프론트엔드를 빌드하고 정적 서버로 엽니다.

```powershell
cd frontend
$env:API_BASE_URL = "http://localhost:8000"
node build.mjs
cd dist
python -m http.server 5500
```

브라우저에서 `http://localhost:5500`을 열고, 백엔드 문서는 `http://localhost:8000/docs`에서 확인합니다. `API_ACCESS_TOKEN`을 설정했다면 화면 상단 **접근 토큰**에 같은 값을 입력합니다. 토큰은 브라우저 탭의 세션 저장소에만 둡니다.

## 환경 변수

| 위치 | 변수 | 용도 |
|---|---|---|
| 백엔드 | `OPENAI_API_KEY` | Codyssey 콘솔의 가상 키. 서버에만 설정 |
| 백엔드 | `OPENAI_BASE_URL` | Codyssey OpenAI 호환 주소 `https://copa.codyssey.kr/v1` |
| 백엔드 | `OPENAI_MODEL` | Codyssey 예제 모델 `gpt-5-mini` |
| 백엔드 | `FIREBASE_SERVICE_ACCOUNT_JSON` | 서비스 계정 JSON 전체 문자열, 배포에서 권장 |
| 백엔드 | `FIREBASE_SERVICE_ACCOUNT_PATH` | 로컬 키 파일 경로. JSON 변수와 둘 중 하나 필요 |
| 백엔드 | `ALLOWED_ORIGINS` | 쉼표로 구분한 프론트엔드 출처. Vercel URL을 정확히 입력 |
| 백엔드 | `API_ACCESS_TOKEN` | `/api/` 요청 보호. 공개 배포 시 긴 임의값 설정 권장 |
| 프론트엔드 빌드 | `API_BASE_URL` | Render API 주소. 브라우저에 공개되는 주소이며 비밀값을 넣지 않음 |

`.env`와 키 파일은 Git에 올리지 마세요. `.env.example`에는 실제 키가 없습니다. Render와 Vercel의 환경 변수 관리 화면에서 각 값을 입력합니다. 접근 토큰은 프론트엔드 빌드 변수로 넣지 않습니다. 이 방식은 소규모 학습용 공유에 적합하며, 여러 사용자에게 공개하려면 개별 인증과 권한 규칙이 필요합니다. Codyssey 주소와 모델은 사용자가 제공한 콘솔 예제를 기준으로 했으며, 실제 키로 호출 검증은 배포 전에 해야 합니다.

## API와 데이터 흐름

| 경로 | 기능 |
|---|---|
| `POST /api/data` | 날짜·값·메모 추가. 같은 날짜는 409 |
| `GET /api/data` | 최신 날짜순 목록 |
| `PUT /api/data/{id}` | 값·메모 수정. 날짜는 변경 불가 |
| `DELETE /api/data/{id}` | 삭제 |
| `GET /api/data/summary` | 기간, 개수, 평균·최고·최저, 최근 추세 |
| `POST /api/conversations` | 대화 수동 저장 |
| `GET /api/conversations` | 메시지를 제외한 목록 |
| `GET /api/conversations/{id}` | 메시지를 포함한 대화 불러오기 |
| `DELETE /api/conversations/{id}` | 대화 삭제 |
| `POST /api/chat` | 요약을 시스템 프롬프트에 삽입, AI 응답, 대화 자동 저장 |

요약의 추세는 마지막 7건 평균과 그 직전 7건 평균을 비교합니다. 데이터가 14건 미만이면 가능한 절반 크기의 구간을 사용합니다. 차이가 ±0.5°C 이내이면 보합입니다. 이는 단순한 저장 데이터 변화 지표이며 강수 영향이나 미래 기온 예측이 아닙니다. 채팅은 요약 수치만 전달하므로 특정 날짜의 값을 묻는 질문에는 답변의 한계가 있습니다. 모델 응답은 최대 350토큰, 이전 대화 문맥은 최근 10개 메시지로 제한합니다.

## 배포

1. 이 프로젝트의 GitHub 저장소는 [daguri2963/seoul-weather-ai](https://github.com/daguri2963/seoul-weather-ai)입니다. GitHub에 코드가 올라간 뒤 Render와 Vercel에서 이 저장소를 연결합니다.
2. Render에서 저장소 루트의 `render.yaml`로 Blueprint를 만들거나 Python Web Service를 만듭니다. **Free** 플랜인지 생성 전에 확인합니다. 설정 파일은 `plan: free`, `rootDir=backend`, 빌드 `pip install -r requirements.txt`, 실행 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`를 명시합니다. 환경 변수에 키, 허용 출처, 접근 토큰을 입력합니다.
3. `seoul-weather-ai` Firebase 프로젝트의 Firestore에는 2024년 데이터 **366건을 이미 등록했습니다**. 다른 Firebase 프로젝트에 배포할 때만 로컬에서 `backend/scripts/import_data.py`를 실행합니다. Render Free 서비스는 셸 실행을 지원하지 않습니다.
4. Vercel에서 저장소의 **Root Directory를 `frontend`**로 지정합니다. `API_BASE_URL=https://<Render 주소>`를 설정하고 배포합니다. 이 프로젝트의 Vercel 기본 주소는 API의 기본 CORS 허용 목록에 포함돼 있습니다. 다른 프론트 주소를 사용하면 Render의 `ALLOWED_ORIGINS`에 해당 주소를 추가한 뒤 재배포합니다.
5. `https://<Render 주소>/health`, `/docs`와 프론트 URL을 열어 확인합니다. Render 무료 서비스가 잠든 뒤 첫 요청은 지연될 수 있으며 화면에 안내가 표시됩니다.

배포 URL: 프론트 [https://seoul-weather-ai-frontend.vercel.app](https://seoul-weather-ai-frontend.vercel.app), 백엔드 API [https://seoul-weather-ai.onrender.com](https://seoul-weather-ai.onrender.com), Swagger [https://seoul-weather-ai.onrender.com/docs](https://seoul-weather-ai.onrender.com/docs). 2026-10-31에 `/health`와 `/docs`의 HTTP 200 응답 및 OpenAPI 경로 7개를 확인했습니다. 루트(`/`)는 화면이 없는 API이므로 404가 정상입니다.

## 검증과 제출

```powershell
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

테스트 4개가 통과했습니다. 요청 검증, 요약 계산, 채팅 프롬프트 주입·자동 저장, 접근 토큰을 확인합니다. 실제 Firestore에서 366건을 다시 읽어 기간 `2024-01-01 ~ 2024-12-31`, 평균 `19.54°C`, 최고 `36.4°C`, 최저 `-8.2°C`를 확인했습니다. Codyssey 실제 키를 이용한 AI 호출은 아직 확인 전입니다.

제출 스크린샷은 실제 서비스 설정 후 촬영해 README에 추가하세요: (1) 요약과 질문·AI 답변이 함께 보이는 화면, (2) 데이터 추가 또는 수정 결과가 보이는 화면, (3) 이전 대화를 불러온 화면. 현재 Codyssey 키와 배포가 완료되지 않아 실제 화면 캡처가 없습니다.

## 출처

기상청 기상자료개방포털, 서울 ASOS 지점 108, 2024년 일자료. 원본 저장소의 [출처 및 이용 조건 안내](https://github.com/daguri2963/seoul-rain-temperature-analysis#출처와-이용-조건)를 유지합니다. 원본 자료는 사후 보정될 수 있습니다.

