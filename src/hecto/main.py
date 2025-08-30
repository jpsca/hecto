import filecmp
import os
import shutil
import typing as t
from collections.abc import Sequence
from fnmatch import fnmatch
from pathlib import Path

import isort
import jinja2

from . import vcs
from .prompt import confirm
from .utils import COLORS, JinjaRender, printf


__all__ = (
    "render_blueprint",
    "sort_imports",
    "sort_imports_in",
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

    For each file, if the file has a `.tt`, `.append`, or `.prepend` extension,
    even if the extension is not the *last one*, like `*.tt.py`, it will be treated
    as a template file and rendered with the provided context.

    * `.tt` files will be rendered and saved to its destinations.
    * `.append` files will be rendered and appended to its destinations.
    * `.prepend` files will be rendered and prepended to its destinations.
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
        envops:
            Jinja2 environment options.
        force:
            Whether to overwrite existing files without asking for confirmation.

    """
    repo = vcs.get_repo(src)
    if repo:
        src = vcs.clone(repo)

    src = Path(src)
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
    envops["undefined"] = jinja2.StrictUndefined
    render = JinjaRender(src, **(envops or {}))
    render.globals.update(context or {})

    for folder, _, files in os.walk(src):
        folder = Path(folder)
        if must_ignore(folder, ignore):
            return
        _src_relfolder = str(folder).replace(str(src), "", 1).lstrip(os.path.sep)
        _dst_relfolder = render.string(_src_relfolder)
        src_relfolder = Path(_src_relfolder)
        dst_relfolder = Path(_dst_relfolder)

        make_folder(dst, dst_relfolder)

        for name in files:
            src_relpath = src_relfolder / name
            if must_ignore(src_relpath, ignore):
                continue
            name = render.string(name)

            if ".tt." in name or name.endswith(".tt"):
                dst_name = name.replace(".tt", "")
                dst_relpath = dst_relfolder / dst_name
                content = render(src_relpath)
                save_file(dst, dst_relpath, content, force=force)
            elif ".append." in name or name.endswith(".append"):
                dst_name = name.replace(".append", "")
                dst_relpath = dst_relfolder / dst_name
                content = render(src_relpath)
                append_to_file(dst, dst_relpath, content)
            elif ".prepend." in name or name.endswith(".prepend"):
                dst_name = name.replace(".prepend", "")
                dst_relpath = dst_relfolder / dst_name
                content = render(src_relpath)
                prepend_to_file(dst, dst_relpath, content)
            else:
                dst_relpath = dst_relfolder / name
                copy_file(src / src_relpath, dst, dst_relpath)


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

    rel_folder = str(rel_folder).rstrip(".")
    display = f"{rel_folder}{os.path.sep}"
    path.mkdir(parents=True, exist_ok=False)
    if rel_folder:
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

    shutil.copy2(str(src_path), str(dst_path))


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
    return filecmp.cmp(str(src_path), str(dst_path), shallow=False)


def contents_are_identical(content: str, dst_path: Path) -> bool:
    return content == dst_path.read_text()


def confirm_overwrite(dst_relpath: str | Path, *, force=False) -> bool:
    printf("conflict", dst_relpath, color=COLORS.CONFLICT)
    if force:
        return True
    return confirm(" Overwrite?")


def sort_imports(code: str) -> str:
    """
    Sort imports in the given code.
    """
    return isort.code(
        code,
        float_to_top=True,
        use_parentheses=True,
        lines_after_imports=2,
        combine_star=True,
        include_trailing_comma=True,
    )


def sort_imports_in(path: Path) -> None:
    """
    Sort imports in the given file.
    """
    code = sort_imports(path.read_text())
    path.write_text(code)
