"""Install or rebuild the DMT curves2 corpus for Rank Hunter.

Normal Rank Hunter use installs the latest validated curves2-db artifact
produced by the DMT corpus workflow. A full reconstruction from the historical
GitHub Actions artifact ledger remains available as a fallback and for explicit
maintenance work.
"""
from __future__ import annotations

import argparse
import base64
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE_REPO = "crhillresearch/dmt-rank-jumps"
SOURCE_REF = "feature/build-curves2-corpus"
SOURCE_PATH = "tools/build_curves2.py"
WORKFLOW_FILE = "build-curves2.yml"
PREBUILT_ARTIFACT = "curves2-db"


def _gh_executable() -> str:
    gh = shutil.which("gh")
    if not gh:
        raise SystemExit(
            "GitHub CLI (gh) is required to install the private DMT corpus. "
            "Install gh and authenticate it with access to "
            "crhillresearch/dmt-rank-jumps."
        )
    return gh


def _gh_json(args):
    proc = subprocess.run(
        [_gh_executable(), *args],
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        raise RuntimeError((proc.stderr or proc.stdout or "").strip())
    return json.loads(proc.stdout)


def _latest_successful_run_id() -> int:
    payload = _gh_json([
        "api",
        "--method", "GET",
        (
            f"repos/{SOURCE_REPO}/actions/workflows/{WORKFLOW_FILE}/runs"
            f"?branch={SOURCE_REF}&status=success&per_page=20"
        ),
    ])
    for run in payload.get("workflow_runs") or []:
        if (
            str(run.get("conclusion") or "") == "success"
            and str(run.get("head_branch") or "") == SOURCE_REF
        ):
            return int(run["id"])
    raise RuntimeError(
        f"No successful {WORKFLOW_FILE} run is available on {SOURCE_REF}."
    )


def _validate_corpus(path: Path) -> dict:
    path = Path(path)
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"Downloaded corpus is missing or empty: {path}")
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    try:
        tables = {
            str(row["name"])
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        required = {"corpus_meta", "curves", "observations"}
        missing = required - tables
        if missing:
            raise RuntimeError(
                "Downloaded corpus is missing tables: " + ", ".join(sorted(missing))
            )
        meta = {
            str(row["key"]): str(row["value"])
            for row in db.execute("SELECT key,value FROM corpus_meta")
        }
        if meta.get("schema_version") != "1":
            raise RuntimeError(
                f"Unsupported curves2 schema {meta.get('schema_version')!r}."
            )
        curves = int(db.execute("SELECT COUNT(*) FROM curves").fetchone()[0])
        observations = int(
            db.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        )
        exact_curves = int(
            db.execute(
                "SELECT COUNT(*) FROM curves WHERE exact_rank IS NOT NULL"
            ).fetchone()[0]
        )
        if curves <= 0 or observations <= 0:
            raise RuntimeError(
                "Downloaded curves2 corpus contains no usable curve evidence."
            )
        return {
            "curves": curves,
            "observations": observations,
            "exact_curves": exact_curves,
            "built_at": meta.get("built_at"),
            "failed_artifacts": int(meta.get("failed_artifacts") or 0),
        }
    finally:
        db.close()


def _download_prebuilt(output: Path) -> dict:
    run_id = _latest_successful_run_id()
    with tempfile.TemporaryDirectory(prefix="rh-curves2-install-") as td:
        dest = Path(td)
        proc = subprocess.run(
            [
                _gh_executable(),
                "run", "download", str(run_id),
                "-R", SOURCE_REPO,
                "-n", PREBUILT_ARTIFACT,
                "-D", str(dest),
            ],
            text=True,
            capture_output=True,
        )
        if proc.returncode:
            raise RuntimeError((proc.stderr or proc.stdout or "").strip())

        candidates = sorted(dest.rglob("curves2.db"))
        if len(candidates) != 1:
            raise RuntimeError(
                f"Expected one curves2.db in {PREBUILT_ARTIFACT}; found "
                f"{len(candidates)}."
            )
        stats = _validate_corpus(candidates[0])
        tmp = output.with_suffix(output.suffix + ".installing")
        if tmp.exists():
            tmp.unlink()
        shutil.copy2(candidates[0], tmp)
        _validate_corpus(tmp)
        tmp.replace(output)
    return {"run_id": run_id, **stats}


def _fetch_builder() -> str:
    gh = _gh_executable()
    api_path = f"repos/{SOURCE_REPO}/contents/{SOURCE_PATH}?ref={SOURCE_REF}"
    proc = subprocess.run(
        [gh, "api", api_path],
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        raise RuntimeError(
            "Could not fetch the authoritative DMT corpus builder via gh.\n"
            + (proc.stderr or proc.stdout or "").strip()
        )
    payload = json.loads(proc.stdout)
    return base64.b64decode(payload["content"]).decode("utf-8")


def _rebuild(args, output: Path, cache: Path) -> int:
    source = _fetch_builder()
    with tempfile.TemporaryDirectory(prefix="rh-dmt-corpus-") as td:
        builder = Path(td) / "build_curves2.py"
        builder.write_text(source, encoding="utf-8")
        cmd = [
            sys.executable,
            str(builder),
            "--output", str(output),
            "--artifact-cache", str(cache),
            "--plugin-id", args.plugin_id,
            "--corpus-id", args.corpus_id,
            "--repo", SOURCE_REPO,
        ]
        if args.project_root:
            cmd += ["--project-root", str(Path(args.project_root).resolve())]
        return subprocess.call(cmd)


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Install DMT curves2 corpus")
    ap.add_argument("--output", required=True)
    ap.add_argument("--artifact-cache", required=True)
    ap.add_argument("--project-root")
    ap.add_argument("--plugin-id", default="dmt_triad_rank4")
    ap.add_argument("--corpus-id", default="curves2")
    ap.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Reconstruct from historical GitHub Actions artifacts instead of installing the latest prebuilt corpus.",
    )
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    output = Path(args.output).resolve()
    cache = Path(args.artifact_cache).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)

    if not args.force_rebuild:
        try:
            stats = _download_prebuilt(output)
            print(
                "RANK_HUNTER_CORPUS_INSTALL="
                + json.dumps(
                    {"output": str(output), "source": "prebuilt", **stats},
                    sort_keys=True,
                ),
                flush=True,
            )
            return 0
        except Exception as exc:
            print(
                f"[curves2] prebuilt install unavailable: {type(exc).__name__}: {exc}",
                file=sys.stderr,
                flush=True,
            )
            print(
                "[curves2] falling back to full artifact-ledger reconstruction.",
                file=sys.stderr,
                flush=True,
            )

    return _rebuild(args, output, cache)


if __name__ == "__main__":
    raise SystemExit(main())
