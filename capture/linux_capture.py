"""Linux 파일 관리자 창을 열어 스크린샷으로 캡처하는 모듈 (X11 전용).

`xdg-open`으로 기본 파일 관리자(nautilus, dolphin, thunar 등)에 폴더를 열게 한 뒤,
`xdotool`로 새로 뜬 창을 찾고 ImageMagick의 `import`로 그 창만 캡처한다.
사전에 시스템 패키지로 xdotool, imagemagick이 설치되어 있어야 한다
(예: Debian/Ubuntu `sudo apt install xdotool imagemagick`).

Wayland 세션에서는 xdotool이 창 목록/제어를 지원하지 않아 동작하지 않을 수 있다.
"""
import os
import shutil
import subprocess
import time


class FileManagerCaptureError(Exception):
    pass


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def _check_dependencies():
    missing = [tool for tool in ("xdotool", "xdg-open", "import") if shutil.which(tool) is None]
    if missing:
        raise FileManagerCaptureError(
            "다음 프로그램이 설치되어 있지 않습니다: " + ", ".join(missing)
            + " (xdotool, imagemagick 패키지를 설치해주세요)"
        )


def capture_folder(folder_path, save_path, open_timeout=5.0, render_wait=0.8, close_after=True):
    """folder_path를 파일 관리자로 열어 그 창을 스크린샷으로 캡처해 save_path에 저장한다."""
    _check_dependencies()
    folder_path = os.path.abspath(folder_path)

    before = _run(["xdotool", "search", "--onlyvisible", "."])
    before_ids = set(before.stdout.split()) if before.returncode == 0 else set()

    open_result = _run(["xdg-open", folder_path])
    if open_result.returncode != 0:
        raise FileManagerCaptureError(f"파일 관리자를 열지 못했습니다: {folder_path}")

    deadline = time.time() + open_timeout
    window_id = None
    while time.time() < deadline and window_id is None:
        after = _run(["xdotool", "search", "--onlyvisible", "."])
        after_ids = set(after.stdout.split()) if after.returncode == 0 else set()
        new_ids = after_ids - before_ids
        if new_ids:
            window_id = sorted(new_ids)[-1]
        else:
            time.sleep(0.2)

    if window_id is None:
        raise FileManagerCaptureError(f"새로 열린 파일 관리자 창을 찾지 못했습니다: {folder_path}")

    _run(["xdotool", "windowactivate", window_id])
    time.sleep(render_wait)

    capture_result = _run(["import", "-window", window_id, save_path])
    if capture_result.returncode != 0:
        raise FileManagerCaptureError(capture_result.stderr.strip() or "import(ImageMagick) 캡처에 실패했습니다.")

    if close_after:
        _run(["xdotool", "windowclose", window_id])
