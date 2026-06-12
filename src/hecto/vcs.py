import atexit
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


__all__ = (
    "get_repo",
    "split_ref",
    "clone",
)

GIT_PREFIX = ("git@", "git://", "git+", "gh:", "gl:")
GIT_POSTFIX = (".git",)

RE_GITHUB = re.compile(r"^gh:/?")
RE_GITLAB = re.compile(r"^gl:/?")


def get_repo(url: str | Path) -> str | None:
    url = str(url)
    base, _ = split_ref(url)
    if not (base.endswith(GIT_POSTFIX) or base.startswith(GIT_PREFIX)):
        return None

    if url.startswith("git+"):
        url = url[4:]

    url = re.sub(RE_GITHUB, "https://github.com/", url)
    url = re.sub(RE_GITLAB, "https://gitlab.com/", url)
    return url


def split_ref(url: str) -> tuple[str, str]:
    """Split an optional `@ref` suffix from a git URL.

    The ref can be a branch, tag, or commit, e.g.:
    `https://github.com/jpsca/hecto.git@v2.0` -> (`https://github.com/jpsca/hecto.git`, `v2.0`)
    Only URLs ending in `.git` can carry a ref, so the `@` in SSH
    URLs like `git@github.com:user/repo.git` is never mistaken for one.
    """
    base, _, ref = url.rpartition("@")
    if base.endswith(GIT_POSTFIX):
        return base, ref
    return url, ""


def clone(url: str) -> str:
    url, ref = split_ref(url)
    location = tempfile.mkdtemp()
    subprocess.check_call(["git", "clone", url, location])
    if ref:
        subprocess.check_call(["git", "-C", location, "checkout", "--quiet", ref])
    git_folder = os.path.join(location, ".git")
    shutil.rmtree(git_folder)
    atexit.register(shutil.rmtree, location, True)
    return location
