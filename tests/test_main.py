from pathlib import Path

import pytest

from hecto.main import (
    append_to_file,
    confirm_overwrite,
    contents_are_identical,
    copy_file,
    delete_file,
    files_are_identical,
    get_src,
    make_folder,
    must_ignore,
    prepend_to_file,
    render_blueprint,
    save_file,
)


# --- get_src ---


def test_get_src(mocker):
    mock_clone = mocker.patch("hecto.main.vcs.clone")
    src = get_src("https://github.com/jpsca/hecto.git#blueprint/new")
    mock_clone.assert_called_once_with("https://github.com/jpsca/hecto.git")
    assert str(src).endswith("/blueprint/new")


def test_get_src_git_url_without_fragment(mocker):
    """Git URL without a '#' fragment should clone and return the root."""
    mock_clone = mocker.patch("hecto.main.vcs.clone", return_value="/tmp/cloned")
    src = get_src("https://github.com/jpsca/hecto.git")
    mock_clone.assert_called_once_with("https://github.com/jpsca/hecto.git")
    assert src == Path("/tmp/cloned")


def test_get_src_local_path_with_hash(tmp_path):
    """Local paths containing '#' should not be split."""
    path = tmp_path / "project#2"
    path.mkdir()
    result = get_src(str(path))
    assert result == path


# --- must_ignore ---


def test_must_ignore_matches_name(tmp_path):
    assert must_ignore(Path("__pycache__"), ("__pycache__",)) is True


def test_must_ignore_matches_pattern(tmp_path):
    assert must_ignore(Path("sub/__pycache__"), ("*/__pycache__",)) is True


def test_must_ignore_no_match():
    assert must_ignore(Path("src/main.py"), ("__pycache__", ".DS_Store")) is False


# --- make_folder ---


def test_make_folder_creates_subfolder(tmp_path, capsys):
    make_folder(tmp_path, "new_sub")
    assert (tmp_path / "new_sub").is_dir()
    captured = capsys.readouterr()
    assert "create" in captured.out
    assert "new_sub" in captured.out


def test_make_folder_existing(tmp_path, capsys):
    (tmp_path / "existing").mkdir()
    make_folder(tmp_path, "existing")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_make_folder_root(tmp_path, capsys):
    # When rel_folder resolves to root_path itself, no print
    dst = tmp_path / "output"
    make_folder(dst, ".")
    assert dst.is_dir()
    captured = capsys.readouterr()
    assert captured.out == ""


# --- copy_file ---


def test_copy_file_new(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("hello")
    dst = tmp_path / "dst"
    dst.mkdir()

    copy_file(src / "a.txt", dst, "a.txt")
    assert (dst / "a.txt").read_text() == "hello"
    captured = capsys.readouterr()
    assert "create" in captured.out


def test_copy_file_identical(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("hello")
    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "a.txt").write_text("hello")

    copy_file(src / "a.txt", dst, "a.txt")
    captured = capsys.readouterr()
    assert "identical" in captured.out


def test_copy_file_overwrite(tmp_path, stdin, capsys):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("new content")
    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "a.txt").write_text("old content")

    stdin.append("y\n")
    copy_file(src / "a.txt", dst, "a.txt")
    assert (dst / "a.txt").read_text() == "new content"
    captured = capsys.readouterr()
    assert "conflict" in captured.out
    assert "update" in captured.out


def test_copy_file_skip(tmp_path, stdin, capsys):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("new content")
    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "a.txt").write_text("old content")

    stdin.append("n\n")
    copy_file(src / "a.txt", dst, "a.txt")
    assert (dst / "a.txt").read_text() == "old content"
    captured = capsys.readouterr()
    assert "skipped" in captured.out


def test_copy_file_force(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("new content")
    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "a.txt").write_text("old content")

    copy_file(src / "a.txt", dst, "a.txt", force=True)
    assert (dst / "a.txt").read_text() == "new content"
    captured = capsys.readouterr()
    assert "update" in captured.out


# --- append_to_file ---


def test_append_to_file_new(tmp_path, capsys):
    append_to_file(tmp_path, "new.txt", "content\n")
    assert (tmp_path / "new.txt").read_text() == "content\n"
    captured = capsys.readouterr()
    assert "create" in captured.out


def test_append_to_file_existing(tmp_path, capsys):
    (tmp_path / "f.txt").write_text("line1\n")
    append_to_file(tmp_path, "f.txt", "line2\n")
    assert (tmp_path / "f.txt").read_text() == "line1\nline2\n"
    captured = capsys.readouterr()
    assert "append" in captured.out


def test_append_to_file_existing_no_trailing_newline(tmp_path, capsys):
    (tmp_path / "f.txt").write_text("line1")
    append_to_file(tmp_path, "f.txt", "line2\n")
    assert (tmp_path / "f.txt").read_text() == "line1\nline2\n"


def test_append_to_file_duplicate(tmp_path, capsys):
    (tmp_path / "f.txt").write_text("already here\n")
    append_to_file(tmp_path, "f.txt", "already here\n")
    assert (tmp_path / "f.txt").read_text() == "already here\n"
    captured = capsys.readouterr()
    assert "skipped" in captured.out


# --- prepend_to_file ---


def test_prepend_to_file_new(tmp_path, capsys):
    prepend_to_file(tmp_path, "new.txt", "content\n")
    assert (tmp_path / "new.txt").read_text() == "content\n"
    captured = capsys.readouterr()
    assert "create" in captured.out


def test_prepend_to_file_existing(tmp_path, capsys):
    (tmp_path / "f.txt").write_text("line2\n")
    prepend_to_file(tmp_path, "f.txt", "line1\n")
    assert (tmp_path / "f.txt").read_text() == "line1\nline2\n"
    captured = capsys.readouterr()
    assert "prepend" in captured.out


def test_prepend_to_file_no_trailing_newline(tmp_path, capsys):
    (tmp_path / "f.txt").write_text("line2\n")
    prepend_to_file(tmp_path, "f.txt", "line1")
    assert (tmp_path / "f.txt").read_text() == "line1\nline2\n"


def test_prepend_to_file_duplicate(tmp_path, capsys):
    (tmp_path / "f.txt").write_text("already here\n")
    prepend_to_file(tmp_path, "f.txt", "already here\n")
    assert (tmp_path / "f.txt").read_text() == "already here\n"
    captured = capsys.readouterr()
    assert "skipped" in captured.out


# --- delete_file ---


def test_delete_file_existing(tmp_path, capsys):
    target = tmp_path / "hello.txt"
    target.write_text("some content")
    assert target.exists()

    delete_file(tmp_path, "hello.txt")

    assert not target.exists()
    captured = capsys.readouterr()
    assert "delete" in captured.out


def test_delete_file_nonexistent(tmp_path, capsys):
    delete_file(tmp_path, "missing.txt")

    assert not (tmp_path / "missing.txt").exists()
    captured = capsys.readouterr()
    assert "skipped" in captured.out


# --- save_file ---


def test_save_file_new(tmp_path, capsys):
    save_file(tmp_path, "new.txt", "hello\n")
    assert (tmp_path / "new.txt").read_text() == "hello\n"
    captured = capsys.readouterr()
    assert "create" in captured.out


def test_save_file_identical(tmp_path, capsys):
    (tmp_path / "f.txt").write_text("hello\n")
    save_file(tmp_path, "f.txt", "hello\n")
    captured = capsys.readouterr()
    assert "identical" in captured.out


def test_save_file_overwrite(tmp_path, stdin, capsys):
    (tmp_path / "f.txt").write_text("old\n")
    stdin.append("y\n")
    save_file(tmp_path, "f.txt", "new\n")
    assert (tmp_path / "f.txt").read_text() == "new\n"
    captured = capsys.readouterr()
    assert "update" in captured.out


def test_save_file_skip(tmp_path, stdin, capsys):
    (tmp_path / "f.txt").write_text("old\n")
    stdin.append("n\n")
    save_file(tmp_path, "f.txt", "new\n")
    assert (tmp_path / "f.txt").read_text() == "old\n"
    captured = capsys.readouterr()
    assert "skipped" in captured.out


def test_save_file_force(tmp_path, capsys):
    (tmp_path / "f.txt").write_text("old\n")
    save_file(tmp_path, "f.txt", "new\n", force=True)
    assert (tmp_path / "f.txt").read_text() == "new\n"
    captured = capsys.readouterr()
    assert "update" in captured.out


# --- files_are_identical / contents_are_identical ---


def test_files_are_identical_true(tmp_path):
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "b.txt").write_text("same")
    assert files_are_identical(tmp_path / "a.txt", tmp_path / "b.txt") is True


def test_files_are_identical_false(tmp_path):
    (tmp_path / "a.txt").write_text("one")
    (tmp_path / "b.txt").write_text("two")
    assert files_are_identical(tmp_path / "a.txt", tmp_path / "b.txt") is False


def test_contents_are_identical_true(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    assert contents_are_identical("hello", tmp_path / "a.txt") is True


def test_contents_are_identical_false(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    assert contents_are_identical("world", tmp_path / "a.txt") is False


# --- confirm_overwrite ---


def test_confirm_overwrite_force(capsys):
    result = confirm_overwrite("f.txt", force=True)
    assert result is True
    captured = capsys.readouterr()
    assert "conflict" in captured.out


def test_confirm_overwrite_yes(stdin, capsys):
    stdin.append("y\n")
    result = confirm_overwrite("f.txt")
    assert result is True


def test_confirm_overwrite_no(stdin, capsys):
    stdin.append("n\n")
    result = confirm_overwrite("f.txt")
    assert result is False


# --- render_blueprint integration ---


def test_render_blueprint_invalid_src(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        render_blueprint(tmp_path / "nonexistent", tmp_path / "dst")


def test_render_blueprint_tt_template(tmp_path):
    src = tmp_path / "blueprint"
    src.mkdir()
    (src / "greeting.txt.tt").write_text("Hello, [[ name ]]!\n")

    dst = tmp_path / "output"
    dst.mkdir()

    render_blueprint(src, dst, {"name": "World"})
    assert (dst / "greeting.txt").read_text() == "Hello, World!\n"


def test_render_blueprint_tt_mid_extension(tmp_path):
    src = tmp_path / "blueprint"
    src.mkdir()
    (src / "config.tt.json").write_text('{"key": "[[ value ]]"}\n')

    dst = tmp_path / "output"
    dst.mkdir()

    render_blueprint(src, dst, {"value": "42"})
    assert (dst / "config.json").read_text() == '{"key": "42"}\n'


def test_render_blueprint_append(tmp_path):
    src = tmp_path / "blueprint"
    src.mkdir()
    (src / "log.txt.append").write_text("new line\n")

    dst = tmp_path / "output"
    dst.mkdir()
    (dst / "log.txt").write_text("existing\n")

    render_blueprint(src, dst)
    assert (dst / "log.txt").read_text() == "existing\nnew line\n"


def test_render_blueprint_prepend(tmp_path):
    src = tmp_path / "blueprint"
    src.mkdir()
    (src / "log.txt.prepend").write_text("first line\n")

    dst = tmp_path / "output"
    dst.mkdir()
    (dst / "log.txt").write_text("second line\n")

    render_blueprint(src, dst)
    assert (dst / "log.txt").read_text() == "first line\nsecond line\n"


def test_render_blueprint_copy(tmp_path):
    src = tmp_path / "blueprint"
    src.mkdir()
    (src / "plain.txt").write_text("just copy me")

    dst = tmp_path / "output"
    dst.mkdir()

    render_blueprint(src, dst)
    assert (dst / "plain.txt").read_text() == "just copy me"


def test_render_blueprint_delete(tmp_path):
    src = tmp_path / "blueprint"
    src.mkdir()
    (src / "remove_me.txt.delete").write_text("")

    dst = tmp_path / "output"
    dst.mkdir()
    (dst / "remove_me.txt").write_text("I should be deleted")

    render_blueprint(src, dst)
    assert not (dst / "remove_me.txt").exists()


def test_render_blueprint_delete_missing(tmp_path, capsys):
    src = tmp_path / "blueprint"
    src.mkdir()
    (src / "nonexistent.txt.delete").write_text("")

    dst = tmp_path / "output"
    dst.mkdir()

    render_blueprint(src, dst)
    assert not (dst / "nonexistent.txt").exists()
    captured = capsys.readouterr()
    assert "skipped" in captured.out


def test_render_blueprint_delete_mid_extension(tmp_path):
    src = tmp_path / "blueprint"
    src.mkdir()
    (src / "config.delete.json").write_text("")

    dst = tmp_path / "output"
    dst.mkdir()
    (dst / "config.json").write_text("old config")

    render_blueprint(src, dst)
    assert not (dst / "config.json").exists()


def test_render_blueprint_ignore_folder(tmp_path, capsys):
    src = tmp_path / "blueprint"
    src.mkdir()
    pycache = src / "__pycache__"
    pycache.mkdir()
    (pycache / "cached.pyc").write_bytes(b"\x00")
    (src / "keep.txt").write_text("keep")

    dst = tmp_path / "output"
    dst.mkdir()

    render_blueprint(src, dst)
    assert (dst / "keep.txt").exists()
    assert not (dst / "__pycache__").exists()


def test_render_blueprint_ignore_file(tmp_path, capsys):
    src = tmp_path / "blueprint"
    src.mkdir()
    (src / ".DS_Store").write_bytes(b"\x00")
    (src / "keep.txt").write_text("keep")

    dst = tmp_path / "output"
    dst.mkdir()

    render_blueprint(src, dst)
    assert (dst / "keep.txt").exists()
    assert not (dst / ".DS_Store").exists()


def test_render_blueprint_subfolder(tmp_path, capsys):
    src = tmp_path / "blueprint"
    sub = src / "subdir"
    sub.mkdir(parents=True)
    (sub / "file.txt").write_text("nested")

    dst = tmp_path / "output"
    dst.mkdir()

    render_blueprint(src, dst)
    assert (dst / "subdir" / "file.txt").read_text() == "nested"
    captured = capsys.readouterr()
    assert "subdir" in captured.out


def test_render_blueprint_force_copy(tmp_path, capsys):
    src = tmp_path / "blueprint"
    src.mkdir()
    (src / "f.txt").write_text("new")

    dst = tmp_path / "output"
    dst.mkdir()
    (dst / "f.txt").write_text("old")

    render_blueprint(src, dst, force=True)
    assert (dst / "f.txt").read_text() == "new"
