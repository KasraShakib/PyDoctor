"""Bounded PEP 440 version and specifier evaluation without third-party packages.

The engine must stay dependency-free, so this module implements the subset of
PEP 440 needed to answer "is this installed version acceptable?". Anything that
cannot be parsed is reported as unknown by callers instead of being guessed.
"""

import itertools
import re
from dataclasses import dataclass
from functools import total_ordering

_VERSION_RE = re.compile(
    r"""
    ^\s*v?
    (?:(?P<epoch>[0-9]+)!)?
    (?P<release>[0-9]+(?:\.[0-9]+)*)
    (?P<pre>[-_.]?(?P<pre_l>alpha|beta|preview|pre|a|b|c|rc)[-_.]?(?P<pre_n>[0-9]+)?)?
    (?P<post>(?:-(?P<post_n1>[0-9]+))|(?:[-_.]?(?P<post_l>post|rev|r)[-_.]?(?P<post_n2>[0-9]+)?))?
    (?P<dev>[-_.]?(?P<dev_l>dev)[-_.]?(?P<dev_n>[0-9]+)?)?
    (?:\+(?P<local>[a-z0-9]+(?:[-_.][a-z0-9]+)*))?
    \s*$
    """,
    re.VERBOSE | re.IGNORECASE,
)

_PRE_RANK = {"a": 0, "b": 1, "rc": 2}
_PRE_ALIASES = {"alpha": "a", "beta": "b", "c": "rc", "pre": "rc", "preview": "rc"}


def _local_key(local: str | None) -> tuple:
    if not local:
        return ()
    parts = re.split(r"[-_.]", local.lower())
    return tuple((1, int(part)) if part.isdigit() else (0, part) for part in parts)


@total_ordering
@dataclass(frozen=True)
class Version:
    """A parsed PEP 440 version with deterministic ordering."""

    text: str
    epoch: int
    release: tuple[int, ...]
    pre: tuple[str, int] | None
    post: int | None
    dev: int | None
    local: str | None

    def _key(self) -> tuple:
        release = tuple(
            reversed(list(itertools.dropwhile(lambda part: part == 0, reversed(self.release))))
        )
        if self.pre is None and self.post is None and self.dev is not None:
            pre_key = (-1, 0, 0)
        elif self.pre is None:
            pre_key = (1, 0, 0)
        else:
            pre_key = (0, _PRE_RANK[self.pre[0]], self.pre[1])
        post_key = (-1, 0) if self.post is None else (0, self.post)
        dev_key = (1, 0) if self.dev is None else (0, self.dev)
        return (self.epoch, release, pre_key, post_key, dev_key, _local_key(self.local))

    def public_key(self) -> tuple:
        """Return the comparison key that ignores a local version label."""
        return self._key()[:-1]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() == other._key()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() < other._key()

    def __hash__(self) -> int:
        return hash(self._key())


def parse_version(text: str) -> Version:
    """Parse a PEP 440 version or raise ValueError for unsupported syntax."""
    match = _VERSION_RE.match(text)
    if not match:
        raise ValueError(f"Unsupported version syntax: {text!r}")
    release = tuple(int(part) for part in match["release"].split("."))
    pre = None
    if match["pre_l"]:
        label = match["pre_l"].lower()
        pre = (_PRE_ALIASES.get(label, label), int(match["pre_n"] or 0))
    post = None
    if match["post_n1"]:
        post = int(match["post_n1"])
    elif match["post_l"]:
        post = int(match["post_n2"] or 0)
    dev = int(match["dev_n"] or 0) if match["dev_l"] else None
    return Version(
        text=text.strip(),
        epoch=int(match["epoch"] or 0),
        release=release,
        pre=pre,
        post=post,
        dev=dev,
        local=match["local"],
    )


_SPEC_RE = re.compile(r"^\s*(===|~=|==|!=|<=|>=|<|>)\s*(\S+)\s*$")


@dataclass(frozen=True)
class Specifier:
    """One PEP 440 comparison clause such as ``>=1.2`` or ``==1.4.*``."""

    operator: str
    value: str

    def contains(self, candidate: Version) -> bool:
        if self.operator == "===":
            return candidate.text.strip().casefold() == self.value.casefold()
        if self.value.endswith(".*"):
            return self._wildcard(candidate, negate=self.operator == "!=")
        spec = parse_version(self.value)
        if self.operator == "==":
            if spec.local is None:
                return candidate.public_key() == spec.public_key()
            return candidate == spec
        if self.operator == "!=":
            if spec.local is None:
                return candidate.public_key() != spec.public_key()
            return candidate != spec
        if self.operator == "~=":
            return self._compatible(candidate, spec)
        if self.operator == "<=":
            return candidate <= spec
        if self.operator == ">=":
            return candidate >= spec
        if self.operator == "<":
            return candidate < spec and not _prerelease_excluded(spec, candidate)
        if self.operator == ">":
            return candidate > spec and not _postrelease_excluded(spec, candidate)
        raise ValueError(f"Unsupported operator: {self.operator}")

    def _wildcard(self, candidate: Version, negate: bool) -> bool:
        prefix_text = self.value[:-2]
        prefix = parse_version(prefix_text)
        length = len(prefix.release)
        matched = (
            candidate.epoch == prefix.epoch
            and candidate.release[:length] == prefix.release[:length]
        )
        return not matched if negate else matched

    def _compatible(self, candidate: Version, spec: Version) -> bool:
        if len(spec.release) < 2:
            raise ValueError("Compatible-release specifier needs at least two release parts.")
        if candidate < spec:
            return False
        prefix = spec.release[:-1]
        return (
            candidate.epoch == spec.epoch
            and candidate.release[: len(prefix)] == prefix
        )


def _prerelease_excluded(spec: Version, candidate: Version) -> bool:
    """PEP 440: ``<V`` excludes pre-releases of the same final release."""
    if spec.pre is None and spec.dev is None and spec.post is None:
        return (
            (candidate.pre is not None or candidate.dev is not None)
            and candidate.release == spec.release
            and candidate.epoch == spec.epoch
        )
    return False


def _postrelease_excluded(spec: Version, candidate: Version) -> bool:
    """PEP 440: ``>V`` excludes post-releases of the same final release."""
    if spec.post is None and spec.pre is None and spec.dev is None:
        return (
            candidate.post is not None
            and candidate.release == spec.release
            and candidate.epoch == spec.epoch
        )
    return False


@dataclass(frozen=True)
class SpecifierSet:
    """A comma-separated conjunction of PEP 440 clauses."""

    specifiers: tuple[Specifier, ...]

    @classmethod
    def parse(cls, text: str) -> "SpecifierSet":
        clauses = []
        for raw in text.split(","):
            clause = raw.strip()
            if not clause:
                continue
            match = _SPEC_RE.match(clause)
            if not match:
                raise ValueError(f"Unsupported specifier: {clause!r}")
            clauses.append(Specifier(match[1], match[2]))
        if not clauses:
            raise ValueError("Empty specifier set.")
        return cls(tuple(clauses))

    def contains(self, version: str) -> bool:
        candidate = parse_version(version)
        return all(specifier.contains(candidate) for specifier in self.specifiers)


def evaluate_specifier(specifier: str | None, version: str | None) -> bool | None:
    """Return True/False, or None when either side cannot be parsed."""
    if specifier is None or not specifier.strip():
        return True
    if version is None:
        return None
    try:
        return SpecifierSet.parse(specifier).contains(version)
    except ValueError:
        return None
