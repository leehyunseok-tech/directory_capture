"""폴더 구조 목록화 및 폴더별 창 스크린샷 캡처 GUI.

목록화(폴더/파일 텍스트 목록)는 모든 OS에서 동작한다.
폴더별 스크린샷 캡처는 OS마다 다른 방식으로 구현되어 있다.
  - Windows: 탐색기(explorer.exe) 창을 열어 캡처 (capture/explorer_capture.py)
  - macOS: Finder 창을 열어 캡처 (capture/finder_capture.py)
  - Linux(X11): 기본 파일 관리자 창을 열어 캡처 (capture/linux_capture.py)
"""
import ctypes
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from capture.job_control import JobCancelled, JobControl
from capture.tree_lister import DEFAULT_EXCLUDE_PATTERNS, build_folder_list, write_listing_report

if sys.platform == "win32":
    from capture.explorer_capture import ExplorerCaptureError, capture_folder

    # 배율(DPI 스케일링) 설정이 100%가 아닌 화면에서 창 좌표와 실제 화면 캡처 좌표가
    # 어긋나는 것을 막기 위해, 창을 만들기 전에 프로세스를 모니터별 DPI 인식으로 설정한다.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass
elif sys.platform == "darwin":
    from capture.finder_capture import FinderCaptureError as ExplorerCaptureError, capture_folder
elif sys.platform.startswith("linux"):
    from capture.linux_capture import FileManagerCaptureError as ExplorerCaptureError, capture_folder
else:
    capture_folder = None
    ExplorerCaptureError = Exception


def capture_save_path(root_path, folder_path, screenshots_dir):
    """폴더의 스크린샷 저장 경로를 실제 폴더 계층과 동일하게 미러링해서 계산한다.

    예: 대상 폴더 A 아래 B, B 아래 D가 있다면
      A 자신          -> screenshots/A.png
      B (A의 하위)     -> screenshots/A/B.png
      D (B의 하위)     -> screenshots/A/B/D.png
    폴더명은 이미 파일시스템에 존재하는 이름이므로 별도 치환 없이 그대로 사용한다.
    """
    root_path = os.path.abspath(root_path)
    folder_path = os.path.abspath(folder_path)
    root_name = os.path.basename(root_path) or root_path
    rel = os.path.relpath(folder_path, root_path)
    parts = [root_name] if rel == "." else [root_name, *rel.split(os.sep)]

    parent_dir = os.path.join(screenshots_dir, *parts[:-1])
    return os.path.join(parent_dir, f"{parts[-1]}.png")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("폴더 목록/캡처 도구")

        self.worker_thread = None
        self.control = None
        self._build_widgets()

        # 위젯 내용에 필요한 실제 크기로 창을 맞춰 요소가 잘리지 않게 한다.
        self.update_idletasks()
        self.geometry(f"{self.winfo_reqwidth()}x{self.winfo_reqheight()}")
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

    def _build_widgets(self):
        pad = {"padx": 8, "pady": 4}

        frame_paths = ttk.Frame(self)
        frame_paths.pack(fill="x", **pad)

        ttk.Label(frame_paths, text="대상 폴더:").grid(row=0, column=0, sticky="w")
        self.root_path_var = tk.StringVar()
        ttk.Entry(frame_paths, textvariable=self.root_path_var, width=60).grid(row=0, column=1, sticky="we")
        ttk.Button(frame_paths, text="찾아보기", command=self._browse_root).grid(row=0, column=2)

        ttk.Label(frame_paths, text="결과 저장 폴더:").grid(row=1, column=0, sticky="w")
        self.output_path_var = tk.StringVar()
        ttk.Entry(frame_paths, textvariable=self.output_path_var, width=60).grid(row=1, column=1, sticky="we")
        ttk.Button(frame_paths, text="찾아보기", command=self._browse_output).grid(row=1, column=2)

        frame_paths.columnconfigure(1, weight=1)

        frame_opts = ttk.LabelFrame(self, text="옵션")
        frame_opts.pack(fill="x", **pad)
        frame_opts.columnconfigure(1, weight=1)

        self.do_listing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame_opts, text="폴더 목록을 텍스트로 저장", variable=self.do_listing_var
        ).grid(row=0, column=0, sticky="w", padx=8, pady=4)

        self.do_capture_var = tk.BooleanVar(value=True)
        capture_check = ttk.Checkbutton(
            frame_opts, text="폴더별 창 스크린샷 캡처 (탐색기/Finder/파일 관리자)", variable=self.do_capture_var
        )
        capture_check.grid(row=1, column=0, sticky="w", padx=8, pady=4)
        if capture_folder is None:
            capture_check.state(["disabled"])
            self.do_capture_var.set(False)
            ttk.Label(
                frame_opts, text="(현재 OS에서는 창 스크린샷 캡처를 지원하지 않습니다)"
            ).grid(row=1, column=1, sticky="w")

        ttk.Label(
            frame_opts, text="캡처 최대 깊이 (0=대상 폴더만, -1=제한 없음):"
        ).grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.max_depth_var = tk.StringVar(value="1")
        ttk.Entry(frame_opts, textvariable=self.max_depth_var, width=6).grid(row=2, column=1, sticky="w")

        ttk.Label(
            frame_opts, text="제외할 폴더 이름 패턴 - 목록/캡처 공통 (쉼표로 구분, * 사용 가능):"
        ).grid(row=3, column=0, sticky="w", padx=8, pady=4)
        self.exclude_patterns_var = tk.StringVar(value=", ".join(DEFAULT_EXCLUDE_PATTERNS))
        ttk.Entry(frame_opts, textvariable=self.exclude_patterns_var, width=40).grid(
            row=3, column=1, columnspan=2, sticky="we", padx=(0, 8)
        )

        frame_controls = ttk.Frame(self)
        frame_controls.pack(**pad)

        self.start_button = ttk.Button(frame_controls, text="시작", command=self._start)
        self.start_button.grid(row=0, column=0, padx=4)

        self.pause_button = ttk.Button(frame_controls, text="일시정지", command=self._toggle_pause)
        self.pause_button.state(["disabled"])
        self.pause_button.grid(row=0, column=1, padx=4)

        self.stop_button = ttk.Button(frame_controls, text="정지", command=self._stop)
        self.stop_button.state(["disabled"])
        self.stop_button.grid(row=0, column=2, padx=4)

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x", **pad)

        self.log_text = tk.Text(self, height=16, state="disabled")
        self.log_text.pack(fill="both", expand=True, **pad)

    def _browse_root(self):
        path = filedialog.askdirectory(title="대상 폴더 선택")
        if path:
            self.root_path_var.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="결과 저장 폴더 선택")
        if path:
            self.output_path_var.set(path)

    def _log(self, message):
        self.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _set_progress_max(self, maximum):
        self.after(0, lambda: self.progress.configure(maximum=max(maximum, 1), value=0))

    def _step_progress(self):
        self.after(0, self.progress.step, 1)

    def _set_running(self, running):
        def _update():
            self.start_button.state(["disabled" if running else "!disabled"])
            self.pause_button.state(["!disabled" if running else "disabled"])
            self.stop_button.state(["!disabled" if running else "disabled"])
            if not running:
                self.pause_button.configure(text="일시정지")

        self.after(0, _update)

    def _toggle_pause(self):
        if self.control is None:
            return
        if self.control.is_paused():
            self.control.resume()
            self.pause_button.configure(text="일시정지")
            self._log("작업을 재개합니다.")
        else:
            self.control.pause()
            self.pause_button.configure(text="재개")
            self._log("작업을 일시정지합니다.")

    def _stop(self):
        if self.control is None:
            return
        self.control.stop()
        self.stop_button.state(["disabled"])
        self._log("정지를 요청했습니다. 진행 중인 폴더 처리가 끝나는 대로 중지됩니다.")

    def _start(self):
        root_path = self.root_path_var.get().strip()
        output_path = self.output_path_var.get().strip()

        if not root_path or not os.path.isdir(root_path):
            messagebox.showerror("오류", "대상 폴더를 올바르게 선택해주세요.")
            return
        if not output_path:
            messagebox.showerror("오류", "결과 저장 폴더를 선택해주세요.")
            return
        try:
            max_depth = int(self.max_depth_var.get())
        except ValueError:
            messagebox.showerror("오류", "캡처 최대 깊이는 정수여야 합니다.")
            return

        exclude_patterns = [
            p.strip() for p in self.exclude_patterns_var.get().split(",") if p.strip()
        ]

        os.makedirs(output_path, exist_ok=True)

        self.control = JobControl()
        self._set_running(True)
        self.worker_thread = threading.Thread(
            target=self._run_job,
            args=(
                root_path,
                output_path,
                self.do_listing_var.get(),
                self.do_capture_var.get(),
                max_depth,
                exclude_patterns,
                self.control,
            ),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_job(self, root_path, output_path, do_listing, do_capture, max_depth, exclude_patterns, control):
        try:
            if exclude_patterns:
                self._log(f"제외 패턴 적용: {', '.join(exclude_patterns)}")

            if do_listing:
                self._log("폴더 목록을 생성하는 중...")
                listing_file = os.path.join(output_path, "directory_listing.txt")
                write_listing_report(
                    root_path, listing_file, max_depth=-1, control=control, exclude_patterns=exclude_patterns
                )
                self._log(f"폴더 목록 저장 완료: {listing_file}")

            if do_capture:
                if capture_folder is None:
                    self._log("이 운영체제에서는 창 스크린샷 캡처를 지원하지 않습니다.")
                else:
                    folders = build_folder_list(
                        root_path, max_depth=max_depth, control=control, exclude_patterns=exclude_patterns
                    )
                    screenshots_dir = os.path.join(output_path, "screenshots")
                    os.makedirs(screenshots_dir, exist_ok=True)

                    self._set_progress_max(len(folders))
                    for folder_path, _depth in folders:
                        control.checkpoint()
                        save_path = capture_save_path(root_path, folder_path, screenshots_dir)
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        self._log(f"캡처 중: {folder_path}")
                        try:
                            capture_folder(folder_path, save_path)
                            self._log(f"  -> 저장: {save_path}")
                        except ExplorerCaptureError as exc:
                            self._log(f"  -> 실패: {exc}")
                        self._step_progress()

            self._log("작업이 완료되었습니다.")
        except JobCancelled:
            self._log("사용자 요청으로 작업이 중지되었습니다.")
        except Exception as exc:
            self._log(f"오류 발생: {exc}")
        finally:
            self.control = None
            self._set_running(False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
