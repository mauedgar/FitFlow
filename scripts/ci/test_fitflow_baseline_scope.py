"""Negative matrix for the real FitFlow baseline GitHub Actions scope script.

Uses disposable local Git repositories; no GitHub API, DB, Docker or secrets.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/fitflow-baseline-ci.yml"
STEP_NAME = "      - name: Record subject SHA/tree and decide changed scope"


def real_workflow_scope_script() -> str:
    """Return the literal Bash body executed by the workflow (not a copy)."""
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    start = lines.index(STEP_NAME)
    marker = next(i for i in range(start + 1, len(lines)) if lines[i] == "        run: |")
    script: list[str] = []
    for line in lines[marker + 1 :]:
        if line.startswith("          "):
            script.append(line[10:])
        elif line == "":
            script.append("")
        else:
            break
    assert script and script[0] == "set -euo pipefail", "missing executable shell body"
    assert 'git diff --name-only -z "$from" "$SUBJECT_SHA"' in "\n".join(script)
    return "\n".join(script) + "\n"


class TestBaselineScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = real_workflow_scope_script()
        cls.git = shutil.which("git")
        if not cls.git:
            raise unittest.SkipTest("git not installed")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="fitflow-scope-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "ir001-fixture@example.invalid")
        self._git("config", "user.name", "CI Scope Fixture")
        self.write("README.md", "base\n")
        self._git("add", "-A")
        self._git("commit", "-qm", "synthetic-base")
        self.base = self._git("rev-parse", "HEAD").stdout.strip()
        self._git("remote", "add", "origin", str(self.root))

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run((self.git or "git", *args), cwd=self.root, text=True, capture_output=True, check=True)

    def write(self, path: str, content: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def commit_changes(self, paths: list[str], delete_paths: list[str] | None = None) -> str:
        for path in paths:
            self.write(path, "synthetic-modification\n")
        for path in delete_paths or []:
            (self.root / path).unlink()
        self._git("add", "-A")
        self._git("commit", "-qm", "synthetic-head")
        return self._git("rev-parse", "HEAD").stdout.strip()

    def invoke(
        self,
        head: str,
        *,
        event: str = "pull_request",
        before: str = "",
        base: str | None = None,
        intercept_diff: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
        output = Path(self.temp.name) / "github_output.txt"
        output.write_text("", encoding="utf-8")
        env = os.environ.copy()
        env.update({
            "SUBJECT_SHA": head,
            "BASE_SHA": self.base if base is None else base,
            "BEFORE_SHA": before,
            "EVENT_NAME": event,
            "GITHUB_OUTPUT": str(output),
        })
        if intercept_diff:
            fake_bin = Path(self.temp.name) / "bin"
            fake_bin.mkdir(exist_ok=True)
            shim = fake_bin / "git"
            shim.write_text(
                '#!/bin/sh\nif [ "$1" = diff ]; then exit 73; fi\nexec "'
                + self.git + '" "$@"\n', encoding="utf-8"
            )
            shim.chmod(0o755)
            env["PATH"] = str(fake_bin) + os.pathsep + env["PATH"]
        result = subprocess.run(
            ["bash", "-c", self.script], cwd=self.root,
            text=True, capture_output=True, env=env, check=False,
        )
        values = dict(
            line.split("=", 1)
            for line in output.read_text(encoding="utf-8").splitlines()
            if "=" in line
        )
        return result, values

    def test_changed_path_classification_matrix(self) -> None:
        cases = (
            (["docs/changes.md"], ("false", "false")),
            (["README.md"], ("false", "false")),
            ([".github/pull_request_template.md"], ("false", "false")),
            (["backend/tests/test_synthetic.py"], ("true", "false")),
            (["pyproject.toml"], ("true", "false")),
            (["scripts/ci/new_check.py"], ("true", "false")),
            (["frontend/src/App.tsx"], ("false", "true")),
            ([".github/workflows/new.yml"], ("true", "true")),
            (["future/unknown.data"], ("true", "true")),
            (["backend/demo.py", "frontend/src/demo.ts"], ("true", "true")),
        )
        for paths, wanted in cases:
            with self.subTest(paths=paths):
                self.setUp()
                head = self.commit_changes(paths)
                result, got = self.invoke(head)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((got.get("backend"), got.get("frontend")), wanted)

    def test_deleted_backend_path_still_selects_backend(self) -> None:
        self.write("backend/tests/deleted.py", "present\n")
        self._git("add", "-A")
        self._git("commit", "-qm", "fixture-file-to-delete")
        self.base = self._git("rev-parse", "HEAD").stdout.strip()
        head = self.commit_changes([], delete_paths=["backend/tests/deleted.py"])
        result, got = self.invoke(head)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((got["backend"], got["frontend"]), ("true", "false"))

    def test_push_with_known_before_uses_changed_paths(self) -> None:
        head = self.commit_changes(["frontend/src/test.ts"])
        result, got = self.invoke(head, event="push", before=self.base)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((got["backend"], got["frontend"]), ("false", "true"))

    def test_push_with_missing_before_fails_safe_both(self) -> None:
        head = self.commit_changes(["docs/synthetic.md"])
        result, got = self.invoke(head, event="push", before="0" * 40)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((got["backend"], got["frontend"]), ("true", "true"))

    def test_wrong_subject_sha_fails_closed(self) -> None:
        self.commit_changes(["docs/synthetic.md"])
        result, got = self.invoke("1" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(got, {})

    def test_invalid_pr_base_fails_closed(self) -> None:
        head = self.commit_changes(["docs/synthetic.md"])
        result, got = self.invoke(head, base="1" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(got, {})

    def test_actual_git_diff_failure_fails_closed(self) -> None:
        head = self.commit_changes(["docs/synthetic.md"])
        result, got = self.invoke(head, intercept_diff=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(got, {})


if __name__ == "__main__":
    unittest.main()
