"""Deterministic PEP 514 tests with an in-memory, read-only winreg fixture."""

import ntpath
import unittest
from unittest.mock import patch

from pydoctor.discovery_registry import discover_registry


class Key:
    def __init__(self, registry, identity):
        self.registry, self.identity = registry, identity

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.registry.closed += 1


class FakeRegistry:
    HKEY_CURRENT_USER = "CU"
    HKEY_LOCAL_MACHINE = "LM"
    KEY_READ = 1
    KEY_WOW64_32KEY = 32
    KEY_WOW64_64KEY = 64
    REG_SZ = 1
    REG_EXPAND_SZ = 2

    def __init__(self):
        self.tree = {}
        self.denied = set()
        self.closed = 0
        self.opened = []

    def add(self, hive, view, path, values=None):
        parts = path.split("\\")
        for index in range(1, len(parts) + 1):
            self.tree.setdefault((hive, view, "\\".join(parts[:index])), {})
        self.tree[hive, view, path].update(values or {})

    def registration(self, hive="CU", view=0, company="PythonCore", tag="3.12",
                     values=None, install=None):
        path = "Software\\Python\\" + company + "\\" + tag
        self.add(hive, view, path, values)
        if install is not None:
            self.add(hive, view, path + "\\InstallPath", install)
        return path

    def OpenKey(self, hive, path, reserved, access):
        assert reserved == 0
        assert access in (1, 33, 65)  # Read only, with an optional view selector.
        view = access & (32 | 64)
        identity = (hive, view, path)
        self.opened.append(identity)
        if identity in self.denied:
            raise PermissionError("fixture denied")
        if identity not in self.tree:
            raise FileNotFoundError(path)
        return Key(self, identity)

    def EnumKey(self, key, index):
        hive, view, path = key.identity
        children = sorted({p[len(path) + 1:].split("\\")[0]
                           for h, v, p in self.tree
                           if h == hive and v == view and p.startswith(path + "\\")})
        if index >= len(children):
            error = OSError("No more items")
            error.winerror = 259
            raise error
        return children[index]

    def QueryValueEx(self, key, name):
        try:
            value = self.tree[key.identity][name]
        except KeyError:
            raise FileNotFoundError(name) from None
        if isinstance(value, Exception):
            raise value
        return value


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = FakeRegistry()

    def test_hkcu_registration_and_pythoncore_fallback(self):
        self.registry.registration(values={"Version": ("3.12.9", 1),
                                            "SysArchitecture": ("64bit", 1)},
                                   install={"": (r"C:\Python312", 1)})
        result = discover_registry(self.registry)
        self.assertEqual(len(result.hints), 1)
        hint = result.hints[0]
        self.assertEqual(hint.executable, ntpath.join(r"C:\Python312", "python.exe"))
        self.assertEqual((hint.version, hint.implementation, hint.architecture),
                         ("3.12.9", "CPython", "64bit"))
        self.assertEqual(dict(hint.evidence.metadata)["hive"], "HKCU")
        self.assertFalse(result.issues)
        self.assertGreater(self.registry.closed, 0)

    def test_hklm_both_registry_views(self):
        for view in (32, 64):
            self.registry.registration("LM", view, install={"": (fr"C:\Python{view}", 1)})
        result = discover_registry(self.registry)
        self.assertEqual({dict(h.evidence.metadata)["view"] for h in result.hints}, {"32", "64"})
        self.assertEqual(len(result.hints), 2)

    def test_enumerates_multiple_companies_and_tags(self):
        for company in ("PythonCore", "Vendor"):
            for tag in ("3.12", "custom"):
                self.registry.registration(company=company, tag=tag,
                                           install={"ExecutablePath": (r"D:\Vendor\python.exe", 1)})
        self.assertEqual(len(discover_registry(self.registry).hints), 4)

    def test_third_party_explicit_executable(self):
        self.registry.registration(company="Vendor", tag="custom",
                                   values={"SysVersion": ("3.11", 1)},
                                   install={"": (r"D:\Vendor", 1),
                                            "ExecutablePath": (r"D:\Vendor\bin\pypy.exe", 1)})
        hint = discover_registry(self.registry).hints[0]
        self.assertEqual(hint.executable, r"D:\Vendor\bin\pypy.exe")
        self.assertEqual(hint.version, "3.11")
        self.assertIsNone(hint.implementation)

    def test_third_party_without_executable_is_not_inferred(self):
        self.registry.registration(company="Vendor", install={"": (r"C:\Vendor", 1)})
        self.assertIsNone(discover_registry(self.registry).hints[0].executable)

    def test_explicit_executable_overrides_pythoncore_fallback(self):
        self.registry.registration(install={"": (r"C:\Python", 1),
                                            "ExecutablePath": (r"D:\Other\python.exe", 1)})
        self.assertEqual(discover_registry(self.registry).hints[0].executable,
                         r"D:\Other\python.exe")

    def test_pylauncher_company_ignored_case_insensitively(self):
        self.registry.registration(company="pYLaUnChEr", install={"": (r"C:\Launcher", 1)})
        self.assertEqual(discover_registry(self.registry).hints, ())

    def test_missing_registry_keys(self):
        self.assertEqual(discover_registry(self.registry).hints, ())
        self.assertEqual(discover_registry(self.registry).issues, ())

    def test_missing_install_key_preserves_registration(self):
        self.registry.registration()
        result = discover_registry(self.registry)
        self.assertIsNone(result.hints[0].executable)
        self.assertIn("registry_install_path_missing", {i.code for i in result.issues})

    def test_inaccessible_root_does_not_block_machine_registration(self):
        self.registry.denied.add(("CU", 0, "Software\\Python"))
        self.registry.registration("LM", 64, install={"": (r"C:\Python", 1)})
        result = discover_registry(self.registry)
        self.assertEqual(len(result.hints), 1)
        self.assertIn("registry_key_inaccessible", {i.code for i in result.issues})

    def test_inaccessible_registration_preserves_evidence(self):
        path = self.registry.registration()
        self.registry.denied.add(("CU", 0, path))
        result = discover_registry(self.registry)
        self.assertEqual(len(result.hints), 1)
        self.assertTrue(result.hints[0].issues)

    def test_malformed_values_and_wrong_types(self):
        for malformed in ((123, 4), (123, 1), ("", 1), ("x\x00y", 1)):
            with self.subTest(malformed=malformed):
                self.registry = FakeRegistry()
                self.registry.registration(values={"Version": malformed},
                                           install={"": (r"C:\Python", 1),
                                                    "ExecutablePath": malformed})
                result = discover_registry(self.registry)
                self.assertIsNone(result.hints[0].executable)
                self.assertIsNone(result.hints[0].version)
                self.assertIn("registry_value_malformed", {i.code for i in result.issues})

    def test_inaccessible_value_is_reported(self):
        self.registry.registration(install={"ExecutablePath": PermissionError("denied")})
        result = discover_registry(self.registry)
        self.assertIsNone(result.hints[0].executable)
        self.assertIn("registry_value_inaccessible", {i.code for i in result.issues})

    def test_relative_install_path_has_no_fallback(self):
        self.registry.registration(install={"": ("relative", 1)})
        self.assertIsNone(discover_registry(self.registry).hints[0].executable)

    def test_expandable_registry_string(self):
        self.registry.registration(install={"ExecutablePath": (r"%PYD_TEST_ROOT%\python.exe", 2)})
        with patch.dict("os.environ", {"PYD_TEST_ROOT": r"C:\Python"}, clear=True):
            self.assertEqual(discover_registry(self.registry).hints[0].executable,
                             r"C:\Python\python.exe")
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(discover_registry(self.registry).hints[0].executable)

    def test_registry_bounds_report_incompleteness(self):
        self.registry.registration(tag="one")
        self.registry.registration(tag="two")
        with patch("pydoctor.discovery_registry.MAX_SUBKEYS", 1):
            result = discover_registry(self.registry)
        self.assertIn("registry_limit", {i.code for i in result.issues})

    def test_enumeration_permission_error(self):
        self.registry.add("CU", 0, "Software\\Python")
        with patch.object(self.registry, "EnumKey", side_effect=PermissionError):
            result = discover_registry(self.registry)
        self.assertIn("registry_enumeration_failed", {i.code for i in result.issues})
