# 이 프로젝트를 단일 실행 파일(exe)로 빌드한다.
# 가상환경(.venv)이 없으면 먼저 만들고 필요한 패키지를 설치한 뒤 PyInstaller로 빌드한다.
# 결과물: dist\DirectoryCapture.exe (파이썬 설치 없는 PC에서도 바로 실행 가능)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    Write-Host "가상환경(.venv)이 없어 새로 만듭니다..."
    python -m venv .venv
}

& ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
& ".venv\Scripts\python.exe" -m pip install --quiet pyinstaller

& ".venv\Scripts\pyinstaller.exe" --noconfirm --onefile --windowed --name DirectoryCapture main.py

Write-Host ""
Write-Host "빌드 완료: dist\DirectoryCapture.exe"
Write-Host "이 파일 하나만 다른 Windows PC로 복사해서 그대로 실행하면 됩니다."
