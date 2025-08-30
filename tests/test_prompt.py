from hecto import ask, confirm


def test_ask(stdin, capsys):
    """Test basic ask functionality."""
    question = "What is your name?"
    name = "Inigo Montoya"

    stdin.append(name + "\n")
    response = ask(question, default="")

    stdout, _ = capsys.readouterr()
    assert response == name
    assert stdout == question


def test_ask_no_response(stdin, capsys):
    """Asks with no response should ask again."""
    question = "What is your name?"
    name = "Inigo Montoya"

    stdin.append("\n" + name + "\n")
    response = ask(question)

    stdout, _ = capsys.readouterr()
    assert response == name
    assert stdout == question * 2


def test_ask_default_no_input(stdin, capsys):
    """Asks with default and no response should use default."""
    question = "What is your name?"
    default = "The Nameless One"

    stdin.append("\n")
    response = ask(question, default=default)

    out, _ = capsys.readouterr()
    assert response == default
    assert out == f"{question} [{default}] "


def test_ask_default_overridden(stdin, capsys):
    """Asks with default and response should use response."""
    question = "What is your name?"
    default = "The Nameless One"
    name = "Buttercup"

    stdin.append(name + "\n")
    response = ask(question, default=default)

    out, _ = capsys.readouterr()
    assert response == name
    assert out == f"{question} [{default}] "


def test_confirm(stdin, capsys):
    question = "Are you sure?"
    stdin.append("yes\n")
    response = confirm(question)
    stdout, _ = capsys.readouterr()
    assert response is True
    assert stdout == f"{question} [y/N] "


def test_confirm_false(stdin, capsys):
    question = "Are you sure?"
    stdin.append("n\n")
    response = confirm(question)
    stdout, _ = capsys.readouterr()
    assert response is False
    assert stdout == f"{question} [y/N] "


def test_confirm_default_true(stdin, capsys):
    question = "Are you sure?"
    stdin.append("\n")
    response = confirm(question, default=True)
    stdout, _ = capsys.readouterr()
    assert response is True
    assert stdout == f"{question} [Y/n] "


def test_confirm_default_false(stdin, capsys):
    question = "Are you sure?"
    stdin.append("\n")
    response = confirm(question, default=False)
    stdout, _ = capsys.readouterr()
    assert response is False
    assert stdout == f"{question} [y/N] "
