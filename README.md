# 폴더 목록/캡처 도구 (Directory Capture)

지정한 폴더 하위의 폴더/파일 구조를 텍스트로 목록화하고, 각 폴더를 파일 관리자 창으로 열어
스크린샷으로 남길 수 있는 GUI 도구입니다.

- 폴더 목록화: Windows / macOS / Linux 공용
- 폴더별 창 스크린샷 캡처: Windows(탐색기) / macOS(Finder) / Linux(X11, 기본 파일 관리자) 모두 지원

> **참고**: macOS/Linux 캡처 구현은 각 OS의 공식 방식(AppleScript+screencapture, xdotool+ImageMagick)을
> 그대로 따라 작성했지만, 이 프로젝트는 Windows 환경에서 개발되어 **macOS/Linux에서는 직접 실행
> 테스트를 하지 못했습니다.** 처음 사용하실 때 폴더 1~2개로 먼저 시험해보시고, 문제가 있으면
> 알려주세요.

## 요구사항

- Python 3.9 이상
- **Windows**: 별도 시스템 설치 불필요 (`pywin32`, `Pillow`는 pip로 설치)
- **macOS**: 추가 설치 불필요 (`osascript`, `screencapture`는 macOS 기본 구성요소)
- **Linux**: X11 세션 + 시스템 패키지 `xdotool`, `imagemagick` 필요 (Wayland는 미지원, 아래
  "OS별 캡처 방식" 참고)

## 설치 (가상환경)

PC 전체 파이썬 환경에 영향을 주지 않도록, 이 프로젝트 폴더 안에 가상환경(`.venv`)을
만들어 그 안에서만 패키지를 설치/실행합니다.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Windows (cmd)**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

**macOS / Linux (bash/zsh)**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt`에는 다음 패키지가 포함되어 있습니다. `pywin32`, `Pillow` 모두
`sys_platform == "win32"` 조건이 걸려 있어 macOS/Linux에서는 애초에 설치되지 않습니다
(두 플랫폼은 pip 패키지 대신 OS 기본 명령/시스템 패키지로 캡처를 구현했기 때문입니다).

- `pywin32` — 탐색기 창 제어 및 캡처 (Windows 전용)
- `Pillow` — 화면 캡처 이미지 저장 (Windows 전용)

가상환경은 `.venv` 폴더 하나에만 설치되므로, 프로젝트 폴더를 통째로 지우면
설치된 패키지도 함께 사라지고 시스템 파이썬에는 아무 영향이 없습니다.
작업을 마친 뒤에는 `deactivate` 명령으로 가상환경을 빠져나올 수 있습니다.

## 실행

가상환경을 활성화한 상태에서 실행합니다.

```bash
python main.py
```

가상환경을 활성화하지 않고 바로 실행하려면 가상환경의 파이썬을 직접 지정해도 됩니다.

```bash
# Windows
.venv\Scripts\python.exe main.py

# macOS / Linux
.venv/bin/python main.py
```

실행하면 아래와 같은 GUI 창이 뜹니다.

1. **대상 폴더**: 목록화/캡처할 최상위 폴더를 "찾아보기"로 선택
2. **결과 저장 폴더**: 결과 파일(텍스트, 스크린샷)이 저장될 폴더를 선택
3. **옵션**
   - `폴더 목록을 텍스트로 저장`: 체크 시 대상 폴더 하위 전체를 재귀적으로 훑어 `directory_listing.txt` 생성
   - `폴더별 탐색기 창 스크린샷 캡처`: 체크 시 각 폴더를 파일 관리자(Windows 탐색기 / macOS Finder /
     Linux 파일 관리자)로 열어 창을 캡처. 캡처를 전혀 지원하지 않는 환경(예: Linux Wayland)에서는
     이 옵션이 자동으로 비활성화되고 안내 문구가 표시됩니다.
   - `캡처 최대 깊이`: 스크린샷을 남길 하위 폴더 범위
     - `0` = 대상 폴더 자신만
     - `1` = 대상 폴더 + 바로 아래 하위 폴더까지 (기본값)
     - `2` 이상 = 해당 단계까지
     - `-1` = 제한 없음(모든 하위 폴더). 폴더 수가 많으면 탐색기 창을 그만큼 여닫으므로 시간이 오래 걸릴 수 있습니다.
   - `캡처에서 제외할 폴더 이름 패턴`: 쉼표로 구분된 glob 패턴 목록. 이름이 패턴과 일치하는 폴더는
     스크린샷 대상에서 제외되고, 그 하위 폴더도 함께 건너뜁니다. 기본값은 `.*`로, `.git`, `.venv`,
     `.claude`처럼 점(.)으로 시작하는 모든 폴더가 기본적으로 제외됩니다. 필요하면 쉼표로 이어서
     `node_modules`, `__pycache__` 등 원하는 패턴을 추가할 수 있습니다. (`directory_listing.txt`
     텍스트 목록에는 이 제외 설정과 무관하게 모든 폴더/파일이 그대로 표시됩니다.)
4. **시작 / 일시정지 / 정지** 버튼으로 작업을 제어할 수 있습니다.
   - **시작**: 작업을 백그라운드로 실행. 진행 상황은 하단 로그 창과 진행 바에 표시됩니다.
   - **일시정지 / 재개**: 현재 처리 중인 폴더까지만 마치고 다음 폴더로 넘어가기 전에 멈춥니다.
     다시 누르면 멈춘 지점부터 이어서 진행합니다.
   - **정지**: 작업을 완전히 중단합니다. 그때까지 만들어진 목록/스크린샷은 그대로 결과 폴더에 남습니다.
     (일시정지 중에 눌러도 즉시 중단 처리됩니다.)

## 출력 결과

결과 저장 폴더 아래에 다음이 생성됩니다.

```
결과폴더/
├─ directory_listing.txt
└─ screenshots/
   ├─ A.png            # 대상 폴더(A) 자신의 캡처
   └─ A/
      ├─ B.png         # A의 하위 폴더 B의 캡처
      ├─ C.png         # A의 하위 폴더 C의 캡처
      └─ B/
         └─ D.png      # B의 하위 폴더 D의 캡처
```

`directory_listing.txt`는 `tree` 명령처럼 폴더/파일 구조를 그대로 눈으로 볼 수 있는
트리 형태로 저장됩니다. 예:

```
A
├── B
│   ├── D
│   │   └── d1.txt (2 bytes)
│   └── b1.txt (2 bytes)
├── C
│   └── c1.txt (2 bytes)
└── note.txt (9 bytes)
```

`screenshots/` 아래는 실제 폴더 계층 구조를 그대로 미러링합니다. 폴더 X의 캡처 이미지는
X의 부모 폴더와 동일한 경로에 `X.png`로 저장되고, X에 하위 폴더가 있으면 그 하위 폴더들의
캡처는 `X/` 디렉터리 안에 다시 같은 방식으로 저장됩니다. 폴더 이름이 이미 파일시스템에서
쓰이던 이름 그대로 사용되므로 경로만 보고도 원래 어느 폴더였는지 바로 알 수 있습니다.

`directory_listing.txt`는 항상 대상 폴더 전체를 기준으로 생성되며(깊이 제한 없음, 제외 패턴도
적용되지 않음), 스크린샷만 "캡처 최대 깊이"와 "캡처에서 제외할 폴더 이름 패턴"의 영향을 받습니다.

## OS별 캡처 방식

| OS | 여는 방법 | 캡처 방법 | 추가 설치 |
| --- | --- | --- | --- |
| Windows | `explorer.exe 폴더경로` | Windows Shell COM(`Shell.Application`)으로 정확한 창을 찾아 `GetWindowRect` + 화면 캡처 | 없음 (pip로 pywin32/Pillow 설치) |
| macOS | Finder에서 `open (POSIX file ...)` | AppleScript로 앞쪽 창의 좌표를 읽고 `screencapture -R`로 그 영역만 캡처 | 없음 (osascript, screencapture는 macOS 기본 제공) |
| Linux (X11) | `xdg-open 폴더경로` (기본 파일 관리자) | `xdotool`로 새로 뜬 창을 찾고 ImageMagick `import -window`로 그 창만 캡처 | `xdotool`, `imagemagick` 시스템 패키지 (예: `sudo apt install xdotool imagemagick`) |

각 방식 모두 캡처가 끝나면 해당 창을 자동으로 닫으려 시도합니다. 폴더 개수가 많으면
창이 반복적으로 열렸다 닫히므로, 작업 중에는 컴퓨터를 다른 용도로 사용하지 않는 것을
권장합니다.

Windows에서는 화면 배율(디스플레이 확대/축소, DPI 스케일링)에 관계없이 창 좌표와 실제
화면 캡처 좌표가 어긋나지 않도록, 프로그램 시작 시 프로세스를 모니터별 DPI 인식으로
설정합니다. (배율 100%가 아닌 화면에서도 캡처 영역이 잘리지 않습니다.)

**캡처 중 다른 창에 가려지는 문제 방지**: Windows/macOS는 화면의 특정 영역을 그대로
캡처하는 방식이라, 캡처하려는 창 위에 다른 창(알림, 다른 프로그램 등)이 떠 있으면 그
창까지 함께 찍힐 수 있습니다. 이를 막기 위해 Windows는 캡처 직전 대상 창을 z-order
맨 위로 강제로 올린 뒤 캡처합니다(키보드 포커스는 뺏지 않아 다른 작업 중이어도 방해되지
않습니다). macOS는 AppleScript `activate`로 Finder를 앞으로 가져온 뒤 캡처합니다.
Linux는 창의 화면 영역이 아니라 창 자체의 렌더링 버퍼를 직접 캡처(`import -window`)하는
방식이라 애초에 다른 창에 가려지는 문제가 없습니다.

## 제한 사항

- **Linux는 X11 세션에서만 캡처가 동작합니다.** Wayland 세션에서는 `xdotool`이 창 목록/제어를
  가져오지 못해 캡처가 실패할 수 있습니다(목록화 기능 자체는 Wayland에서도 정상 동작합니다).
- macOS/Linux 캡처 구현은 이 세션에서 실제 macOS/Linux 장비로 검증하지 못했습니다. 각 OS의
  표준 API/명령(AppleScript, xdotool 등)을 문서대로 사용했지만, 배포 전 해당 OS에서 직접
  확인해보시기를 권장합니다.
- 경로 길이가 매우 긴 폴더(Windows `MAX_PATH` 제한 인근)나 접근 권한이 없는 폴더는
  목록화/캡처가 실패할 수 있으며, 실패 시 로그와 `directory_listing.txt`에 사유가 표시됩니다.

## 실행 파일(exe)로 패키징하기 (Windows)

이 패키징 방법은 Windows 전용입니다. PyInstaller는 빌드를 실행한 OS용 결과물만 만들 수 있어
(크로스 컴파일 미지원), macOS/Linux용 실행 파일이 필요하다면 해당 OS에서 동일한 방식으로
`pyinstaller --onefile main.py`를 실행해야 합니다. macOS/Linux는 대부분 Python이 기본
설치되어 있으므로, "설치 (가상환경)" 절차로 바로 실행하는 것도 좋은 방법입니다.

Python이 설치되어 있지 않은 다른 Windows PC에서도 바로 실행할 수 있도록, PyInstaller로
단일 exe 파일을 만들 수 있습니다. 이 exe 하나에는 파이썬 인터프리터와 필요한 패키지가
모두 포함되므로, 대상 PC에 Python이나 별도 설치 과정이 전혀 필요 없습니다.

**빌드 (개발 PC에서 한 번만 수행)**

```powershell
.\build.ps1
```

가상환경이 없으면 자동으로 만들고, `requirements.txt`와 `pyinstaller`를 설치한 뒤
빌드합니다. 완료되면 `dist\DirectoryCapture.exe`가 생성됩니다.

수동으로 직접 실행하고 싶다면 다음과 같이 해도 됩니다.

```powershell
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\pyinstaller.exe --noconfirm --onefile --windowed --name DirectoryCapture main.py
```

**배포 / 실행**

- `dist\DirectoryCapture.exe` 파일 하나만 USB나 공유 폴더 등으로 옮겨서, 대상 Windows PC에서
  더블클릭하면 바로 실행됩니다. 설치 과정이나 Python, pip 등이 전혀 필요 없습니다.
- 최초 실행 시 SmartScreen/백신 경고가 뜰 수 있습니다(서명되지 않은 exe이기 때문). "추가 정보 →
  실행" 등으로 진행하면 됩니다. 조직 내 배포 시 경고를 없애려면 코드 서명 인증서가 필요합니다.
- 코드를 수정한 뒤에는 `.\build.ps1`을 다시 실행하면 `dist\DirectoryCapture.exe`가 최신 내용으로
  갱신됩니다.

## 캡처 모듈 구조

`main.py`는 `sys.platform`에 따라 아래 모듈 중 하나에서 `capture_folder(folder_path, save_path)`를
가져와 사용합니다. 세 모듈 모두 같은 함수 시그니처를 따르므로, 다른 OS나 다른 파일 관리자를
추가로 지원하고 싶다면 동일한 시그니처의 새 모듈을 만들고 `main.py`의 분기만 추가하면 됩니다.

- `capture/explorer_capture.py` — Windows
- `capture/finder_capture.py` — macOS
- `capture/linux_capture.py` — Linux (X11)
