import shutil
import subprocess
from os.path import exists, join
from pathlib import Path

from hecto import vcs


def test_get_repo():
    get = vcs.get_repo

    assert get("git@git.myproject.org:MyProject") == "git@git.myproject.org:MyProject"
    assert get("git://git.myproject.org/MyProject") == "git://git.myproject.org/MyProject"
    assert get("https://github.com/jpsca/hecto.git") == "https://github.com/jpsca/hecto.git"
    assert get("gh:/jpsca/hecto.git") == "https://github.com/jpsca/hecto.git"
    assert get("gh:jpsca/hecto.git") == "https://github.com/jpsca/hecto.git"
    assert get("gl:jpsca/hecto.git") == "https://gitlab.com/jpsca/hecto.git"
    assert get("git+https://git.myproject.org/MyProject") == "https://git.myproject.org/MyProject"
    assert get("git+ssh://git.myproject.org/MyProject") == "ssh://git.myproject.org/MyProject"
    assert get("git://git.myproject.org/MyProject.git@master")
    assert get("git://git.myproject.org/MyProject.git@v1.0")
    assert get("git://git.myproject.org/MyProject.git@da39a3ee5e6b4b0d3255bfef956018")

    # gh:/gl: shorthand without .git suffix
    assert get("gh:jpsca/hecto") == "https://github.com/jpsca/hecto"
    assert get("gl:jpsca/hecto") == "https://gitlab.com/jpsca/hecto"
    assert get("gh:/jpsca/hecto") == "https://github.com/jpsca/hecto"

    assert get("http://google.com") is None
    assert get("git.myproject.org/MyProject") is None


def test_split_ref():
    split = vcs.split_ref

    assert split("https://github.com/jpsca/hecto.git") == ("https://github.com/jpsca/hecto.git", "")
    assert split("https://github.com/jpsca/hecto.git@v2.0") == ("https://github.com/jpsca/hecto.git", "v2.0")
    assert split("git@github.com:jpsca/hecto.git") == ("git@github.com:jpsca/hecto.git", "")
    assert split("git@github.com:jpsca/hecto.git@main") == ("git@github.com:jpsca/hecto.git", "main")
    assert split("gh:jpsca/hecto.git@v2.0") == ("gh:jpsca/hecto.git", "v2.0")
    assert split("/local/path") == ("/local/path", "")


def test_get_repo_with_ref():
    get = vcs.get_repo

    assert get("https://github.com/jpsca/hecto.git@v2.0") == "https://github.com/jpsca/hecto.git@v2.0"
    assert get("gh:jpsca/hecto.git@v2.0") == "https://github.com/jpsca/hecto.git@v2.0"


def test_clone():
    tmp = vcs.clone("https://github.com/jpsca/hecto.git")
    assert tmp
    assert exists(join(tmp, "pyproject.toml"))
    shutil.rmtree(tmp)


def test_clone_at_ref(tmp_path):
    src = tmp_path / "repo.git"
    subprocess.check_call(["git", "init", "--quiet", str(src)])

    def run(*cmd):
        subprocess.check_call(
            ["git", "-C", str(src), "-c", "user.email=test@test", "-c", "user.name=test", *cmd]
        )

    (src / "file.txt").write_text("one")
    run("add", ".")
    run("commit", "--quiet", "-m", "one")
    run("tag", "v1")
    (src / "file.txt").write_text("two")
    run("add", ".")
    run("commit", "--quiet", "-m", "two")

    tagged = vcs.clone(f"{src}@v1")
    assert (Path(tagged) / "file.txt").read_text() == "one"

    head = vcs.clone(str(src))
    assert (Path(head) / "file.txt").read_text() == "two"
