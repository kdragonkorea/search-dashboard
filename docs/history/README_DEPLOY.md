# Hugging Face Spaces 배포 가이드

## 1. Hugging Face 계정 생성
https://huggingface.co/join

## 2. 새 Space 생성
1. https://huggingface.co/new-space 접속
2. Space name: `search-dashboard` (원하는 이름)
3. License: MIT
4. Select the Space SDK: **Streamlit**
5. Space hardware: **CPU basic (free)**
6. Create Space 클릭

## 3. 파일 업로드
다음 파일들을 Space에 업로드:
- app.py
- data_loader.py
- visualizations.py
- requirements.txt
- packages.txt (선택사항)
- .streamlit/secrets.toml (Secrets로 설정)

## 4. Secrets 설정
Space Settings → Repository secrets → Add a secret:
- Name: `GDRIVE_FILE_ID`
- Value: `1Ly6-c0JYpiWGTx56-QHQdzAEZI6axf-i`

## 5. 완료!
Space가 자동으로 빌드되고 실행됩니다.
URL: https://huggingface.co/spaces/[username]/search-dashboard
