(function () {
  "use strict";

  const { useState, useEffect, useMemo, useRef } = React;
  const h = React.createElement;

  const MODE_IDS = [
    "environment",
    "packages",
    "notebooks",
    "error",
    "repair",
    "discovery",
    "compare",
  ];

  /**
   * All user-facing copy lives here. Keys are shared across languages; a missing
   * translation falls back to English and then to the key itself.
   */
  const STRINGS = {
    en: {
      "brand.sub": "diagnostics",
      "bridge.live": "bridge live",
      "bridge.preview": "browser preview",
      "bridge.connecting": "connecting",
      "engine": "engine {version}",
      "hero.eyebrow": "Python environment diagnostics",
      "hero.title": "Understand your Python environment.",
      "hero.sub": "Find the right interpreter, inspect packages, and explain errors \u2014 read-only.",
      "label.interpreter": "Interpreter",
      "label.project": "Project",
      "label.traceback": "Traceback",
      "ph.interpreter": "C:\\Path\\To\\python.exe",
      "ph.project": "Optional project folder",
      "ph.traceback": "Paste a Python traceback here",
      "btn.run": "Run check",
      "btn.running": "Running\u2026",
      "btn.json": "Raw JSON",
      "title.chev": "Discovered interpreters",
      "menu.empty": "No interpreters discovered",
      "hint.repair": "Run a diagnostic report first; the repair plan uses it.",
      "mode.environment": "Full report",
      "mode.environment.hint": "Interpreter, packages, notebooks",
      "mode.packages": "Packages",
      "mode.packages.hint": "Inventory and dependency problems",
      "mode.notebooks": "Notebooks",
      "mode.notebooks.hint": "Kernels and notebook metadata",
      "mode.error": "Explain error",
      "mode.error.hint": "Paste a traceback",
      "mode.repair": "Repair plan",
      "mode.repair.hint": "Dry-run steps from the last report",
      "mode.discovery": "Discover",
      "mode.discovery.hint": "List Python installations",
      "mode.compare": "Compare",
      "mode.compare.hint": "Intended interpreter vs discovery",
      "verdict.error.label": "Needs attention",
      "verdict.error.note": "At least one finding is marked ERROR.",
      "verdict.warning.label": "Review recommended",
      "verdict.warning.note": "Some findings may affect this environment.",
      "verdict.ok.label": "No blocking issues",
      "verdict.ok.note": "No ERROR or WARNING findings were reported.",
      "scope.environment": "Environment report",
      "scope.packages": "Package diagnostics",
      "scope.discovery": "Python discovery",
      "scope.comparison": "Interpreter comparison",
      "scope.notebooks": "Notebook diagnostics",
      "scope.error": "Error explanation",
      "scope.repair": "Repair plan",
      "scope.info": "Engine information",
      "scope.report": "Report",
      "metric.distributions": "distributions",
      "metric.missing_deps": "missing deps",
      "metric.conflicts": "conflicts",
      "metric.findings": "findings",
      "metric.dependencies": "dependencies",
      "metric.missing": "missing",
      "metric.candidates": "candidates",
      "metric.outcome": "outcome",
      "metric.notebooks": "notebooks",
      "metric.kernels": "kernels",
      "metric.frames": "frames",
      "metric.exception": "exception",
      "metric.steps": "steps",
      "metric.version": "version",
      "metric.modes": "modes",
      "meta.interpreter": "Interpreter",
      "meta.project": "Project",
      "meta.comparison": "Comparison",
      "meta.notebooks": "Notebooks",
      "meta.kernels": "Kernels",
      "meta.prefix": "Prefix",
      "meta.python_version": "Python version",
      "meta.intended": "Intended",
      "meta.matched": "Matched",
      "meta.verification": "Verification",
      "meta.target": "Target",
      "meta.kind": "Kind",
      "meta.source": "Source",
      "meta.message": "Message",
      "meta.source_report": "Source report",
      "meta.engine": "Engine",
      "meta.engine_python": "Engine Python",
      "list.findings": "Findings",
      "list.candidates": "Candidates",
      "list.steps": "Steps",
      "empty.findings": "No findings for this report.",
      "empty.ready": "Pick an interpreter and run a check. Everything is read-only.",
      "pill.noexec": "No target execution",
      "pill.noimports": "No imports",
      "pill.nopip": "No pip",
      "pill.nomutations": "No mutations",
      "foot": "Read-only diagnostics \u00b7 no telemetry \u00b7 reports stay on this machine",
      "cand.noexec": "(no executable)",
      "cand.nometa": "no metadata",
      "step.title": "Step",
      "step.nocmd": "(no command)",
      "step.verify": "Verify: {value}",
      "verdict.candidates": "{count} candidate found",
      "verdict.candidates.plural": "{count} candidates found",
      "verdict.steps": "{count} dry-run step",
      "verdict.steps.plural": "{count} dry-run steps",
      "verdict.discovery.note": "Read-only discovery across registry, launcher, PATH, and active hints.",
      "verdict.matched.label": "Interpreter matched",
      "verdict.matched.note": "Path or file identity matched discovery evidence.",
      "verdict.mismatch.label": "Interpreter differs",
      "verdict.mismatch.note": "The intended path does not match discovery evidence.",
      "verdict.insufficient.label": "Not enough evidence",
      "verdict.insufficient.note": "The comparison could not confirm a match.",
      "verdict.repair.note": "Nothing is executed while building this plan.",
      "verdict.engine.label": "Engine ready",
      "verdict.engine.note": "Metadata for the local diagnostic engine.",
      "theme.toggle": "Switch theme",
      "lang.toggle": "Switch language",
      "error.bridge":
        "The desktop bridge is unavailable. Launch PyDoctor with the desktop app rather than a plain browser.",
      "error.unknown": "Unknown error",
    },
    fa: {
      "brand.sub": "\u062a\u0634\u062e\u06cc\u0635 \u0645\u062d\u06cc\u0637",
      "bridge.live": "\u0627\u062a\u0635\u0627\u0644 \u0628\u0631\u0642\u0631\u0627\u0631",
      "bridge.preview": "\u067e\u06cc\u0634\u200c\u0646\u0645\u0627\u06cc\u0634 \u0645\u0631\u0648\u0631\u06af\u0631",
      "bridge.connecting": "\u062f\u0631 \u062d\u0627\u0644 \u0627\u062a\u0635\u0627\u0644",
      "engine": "\u0645\u0648\u062a\u0648\u0631 {version}",
      "hero.eyebrow": "\u062a\u0634\u062e\u06cc\u0635 \u0645\u062d\u06cc\u0637 \u067e\u0627\u06cc\u062a\u0648\u0646",
      "hero.title": "\u0645\u062d\u06cc\u0637 \u067e\u0627\u06cc\u062a\u0648\u0646 \u062e\u0648\u062f \u0631\u0627 \u0628\u0634\u0646\u0627\u0633\u06cc\u062f.",
      "hero.sub":
        "\u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631 \u062f\u0631\u0633\u062a \u0631\u0627 \u067e\u06cc\u062f\u0627 \u06a9\u0646\u06cc\u062f\u060c \u067e\u06a9\u06cc\u062c\u200c\u0647\u0627 \u0631\u0627 \u0628\u0631\u0631\u0633\u06cc \u06a9\u0646\u06cc\u062f \u0648 \u062e\u0637\u0627\u0647\u0627 \u0631\u0627 \u062a\u0648\u0636\u06cc\u062d \u062f\u0647\u06cc\u062f \u2014 \u0641\u0642\u0637 \u062e\u0648\u0627\u0646\u062f\u0646\u06cc.",
      "label.interpreter": "\u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631",
      "label.project": "\u067e\u0631\u0648\u0698\u0647",
      "label.traceback": "\u0631\u0647\u06af\u06cc\u0631 \u062e\u0637\u0627",
      "ph.interpreter": "C:\\Path\\To\\python.exe",
      "ph.project": "\u067e\u0648\u0634\u0647 \u067e\u0631\u0648\u0698\u0647 (\u0627\u062e\u062a\u06cc\u0627\u0631\u06cc)",
      "ph.traceback": "\u0631\u0647\u06af\u06cc\u0631 \u062e\u0637\u0627\u06cc \u067e\u0627\u06cc\u062a\u0648\u0646 \u0631\u0627 \u0627\u06cc\u0646\u062c\u0627 \u0628\u0686\u0633\u0628\u0627\u0646\u06cc\u062f",
      "btn.run": "\u0627\u062c\u0631\u0627\u06cc \u0628\u0631\u0631\u0633\u06cc",
      "btn.running": "\u062f\u0631 \u062d\u0627\u0644 \u0627\u062c\u0631\u0627\u2026",
      "btn.json": "JSON \u062e\u0627\u0645",
      "title.chev": "\u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631\u0647\u0627\u06cc \u06a9\u0634\u0641\u200c\u0634\u062f\u0647",
      "menu.empty": "\u0647\u06cc\u0686 \u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631\u06cc \u067e\u06cc\u062f\u0627 \u0646\u0634\u062f",
      "hint.repair":
        "\u0627\u0628\u062a\u062f\u0627 \u06cc\u06a9 \u06af\u0632\u0627\u0631\u0634 \u062a\u0634\u062e\u06cc\u0635\u06cc \u0627\u062c\u0631\u0627 \u06a9\u0646\u06cc\u062f\u061b \u0646\u0642\u0634\u0647 \u062a\u0639\u0645\u06cc\u0631 \u0627\u0632 \u0622\u0646 \u0627\u0633\u062a\u0641\u0627\u062f\u0647 \u0645\u06cc\u200c\u06a9\u0646\u062f.",
      "mode.environment": "\u06af\u0632\u0627\u0631\u0634 \u06a9\u0627\u0645\u0644",
      "mode.environment.hint":
        "\u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631\u060c \u067e\u06a9\u06cc\u062c\u200c\u0647\u0627\u060c \u0646\u0648\u062a\u200c\u0628\u0648\u06a9\u200c\u0647\u0627",
      "mode.packages": "\u067e\u06a9\u06cc\u062c\u200c\u0647\u0627",
      "mode.packages.hint":
        "\u0641\u0647\u0631\u0633\u062a \u067e\u06a9\u06cc\u062c\u200c\u0647\u0627 \u0648 \u0645\u0634\u06a9\u0644\u0627\u062a \u0648\u0627\u0628\u0633\u062a\u06af\u06cc",
      "mode.notebooks": "\u0646\u0648\u062a\u200c\u0628\u0648\u06a9\u200c\u0647\u0627",
      "mode.notebooks.hint":
        "\u06a9\u0631\u0646\u0644\u200c\u0647\u0627 \u0648 \u0641\u0631\u0627\u062f\u0627\u062f\u0647 \u0646\u0648\u062a\u200c\u0628\u0648\u06a9",
      "mode.error": "\u062a\u0648\u0636\u06cc\u062d \u062e\u0637\u0627",
      "mode.error.hint": "\u0631\u0647\u06af\u06cc\u0631 \u062e\u0637\u0627 \u0631\u0627 \u0628\u0686\u0633\u0628\u0627\u0646\u06cc\u062f",
      "mode.repair": "\u0646\u0642\u0634\u0647 \u062a\u0639\u0645\u06cc\u0631",
      "mode.repair.hint":
        "\u06af\u0627\u0645\u200c\u0647\u0627\u06cc \u0622\u0632\u0645\u0627\u06cc\u0634\u06cc \u0628\u0631 \u0627\u0633\u0627\u0633 \u0622\u062e\u0631\u06cc\u0646 \u06af\u0632\u0627\u0631\u0634",
      "mode.discovery": "\u06a9\u0634\u0641",
      "mode.discovery.hint": "\u0641\u0647\u0631\u0633\u062a \u0646\u0635\u0628\u200c\u0647\u0627\u06cc \u067e\u0627\u06cc\u062a\u0648\u0646",
      "mode.compare": "\u0645\u0642\u0627\u06cc\u0633\u0647",
      "mode.compare.hint":
        "\u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631 \u0645\u0648\u0631\u062f\u0646\u0638\u0631 \u062f\u0631 \u0628\u0631\u0627\u0628\u0631 \u06a9\u0634\u0641",
      "verdict.error.label": "\u0646\u06cc\u0627\u0632\u0645\u0646\u062f \u0628\u0631\u0631\u0633\u06cc",
      "verdict.error.note":
        "\u062d\u062f\u0627\u0642\u0644 \u06cc\u06a9 \u06cc\u0627\u0641\u062a\u0647 \u0628\u0627 \u0633\u0637\u062d ERROR \u062b\u0628\u062a \u0634\u062f\u0647 \u0627\u0633\u062a.",
      "verdict.warning.label": "\u0628\u0627\u0632\u0628\u06cc\u0646\u06cc \u062a\u0648\u0635\u06cc\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f",
      "verdict.warning.note":
        "\u0628\u0631\u062e\u06cc \u06cc\u0627\u0641\u062a\u0647\u200c\u0647\u0627 \u0645\u0645\u06a9\u0646 \u0627\u0633\u062a \u0631\u0648\u06cc \u0627\u06cc\u0646 \u0645\u062d\u06cc\u0637 \u0627\u062b\u0631 \u0628\u06af\u0630\u0627\u0631\u0646\u062f.",
      "verdict.ok.label": "\u0645\u0634\u06a9\u0644 \u0628\u0627\u0632\u062f\u0627\u0631\u0646\u062f\u0647\u200c\u0627\u06cc \u0648\u062c\u0648\u062f \u0646\u062f\u0627\u0631\u062f",
      "verdict.ok.note":
        "\u0647\u06cc\u0686 \u06cc\u0627\u0641\u062a\u0647\u200c\u0627\u06cc \u0628\u0627 \u0633\u0637\u062d ERROR \u06cc\u0627 WARNING \u06af\u0632\u0627\u0631\u0634 \u0646\u0634\u062f.",
      "scope.environment": "\u06af\u0632\u0627\u0631\u0634 \u0645\u062d\u06cc\u0637",
      "scope.packages": "\u062a\u0634\u062e\u06cc\u0635 \u067e\u06a9\u06cc\u062c\u200c\u0647\u0627",
      "scope.discovery": "\u06a9\u0634\u0641 \u067e\u0627\u06cc\u062a\u0648\u0646",
      "scope.comparison": "\u0645\u0642\u0627\u06cc\u0633\u0647 \u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631",
      "scope.notebooks": "\u062a\u0634\u062e\u06cc\u0635 \u0646\u0648\u062a\u200c\u0628\u0648\u06a9",
      "scope.error": "\u062a\u0648\u0636\u06cc\u062d \u062e\u0637\u0627",
      "scope.repair": "\u0646\u0642\u0634\u0647 \u062a\u0639\u0645\u06cc\u0631",
      "scope.info": "\u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0645\u0648\u062a\u0648\u0631",
      "scope.report": "\u06af\u0632\u0627\u0631\u0634",
      "metric.distributions": "\u062a\u0648\u0632\u06cc\u0639\u200c\u0647\u0627",
      "metric.missing_deps": "\u0648\u0627\u0628\u0633\u062a\u06af\u06cc\u200c\u0647\u0627\u06cc \u06af\u0645\u0634\u062f\u0647",
      "metric.conflicts": "\u062a\u0636\u0627\u062f\u0647\u0627",
      "metric.findings": "\u06cc\u0627\u0641\u062a\u0647\u200c\u0647\u0627",
      "metric.dependencies": "\u0648\u0627\u0628\u0633\u062a\u06af\u06cc\u200c\u0647\u0627",
      "metric.missing": "\u06af\u0645\u0634\u062f\u0647",
      "metric.candidates": "\u06af\u0632\u06cc\u0646\u0647\u200c\u0647\u0627",
      "metric.outcome": "\u0646\u062a\u06cc\u062c\u0647",
      "metric.notebooks": "\u0646\u0648\u062a\u200c\u0628\u0648\u06a9\u200c\u0647\u0627",
      "metric.kernels": "\u06a9\u0631\u0646\u0644\u200c\u0647\u0627",
      "metric.frames": "\u0641\u0631\u06cc\u0645\u200c\u0647\u0627",
      "metric.exception": "\u0627\u0633\u062a\u062b\u0646\u0627",
      "metric.steps": "\u06af\u0627\u0645\u200c\u0647\u0627",
      "metric.version": "\u0646\u0633\u062e\u0647",
      "metric.modes": "\u062d\u0627\u0644\u062a\u200c\u0647\u0627",
      "meta.interpreter": "\u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631",
      "meta.project": "\u067e\u0631\u0648\u0698\u0647",
      "meta.comparison": "\u0645\u0642\u0627\u06cc\u0633\u0647",
      "meta.notebooks": "\u0646\u0648\u062a\u200c\u0628\u0648\u06a9\u200c\u0647\u0627",
      "meta.kernels": "\u06a9\u0631\u0646\u0644\u200c\u0647\u0627",
      "meta.prefix": "\u067e\u06cc\u0634\u0648\u0646\u062f",
      "meta.python_version": "\u0646\u0633\u062e\u0647 \u067e\u0627\u06cc\u062a\u0648\u0646",
      "meta.intended": "\u0645\u0648\u0631\u062f\u0646\u0638\u0631",
      "meta.matched": "\u062a\u0637\u0628\u06cc\u0642\u200c\u06cc\u0627\u0641\u062a\u0647",
      "meta.verification": "\u0627\u0639\u062a\u0628\u0627\u0631\u0633\u0646\u062c\u06cc",
      "meta.target": "\u0647\u062f\u0641",
      "meta.kind": "\u0646\u0648\u0639",
      "meta.source": "\u0645\u0646\u0628\u0639",
      "meta.message": "\u067e\u06cc\u0627\u0645",
      "meta.source_report": "\u06af\u0632\u0627\u0631\u0634 \u0645\u0628\u0646\u0627",
      "meta.engine": "\u0645\u0648\u062a\u0648\u0631",
      "meta.engine_python": "\u067e\u0627\u06cc\u062a\u0648\u0646 \u0645\u0648\u062a\u0648\u0631",
      "list.findings": "\u06cc\u0627\u0641\u062a\u0647\u200c\u0647\u0627",
      "list.candidates": "\u06af\u0632\u06cc\u0646\u0647\u200c\u0647\u0627",
      "list.steps": "\u06af\u0627\u0645\u200c\u0647\u0627",
      "empty.findings":
        "\u0628\u0631\u0627\u06cc \u0627\u06cc\u0646 \u06af\u0632\u0627\u0631\u0634 \u06cc\u0627\u0641\u062a\u0647\u200c\u0627\u06cc \u0648\u062c\u0648\u062f \u0646\u062f\u0627\u0631\u062f.",
      "empty.ready":
        "\u06cc\u06a9 \u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f \u0648 \u0628\u0631\u0631\u0633\u06cc \u0631\u0627 \u0627\u062c\u0631\u0627 \u06a9\u0646\u06cc\u062f. \u0647\u0645\u0647\u200c\u0686\u06cc\u0632 \u0641\u0642\u0637 \u062e\u0648\u0627\u0646\u062f\u0646\u06cc \u0627\u0633\u062a.",
      "pill.noexec": "\u0628\u062f\u0648\u0646 \u0627\u062c\u0631\u0627\u06cc \u0647\u062f\u0641",
      "pill.noimports": "\u0628\u062f\u0648\u0646 \u0627\u06cc\u0645\u067e\u0648\u0631\u062a",
      "pill.nopip": "\u0628\u062f\u0648\u0646 pip",
      "pill.nomutations": "\u0628\u062f\u0648\u0646 \u062a\u063a\u06cc\u06cc\u0631",
      "foot":
        "\u062a\u0634\u062e\u06cc\u0635 \u0641\u0642\u0637 \u062e\u0648\u0627\u0646\u062f\u0646\u06cc \u00b7 \u0628\u062f\u0648\u0646 \u062a\u0644\u0645\u062a\u0631\u06cc \u00b7 \u06af\u0632\u0627\u0631\u0634\u200c\u0647\u0627 \u0631\u0648\u06cc \u0647\u0645\u06cc\u0646 \u062f\u0633\u062a\u06af\u0627\u0647 \u0645\u06cc\u200c\u0645\u0627\u0646\u0646\u062f",
      "cand.noexec": "(\u0628\u062f\u0648\u0646 \u0641\u0627\u06cc\u0644 \u0627\u062c\u0631\u0627\u06cc\u06cc)",
      "cand.nometa": "\u0628\u062f\u0648\u0646 \u0641\u0631\u0627\u062f\u0627\u062f\u0647",
      "step.title": "\u06af\u0627\u0645",
      "step.nocmd": "(\u0628\u062f\u0648\u0646 \u062f\u0633\u062a\u0648\u0631)",
      "step.verify": "\u0628\u0631\u0631\u0633\u06cc: {value}",
      "verdict.candidates": "{count} \u06af\u0632\u06cc\u0646\u0647 \u067e\u06cc\u062f\u0627 \u0634\u062f",
      "verdict.candidates.plural": "{count} \u06af\u0632\u06cc\u0646\u0647 \u067e\u06cc\u062f\u0627 \u0634\u062f",
      "verdict.steps": "{count} \u06af\u0627\u0645 \u0622\u0632\u0645\u0627\u06cc\u0634\u06cc",
      "verdict.steps.plural": "{count} \u06af\u0627\u0645 \u0622\u0632\u0645\u0627\u06cc\u0634\u06cc",
      "verdict.discovery.note":
        "\u06a9\u0634\u0641 \u0641\u0642\u0637 \u062e\u0648\u0627\u0646\u062f\u0646\u06cc \u0627\u0632 \u0631\u062c\u06cc\u0633\u062a\u0631\u06cc\u060c \u0644\u0627\u0646\u0686\u0631\u060c PATH \u0648 \u0646\u0634\u0627\u0646\u0647\u200c\u0647\u0627\u06cc \u0641\u0639\u0627\u0644.",
      "verdict.matched.label": "\u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631 \u0645\u0637\u0627\u0628\u0642\u062a \u062f\u0627\u0631\u062f",
      "verdict.matched.note":
        "\u0645\u0633\u06cc\u0631 \u06cc\u0627 \u0647\u0648\u06cc\u062a \u0641\u0627\u06cc\u0644 \u0628\u0627 \u0634\u0648\u0627\u0647\u062f \u06a9\u0634\u0641 \u0645\u0637\u0627\u0628\u0642\u062a \u062f\u0627\u0631\u062f.",
      "verdict.mismatch.label": "\u0627\u06cc\u0646\u062a\u0631\u067e\u0631\u062a\u0631 \u0645\u062a\u0641\u0627\u0648\u062a \u0627\u0633\u062a",
      "verdict.mismatch.note":
        "\u0645\u0633\u06cc\u0631 \u0645\u0648\u0631\u062f\u0646\u0638\u0631 \u0628\u0627 \u0634\u0648\u0627\u0647\u062f \u06a9\u0634\u0641 \u0645\u0637\u0627\u0628\u0642\u062a \u0646\u062f\u0627\u0631\u062f.",
      "verdict.insufficient.label": "\u0634\u0648\u0627\u0647\u062f \u06a9\u0627\u0641\u06cc \u0646\u06cc\u0633\u062a",
      "verdict.insufficient.note":
        "\u0645\u0642\u0627\u06cc\u0633\u0647 \u0646\u062a\u0648\u0627\u0646\u0633\u062a \u062a\u0637\u0627\u0628\u0642 \u0631\u0627 \u062a\u0623\u06cc\u06cc\u062f \u06a9\u0646\u062f.",
      "verdict.repair.note":
        "\u0647\u0646\u06af\u0627\u0645 \u0633\u0627\u062e\u062a \u0627\u06cc\u0646 \u0646\u0642\u0634\u0647 \u0647\u06cc\u0686 \u0686\u06cc\u0632\u06cc \u0627\u062c\u0631\u0627 \u0646\u0645\u06cc\u200c\u0634\u0648\u062f.",
      "verdict.engine.label": "\u0645\u0648\u062a\u0648\u0631 \u0622\u0645\u0627\u062f\u0647 \u0627\u0633\u062a",
      "verdict.engine.note":
        "\u0641\u0631\u0627\u062f\u0627\u062f\u0647 \u0645\u0648\u062a\u0648\u0631 \u062a\u0634\u062e\u06cc\u0635\u06cc \u0645\u062d\u0644\u06cc.",
      "theme.toggle": "\u062a\u063a\u06cc\u06cc\u0631 \u067e\u0648\u0633\u062a\u0647",
      "lang.toggle": "\u062a\u063a\u06cc\u06cc\u0631 \u0632\u0628\u0627\u0646",
      "error.bridge":
        "\u067e\u0644 \u062f\u0633\u06a9\u062a\u0627\u067e \u062f\u0631 \u062f\u0633\u062a\u0631\u0633 \u0646\u06cc\u0633\u062a. PyDoctor \u0631\u0627 \u0628\u0627 \u0628\u0631\u0646\u0627\u0645\u0647 \u062f\u0633\u06a9\u062a\u0627\u067e \u0627\u062c\u0631\u0627 \u06a9\u0646\u06cc\u062f\u060c \u0646\u0647 \u062f\u0631 \u0645\u0631\u0648\u0631\u06af\u0631.",
      "error.unknown": "\u062e\u0637\u0627\u06cc \u0646\u0627\u0634\u0646\u0627\u062e\u062a\u0647",
    },
  };

  function translator(lang) {
    const table = STRINGS[lang] || STRINGS.en;
    const fallback = STRINGS.en;
    return function t(key, vars) {
      let value = table[key];
      if (value === undefined) value = fallback[key];
      if (value === undefined) value = key;
      if (vars) {
        Object.keys(vars).forEach(function (name) {
          value = value.split("{" + name + "}").join(String(vars[name]));
        });
      }
      return value;
    };
  }

  function readPreference(key, fallback) {
    try {
      const stored = window.localStorage.getItem(key);
      return stored || fallback;
    } catch (ignored) {
      return fallback;
    }
  }

  function writePreference(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (ignored) {
      /* Storage can be unavailable in locked-down profiles; ignore. */
    }
  }

  function systemTheme() {
    try {
      return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
    } catch (ignored) {
      return "dark";
    }
  }

  function toneFor(value) {
    const v = String(value || "").toUpperCase();
    if (v === "ERROR") return "error";
    if (v === "WARNING") return "warning";
    if (v === "INFO") return "info";
    if (v === "CONFIRMED" || v === "SATISFIED" || v === "MATCHED") return "ok";
    if (v === "UNKNOWN" || v === "LIKELY" || v === "PARTIAL") return "warning";
    return "muted";
  }

  function asArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function asRecord(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  }

  function text(value) {
    if (value === null || value === undefined || value === "") return "\u2014";
    return String(value);
  }

  function errorText(err, t) {
    if (!err) return t("error.unknown");
    if (typeof err === "string") return err;
    if (err.message) return String(err.message);
    try {
      return JSON.stringify(err);
    } catch (ignored) {
      return String(err);
    }
  }

  function bridgeApi(t) {
    if (!window.pywebview || !window.pywebview.api) {
      throw new Error(t("error.bridge"));
    }
    return window.pywebview.api;
  }

  function waitForBridge(timeoutMs) {
    if (window.pywebview && window.pywebview.api) return Promise.resolve(true);
    return new Promise(function (resolve) {
      let settled = false;
      function finish(ready) {
        if (settled) return;
        settled = true;
        window.removeEventListener("pywebviewready", onReady);
        clearTimeout(timer);
        resolve(ready);
      }
      function onReady() {
        finish(true);
      }
      const timer = setTimeout(function () {
        finish(Boolean(window.pywebview && window.pywebview.api));
      }, timeoutMs);
      window.addEventListener("pywebviewready", onReady);
    });
  }

  function verdictFromFindings(findings, t) {
    const severities = findings.map(function (item) {
      return String((item && item.severity) || "").toUpperCase();
    });
    if (severities.indexOf("ERROR") !== -1) {
      return { label: t("verdict.error.label"), note: t("verdict.error.note"), tone: "error" };
    }
    if (severities.indexOf("WARNING") !== -1) {
      return {
        label: t("verdict.warning.label"),
        note: t("verdict.warning.note"),
        tone: "warning",
      };
    }
    return { label: t("verdict.ok.label"), note: t("verdict.ok.note"), tone: "ok" };
  }

  function summarize(report, t) {
    const scope = report.scope || "";
    const findings = asArray(report.findings);
    const base = { findings: findings, kind: "findings", list: findings, metrics: [], meta: [] };

    if (scope === "environment_report") {
      const summary = asRecord(report.summary);
      return Object.assign({}, base, {
        title: t("scope.environment"),
        verdict: verdictFromFindings(findings, t),
        metrics: [
          { label: t("metric.distributions"), value: text(summary.distributions) },
          {
            label: t("metric.missing_deps"),
            value: text(summary.missing_dependencies),
            bad: Number(summary.missing_dependencies) > 0,
          },
          {
            label: t("metric.conflicts"),
            value: text(summary.version_conflicts),
            bad: Number(summary.version_conflicts) > 0,
          },
          { label: t("metric.findings"), value: String(findings.length) },
        ],
        meta: [
          [t("meta.interpreter"), text(report.interpreter)],
          [t("meta.project"), text(report.project)],
          [t("meta.comparison"), text(summary.comparison_outcome)],
          [t("meta.notebooks"), text(summary.notebooks)],
          [t("meta.kernels"), text(summary.kernels)],
        ],
      });
    }

    if (scope === "package_diagnostics") {
      const distributions = asArray(report.distributions);
      const dependencies = asArray(report.dependencies).map(asRecord);
      const missing = dependencies.filter(function (item) {
        return item.status === "MISSING";
      }).length;
      const conflicts = dependencies.filter(function (item) {
        return item.status === "VERSION_CONFLICT";
      }).length;
      return Object.assign({}, base, {
        title: t("scope.packages"),
        verdict: verdictFromFindings(findings, t),
        metrics: [
          { label: t("metric.distributions"), value: String(distributions.length) },
          { label: t("metric.dependencies"), value: String(dependencies.length) },
          { label: t("metric.missing"), value: String(missing), bad: missing > 0 },
          { label: t("metric.conflicts"), value: String(conflicts), bad: conflicts > 0 },
        ],
        meta: [
          [t("meta.interpreter"), text(report.interpreter)],
          [t("meta.prefix"), text(report.interpreter_prefix)],
          [t("meta.python_version"), text(report.python_version)],
        ],
      });
    }

    if (scope === "python_discovery") {
      const candidates = asArray(report.candidates).map(asRecord);
      return Object.assign({}, base, {
        title: t("scope.discovery"),
        kind: "candidates",
        list: candidates,
        verdict: {
          label: t(candidates.length === 1 ? "verdict.candidates" : "verdict.candidates.plural", {
            count: candidates.length,
          }),
          note: t("verdict.discovery.note"),
          tone: "ok",
        },
        metrics: [{ label: t("metric.candidates"), value: String(candidates.length) }],
        meta: [[t("meta.project"), text(report.project)]],
      });
    }

    if (scope === "intended_interpreter_comparison") {
      const outcome = String(report.outcome || "");
      let verdict;
      if (outcome === "MATCHED") {
        verdict = {
          label: t("verdict.matched.label"),
          note: t("verdict.matched.note"),
          tone: "ok",
        };
      } else if (outcome === "MISMATCH") {
        verdict = {
          label: t("verdict.mismatch.label"),
          note: t("verdict.mismatch.note"),
          tone: "warning",
        };
      } else {
        verdict = {
          label: t("verdict.insufficient.label"),
          note: t("verdict.insufficient.note"),
          tone: "warning",
        };
      }
      return Object.assign({}, base, {
        title: t("scope.comparison"),
        verdict: verdict,
        metrics: [{ label: t("metric.outcome"), value: text(report.outcome) }],
        meta: [
          [t("meta.intended"), text(report.intended_path)],
          [t("meta.matched"), text(report.matched_executable)],
          [t("meta.verification"), text(report.interpreter_verification)],
        ],
      });
    }

    if (scope === "notebook_diagnostics") {
      return Object.assign({}, base, {
        title: t("scope.notebooks"),
        verdict: verdictFromFindings(findings, t),
        metrics: [
          { label: t("metric.notebooks"), value: String(asArray(report.notebooks).length) },
          { label: t("metric.kernels"), value: String(asArray(report.kernels).length) },
        ],
        meta: [
          [t("meta.target"), text(report.target)],
          [t("meta.kind"), text(report.target_kind)],
        ],
      });
    }

    if (scope === "error_explanation") {
      return Object.assign({}, base, {
        title: t("scope.error"),
        verdict: verdictFromFindings(findings, t),
        metrics: [
          { label: t("metric.frames"), value: String(asArray(report.frames).length) },
          { label: t("metric.exception"), value: text(report.exception_type) },
        ],
        meta: [
          [t("meta.source"), text(report.source)],
          [t("meta.message"), text(report.message)],
        ],
      });
    }

    if (scope === "repair_plan") {
      const steps = asArray(report.steps);
      return Object.assign({}, base, {
        title: t("scope.repair"),
        kind: "steps",
        list: steps,
        verdict: {
          label: t(steps.length === 1 ? "verdict.steps" : "verdict.steps.plural", {
            count: steps.length,
          }),
          note: t("verdict.repair.note"),
          tone: "ok",
        },
        metrics: [{ label: t("metric.steps"), value: String(steps.length) }],
        meta: [[t("meta.source_report"), text(report.source_report)]],
      });
    }

    if (scope === "engine_info") {
      const modes = asRecord(report.modes);
      return Object.assign({}, base, {
        title: t("scope.info"),
        verdict: { label: t("verdict.engine.label"), note: t("verdict.engine.note"), tone: "ok" },
        metrics: [
          { label: t("metric.version"), value: text(report.version) },
          { label: t("metric.modes"), value: String(Object.keys(modes).length) },
        ],
        meta: [
          [t("meta.engine"), text(report.name)],
          [t("meta.engine_python"), text(report.engine_python)],
        ],
      });
    }

    return Object.assign({}, base, {
      title: t("scope.report"),
      verdict: verdictFromFindings(findings, t),
    });
  }

  function Badge(props) {
    return h("span", { className: "badge " + props.tone }, props.label);
  }

  function Metric(props) {
    return h(
      "span",
      { className: "metric" + (props.bad ? " bad" : "") },
      h("b", null, props.value),
      props.label,
    );
  }

  function FindingItem(props) {
    const finding = props.finding || {};
    const t = props.t;
    const [open, setOpen] = useState(false);
    const tone = toneFor(finding.severity);
    const evidence = asArray(finding.evidence).slice(0, 8);
    const nextSteps = asArray(finding.next_steps).slice(0, 5);
    const hasBody = Boolean(finding.explanation) || evidence.length > 0 || nextSteps.length > 0;
    return h(
      "div",
      { className: "finding " + tone },
      h(
        "div",
        {
          className: "finding-head",
          onClick: function () {
            if (hasBody) setOpen(!open);
          },
        },
        h(Badge, { tone: tone, label: finding.severity || "INFO" }),
        h("span", { className: "code" }, finding.code || "unknown"),
        h("span", { className: "sum" }, finding.summary || ""),
        h(Badge, { tone: "muted", label: finding.confidence || "UNKNOWN" }),
        hasBody ? h("span", { className: "meta2" }, open ? "\u2212" : "+") : null,
      ),
      open
        ? h(
            "div",
            { className: "finding-body" },
            finding.explanation ? h("p", null, finding.explanation) : null,
            evidence.length
              ? h(
                  "ul",
                  { className: "evidence" },
                  evidence.map(function (item, index) {
                    return h("li", { key: index, title: String(item) }, "\u00b7 " + String(item));
                  }),
                )
              : null,
            nextSteps.length
              ? h(
                  "div",
                  { className: "next" },
                  nextSteps.map(function (step, index) {
                    return h("div", { key: index }, "\u2192 " + String(step));
                  }),
                )
              : null,
          )
        : null,
    );
  }

  function CandidateRow(props) {
    const candidate = props.candidate || {};
    const t = props.t;
    const detail = [candidate.version, candidate.implementation]
      .concat(asArray(candidate.sources))
      .filter(Boolean)
      .join(" \u00b7 ");
    return h(
      "div",
      { className: "cand" },
      h(Badge, { tone: toneFor(candidate.confidence), label: candidate.confidence || "UNKNOWN" }),
      h("span", { className: "path", title: candidate.executable || "" }, candidate.executable || t("cand.noexec")),
      h("span", { className: "meta2" }, detail || t("cand.nometa")),
    );
  }

  function StepRow(props) {
    const step = props.step || {};
    const t = props.t;
    return h(
      "div",
      { className: "step" },
      h("div", { className: "num" }, String(props.index + 1)),
      h(
        "div",
        null,
        h("div", null, step.title || t("step.title")),
        h("div", { className: "argv" }, asArray(step.argv).join(" ") || t("step.nocmd")),
        h("div", { className: "verify" }, t("step.verify", { value: text(step.verification) })),
      ),
    );
  }

  function App() {
    const [lang, setLang] = useState(function () {
      return readPreference("pyd.lang", "en");
    });
    const [theme, setTheme] = useState(function () {
      return readPreference("pyd.theme", systemTheme());
    });
    const t = useMemo(
      function () {
        return translator(lang);
      },
      [lang],
    );

    const [bridge, setBridge] = useState(null);
    const [info, setInfo] = useState(null);
    const [candidates, setCandidates] = useState([]);
    const [interpreter, setInterpreter] = useState("");
    const [project, setProject] = useState("");
    const [mode, setMode] = useState("environment");
    const [traceback, setTraceback] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [report, setReport] = useState(null);
    const [lastReport, setLastReport] = useState(null);
    const [view, setView] = useState("list");
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef(null);
    const runRef = useRef(null);

    useEffect(
      function () {
        document.documentElement.lang = lang;
        document.documentElement.dir = lang === "fa" ? "rtl" : "ltr";
        writePreference("pyd.lang", lang);
      },
      [lang],
    );

    useEffect(
      function () {
        document.documentElement.dataset.theme = theme;
        writePreference("pyd.theme", theme);
      },
      [theme],
    );

    useEffect(function () {
      let cancelled = false;
      waitForBridge(5000).then(async function (ready) {
        if (cancelled) return;
        setBridge(ready);
        if (!ready) return;
        try {
          const meta = await bridgeApi(t).engine_info();
          if (!cancelled) setInfo(meta);
          const result = await bridgeApi(t).discover("");
          if (cancelled) return;
          const found = asArray(result.candidates);
          setCandidates(found);
          const first = found.find(function (item) {
            return item && item.executable;
          });
          if (first) setInterpreter(first.executable);
        } catch (err) {
          if (!cancelled) setError(errorText(err, t));
        }
      });
      return function () {
        cancelled = true;
      };
      // The bridge is resolved once; translations are read through the ref-like t.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(function () {
      function onDocumentClick(event) {
        if (menuRef.current && !menuRef.current.contains(event.target)) setMenuOpen(false);
      }
      document.addEventListener("mousedown", onDocumentClick);
      return function () {
        document.removeEventListener("mousedown", onDocumentClick);
      };
    }, []);

    const needsInterpreter = ["discovery", "error", "repair", "notebooks"].indexOf(mode) === -1;
    const needsProject = mode === "notebooks";
    const canRun =
      bridge === true &&
      !loading &&
      (!needsInterpreter || interpreter.trim().length > 0) &&
      (!needsProject || project.trim().length > 0) &&
      (mode !== "error" || traceback.trim().length > 0) &&
      (mode !== "repair" || lastReport !== null);

    const run = async function () {
      if (!canRun) return;
      setLoading(true);
      setError("");
      setMenuOpen(false);
      try {
        const payload =
          mode === "error" ? traceback : mode === "repair" ? JSON.stringify(lastReport) : "";
        const result = await bridgeApi(t).run_report(
          mode,
          interpreter.trim(),
          project.trim(),
          payload,
        );
        setReport(result);
        if (mode !== "repair") setLastReport(result);
        setView("list");
      } catch (err) {
        setError(errorText(err, t));
      } finally {
        setLoading(false);
      }
    };
    runRef.current = run;

    useEffect(function () {
      function onKey(event) {
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
          event.preventDefault();
          if (runRef.current) runRef.current();
        }
      }
      window.addEventListener("keydown", onKey);
      return function () {
        window.removeEventListener("keydown", onKey);
      };
    }, []);

    const summary = useMemo(
      function () {
        return report ? summarize(report, t) : null;
      },
      [report, t],
    );

    const enterRun = function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        run();
      }
    };

    const available = candidates.filter(function (item) {
      return item && item.executable;
    });

    const menu = menuOpen
      ? h(
          "div",
          { className: "menu" },
          available.length
            ? available.map(function (item) {
                return h(
                  "button",
                  {
                    key: item.executable,
                    onClick: function () {
                      setInterpreter(item.executable);
                      setMenuOpen(false);
                    },
                  },
                  h("div", null, item.executable),
                  h(
                    "div",
                    { className: "muted" },
                    [item.version, item.implementation]
                      .concat(asArray(item.sources))
                      .filter(Boolean)
                      .join(" \u00b7 "),
                  ),
                );
              })
            : h("div", { className: "muted", style: { padding: "8px 10px" } }, t("menu.empty")),
        )
      : null;

    const command = h(
      "div",
      { className: "command" },
      h(
        "div",
        { className: "cmd-row" },
        h(
          "div",
          { className: "field interp", ref: menuRef },
          h("label", null, t("label.interpreter")),
          h("input", {
            value: interpreter,
            placeholder: t("ph.interpreter"),
            onChange: function (event) {
              setInterpreter(event.target.value);
            },
            onKeyDown: enterRun,
          }),
          h(
            "button",
            {
              className: "chev",
              title: t("title.chev"),
              onClick: function () {
                setMenuOpen(!menuOpen);
              },
            },
            "\u25be",
          ),
          menu,
        ),
        h(
          "div",
          { className: "field" },
          h("label", null, t("label.project")),
          h("input", {
            value: project,
            placeholder: t("ph.project"),
            onChange: function (event) {
              setProject(event.target.value);
            },
            onKeyDown: enterRun,
          }),
        ),
        h(
          "button",
          { className: "run", onClick: run, disabled: !canRun },
          loading ? t("btn.running") : t("btn.run"),
        ),
      ),
      h(
        "div",
        { className: "chips" },
        MODE_IDS.map(function (id) {
          return h(
            "button",
            {
              key: id,
              "data-mode": id,
              title: t("mode." + id + ".hint"),
              className: "chip" + (mode === id ? " active" : ""),
              onClick: function () {
                setMode(id);
              },
            },
            t("mode." + id),
          );
        }),
      ),
      mode === "error"
        ? h(
            "div",
            { className: "field trace" },
            h("label", null, t("label.traceback")),
            h("textarea", {
              rows: 7,
              value: traceback,
              placeholder: t("ph.traceback"),
              onChange: function (event) {
                setTraceback(event.target.value);
              },
            }),
          )
        : null,
      mode === "repair" && !lastReport ? h("p", { className: "hint" }, t("hint.repair")) : null,
    );

    const hero = h(
      "section",
      { className: "hero" + (report ? " compact" : "") },
      h("div", { className: "eyebrow" }, t("hero.eyebrow")),
      h("h1", null, report && summary ? summary.title : t("hero.title")),
      h("p", null, t("hero.sub")),
      command,
    );

    let body;
    if (error) {
      body = h("div", { className: "alert" }, error);
    } else if (loading) {
      body = h(
        "div",
        { className: "skeleton" },
        h("div", { className: "sk", style: { width: "38%" } }),
        h("div", { className: "sk", style: { width: "72%" } }),
        h("div", { className: "sk", style: { width: "56%" } }),
      );
    } else if (report && summary) {
      const listLabel =
        summary.kind === "candidates"
          ? t("list.candidates")
          : summary.kind === "steps"
            ? t("list.steps")
            : t("list.findings");
      let listContent;
      if (view === "json") {
        listContent = h("pre", { className: "json" }, JSON.stringify(report, null, 2));
      } else if (summary.kind === "candidates") {
        listContent = h(
          "div",
          { className: "feed" },
          summary.list.map(function (item, index) {
            return h(CandidateRow, { key: index, candidate: item, t: t });
          }),
        );
      } else if (summary.kind === "steps") {
        listContent = h(
          "div",
          { className: "steps" },
          summary.list.map(function (item, index) {
            return h(StepRow, { key: index, step: item, index: index, t: t });
          }),
        );
      } else if (summary.list.length === 0) {
        listContent = h("div", { className: "empty" }, t("empty.findings"));
      } else {
        listContent = h(
          "div",
          { className: "feed" },
          summary.list.map(function (item, index) {
            return h(FindingItem, { key: index, finding: item, t: t });
          }),
        );
      }

      body = h(
        "div",
        { className: "result" },
        h(
          "div",
          { className: "verdict" },
          h(
            "div",
            null,
            h(
              "h2",
              null,
              h("span", { className: "mark " + summary.verdict.tone }),
              summary.verdict.label,
            ),
            h("p", null, summary.verdict.note),
          ),
          h("span", { className: "pill" }, "schema " + text(report.schema_version)),
        ),
        summary.metrics.length
          ? h(
              "div",
              { className: "metrics" },
              summary.metrics.map(function (item) {
                return h(Metric, { key: item.label, ...item });
              }),
            )
          : null,
        summary.meta.length
          ? h(
              "div",
              { className: "meta" },
              summary.meta.map(function (row) {
                return h(
                  "div",
                  { key: row[0], className: "meta-row" },
                  h("span", null, row[0]),
                  h("span", { title: row[1] }, row[1]),
                );
              }),
            )
          : null,
        h(
          "div",
          { className: "toolbar" },
          h("h3", null, listLabel),
          h(
            "div",
            { className: "seg" },
            h(
              "button",
              {
                className: view === "list" ? "active" : "",
                onClick: function () {
                  setView("list");
                },
              },
              listLabel,
            ),
            h(
              "button",
              {
                className: view === "json" ? "active" : "",
                onClick: function () {
                  setView("json");
                },
              },
              t("btn.json"),
            ),
          ),
        ),
        listContent,
      );
    } else {
      body = h(
        "div",
        { className: "empty" },
        h("div", null, t("empty.ready")),
        h(
          "div",
          { className: "row" },
          h("span", { className: "pill" }, t("pill.noexec")),
          h("span", { className: "pill" }, t("pill.noimports")),
          h("span", { className: "pill" }, t("pill.nopip")),
          h("span", { className: "pill" }, t("pill.nomutations")),
        ),
      );
    }

    const bridgeLabel =
      bridge === true
        ? t("bridge.live")
        : bridge === false
          ? t("bridge.preview")
          : t("bridge.connecting");

    return h(
      "div",
      { className: "app" },
      h("div", { className: "aurora" }),
      h(
        "header",
        { className: "topbar" },
        h(
          "div",
          { className: "brand" },
          h("img", { className: "logo", src: "./assets/icon.svg", alt: "" }),
          h("span", null, "PyDoctor"),
          h("small", null, t("brand.sub")),
        ),
        h(
          "div",
          { className: "top-right" },
          info ? h("span", { className: "pill hide-sm" }, t("engine", { version: text(info.version) })) : null,
          h(
            "span",
            { className: "pill hide-sm" },
            h("span", { className: "dot" + (bridge ? "" : " off") }),
            bridgeLabel,
          ),
          h(
            "button",
            {
              className: "toggle",
              title: t("theme.toggle"),
              "aria-label": t("theme.toggle"),
              onClick: function () {
                setTheme(theme === "dark" ? "light" : "dark");
              },
            },
            theme === "dark" ? "\u263c" : "\u263e",
          ),
          h(
            "button",
            {
              className: "toggle lang",
              title: t("lang.toggle"),
              "aria-label": t("lang.toggle"),
              onClick: function () {
                setLang(lang === "en" ? "fa" : "en");
              },
            },
            lang === "en" ? "\u0641\u0627" : "EN",
          ),
        ),
      ),
      h("main", { className: "stage" }, hero, body),
      h("footer", { className: "foot" }, t("foot")),
    );
  }

  ReactDOM.createRoot(document.getElementById("root")).render(h(App));
})();
