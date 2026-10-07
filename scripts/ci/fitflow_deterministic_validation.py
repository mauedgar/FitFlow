"""FitFlow deterministic validation binding v0.

Product-specific validation profile. Portable request/receipt compatibility is
validated by Tecnotron's pinned TypeScript/Zod contract in GitHub Actions.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Literal, TypedDict

PROFILE_ID = "fitflow-backend-regression"
PROFILE_VERSION = "v0"
REQUEST_SCHEMA = "tecnotron-deterministic-validation-request/v0"
RECEIPT_SCHEMA = "tecnotron-deterministic-validation-receipt/v0"


class Subject(TypedDict, total=False):
    repository: str
    commit: str
    tree: str
    expected_ref: str


class ExecutionRef(TypedDict):
    provider: Literal["github-actions"]
    run_id: str
    run_attempt: int
    workflow_ref: str
    workflow_sha: str


class Check(TypedDict, total=False):
    id: str
    status: Literal["PASS", "FAIL", "BLOCKED", "UNAVAILABLE", "CANCELLED", "UNKNOWN"]
    elapsed_ms: int
    reason: str


class CommandResult(TypedDict, total=False):
    status: Literal["PASS", "FAIL", "UNAVAILABLE", "UNKNOWN"]
    elapsed_ms: int
    reason: str


ObserveSubject = Callable[[Path, str], Subject]
ExecuteCommand = Callable[[Path], CommandResult]


def _git_value(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"GIT_COMMAND_FAILED git {' '.join(args)}: {detail}")
    return completed.stdout.strip()


def observe_subject(root: Path, repository: str) -> Subject:
    return {
        "repository": repository,
        "commit": _git_value(root, "rev-parse", "HEAD"),
        "tree": _git_value(root, "rev-parse", "HEAD^{tree}"),
    }


def execute_backend_regression(root: Path) -> CommandResult:
    started = time.monotonic_ns()
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "tests"],
            cwd=root / "backend",
            check=False,
        )
    except FileNotFoundError as exc:
        elapsed = (time.monotonic_ns() - started) // 1_000_000
        return {
            "status": "UNAVAILABLE",
            "elapsed_ms": int(elapsed),
            "reason": f"backend-tests: {exc}",
        }
    except OSError as exc:
        elapsed = (time.monotonic_ns() - started) // 1_000_000
        return {
            "status": "UNKNOWN",
            "elapsed_ms": int(elapsed),
            "reason": f"backend-tests: {exc}",
        }

    elapsed = (time.monotonic_ns() - started) // 1_000_000
    if completed.returncode != 0:
        return {
            "status": "FAIL",
            "elapsed_ms": int(elapsed),
            "reason": f"backend-tests: exit code {completed.returncode}",
        }
    return {"status": "PASS", "elapsed_ms": int(elapsed)}


def _subjects_match(requested: Subject, observed: Subject) -> bool:
    if requested["repository"] != observed["repository"]:
        return False
    if requested["commit"] != observed["commit"]:
        return False
    expected_tree = requested.get("tree")
    return expected_tree is None or expected_tree == observed.get("tree")


def _execution_from_environment() -> ExecutionRef:
    attempt_raw = os.environ.get("GITHUB_RUN_ATTEMPT", "")
    try:
        attempt = int(attempt_raw)
    except ValueError as exc:
        raise RuntimeError("GITHUB_RUN_ATTEMPT must be a positive integer") from exc
    if attempt < 1:
        raise RuntimeError("GITHUB_RUN_ATTEMPT must be a positive integer")

    values = {
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_ref": os.environ.get("GITHUB_WORKFLOW_REF"),
        "workflow_sha": os.environ.get("GITHUB_WORKFLOW_SHA"),
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RuntimeError(f"missing GitHub execution identity: {', '.join(missing)}")

    return {
        "provider": "github-actions",
        "run_id": str(values["run_id"]),
        "run_attempt": attempt,
        "workflow_ref": str(values["workflow_ref"]),
        "workflow_sha": str(values["workflow_sha"]),
    }


def _write_json(target: Path, value: object) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run_validation(
    *,
    repository_root: Path,
    repository: str,
    subject_sha: str,
    expected_tree: str | None,
    execution: ExecutionRef,
    operation_id: str | None = None,
    execution_attempt_id: str | None = None,
    observe: ObserveSubject = observe_subject,
    execute: ExecuteCommand = execute_backend_regression,
) -> tuple[dict[str, object], dict[str, object], int]:
    subject: Subject = {
        "repository": repository,
        "commit": subject_sha,
    }
    if expected_tree:
        subject["tree"] = expected_tree

    request: dict[str, object] = {
        "schema_version": REQUEST_SCHEMA,
        "subject": subject,
        "profile": {"id": PROFILE_ID, "version": PROFILE_VERSION},
        "evidence_refs": [],
    }
    if operation_id is not None or execution_attempt_id is not None:
        if not operation_id or not execution_attempt_id:
            raise ValueError("operation_id and execution_attempt_id must be provided together")
        if operation_id == execution_attempt_id:
            raise ValueError("execution_attempt_id must remain distinct from operation_id")
        request["correlation"] = {
            "operation_id": operation_id,
            "execution_attempt_id": execution_attempt_id,
        }

    base: dict[str, object] = {
        "schema_version": RECEIPT_SCHEMA,
        "requested_subject": subject,
        "profile": {"id": PROFILE_ID, "version": PROFILE_VERSION},
        "execution": execution,
        "effect_state": "NONE",
        "artifact_refs": [],
        "evidence_refs": [],
    }

    try:
        observed = observe(repository_root, repository)
    except Exception as exc:  # noqa: BLE001
        reason = f"subject-observation: {exc}"
        receipt = {
            **base,
            "observed_subject": None,
            "correspondence": "UNKNOWN",
            "checks": [{"id": "subject-observation", "status": "UNKNOWN", "elapsed_ms": 0, "reason": reason}],
            "conclusion": "UNKNOWN",
            "reason": reason,
        }
        return request, receipt, 2

    if not _subjects_match(subject, observed):
        reason = "observed Git subject does not match requested subject"
        receipt = {
            **base,
            "observed_subject": observed,
            "correspondence": "MISMATCH",
            "checks": [{"id": "subject-correspondence", "status": "FAIL", "elapsed_ms": 0, "reason": reason}],
            "conclusion": "FAIL",
            "reason": reason,
        }
        return request, receipt, 1

    checks: list[Check] = [{"id": "subject-correspondence", "status": "PASS", "elapsed_ms": 0}]
    result = execute(repository_root)
    check: Check = {
        "id": "backend-tests",
        "status": result["status"],
        "elapsed_ms": result["elapsed_ms"],
    }
    if result.get("reason"):
        check["reason"] = str(result["reason"])
    checks.append(check)

    conclusion = result["status"]
    receipt: dict[str, object] = {
        **base,
        "observed_subject": observed,
        "correspondence": "EXACT",
        "checks": checks,
        "conclusion": conclusion,
    }

    if conclusion == "PASS":
        return request, receipt, 0

    reason = str(result.get("reason") or "backend-tests did not pass")
    receipt["reason"] = reason
    return request, receipt, 1 if conclusion == "FAIL" else 2


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--expected-tree")
    parser.add_argument("--operation-id")
    parser.add_argument("--execution-attempt-id")
    parser.add_argument("--request-output", required=True)
    parser.add_argument("--receipt-output", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    execution = _execution_from_environment()
    request, receipt, exit_code = run_validation(
        repository_root=Path.cwd(),
        repository=args.repository,
        subject_sha=args.subject_sha,
        expected_tree=args.expected_tree,
        operation_id=args.operation_id,
        execution_attempt_id=args.execution_attempt_id,
        execution=execution,
    )
    _write_json(Path(args.request_output), request)
    _write_json(Path(args.receipt_output), receipt)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
