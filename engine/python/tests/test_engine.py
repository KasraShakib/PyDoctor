"""Engine package smoke tests compatible with unittest and pytest."""

import unittest

from pydoctor import __version__


class EngineTests(unittest.TestCase):
    def test_version_is_defined(self) -> None:
        self.assertEqual(__version__, "0.1.0")
