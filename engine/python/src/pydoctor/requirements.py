"""Bounded PEP 508 requirement and environment-marker parsing.

Only the syntax needed for dependency diagnostics is supported. Unsupported or
ambiguous input raises, and callers record an explicit unknown result rather
than inventing a satisfied or missing dependency.
"""

import os
import platform
import re
from dataclasses import dataclass

from pydoctor.versions import parse_version

_NAME = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
_NAME_RE = re.compile(rf"^\s*(?P<name>{_NAME})\s*(?:\[(?P<extras>[^\]]*)\])?\s*(?P<rest>.*)$")
_DIRECT_RE = re.compile(
    rf"^\s*(?P<name>{_NAME})\s*(?:\[(?P<extras>[^\]]*)\])?\s*@\s*(?P<url>\S.*)$"
)
_EXTRA_NAME_RE = re.compile(rf"^{_NAME}$")


class RequirementError(ValueError):
    """A requirement string could not be parsed with the supported subset."""


def normalize_name(name: str) -> str:
    """Normalize a distribution name per PEP 503 for case-insensitive lookup."""
    return re.sub(r"[-_.]+", "-", name.strip()).lower()


@dataclass(frozen=True)
class Requirement:
    """A parsed requirement without evaluating its marker or URL."""

    raw: str
    name: str
    normalized_name: str
    extras: tuple[str, ...] = ()
    specifier: str | None = None
    marker: str | None = None
    url: str | None = None


def _split_marker(text: str) -> tuple[str, str | None]:
    body, separator, marker = text.partition(";")
    if not separator:
        return text.strip(), None
    marker = marker.strip()
    return body.strip(), marker or None


def _parse_extras(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    extras = []
    for part in raw.split(","):
        extra = part.strip()
        if not extra:
            continue
        if not _EXTRA_NAME_RE.match(extra):
            raise RequirementError(f"Invalid extra name: {extra!r}")
        extras.append(extra)
    return tuple(extras)


def parse_requirement(text: str) -> Requirement:
    """Parse ``name[extras] specifier ; marker`` or ``name @ url ; marker``."""
    raw = text.strip()
    if not raw:
        raise RequirementError("Empty requirement string.")
    body, marker = _split_marker(raw)

    direct = _DIRECT_RE.match(body)
    if direct:
        name = direct["name"]
        return Requirement(
            raw=raw,
            name=name,
            normalized_name=normalize_name(name),
            extras=_parse_extras(direct["extras"]),
            specifier=None,
            marker=marker,
            url=direct["url"].strip(),
        )

    match = _NAME_RE.match(body)
    if not match:
        raise RequirementError(f"Unsupported requirement syntax: {raw!r}")
    name = match["name"]
    rest = match["rest"].strip()
    if rest.startswith("(") and rest.endswith(")"):
        rest = rest[1:-1].strip()
    if rest.startswith("@"):
        raise RequirementError(f"Direct reference is missing a URL: {raw!r}")
    return Requirement(
        raw=raw,
        name=name,
        normalized_name=normalize_name(name),
        extras=_parse_extras(match["extras"]),
        specifier=rest or None,
        marker=marker,
    )


class MarkerNotEvaluated(ValueError):
    """The marker uses a variable or syntax outside the supported subset."""


_TOKEN_RE = re.compile(
    r"""
    \s*(?:
        (?P<string>'[^']*'|"[^"]*")
      | (?P<op>===|~=|==|!=|<=|>=|<|>|\(|\))
      | (?P<name>[A-Za-z_][A-Za-z0-9_.]*)
    )
    """,
    re.VERBOSE,
)


def _tokenize(marker: str) -> list[tuple[str, str]]:
    tokens = []
    position = 0
    while position < len(marker):
        match = _TOKEN_RE.match(marker, position)
        if not match:
            if marker[position:].strip() == "":
                break
            raise MarkerNotEvaluated(f"Unsupported marker syntax near {marker[position:]!r}")
        kind = match.lastgroup
        value = match.group(kind)
        tokens.append((kind, value))
        position = match.end()
    return tokens


class _MarkerParser:
    def __init__(self, tokens: list[tuple[str, str]], context: dict[str, str]) -> None:
        self.tokens = tokens
        self.context = context
        self.index = 0

    def _peek(self) -> tuple[str, str] | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def _take(self) -> tuple[str, str]:
        token = self._peek()
        if token is None:
            raise MarkerNotEvaluated("Unexpected end of marker.")
        self.index += 1
        return token

    def _accept_name(self, name: str) -> bool:
        token = self._peek()
        if token and token[0] == "name" and token[1].lower() == name:
            self.index += 1
            return True
        return False

    def parse(self) -> bool:
        value = self._or()
        if self._peek() is not None:
            raise MarkerNotEvaluated("Unexpected trailing marker tokens.")
        return value

    def _or(self) -> bool:
        value = self._and()
        while self._accept_name("or"):
            right = self._and()
            value = value or right
        return value

    def _and(self) -> bool:
        value = self._atom()
        while self._accept_name("and"):
            right = self._atom()
            value = value and right
        return value

    def _atom(self) -> bool:
        token = self._peek()
        if token == ("op", "("):
            self.index += 1
            value = self._or()
            closing = self._take()
            if closing != ("op", ")"):
                raise MarkerNotEvaluated("Unbalanced marker parentheses.")
            return value
        return self._comparison()

    def _value(self) -> str:
        kind, value = self._take()
        if kind == "string":
            return value[1:-1]
        if kind == "name":
            if value in self.context:
                return self.context[value]
            raise MarkerNotEvaluated(f"Unknown marker variable: {value!r}")
        raise MarkerNotEvaluated(f"Unexpected marker token: {value!r}")

    def _operator(self) -> str | None:
        token = self._peek()
        if token is None:
            return None
        kind, value = token
        if kind == "op":
            self.index += 1
            return value
        if kind == "name" and value.lower() == "in":
            self.index += 1
            return "in"
        if kind == "name" and value.lower() == "not":
            self.index += 1
            if not self._accept_name("in"):
                raise MarkerNotEvaluated("Expected 'in' after 'not'.")
            return "not in"
        return None

    def _comparison(self) -> bool:
        left = self._value()
        operator = self._operator()
        if operator is None:
            raise MarkerNotEvaluated("Marker comparison is missing an operator.")
        right = self._value()
        return _compare(left, operator, right)


def _compare(left: str, operator: str, right: str) -> bool:
    if operator == "in":
        return left in right
    if operator == "not in":
        return left not in right
    if operator == "===":
        return left.casefold() == right.casefold()
    if operator in {"==", "!="}:
        try:
            equal = parse_version(left) == parse_version(right)
        except ValueError:
            equal = left == right
        return equal if operator == "==" else not equal
    try:
        candidate = parse_version(left)
        reference = parse_version(right)
    except ValueError as exc:
        raise MarkerNotEvaluated("Non-version marker comparison.") from exc
    if operator == "<":
        return candidate < reference
    if operator == "<=":
        return candidate <= reference
    if operator == ">":
        return candidate > reference
    if operator == ">=":
        return candidate >= reference
    if operator == "~=":
        from pydoctor.versions import evaluate_specifier

        result = evaluate_specifier(f"~={right}", left)
        if result is None:
            raise MarkerNotEvaluated("Unsupported compatible-release marker.")
        return result
    raise MarkerNotEvaluated(f"Unsupported marker operator: {operator!r}")


def marker_references_extra(marker: str) -> bool:
    """Detect markers whose truth depends on an optional extra."""
    return re.search(r"\bextra\b", marker) is not None


def marker_context(python_version: str | None) -> dict[str, str]:
    """Build the subset of PEP 508 environment variables the engine can know.

    The target interpreter is not executed, so its platform is assumed to match
    the host. Missing variables remain unknown rather than being guessed.
    """
    context: dict[str, str] = {
        "sys_platform": "win32" if os.name == "nt" else "linux",
        "os_name": "nt" if os.name == "nt" else "posix",
        "platform_system": "Windows" if os.name == "nt" else platform.system(),
    }
    if python_version:
        context["python_full_version"] = python_version
        context["python_version"] = ".".join(python_version.split(".")[:2])
    return context


def evaluate_marker(marker: str, context: dict[str, str]) -> bool:
    """Evaluate a marker or raise MarkerNotEvaluated."""
    return _MarkerParser(_tokenize(marker), context).parse()
