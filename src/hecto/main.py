import filecmp
import os
import shutil
import typing as t
from collections.abc import Sequence
from fnmatch import fnmatch
from pathlib import Path

import jinja2

from . import vcs
from .prompt import confirm
from .utils import COLORS, JinjaRender, printf


__all__ = (
    "render_blueprint",
)

IGNORE = (
    ".DS_Store",
    "__pycache__",
    "*/__pycache__",
    "*/.DS_Store",
)


def render_blueprint(
    src: str | Path,
    dst: str | Path,
    context: dict[str, t.Any] | None = None,
    *,
    ignore: Sequence[str] = IGNORE,
    envops: dict | None = None,
    force: bool = False,
) -> None:
    """
    Renders a blueprint into a destination folder.

    For each file, if the file has a `.tt`, `.append`, `.prepend`, or `.delete`
    extension, even if the extension is not the *last one*, like `*.tt.py`, it will
    be treated as a special file.

    * `.tt` files will be rendered and saved to its destinations.
    * `.append` files will be rendered and appended to its destinations.
    * `.prepend` files will be rendered and prepended to its destinations.
    * `.delete` files will cause matching destination files to be deleted.
    * Other files will be copied as-is.

    To be able to work with regular Jinja files, the files are rendered using
    `[[` and `]]` instead of `{{` and `}}`; and `[%` and `%]` instead of `{%` and `%}`.
    You can also use these delimiters in your file names.

    If the files already exists and `force` is `False`, you will be asked for
    confirmation before overwriting them.

    Arguments:
        src:
            Path of the folder to render from, or URL of a git-based repository.
        dst:
            Destination path for the blueprint.
        context:
            Context variables for Jinja2 templates.
        ignore:
            List of file patterns to ignore.
            Default is (".DS_Store", "__pycache__", "*/__pycache__", "*/.DS_Store")
        envops:
            Jinja2 environment options.
        force:
            Whether to overwrite existing files without asking for confirmation.

    """
    src = get_src(src)
    if not src.is_dir():
        raise ValueError(f"Source directory '{src}' does not exist")

    dst = Path(dst)

    envops = envops or {}
    envops.setdefault("block_start_string", "[%")
    envops.setdefault("block_end_string", "%]")
    envops.setdefault("variable_start_string", "[[")
    envops.setdefault("variable_end_string", "]]")
    envops.setdefault("comment_start_string", "[#")
    envops.setdefault("comment_end_string", "#]")
    envops.setdefault("keep_trailing_newline", True)
    envops.setdefault("undefined", jinja2.StrictUndefined)
    render = JinjaRender(src, **envops)
    render.globals.update(context or {})

    for folder_str, dirnames, files in os.walk(src):
        folder = Path(folder_str)
        rel = folder.relative_to(src)
        dirnames[:] = [d for d in dirnames if not must_ignore(rel / d, ignore)]
        if must_ignore(rel, ignore):
            continue
        src_relfolder = rel
        dst_relfolder = Path(render.string(str(src_relfolder)))

        make_folder(dst, dst_relfolder)

        for name in files:
            src_relpath = src_relfolder / name
            if must_ignore(src_relpath, ignore):
                continue
            rendered_name = render.string(name)

            if ".tt." in rendered_name or rendered_name.endswith(".tt"):
                dst_name = rendered_name.replace(".tt", "", 1)
                dst_relpath = dst_relfolder / dst_name
                content = render(src_relpath)
                save_file(dst, dst_relpath, content, force=force)
            elif ".append." in rendered_name or rendered_name.endswith(".append"):
                dst_name = rendered_name.replace(".append", "", 1)
                dst_relpath = dst_relfolder / dst_name
                content = render(src_relpath)
                append_to_file(dst, dst_relpath, content)
            elif ".prepend." in rendered_name or rendered_name.endswith(".prepend"):
                dst_name = rendered_name.replace(".prepend", "", 1)
                dst_relpath = dst_relfolder / dst_name
                content = render(src_relpath)
                prepend_to_file(dst, dst_relpath, content)
            elif ".delete." in rendered_name or rendered_name.endswith(".delete"):
                dst_name = rendered_name.replace(".delete", "", 1)
                dst_relpath = dst_relfolder / dst_name
                delete_file(dst, dst_relpath)
            else:
                dst_relpath = dst_relfolder / rendered_name
                copy_file(src / src_relpath, dst, dst_relpath, force=force)


def get_src(src: str | Path) -> Path:
    src_str = str(src)
    src_path = ""

    if "#" in src_str:
        url_part, src_path = src_str.split("#", 1)
        repo = vcs.get_repo(url_part)
        if repo:
            return Path(vcs.clone(repo)) / src_path
        # Not a git URL — treat the whole string as a local path
        return Path(src)

    repo = vcs.get_repo(src_str)
    if repo:
        return Path(vcs.clone(repo))

    return Path(src)


def must_ignore(path: Path, ignore: Sequence[str]) -> bool:
    name = path.name
    str_path = str(path)
    for pattern in ignore:
        if fnmatch(name, pattern) or fnmatch(str_path, pattern):
            return True
    return False


def make_folder(root_path: Path, rel_folder: str | Path) -> None:
    path = root_path / rel_folder
    if path.exists():
        return

    path.mkdir(parents=True, exist_ok=True)
    if path != root_path:
        display = f"{rel_folder}{os.path.sep}"
        printf("create", display, color=COLORS.OK)


def copy_file(
    src_path: Path, root_path: Path, dst_relpath: str | Path, *, force=False
) -> None:
    dst_path = root_path / dst_relpath
    if dst_path.exists():
        if files_are_identical(src_path, dst_path):
            printf("identical", dst_relpath)
            return
        if not confirm_overwrite(dst_relpath, force=force):
            printf("skipped", dst_relpath, color=COLORS.WARNING)
            return
        printf("update", dst_relpath, color=COLORS.WARNING)
    else:
        printf("create", dst_relpath, color=COLORS.OK)

    shutil.copy2(src_path, dst_path)


def append_to_file(root_path: Path, dst_relpath: str | Path, new_content: str) -> None:
    dst_path = root_path / dst_relpath
    if dst_path.exists():
        curr_content = dst_path.read_text()
        if new_content in curr_content:
            printf("skipped", dst_relpath, color=COLORS.WARNING)
            return

        if not curr_content.endswith("\n"):
            curr_content += "\n"
        new_content = curr_content + new_content
        printf("append", dst_relpath, color=COLORS.WARNING)
    else:
        dst_path.touch(exist_ok=True)
        printf("create", dst_relpath, color=COLORS.OK)

    dst_path.write_text(new_content)


def prepend_to_file(root_path: Path, dst_relpath: str | Path, new_content: str) -> None:
    dst_path = root_path / dst_relpath
    if dst_path.exists():
        curr_content = dst_path.read_text()
        if new_content in curr_content:
            printf("skipped", dst_relpath, color=COLORS.WARNING)
            return

        if not new_content.endswith("\n"):
            new_content += "\n"
        new_content = new_content + curr_content
        printf("prepend", dst_relpath, color=COLORS.WARNING)
    else:
        dst_path.touch(exist_ok=True)
        printf("create", dst_relpath, color=COLORS.OK)

    dst_path.write_text(new_content)


def delete_file(root_path: Path, dst_relpath: str | Path) -> None:
    dst_path = root_path / dst_relpath
    if dst_path.exists():
        dst_path.unlink()
        printf("delete", dst_relpath, color=COLORS.WARNING)
    else:
        printf("skipped", dst_relpath, color=COLORS.WARNING)


def save_file(
    root_path: Path, dst_relpath: str | Path, content: str, *, force=False
) -> None:
    dst_path = root_path / dst_relpath
    if dst_path.exists():
        if contents_are_identical(content, dst_path):
            printf("identical", dst_relpath)
            return
        if not confirm_overwrite(dst_relpath, force=force):
            printf("skipped", dst_relpath, color=COLORS.WARNING)
            return
        printf("update", dst_relpath, color=COLORS.WARNING)
    else:
        printf("create", dst_relpath, color=COLORS.OK)

    dst_path.write_text(content)


def files_are_identical(src_path: Path, dst_path: Path) -> bool:
    return filecmp.cmp(src_path, dst_path, shallow=False)


def contents_are_identical(content: str, dst_path: Path) -> bool:
    return content == dst_path.read_text()


def confirm_overwrite(dst_relpath: str | Path, *, force=False) -> bool:
    printf("conflict", dst_relpath, color=COLORS.CONFLICT)
    if force:
        return True
    return confirm(" Overwrite?")
