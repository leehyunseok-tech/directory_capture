"""macOS Finder 창을 열어 스크린샷으로 캡처하는 모듈 (macOS 전용).

AppleScript(osascript)로 Finder에 폴더를 열게 한 뒤 앞쪽 창의 좌표를 읽어,
macOS 내장 명령인 screencapture로 그 영역만 캡처한다. 별도 설치 없이
macOS 기본 구성요소(osascript, screencapture)만으로 동작한다.
"""
import os
import subprocess
import time


class FinderCaptureError(Exception):
    pass


def _run_osascript(script):
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        raise FinderCaptureError(result.stderr.strip() or "osascript 실행에 실패했습니다.")
    return result.stdout.strip()


def capture_folder(folder_path, save_path, render_wait=0.8, close_after=True):
    """folder_path를 Finder로 열어 그 창을 스크린샷으로 캡처해 save_path에 저장한다."""
    folder_path = os.path.abspath(folder_path)
    posix_path = folder_path.replace("\\", "\\\\").replace('"', '\\"')

    open_script = f'''
    tell application "Finder"
        activate
        open (POSIX file "{posix_path}" as alias)
        set b to bounds of front window
        return ((item 1 of b) as string) & "," & ((item 2 of b) as string) & "," & ((item 3 of b) as string) & "," & ((item 4 of b) as string)
    end tell
    '''
    try:
        bounds_str = _run_osascript(open_script)
    except FinderCaptureError as exc:
        raise FinderCaptureError(f"Finder 창을 열지 못했습니다: {folder_path} ({exc})")

    time.sleep(render_wait)

    try:
        x1, y1, x2, y2 = (int(v.strip()) for v in bounds_str.split(","))
    except ValueError:
        raise FinderCaptureError(f"Finder 창 좌표를 읽지 못했습니다: {bounds_str}")

    region = f"{x1},{y1},{x2 - x1},{y2 - y1}"
    result = subprocess.run(["screencapture", "-x", "-R", region, save_path], capture_output=True, text=True)
    if result.returncode != 0:
        raise FinderCaptureError(result.stderr.strip() or "screencapture 실행에 실패했습니다.")

    if close_after:
        try:
            _run_osascript('tell application "Finder" to close front window')
        except FinderCaptureError:
            pass
