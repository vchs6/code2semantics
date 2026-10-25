"""版本标识（design 决策 3 + spec「按来源项目版本判定命中」）。

- Git 仓库：当前 commit（git rev-parse HEAD）。
- 非 Git 本地文件夹：内容指纹（视为"始终当前版本"）。

指纹算法属 design Q1（未回填）；本实现采用最保守的全文件哈希 + 目录结构，
并显式标注该暂态，待有限调研后回填固化。
"""
import hashlib
import subprocess
from pathlib import Path


def git_head(project):
    try:
        out = subprocess.run(
            ["git", "-C", str(project), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return None


def folder_fingerprint(project):
    """最保守：全文件内容哈希（Q1 未回填的暂态算法）。"""
    root = Path(project)
    if not root.is_dir():
        return None
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            h.update(rel.encode("utf-8"))
            h.update(p.read_bytes())
    return f"fp:{h.hexdigest()[:16]}"


def current_version(project):
    """当前版本：Git commit 优先，非 Git 回退内容指纹。"""
    head = git_head(project)
    if head:
        return head
    return folder_fingerprint(project)
