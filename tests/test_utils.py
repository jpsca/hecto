from hecto.utils import JinjaRender, printf


def test_jinja_render_call(tmp_path):
    (tmp_path / "hello.txt").write_text("Hello, {{ name }}!")
    render = JinjaRender(tmp_path)
    result = render("hello.txt", name="World")
    assert result == "Hello, World!"


def test_jinja_render_filters_property(tmp_path):
    render = JinjaRender(tmp_path)
    filters = render.filters
    assert isinstance(filters, dict)


def test_jinja_render_tests_property(tmp_path):
    render = JinjaRender(tmp_path)
    tests = render.tests
    assert isinstance(tests, dict)


def test_jinja_render_no_autoescape(tmp_path):
    """Templates should not HTML-escape content."""
    (tmp_path / "data.txt").write_text("{{ value }}")
    render = JinjaRender(tmp_path)
    result = render("data.txt", value="Tom & Jerry <3")
    assert result == "Tom & Jerry <3"


def test_printf_alignment(capsys):
    printf("create", "file.txt")
    captured = capsys.readouterr()
    assert "create" in captured.out
    assert "file.txt" in captured.out
