import typing as t
from enum import IntEnum
from pathlib import Path

import jinja2


__all__ = (
    "COLORS",
    "JinjaRender",
    "printf",
)


class COLORS(IntEnum):
  RED = 31
  GREEN = 32
  YELLOW = 33
  BLUE = 34
  MAGENTA = 35
  CYAN = 36
  LIGHT_GRAY = 37
  DEFAULT = 39
  DARK_GRAY = 90
  LIGHT_RED = 91
  LIGHT_GREEN = 92
  LIGHT_YELLOW = 93
  LIGHT_BLUE = 94
  LIGHT_MAGENTA = 95
  LIGHT_CYAN = 96
  WHITE = 97

  OK = GREEN
  CONFLICT = RED
  WARNING = YELLOW


class JinjaRender:
    def __init__(self, templates: str | Path, **envops) -> None:
        self.loader = jinja2.FileSystemLoader(str(templates))
        self.env = jinja2.Environment(
            loader=self.loader,
            autoescape=jinja2.select_autoescape(default=True),
            **envops,
        )
        self.env.globals["render"] = self.render

    @property
    def globals(self) -> dict:
        return self.env.globals

    @property
    def filters(self) -> dict:
        return self.env.filters

    @property
    def tests(self) -> dict:
        return self.env.tests

    def __call__(self, relpath: str | Path, **context) -> str:
        return self.render(relpath, **context)

    def string(self, string: str, **context) -> str:
        tmpl = self.env.from_string(string)
        return tmpl.render(**context)

    def render(self, relpath: str | Path, **context) -> str:
        tmpl = self.env.get_template(str(relpath))
        return tmpl.render(**context)


def printf(
    verb: str,
    msg: t.Any = "",
    color: int = COLORS.CYAN,
    indent: int = 10,
) -> None:
    verb = f"\033[{color}m{verb}\033[0m".rjust(indent, " ")
    print(f"{verb}  {msg}".rstrip())


