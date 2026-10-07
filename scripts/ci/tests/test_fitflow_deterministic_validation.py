from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "fitflow_deterministic_validation.py"
SPEC = importlib.util.spec_from_file_location("fitflow_deterministic_validation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

SUBJECT = {
    "repository": "mauedgar/FitFlow",
    "commit": "0123456789abcdef0123456789abcdef01234567",
    "tree": "89abcdef0123456789abcdef0123456789abcdef",
}
EXECUTION = {
    "provider": "github-actions",
    "run_id": "123",
    "run_attempt": 1,
    "workflow_ref": "mauedgar/FitFlow/.github/workflows/deterministic-ci.yml@refs/heads/develop",
    "workflow_sha": "fedcba9876543210fedcba9876543210fedcba98",
}


class ValidationRunnerTests(unittest.TestCase):
    def test_pass_requires_exact_subject_and_backend_tests(self) -> None:
        request, receipt, exit_code = MODULE.run_validation(
            repository_root=Path("."),
            repository=SUBJECT["repository"],
            subject_sha=SUBJECT["commit"],
            expected_tree=SUBJECT["tree"],
            execution=EXECUTION,
            observe=lambda _root, _repo: SUBJECT,
            execute=lambda _root: {"status": "PASS", "elapsed_ms": 7},
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(request["profile"], {"id": "fitflow-backend-regression", "version": "v0"})
        self.assertEqual(receipt["correspondence"], "EXACT")
        self.assertEqual(receipt["conclusion"], "PASS")
        self.assertEqual(receipt["effect_state"], "NONE")

    def test_subject_mismatch_fails_before_backend_tests(self) -> None:
        executed = False

        def execute(_root: Path):
            nonlocal executed
            executed = True
            return {"status": "PASS", "elapsed_ms": 1}

        _request, receipt, exit_code = MODULE.run_validation(
            repository_root=Path("."),
            repository=SUBJECT["repository"],
            subject_sha=SUBJECT["commit"],
            expected_tree=SUBJECT["tree"],
            execution=EXECUTION,
            observe=lambda _root, _repo: {**SUBJECT, "commit": "a" * 40},
            execute=execute,
        )
        self.assertEqual(exit_code, 1)
        self.assertFalse(executed)
        self.assertEqual(receipt["correspondence"], "MISMATCH")
        self.assertEqual(receipt["conclusion"], "FAIL")

    def test_backend_failure_preserves_exact_subject_and_terminal_reason(self) -> None:
        _request, receipt, exit_code = MODULE.run_validation(
            repository_root=Path("."),
            repository=SUBJECT["repository"],
            subject_sha=SUBJECT["commit"],
            expected_tree=SUBJECT["tree"],
            execution=EXECUTION,
            observe=lambda _root, _repo: SUBJECT,
            execute=lambda _root: {
                "status": "FAIL",
                "elapsed_ms": 12,
                "reason": "backend-tests: exit code 1",
            },
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(receipt["correspondence"], "EXACT")
        self.assertEqual(receipt["conclusion"], "FAIL")
        self.assertEqual(receipt["reason"], "backend-tests: exit code 1")

    def test_operation_and_attempt_must_be_distinct(self) -> None:
        with self.assertRaises(ValueError):
            MODULE.run_validation(
                repository_root=Path("."),
                repository=SUBJECT["repository"],
                subject_sha=SUBJECT["commit"],
                expected_tree=None,
                execution=EXECUTION,
                operation_id="same",
                execution_attempt_id="same",
                observe=lambda _root, _repo: SUBJECT,
                execute=lambda _root: {"status": "PASS", "elapsed_ms": 1},
            )


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_is_manual_read_only_ubuntu_and_cross_validates_contract(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[3]
            / ".github"
            / "workflows"
            / "deterministic-ci.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("runs-on: ubuntu-latest", workflow)
        self.assertIn("postgres:15-alpine", workflow)
        self.assertIn("redis:7-alpine", workflow)
        self.assertIn("ref: ${{ inputs.subject_sha }}", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("fitflow_deterministic_validation.py", workflow)
        self.assertIn("mauedgar/tecnotron-ai", workflow)
        self.assertIn("f28c812cff4d9c6dd27d71a084fbccfffbadd735", workflow)
        self.assertIn("DeterministicValidationRequest.parse", workflow)
        self.assertIn("DeterministicValidationReceipt.parse", workflow)


if __name__ == "__main__":
    unittest.main()
