"""폴더 구조를 텍스트로 목록화하는 모듈."""
import fnmatch
import os

DEFAULT_EXCLUDE_PATTERNS = [".*"]


def is_excluded(name, exclude_patterns):
    """폴더 이름이 제외 패턴(glob, 예: '.*', 'node_modules') 중 하나와 일치하는지 확인한다."""
    return any(fnmatch.fnmatch(name, pattern) for pattern in exclude_patterns)


def build_folder_list(root_path, max_depth=-1, control=None, exclude_patterns=None):
    """root_path 및 그 하위 폴더들을 (경로, depth) 튜플 리스트로 반환한다.

    max_depth가 -1이면 무제한, 0이면 root_path 자신만 포함한다.
    control이 주어지면 폴더를 순회할 때마다 control.checkpoint()를 호출해
    일시정지/중지 요청에 응답한다.
    exclude_patterns에 이름이 일치하는 폴더는 결과와 하위 탐색에서 모두 제외된다.
    """
    root_path = os.path.abspath(root_path)
    root_depth = root_path.rstrip(os.sep).count(os.sep)
    exclude_patterns = exclude_patterns or []
    folders = [(root_path, 0)]

    for current_dir, dirnames, _ in os.walk(root_path):
        if control is not None:
            control.checkpoint()
        dirnames[:] = [name for name in dirnames if not is_excluded(name, exclude_patterns)]
        depth = current_dir.rstrip(os.sep).count(os.sep) - root_depth
        if max_depth != -1 and depth >= max_depth:
            dirnames[:] = []
            continue
        dirnames.sort()
        for name in dirnames:
            folders.append((os.path.join(current_dir, name), depth + 1))

    return folders


def write_listing_report(root_path, output_file, max_depth=-1, control=None, exclude_patterns=None):
    """root_path 하위 폴더/파일 구조를 tree 명령과 같은 트리 형태로 저장한다.

    exclude_patterns에 이름이 일치하는 폴더는 하위 내용과 함께 목록에서 제외된다.
    """
    root_path = os.path.abspath(root_path)
    exclude_patterns = exclude_patterns or []
    with open(output_file, "w", encoding="utf-8-sig") as f:
        f.write(f"{os.path.basename(root_path) or root_path}\n")
        _write_tree(root_path, prefix="", depth=0, max_depth=max_depth, f=f, control=control, exclude_patterns=exclude_patterns)


def _write_tree(dir_path, prefix, depth, max_depth, f, control, exclude_patterns):
    if control is not None:
        control.checkpoint()

    try:
        entries = sorted(os.listdir(dir_path), key=str.lower)
    except OSError as exc:
        f.write(f"{prefix}└── (읽기 실패: {exc})\n")
        return

    dir_names = [
        name for name in entries
        if os.path.isdir(os.path.join(dir_path, name)) and not is_excluded(name, exclude_patterns)
    ]
    file_names = [name for name in entries if not os.path.isdir(os.path.join(dir_path, name))]
    items = [(name, True) for name in dir_names] + [(name, False) for name in file_names]

    last_index = len(items) - 1
    for i, (name, is_dir) in enumerate(items):
        is_last = i == last_index
        connector = "└── " if is_last else "├── "
        full_path = os.path.join(dir_path, name)

        if is_dir:
            f.write(f"{prefix}{connector}{name}\n")
            if max_depth == -1 or depth < max_depth:
                child_prefix = prefix + ("    " if is_last else "│   ")
                _write_tree(full_path, child_prefix, depth + 1, max_depth, f, control, exclude_patterns)
        else:
            try:
                size_str = f"{os.path.getsize(full_path):,} bytes"
            except OSError:
                size_str = "크기 확인 불가"
            f.write(f"{prefix}{connector}{name} ({size_str})\n")
