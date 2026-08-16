"""작업 진행 중 일시정지/재개/중지를 지원하기 위한 제어 객체."""
import threading


class JobCancelled(Exception):
    """사용자가 중지를 요청했을 때 작업 루프에서 발생시키는 예외."""


class JobControl:
    def __init__(self):
        self._pause_event = threading.Event()
        self._pause_event.set()  # set = 실행 중, clear = 일시정지
        self._stop_event = threading.Event()

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()  # 일시정지 상태로 멈춰 있다면 깨워서 중지 처리되게 함

    def is_paused(self):
        return not self._pause_event.is_set()

    def is_stopped(self):
        return self._stop_event.is_set()

    def checkpoint(self):
        """작업 루프에서 폴더 하나를 처리하기 전에 호출한다.

        중지가 요청되었으면 JobCancelled를 발생시키고,
        일시정지 상태이면 재개되거나 중지될 때까지 대기한다.
        """
        if self._stop_event.is_set():
            raise JobCancelled()
        self._pause_event.wait()
        if self._stop_event.is_set():
            raise JobCancelled()
