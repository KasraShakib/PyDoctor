"""Bounded PEP 514 registry enumeration; winreg is imported only on demand."""

import ntpath

from pydoctor.discovery_models import CandidateHint, DiscoveryIssue, SourceEvidence, SourceResult
from pydoctor.discovery_normalization import absolute_path

MAX_SUBKEYS = 256
MAX_REGISTRATIONS = 1024


def discover_registry(registry=None) -> SourceResult:
    """Read HKCU and both HKLM views, preserving incomplete registrations.

    The injectable registry implements the winreg interface. No write access is
    requested. PythonCore alone gets PEP 514's legacy python.exe fallback.
    """
    if registry is None:
        try:
            import winreg as registry
        except ImportError:
            return SourceResult(issues=(DiscoveryIssue(
                "registry_unavailable", "registry", "winreg is unavailable on this platform."),))
    hints = []
    issues = []

    def issue(code, message, location):
        issues.append(DiscoveryIssue(code, "registry", message, location))

    def names(key, location):
        result = []
        for index in range(MAX_SUBKEYS + 1):
            try:
                name = registry.EnumKey(key, index)
            except OSError as exc:
                if getattr(exc, "winerror", None) != 259:
                    issue("registry_enumeration_failed", type(exc).__name__, location)
                break
            if index == MAX_SUBKEYS:
                issue("registry_limit", "Subkey enumeration limit reached.", location)
                break
            result.append(name)
        return sorted(result, key=lambda s: (s.casefold(), s))

    def value(key, name, location):
        try:
            data, kind = registry.QueryValueEx(key, name)
        except FileNotFoundError:
            return None
        except OSError as exc:
            issue("registry_value_inaccessible", type(exc).__name__, location + "\\" + name)
            return None
        if kind not in (registry.REG_SZ, registry.REG_EXPAND_SZ) or not isinstance(data, str):
            issue("registry_value_malformed", "Expected a registry string.", location + "\\" + name)
            return None
        if not data or "\x00" in data:
            issue("registry_value_malformed", "Empty or NUL-containing registry string.", location)
            return None
        if kind == registry.REG_EXPAND_SZ:
            data = ntpath.expandvars(data)
            if "%" in data:
                issue("registry_value_malformed", "Unresolved expandable string.", location)
                return None
        return data

    roots = (("HKCU", registry.HKEY_CURRENT_USER, "default", 0),
             ("HKLM", registry.HKEY_LOCAL_MACHINE, "64", registry.KEY_WOW64_64KEY),
             ("HKLM", registry.HKEY_LOCAL_MACHINE, "32", registry.KEY_WOW64_32KEY))
    for hive_name, hive, view, flag in roots:
        base = "Software\\Python"
        label = f"{hive_name}[{view}]\\{base}"
        try:
            with registry.OpenKey(hive, base, 0, registry.KEY_READ | flag) as root:
                companies = names(root, label)
        except FileNotFoundError:
            continue
        except OSError as exc:
            issue("registry_key_inaccessible", type(exc).__name__, label)
            continue
        for company in companies:
            if company.casefold() == "pylauncher":
                continue
            company_path = base + "\\" + company
            try:
                with registry.OpenKey(hive, company_path, 0, registry.KEY_READ | flag) as key:
                    tags = names(key, label + "\\" + company)
            except OSError as exc:
                issue("registry_key_inaccessible", type(exc).__name__, label + "\\" + company)
                continue
            for tag in tags:
                if len(hints) >= MAX_REGISTRATIONS:
                    issue("registry_limit", "Registration limit reached.", label)
                    return SourceResult(tuple(hints), tuple(issues))
                path = company_path + "\\" + tag
                location = f"{hive_name}[{view}]\\{path}"
                start = len(issues)
                metadata = {"hive": hive_name, "view": view, "company": company, "tag": tag}
                prefix = executable = None
                explicit = False
                try:
                    with registry.OpenKey(hive, path, 0, registry.KEY_READ | flag) as key:
                        for field in ("DisplayName", "Version", "SysVersion", "SysArchitecture"):
                            text = value(key, field, location)
                            if text is not None:
                                metadata[field] = text
                    try:
                        with registry.OpenKey(hive, path + "\\InstallPath", 0,
                                              registry.KEY_READ | flag) as key:
                            prefix = value(key, "", location + "\\InstallPath")
                            # Presence, even if malformed, prevents legacy fallback.
                            try:
                                registry.QueryValueEx(key, "ExecutablePath")
                                explicit = True
                            except FileNotFoundError:
                                pass
                            except OSError:
                                explicit = True
                            executable = value(key, "ExecutablePath", location + "\\InstallPath")
                            for field in ("WindowedExecutablePath", "ExecutableArguments",
                                          "WindowedExecutableArguments"):
                                text = value(key, field, location + "\\InstallPath")
                                if text is not None:
                                    metadata[field] = text
                    except FileNotFoundError:
                        issue("registry_install_path_missing", "InstallPath key is absent.", location)
                    if (not explicit and company.casefold() == "pythoncore" and prefix
                            and absolute_path(prefix)):
                        executable = ntpath.join(prefix, "python.exe")
                        metadata["executable_fallback"] = "PythonCore"
                except OSError as exc:
                    issue("registry_key_inaccessible", type(exc).__name__, location)
                if prefix:
                    metadata["InstallPath"] = prefix
                hints.append(CandidateHint(
                    executable, SourceEvidence("registry", location, tuple(sorted(metadata.items()))),
                    prefix=prefix, version=metadata.get("Version") or metadata.get("SysVersion"),
                    implementation="CPython" if company.casefold() == "pythoncore" else None,
                    architecture=metadata.get("SysArchitecture"), issues=tuple(issues[start:]),
                ))
    return SourceResult(tuple(hints), tuple(issues))
