"""윈도우 탐색기 창을 열어 스크린샷으로 캡처하는 모듈 (Windows 전용).

macOS/Linux에서는 각각 Finder/파일 관리자를 제어하는 별도 구현이 필요하며,
이 모듈은 win32com(Shell.Application)을 이용해 탐색기 창의 실제 폴더 경로를
확인하므로 동일한 이름의 폴더가 여러 곳에 있어도 정확한 창을 찾아낸다.
"""
import os
import subprocess
import time

import pythoncom
import win32com.client
import win32con
import win32gui
from PIL import ImageGrab


class ExplorerCaptureError(Exception):
    pass


def _normalize(path):
    return os.path.normcase(os.path.abspath(path).rstrip("\\"))


def _find_explorer_window(shell, target_path, timeout, poll_interval=0.2):
    target = _normalize(target_path)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            windows = list(shell.Windows())
        except Exception:
            windows = []
        for w in windows:
            try:
                folder = w.Document.Folder.Self.Path
            except Exception:
                continue
            if _normalize(folder) == target:
                return w
        time.sleep(poll_interval)
    return None


def _bring_to_front(hwnd):
    """캡처 대상 창을 화면 맨 위로 강제로 올린다.

    백그라운드 프로세스에서 SetForegroundWindow는 Windows 정책상 실패하는 경우가 많아
    (포커스를 뺏지 못해) 다른 창이 위에 남은 채로 캡처되는 문제가 있었다. 이를 막기 위해
    HWND_TOPMOST로 잠깐 올렸다가 HWND_NOTOPMOST로 되돌리는 방식으로 z-order만 맨 위로
    옮긴다. SWP_NOACTIVATE를 사용해 사용자가 다른 작업 중이어도 키보드 포커스는 뺏지 않는다.
    """
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass


def capture_folder(folder_path, save_path, open_timeout=5.0, render_wait=0.8, close_after=True):
    """folder_path를 탐색기로 열어 그 창을 스크린샷으로 캡처해 save_path에 저장한다."""
    pythoncom.CoInitialize()
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        subprocess.Popen(["explorer.exe", os.path.abspath(folder_path)])

        window = _find_explorer_window(shell, folder_path, timeout=open_timeout)
        if window is None:
            raise ExplorerCaptureError(f"탐색기 창을 찾지 못했습니다: {folder_path}")

        hwnd = int(window.HWND)
        try:
            _bring_to_front(hwnd)
            time.sleep(render_wait)

            rect = win32gui.GetWindowRect(hwnd)
            image = ImageGrab.grab(bbox=rect, all_screens=True)
            image.save(save_path)
        finally:
            if close_after:
                try:
                    window.Quit()
                except Exception:
                    pass
    finally:
        pythoncom.CoUninitialize()
