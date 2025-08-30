import os
from io import StringIO
from unittest import mock

import pytest


class AppendableStringIO(StringIO):
    def append(self, text):
        pos = self.tell()
        self.seek(0, os.SEEK_END)
        self.write(text)
        self.seek(pos)


@pytest.fixture()
def stdin():
    buffer = AppendableStringIO()
    with mock.patch("sys.stdin", buffer):
        yield buffer
