<h1>
<img src="https://raw.githubusercontent.com/jpsca/hecto/refs/heads/main/hecto.png" align="middle" />
Hecto<sup>(graph)</sup>
</h1>

A **library** for rendering projects templates.

* Works with **local** paths and **git URLs**.
* Your project can include any file and **Hecto** can dynamically replace values in any kind of text files.
* It generates a beautiful output and take care of not overwrite existing files, unless instructed to do so.


## How to use

```bash
pip install hecto
```

```python
from hecto import render_blueprint

# Create a project from a local path
render_blueprint('path/to/project/template', 'path/to/destination', context={"foo": "bar"})

# Or from a git URL.
# You can also use "gh:" as a shortcut of "https://github.com/"
# Or "gl:"  as a shortcut of "https://gitlab.com/"
render_blueprint('https://github.com/jpsca/base36.git', 'path/to/destination')
render_blueprint('gh:jpsca/base36.git', 'path/to/destination')
render_blueprint('gl:jpsca/base36.git', 'path/to/destination')

```


## How it works

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

## API

### `render_blueprint(...)`

```python
def render_blueprint(
    src: str | Path,
    dst: str | Path,
    context: dict[str, t.Any] | None = None,
    *,
    ignore: list[str] | None = None,
    envops: dict | None = None,
    force: bool = False,
) -> None:
    """

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
    ...
```

