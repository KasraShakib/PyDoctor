"""Observe the current runtime without importing user code or changing its environment."""

import os
import platform
import sys

from pydoctor.models import Confidence, DiagnosticReport, Finding, RuntimeEvidence


def collect_runtime() -> RuntimeEvidence:
    """Capture runtime facts; VIRTUAL_ENV is a shell hint, not proof of activation."""
    return RuntimeEvidence(
        executable=sys.executable,
        version=sys.version,
        implementation=platform.python_implementation(),
        prefix=sys.prefix,
        base_prefix=sys.base_prefix,
        sys_path=tuple(sys.path),
        virtual_env=os.environ.get("VIRTUAL_ENV"),
    )


def _activation_finding(runtime: RuntimeEvidence) -> Finding:
    """Compare an absolute activation hint with the runtime prefix conservatively."""
    marker = runtime.virtual_env
    assert marker is not None
    evidence = (f"VIRTUAL_ENV={marker!r}", f"sys.prefix={runtime.prefix!r}")
    command = (
        runtime.executable,
        "-c",
        "import sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix)",
    )
    missing = ()
    try:
        if not os.path.isabs(marker) or not os.path.isabs(runtime.prefix):
            missing = ("Absolute paths are required to compare the activation hint and prefix.",)
            same = None
        else:
            # Compare identities so Windows casing, junctions and symlinks do not
            # become false mismatch findings. Unavailable paths remain unknown.
            same = os.path.samefile(marker, runtime.prefix)
    except (OSError, ValueError) as exc:
        same = None
        missing = (f"Directory identity could not be checked ({type(exc).__name__}).",)

    if same is True:
        return Finding(
            code="environment.activation_hint_matches",
            confidence=Confidence.CONFIRMED,
            summary="VIRTUAL_ENV and sys.prefix identify the same directory.",
            evidence=evidence,
            next_steps=("This agreement does not establish package or interpreter health.",),
        )
    if same is False:
        return Finding(
            code="environment.activation_hint_mismatch",
            confidence=Confidence.LIKELY,
            summary="The shell activation hint may refer to a different Python environment.",
            evidence=evidence + ("The two paths identify different filesystem objects.",),
            missing_information=("Which interpreter the user intended to run.",),
            hypotheses=(
                "VIRTUAL_ENV may be stale or inherited from another shell.",
                "An explicit interpreter may intentionally bypass the shell's environment.",
            ),
            next_steps=(
                "Compare the executable with the interpreter selected in the IDE or terminal.",
                "Run the command in the affected terminal and compare prefixes with this report.",
                "Do not reinstall packages or recreate the environment based on this hint alone.",
            ),
            commands=(command,),
        )
    return Finding(
        code="environment.activation_hint_unverified",
        confidence=Confidence.UNKNOWN,
        summary="The activation hint could not be reliably compared with the runtime prefix.",
        evidence=evidence,
        missing_information=missing,
        hypotheses=(
            "The hint may be relative, stale, inaccessible, or point to a removed environment.",
        ),
        next_steps=(
            "Check that VIRTUAL_ENV contains an absolute, accessible environment directory.",
            "Compare the executable and prefixes in the affected terminal before making changes.",
        ),
        commands=(command,),
    )


def diagnose_runtime(runtime: RuntimeEvidence) -> DiagnosticReport:
    """Explain collected facts without asserting that the environment is healthy."""
    isolated = runtime.prefix != runtime.base_prefix
    findings = [
        Finding(
            code="runtime.observed",
            confidence=Confidence.CONFIRMED,
            summary="The report describes the interpreter running the engine.",
            evidence=(
                f"sys.executable={runtime.executable!r}",
                f"sys.version={runtime.version!r}",
                f"implementation={runtime.implementation!r}",
            ),
        ),
        Finding(
            code="environment.prefix_isolated" if isolated else "environment.prefix_base",
            confidence=Confidence.CONFIRMED,
            summary=(
                "The runtime prefix differs from the base interpreter prefix."
                if isolated
                else "The runtime prefix equals the base interpreter prefix."
            ),
            evidence=(
                f"sys.prefix={runtime.prefix!r}",
                f"sys.base_prefix={runtime.base_prefix!r}",
            ),
            next_steps=(
                "Prefix separation is the standard venv signal, not an environment health check.",
                "Equal prefixes do not rule out Conda or other environment managers.",
            ),
        ),
    ]
    if runtime.virtual_env:
        findings.append(_activation_finding(runtime))
    return DiagnosticReport(runtime=runtime, findings=tuple(findings))


def diagnose_current_environment() -> DiagnosticReport:
    """Collect and evaluate the current interpreter in one read-only operation."""
    return diagnose_runtime(collect_runtime())
