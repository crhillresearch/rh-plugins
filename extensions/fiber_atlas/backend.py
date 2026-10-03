"""Read-only projection helpers for Fiber Atlas.

Scientific boundary
-------------------
Fiber Atlas does not compute or promote rank evidence. It projects durable
Rank Hunter curve rows and already-recorded search artifacts into exploratory
family views. Nagao scores, clustering, rational-height patterns, root-number
patterns, search-yield patterns, bad-prime fingerprints, and visible
neighborhoods are scheduling/research signals only.

The specialization rigorous lower bound shown here is the maximum of the
rigorous lower-bound fields already stored on the curve row: exact_rank,
descent_lower, and generic_lower. The family baseline is resolved separately
from family-level evidence or the installed family manifest; a specialization's
mutable generic_lower field is never reused as the family baseline.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from fractions import Fraction
import json
import math
from pathlib import Path
from typing import Iterable


PLOT_METRICS = {
    "parameter": {
        "label": "parameter value",
        "axis": "t",
    },
    "log_height": {
        "label": "log rational height",
        "axis": "log10 max(|numerator|, denominator)",
    },
    "log_denominator": {
        "label": "log denominator",
        "axis": "log10 denominator",
    },
    "signed_log_numerator": {
        "label": "signed log numerator",
        "axis": "sign(n) · log10(1+|numerator|)",
    },
    "score": {
        "label": "Nagao score",
        "axis": "Nagao score",
    },
    "rigorous_lower": {
        "label": "rigorous lower",
        "axis": "rigorous rank lower bound",
    },
    "rank_jump": {
        "label": "rank jump / baseline excess",
        "axis": "rigorous lower − authoritative family baseline",
    },
    "root_number": {
        "label": "root number",
        "axis": "stored root number",
    },
    "exact_discoveries": {
        "label": "exact point discoveries",
        "axis": "durable exact point-discovery events",
    },
    "quartic_hits": {
        "label": "quartic hits",
        "axis": "persisted quartic point hits",
    },
    "covering_mapped": {
        "label": "covering mapped points",
        "axis": "mapped points from covering attempts",
    },
    "rigorous_points": {
        "label": "rigorous point witnesses",
        "axis": "stored rigorous-independent points",
    },
}


COLOR_METRICS = {
    "rank_jump": "Rank jump / baseline excess",
    "rigorous_lower": "Rigorous lower",
    "score": "Nagao score",
    "root_number": "Root number",
    "exact_rank": "Exact rank status",
}


SEARCH_YIELD_METRICS = {
    "exact_discoveries": "Exact point discoveries",
    "quartic_hits": "Quartic hits",
    "covering_mapped": "Covering mapped points",
    "rigorous_points": "Rigorous point witnesses",
}


@dataclass(frozen=True)
class RationalParameter:
    text: str
    value: Fraction
    numerator: int
    denominator: int
    log_height: float
    log_denominator: float
    signed_log_numerator: float

    @property
    def float_value(self) -> float:
        return safe_float(self.value)


@dataclass(frozen=True)
class FiberRecord:
    curve_id: int
    family: str
    parameter: str
    rational_parameter: RationalParameter | None
    score: float | None
    root_number: int | None
    generic_lower: int | None
    descent_lower: int | None
    exact_rank: int | None
    plugin_id: str | None
    plugin_version: str | None
    status: str | None
    created_at: str | None
    family_spec: str | None = None
    family_sha256: str | None = None
    family_baseline: int | None = None
    family_baseline_kind: str | None = None
    family_baseline_source: str | None = None
    family_baseline_detail: str | None = None
    bad_primes: tuple[int, ...] = ()
    point_discovery_events: int = 0
    exact_discoveries: int = 0
    exact_points: int = 0
    rigorous_points: int = 0
    quartic_searches: int = 0
    quartic_hits: int = 0
    covering_attempts: int = 0
    covering_ratpoints_hits: int = 0
    covering_mapped_points: int = 0

    @property
    def rigorous_lower(self) -> int | None:
        values = [
            value
            for value in (self.exact_rank, self.descent_lower, self.generic_lower)
            if value is not None
        ]
        return max(values) if values else None

    @property
    def rank_jump(self) -> int | None:
        """Difference from the authoritative family baseline.

        When family_baseline_kind is generic_lower_bound this is an excess above
        the recorded generic lower bound, not proof of a jump above the unknown
        exact generic rank.
        """
        lower = self.rigorous_lower
        if lower is None or self.family_baseline is None:
            return None
        return max(0, int(lower) - int(self.family_baseline))

    @property
    def baseline_is_exact(self) -> bool:
        return self.family_baseline_kind == "exact_generic_rank"

    @property
    def exact_known(self) -> bool:
        return self.exact_rank is not None

    @property
    def numerator(self) -> int | None:
        return (
            self.rational_parameter.numerator
            if self.rational_parameter is not None
            else None
        )

    @property
    def denominator(self) -> int | None:
        return (
            self.rational_parameter.denominator
            if self.rational_parameter is not None
            else None
        )


@dataclass(frozen=True)
class FamilyBaseline:
    value: int | None
    kind: str | None
    source: str | None
    detail: str | None = None

    @property
    def exact(self) -> bool:
        return self.kind == "exact_generic_rank"


@dataclass(frozen=True)
class FamilyInventory:
    family: str
    count: int
    max_rigorous_lower: int | None
    max_score: float | None


def safe_float(value, *, limit: float = 1e300) -> float:
    """Convert a numeric value to a finite plotting float with saturation."""
    try:
        out = float(value)
    except (OverflowError, ValueError, TypeError):
        sign = -1.0 if str(value).strip().startswith("-") else 1.0
        return sign * limit
    if math.isnan(out):
        return 0.0
    if math.isinf(out):
        return math.copysign(limit, out)
    return max(-limit, min(limit, out))


def parse_rational_parameter(text: str | None) -> RationalParameter | None:
    """Parse a stored specialization parameter as one exact rational.

    Some Rank Hunter rows can carry chart labels or non-rational parameter text.
    Those rows remain visible in tables but are deliberately omitted from
    parameter-geometry axes rather than guessed or coerced.
    """
    raw = str(text or "").strip()
    if not raw:
        return None
    try:
        value = Fraction(raw)
    except (ValueError, ZeroDivisionError):
        return None

    numerator = int(value.numerator)
    denominator = int(value.denominator)
    height = max(abs(numerator), denominator, 1)
    log_height = math.log10(height)
    log_denominator = math.log10(max(denominator, 1))
    sign = -1.0 if numerator < 0 else (1.0 if numerator > 0 else 0.0)
    signed_log_numerator = sign * math.log10(1 + abs(numerator))

    return RationalParameter(
        text=raw,
        value=value,
        numerator=numerator,
        denominator=denominator,
        log_height=log_height,
        log_denominator=log_denominator,
        signed_log_numerator=signed_log_numerator,
    )


def _int_or_none(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value):
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return out if math.isfinite(out) else None


def _table_exists(db, name: str) -> bool:
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (str(name),),
    ).fetchone() is not None


def _table_columns(db, name: str) -> set[str]:
    if not _table_exists(db, name):
        return set()
    return {
        str(row["name"] if hasattr(row, "keys") else row[1])
        for row in db.execute(f"PRAGMA table_info({name})").fetchall()
    }


def _curve_columns(db) -> set[str]:
    return _table_columns(db, "curves")


def _select_expr(columns: set[str], name: str) -> str:
    return name if name in columns else f"NULL AS {name}"


def _family_evidence_baseline(db, records: Iterable[FiberRecord]) -> FamilyBaseline | None:
    """Resolve rigorous family-level generic-rank evidence when available."""
    rows = list(records)
    columns = _table_columns(db, "family_evidence")
    required = {
        "family_spec",
        "status",
        "generic_lower",
        "generic_upper",
        "exact_generic_rank",
    }
    if not required.issubset(columns):
        return None

    specs = {
        str(record.family_spec).strip()
        for record in rows
        if str(record.family_spec or "").strip()
    }
    if len(specs) != 1:
        return None
    family_spec = next(iter(specs))

    family_sha_select = (
        "family_sha256"
        if "family_sha256" in columns
        else "NULL AS family_sha256"
    )
    evidence = db.execute(
        f"""
        SELECT id,family_spec,{family_sha_select},generic_lower,generic_upper,
               exact_generic_rank,status
        FROM family_evidence
        WHERE family_spec=? AND status='completed'
        ORDER BY id DESC
        """,
        (family_spec,),
    ).fetchall()
    if not evidence:
        return None

    record_shas = {
        str(record.family_sha256).strip()
        for record in rows
        if str(record.family_sha256 or "").strip()
    }
    if len(record_shas) == 1 and "family_sha256" in columns:
        wanted_sha = next(iter(record_shas))
        matching = [
            row
            for row in evidence
            if str(dict(row).get("family_sha256") or "").strip() == wanted_sha
        ]
        if matching:
            evidence = matching

    lowers = []
    uppers = []
    exacts = []
    for row in evidence:
        data = dict(row)
        if data.get("generic_lower") is not None:
            lowers.append(int(data["generic_lower"]))
        if data.get("generic_upper") is not None:
            uppers.append(int(data["generic_upper"]))
        if data.get("exact_generic_rank") is not None:
            value = int(data["exact_generic_rank"])
            exacts.append(value)
            lowers.append(value)
            uppers.append(value)

    lower = max(lowers) if lowers else None
    upper = min(uppers) if uppers else None
    if lower is not None and upper is not None and lower > upper:
        return None
    if lower is not None and upper is not None and lower == upper:
        return FamilyBaseline(
            value=int(lower),
            kind="exact_generic_rank",
            source="family_evidence",
            detail=f"completed family evidence for {family_spec}",
        )
    if lower is not None:
        return FamilyBaseline(
            value=int(lower),
            kind="generic_lower_bound",
            source="family_evidence",
            detail=f"completed family lower-bound evidence for {family_spec}",
        )
    return None


def _manifest_baseline(
    family: str,
    records: Iterable[FiberRecord],
    project_root=None,
) -> FamilyBaseline | None:
    """Resolve the installed family plugin's declared generic-rank baseline."""
    if project_root is None:
        return None
    root = Path(project_root).resolve()
    plugin_root = root / "plugins"
    if not plugin_root.exists():
        return None

    rows = list(records)
    plugin_ids = {
        str(record.plugin_id).strip()
        for record in rows
        if str(record.plugin_id or "").strip()
    }
    family_specs = {
        str(record.family_spec).strip()
        for record in rows
        if str(record.family_spec or "").strip()
    }

    candidates = []
    if len(plugin_ids) == 1:
        candidates.append(plugin_root / next(iter(plugin_ids)) / "plugin.json")
    else:
        candidates.extend(plugin_root.glob("*/plugin.json"))

    for path in candidates:
        if not path.is_file():
            continue
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        if not isinstance(manifest, dict):
            continue

        if len(plugin_ids) != 1:
            curve_family_name = str(manifest.get("curve_family_name") or "").strip()
            if curve_family_name != str(family).strip():
                continue

        claim = manifest
        variants = manifest.get("variants")
        if isinstance(variants, list) and len(family_specs) == 1:
            wanted_spec = next(iter(family_specs))
            for variant in variants:
                if not isinstance(variant, dict):
                    continue
                family_def = variant.get("family") or {}
                if not isinstance(family_def, dict):
                    continue
                if str(family_def.get("spec") or "").strip() == wanted_spec:
                    claim = variant
                    break

        value = claim.get("verified_generic_rank_lower")
        if value is None:
            value = claim.get("generic_rank")
        if value is None and claim is not manifest:
            value = manifest.get("verified_generic_rank_lower")
            if value is None:
                value = manifest.get("generic_rank")

        if isinstance(value, bool):
            continue
        try:
            value = int(value)
        except (TypeError, ValueError):
            continue
        if value < 0:
            continue

        plugin_id = str(manifest.get("id") or path.parent.name)
        version = str(manifest.get("version") or "").strip()
        status = str(
            claim.get("generic_rank_status")
            or claim.get("generic_rank_claim_state")
            or manifest.get("generic_rank_status")
            or manifest.get("generic_rank_claim_state")
            or ""
        ).strip()
        detail = f"{plugin_id}{' v' + version if version else ''}"
        if status:
            detail += f" · {status}"
        return FamilyBaseline(
            value=value,
            kind="generic_lower_bound",
            source="plugin_manifest",
            detail=detail,
        )
    return None


def resolve_family_baseline(
    db,
    family: str,
    records: Iterable[FiberRecord],
    *,
    project_root=None,
) -> FamilyBaseline:
    """Resolve one authoritative family baseline without using fiber promotion state."""
    rows = list(records)
    evidence = _family_evidence_baseline(db, rows)
    if evidence is not None:
        return evidence
    manifest = _manifest_baseline(family, rows, project_root=project_root)
    if manifest is not None:
        return manifest
    return FamilyBaseline(
        value=None,
        kind=None,
        source=None,
        detail="No authoritative family-level generic baseline was found.",
    )


def apply_family_baseline(
    records: Iterable[FiberRecord],
    baseline: FamilyBaseline,
) -> list[FiberRecord]:
    return [
        replace(
            record,
            family_baseline=baseline.value,
            family_baseline_kind=baseline.kind,
            family_baseline_source=baseline.source,
            family_baseline_detail=baseline.detail,
        )
        for record in records
    ]


def _is_prime(value: int) -> bool:
    """Fast primality screen for stored prime labels.

    Never trial-divide to sqrt(n): bad-prime metadata may contain very large
    primes, and that can pin the Streamlit process. For 64-bit integers this is
    deterministic Miller-Rabin; for larger integers the fixed bases are a fast
    strong probable-prime screen suitable for validating already-labelled
    metadata without blocking the UI.
    """
    n = int(value)
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    if n in small:
        return True
    for p in small:
        if n % p == 0:
            return False

    d = n - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    if n < (1 << 64):
        bases = (2, 325, 9375, 28178, 450775, 9780504, 1795265022)
    else:
        bases = small

    for a in bases:
        a %= n
        if a in (0, 1):
            continue
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def _prime_value(value) -> int | None:
    try:
        p = abs(int(str(value).strip()))
    except (TypeError, ValueError):
        return None
    return p if _is_prime(p) else None


def parse_bad_primes_json(raw) -> tuple[int, ...]:
    """Extract exact prime labels from common stored bad-prime JSON shapes.

    This intentionally avoids recursively treating every integer in arbitrary
    metadata as a prime: exponents, valuations, and counters must not become
    fake bad primes.
    """
    if raw is None:
        return ()
    value = raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return ()
        try:
            value = json.loads(text)
        except (TypeError, ValueError):
            return ()

    found: set[int] = set()

    def add(candidate):
        p = _prime_value(candidate)
        if p is not None:
            found.add(p)

    def visit(item, *, list_context=False):
        if isinstance(item, (int, str)):
            if list_context:
                add(item)
            return
        if isinstance(item, list):
            for child in item:
                if isinstance(child, dict):
                    visit(child)
                else:
                    add(child)
            return
        if not isinstance(item, dict):
            return

        for key in ("p", "prime"):
            if key in item:
                add(item.get(key))

        for key in ("primes", "bad_primes", "badPrimes"):
            if key in item and isinstance(item[key], list):
                visit(item[key], list_context=True)

        # A common compact representation is {"2": {...}, "3": {...}}.
        for key in item:
            p = _prime_value(key)
            if p is not None:
                found.add(p)

    visit(value, list_context=isinstance(value, list))
    return tuple(sorted(found))


def list_families(db) -> list[FamilyInventory]:
    """Return stored family inventory without mutating scientific state."""
    columns = _curve_columns(db)
    if "family" not in columns:
        return []

    exact = "exact_rank" if "exact_rank" in columns else "NULL"
    descent = "descent_lower" if "descent_lower" in columns else "NULL"
    generic = "generic_lower" if "generic_lower" in columns else "NULL"
    score = "score" if "score" in columns else "NULL"

    rows = db.execute(
        f"""
        SELECT family,
               COUNT(*) AS n,
               MAX(MAX(COALESCE({exact}, -1),
                       COALESCE({descent}, -1),
                       COALESCE({generic}, -1))) AS max_lower,
               MAX({score}) AS max_score
        FROM curves
        WHERE family IS NOT NULL AND TRIM(family)<>''
        GROUP BY family
        ORDER BY n DESC, family COLLATE NOCASE
        """
    ).fetchall()

    out = []
    for row in rows:
        data = dict(row)
        max_lower = _int_or_none(data.get("max_lower"))
        if max_lower is not None and max_lower < 0:
            max_lower = None
        out.append(
            FamilyInventory(
                family=str(data["family"]),
                count=int(data["n"] or 0),
                max_rigorous_lower=max_lower,
                max_score=_float_or_none(data.get("max_score")),
            )
        )
    return out


def _signal_map(db, family: str) -> dict[int, dict[str, int]]:
    signals: dict[int, dict[str, int]] = defaultdict(
        lambda: {
            "point_discovery_events": 0,
            "exact_discoveries": 0,
            "exact_points": 0,
            "rigorous_points": 0,
            "quartic_searches": 0,
            "quartic_hits": 0,
            "covering_attempts": 0,
            "covering_ratpoints_hits": 0,
            "covering_mapped_points": 0,
        }
    )

    point_cols = _table_columns(db, "points")
    if {"curve_id"}.issubset(point_cols):
        exact_expr = (
            "SUM(CASE WHEN COALESCE(p.exact_verified,0)=1 THEN 1 ELSE 0 END)"
            if "exact_verified" in point_cols
            else "0"
        )
        rigorous_expr = (
            "SUM(CASE WHEN COALESCE(p.rigorous_independent,0)=1 THEN 1 ELSE 0 END)"
            if "rigorous_independent" in point_cols
            else "0"
        )
        rows = db.execute(
            f"""
            SELECT p.curve_id,
                   {exact_expr} AS exact_points,
                   {rigorous_expr} AS rigorous_points
            FROM points p
            JOIN curves c ON c.id=p.curve_id
            WHERE c.family=?
            GROUP BY p.curve_id
            """,
            (str(family),),
        ).fetchall()
        for row in rows:
            data = dict(row)
            target = signals[int(data["curve_id"])]
            target["exact_points"] = int(data.get("exact_points") or 0)
            target["rigorous_points"] = int(data.get("rigorous_points") or 0)

    discovery_cols = _table_columns(db, "point_discoveries")
    if {"curve_id"}.issubset(discovery_cols):
        exact_expr = (
            "SUM(CASE WHEN COALESCE(pd.exact_verified,0)=1 THEN 1 ELSE 0 END)"
            if "exact_verified" in discovery_cols
            else "0"
        )
        rows = db.execute(
            f"""
            SELECT pd.curve_id,
                   COUNT(*) AS discovery_events,
                   {exact_expr} AS exact_discoveries
            FROM point_discoveries pd
            JOIN curves c ON c.id=pd.curve_id
            WHERE c.family=?
            GROUP BY pd.curve_id
            """,
            (str(family),),
        ).fetchall()
        for row in rows:
            data = dict(row)
            target = signals[int(data["curve_id"])]
            target["point_discovery_events"] = int(data.get("discovery_events") or 0)
            target["exact_discoveries"] = int(data.get("exact_discoveries") or 0)

    quartic_cols = _table_columns(db, "quartic_searches")
    if {"curve_id"}.issubset(quartic_cols):
        hits_expr = (
            "SUM(COALESCE(qs.point_count,0))"
            if "point_count" in quartic_cols
            else "0"
        )
        rows = db.execute(
            f"""
            SELECT qs.curve_id,
                   COUNT(*) AS quartic_searches,
                   {hits_expr} AS quartic_hits
            FROM quartic_searches qs
            JOIN curves c ON c.id=qs.curve_id
            WHERE c.family=? AND qs.curve_id IS NOT NULL
            GROUP BY qs.curve_id
            """,
            (str(family),),
        ).fetchall()
        for row in rows:
            data = dict(row)
            target = signals[int(data["curve_id"])]
            target["quartic_searches"] = int(data.get("quartic_searches") or 0)
            target["quartic_hits"] = int(data.get("quartic_hits") or 0)

    covering_cols = _table_columns(db, "covering_search_attempts")
    if {"curve_id"}.issubset(covering_cols):
        rat_expr = (
            "SUM(COALESCE(csa.ratpoints_hits,0))"
            if "ratpoints_hits" in covering_cols
            else "0"
        )
        mapped_expr = (
            "SUM(COALESCE(csa.mapped_points,0))"
            if "mapped_points" in covering_cols
            else "0"
        )
        rows = db.execute(
            f"""
            SELECT csa.curve_id,
                   COUNT(*) AS covering_attempts,
                   {rat_expr} AS covering_ratpoints_hits,
                   {mapped_expr} AS covering_mapped_points
            FROM covering_search_attempts csa
            JOIN curves c ON c.id=csa.curve_id
            WHERE c.family=?
            GROUP BY csa.curve_id
            """,
            (str(family),),
        ).fetchall()
        for row in rows:
            data = dict(row)
            target = signals[int(data["curve_id"])]
            target["covering_attempts"] = int(data.get("covering_attempts") or 0)
            target["covering_ratpoints_hits"] = int(
                data.get("covering_ratpoints_hits") or 0
            )
            target["covering_mapped_points"] = int(
                data.get("covering_mapped_points") or 0
            )

    return signals


def load_family(
    db,
    family: str,
    *,
    include_signals: bool = False,
    project_root=None,
) -> list[FiberRecord]:
    """Load durable curve rows.

    Search-yield history is deliberately lazy. Large research databases can
    contain very large points/discovery/quartic/covering tables, so ordinary
    family switching must not aggregate those tables on every Streamlit rerun.
    """
    columns = _curve_columns(db)
    wanted = (
        "id",
        "family",
        "parameter",
        "score",
        "root_number",
        "generic_lower",
        "descent_lower",
        "exact_rank",
        "plugin_id",
        "plugin_version",
        "family_spec",
        "family_sha256",
        "status",
        "created_at",
    )
    select = ", ".join(_select_expr(columns, name) for name in wanted)
    rows = db.execute(
        f"""
        SELECT {select}
        FROM curves
        WHERE family=?
        ORDER BY id ASC
        """,
        (str(family),),
    ).fetchall()
    signals = _signal_map(db, family) if include_signals else {}

    out = []
    for row in rows:
        data = dict(row)
        curve_id = int(data["id"])
        signal = signals.get(curve_id) or {
            "point_discovery_events": 0,
            "exact_discoveries": 0,
            "exact_points": 0,
            "rigorous_points": 0,
            "quartic_searches": 0,
            "quartic_hits": 0,
            "covering_attempts": 0,
            "covering_ratpoints_hits": 0,
            "covering_mapped_points": 0,
        }
        out.append(
            FiberRecord(
                curve_id=curve_id,
                family=str(data.get("family") or family),
                parameter=str(data.get("parameter") or ""),
                rational_parameter=parse_rational_parameter(data.get("parameter")),
                score=_float_or_none(data.get("score")),
                root_number=_int_or_none(data.get("root_number")),
                generic_lower=_int_or_none(data.get("generic_lower")),
                descent_lower=_int_or_none(data.get("descent_lower")),
                exact_rank=_int_or_none(data.get("exact_rank")),
                plugin_id=(
                    str(data["plugin_id"]) if data.get("plugin_id") is not None else None
                ),
                plugin_version=(
                    str(data["plugin_version"])
                    if data.get("plugin_version") is not None
                    else None
                ),
                family_spec=(
                    str(data["family_spec"])
                    if data.get("family_spec") is not None
                    else None
                ),
                family_sha256=(
                    str(data["family_sha256"])
                    if data.get("family_sha256") is not None
                    else None
                ),
                status=(
                    str(data["status"]) if data.get("status") is not None else None
                ),
                created_at=(
                    str(data["created_at"])
                    if data.get("created_at") is not None
                    else None
                ),
                bad_primes=(),
                point_discovery_events=signal["point_discovery_events"],
                exact_discoveries=signal["exact_discoveries"],
                exact_points=signal["exact_points"],
                rigorous_points=signal["rigorous_points"],
                quartic_searches=signal["quartic_searches"],
                quartic_hits=signal["quartic_hits"],
                covering_attempts=signal["covering_attempts"],
                covering_ratpoints_hits=signal["covering_ratpoints_hits"],
                covering_mapped_points=signal["covering_mapped_points"],
            )
        )
    baseline = resolve_family_baseline(
        db,
        family,
        out,
        project_root=project_root,
    )
    return apply_family_baseline(out, baseline)


def load_bad_prime_signals(db, family: str) -> dict[int, tuple[int, ...]]:
    """Load and parse bad-prime metadata explicitly, never on family switch."""
    columns = _curve_columns(db)
    if "bad_primes_json" not in columns:
        return {}
    rows = db.execute(
        """
        SELECT id, bad_primes_json
        FROM curves
        WHERE family=?
          AND bad_primes_json IS NOT NULL
          AND TRIM(bad_primes_json)<>''
        ORDER BY id ASC
        """,
        (str(family),),
    ).fetchall()
    out = {}
    for row in rows:
        data = dict(row)
        primes = parse_bad_primes_json(data.get("bad_primes_json"))
        if primes:
            out[int(data["id"])] = primes
    return out


def apply_bad_prime_signals(
    records: Iterable[FiberRecord],
    signals: dict[int, tuple[int, ...]] | None,
) -> list[FiberRecord]:
    """Attach a previously loaded bad-prime map without touching the database."""
    signals = signals or {}
    return [
        replace(
            record,
            bad_primes=tuple(signals.get(int(record.curve_id)) or ()),
        )
        for record in records
    ]


def load_search_yield_signals(db, family: str) -> dict[int, dict[str, int]]:
    """Load durable search-yield aggregates explicitly, never on family switch."""
    return {
        int(curve_id): dict(values)
        for curve_id, values in _signal_map(db, family).items()
    }


def apply_search_yield_signals(
    records: Iterable[FiberRecord],
    signals: dict[int, dict[str, int]] | None,
) -> list[FiberRecord]:
    """Attach a previously loaded signal map without touching the database."""
    rows = list(records)
    if not rows:
        return []
    signals = signals or {}
    out = []
    for record in rows:
        signal = signals.get(int(record.curve_id)) or {}
        out.append(
            replace(
                record,
                point_discovery_events=int(signal.get("point_discovery_events") or 0),
                exact_discoveries=int(signal.get("exact_discoveries") or 0),
                exact_points=int(signal.get("exact_points") or 0),
                rigorous_points=int(signal.get("rigorous_points") or 0),
                quartic_searches=int(signal.get("quartic_searches") or 0),
                quartic_hits=int(signal.get("quartic_hits") or 0),
                covering_attempts=int(signal.get("covering_attempts") or 0),
                covering_ratpoints_hits=int(signal.get("covering_ratpoints_hits") or 0),
                covering_mapped_points=int(signal.get("covering_mapped_points") or 0),
            )
        )
    return out


def enrich_search_yield(
    db,
    family: str,
    records: Iterable[FiberRecord],
) -> list[FiberRecord]:
    """Compatibility helper for explicit callers that want one-shot enrichment."""
    return apply_search_yield_signals(
        records,
        load_search_yield_signals(db, family),
    )


def metric_value(record: FiberRecord, metric_key: str) -> float | None:
    p = record.rational_parameter
    if metric_key == "parameter":
        return p.float_value if p is not None else None
    if metric_key == "log_height":
        return p.log_height if p is not None else None
    if metric_key == "log_denominator":
        return p.log_denominator if p is not None else None
    if metric_key == "signed_log_numerator":
        return p.signed_log_numerator if p is not None else None
    if metric_key == "score":
        return record.score
    if metric_key == "rigorous_lower":
        lower = record.rigorous_lower
        return float(lower) if lower is not None else None
    if metric_key == "rank_jump":
        jump = record.rank_jump
        return float(jump) if jump is not None else None
    if metric_key == "root_number":
        return (
            float(record.root_number)
            if record.root_number in (-1, 1)
            else None
        )
    if metric_key == "exact_discoveries":
        return float(record.exact_discoveries)
    if metric_key == "quartic_hits":
        return float(record.quartic_hits)
    if metric_key == "covering_mapped":
        return float(record.covering_mapped_points)
    if metric_key == "rigorous_points":
        return float(record.rigorous_points)
    raise KeyError(metric_key)


def plottable_records(
    records: Iterable[FiberRecord],
    x_metric: str,
    y_metric: str,
) -> list[tuple[FiberRecord, float, float]]:
    out = []
    for record in records:
        x = metric_value(record, x_metric)
        y = metric_value(record, y_metric)
        if x is None or y is None:
            continue
        if not (math.isfinite(x) and math.isfinite(y)):
            continue
        out.append((record, float(x), float(y)))
    return out


def bound_plotted(
    plotted: list[tuple[FiberRecord, float, float]],
    *,
    max_points: int = 3500,
) -> list[tuple[FiberRecord, float, float]]:
    """Bound SVG payload while retaining high-signal fibers deterministically."""
    max_points = max(100, int(max_points))
    if len(plotted) <= max_points:
        return plotted

    priority_count = min(len(plotted), max(50, max_points // 3))
    priority = sorted(
        plotted,
        key=lambda item: (
            -(item[0].rank_jump if item[0].rank_jump is not None else -1),
            -(item[0].rigorous_lower if item[0].rigorous_lower is not None else -1),
            -item[0].exact_discoveries,
            -item[0].quartic_hits,
            -item[0].covering_mapped_points,
            -(item[0].score if item[0].score is not None else -1e300),
            item[0].curve_id,
        ),
    )[:priority_count]
    keep_ids = {item[0].curve_id for item in priority}
    rest = sorted(
        (item for item in plotted if item[0].curve_id not in keep_ids),
        key=lambda item: item[0].curve_id,
    )
    slots = max_points - len(priority)
    if slots <= 0:
        return sorted(priority, key=lambda item: item[0].curve_id)
    step = len(rest) / float(slots)
    sampled = [
        rest[min(len(rest) - 1, int(index * step))]
        for index in range(slots)
        if rest
    ]
    unique = {item[0].curve_id: item for item in priority + sampled}
    return sorted(unique.values(), key=lambda item: item[0].curve_id)


def filter_records(
    records: Iterable[FiberRecord],
    *,
    root_filter: str = "Any",
    exact_filter: str = "Any",
    lower_min: int | None = None,
    lower_max: int | None = None,
    log_height_min: float | None = None,
    log_height_max: float | None = None,
    log_denominator_min: float | None = None,
    log_denominator_max: float | None = None,
) -> list[FiberRecord]:
    out = []
    for record in records:
        if root_filter == "-1" and record.root_number != -1:
            continue
        if root_filter == "+1" and record.root_number != 1:
            continue
        if root_filter == "Unknown" and record.root_number in (-1, 1):
            continue

        if exact_filter == "Exact rank stored" and not record.exact_known:
            continue
        if exact_filter == "Lower bound only" and record.exact_known:
            continue

        lower = record.rigorous_lower
        if lower_min is not None and (lower is None or lower < int(lower_min)):
            continue
        if lower_max is not None and (lower is None or lower > int(lower_max)):
            continue

        p = record.rational_parameter
        if any(
            value is not None
            for value in (
                log_height_min,
                log_height_max,
                log_denominator_min,
                log_denominator_max,
            )
        ):
            if p is None:
                continue
            if log_height_min is not None and p.log_height < float(log_height_min):
                continue
            if log_height_max is not None and p.log_height > float(log_height_max):
                continue
            if (
                log_denominator_min is not None
                and p.log_denominator < float(log_denominator_min)
            ):
                continue
            if (
                log_denominator_max is not None
                and p.log_denominator > float(log_denominator_max)
            ):
                continue
        out.append(record)
    return out


def family_summary(records: Iterable[FiberRecord]) -> dict:
    rows = list(records)
    lowers = [r.rigorous_lower for r in rows if r.rigorous_lower is not None]
    excess = [r for r in rows if (r.rank_jump or 0) > 0]
    exact = [r for r in rows if r.exact_known]
    rational = [r for r in rows if r.rational_parameter is not None]
    scores = [r.score for r in rows if r.score is not None]
    roots = [r.root_number for r in rows if r.root_number in (-1, 1)]
    baseline_record = next(
        (r for r in rows if r.family_baseline is not None),
        None,
    )
    excess_values = [
        r.rank_jump
        for r in rows
        if r.rank_jump is not None
    ]
    return {
        "fibers": len(rows),
        "rational_parameters": len(rational),
        "max_rigorous_lower": max(lowers) if lowers else None,
        "rank_jump_fibers": len(excess),
        "baseline_excess_fibers": len(excess),
        "max_baseline_excess": max(excess_values) if excess_values else None,
        "exact_rank_fibers": len(exact),
        "max_score": max(scores) if scores else None,
        "root_number_known": len(roots),
        "family_baseline": (
            baseline_record.family_baseline
            if baseline_record is not None
            else None
        ),
        "family_baseline_kind": (
            baseline_record.family_baseline_kind
            if baseline_record is not None
            else None
        ),
        "family_baseline_source": (
            baseline_record.family_baseline_source
            if baseline_record is not None
            else None
        ),
        "family_baseline_detail": (
            baseline_record.family_baseline_detail
            if baseline_record is not None
            else None
        ),
    }


def yield_summary(records: Iterable[FiberRecord]) -> dict[str, int]:
    rows = list(records)
    return {
        "discovery_events": sum(r.point_discovery_events for r in rows),
        "exact_discoveries": sum(r.exact_discoveries for r in rows),
        "exact_points": sum(r.exact_points for r in rows),
        "rigorous_points": sum(r.rigorous_points for r in rows),
        "quartic_searches": sum(r.quartic_searches for r in rows),
        "quartic_hits": sum(r.quartic_hits for r in rows),
        "covering_attempts": sum(r.covering_attempts for r in rows),
        "covering_ratpoints_hits": sum(r.covering_ratpoints_hits for r in rows),
        "covering_mapped_points": sum(r.covering_mapped_points for r in rows),
    }


def bad_prime_fingerprint(
    records: Iterable[FiberRecord],
    *,
    limit: int = 16,
) -> list[dict[str, float | int]]:
    rows = list(records)
    counts: Counter[int] = Counter()
    with_metadata = 0
    for record in rows:
        if record.bad_primes:
            with_metadata += 1
            counts.update(set(record.bad_primes))
    denominator = max(1, with_metadata)
    return [
        {
            "prime": int(prime),
            "fibers": int(count),
            "share": float(count) / denominator,
            "metadata_fibers": with_metadata,
        }
        for prime, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[: max(1, int(limit))]
    ]


def selection_payload(
    records: Iterable[FiberRecord],
    *,
    family: str,
    view: str,
    x_metric: str,
    y_metric: str,
    color_metric: str,
    filters: dict | None = None,
) -> dict:
    """Serialize one explicit Fiber Atlas research selection.

    The payload is intentionally execution-free. Core UI handoff code owns
    routing it to Target/Pipelines and adds the deterministic selection hash.
    """
    rows = list(records)
    parameters = []
    for record in rows:
        parameters.append(
            {
                "curve_id": int(record.curve_id),
                "parameter": str(record.parameter),
                "rigorous_lower": record.rigorous_lower,
                "generic_lower": record.generic_lower,
                "family_baseline": record.family_baseline,
                "family_baseline_kind": record.family_baseline_kind,
                "baseline_excess": record.rank_jump,
                "rank_jump": (
                    record.rank_jump if record.baseline_is_exact else None
                ),
                "score": record.score,
                "root_number": record.root_number,
            }
        )

    rational = [
        record.rational_parameter
        for record in rows
        if record.rational_parameter is not None
    ]
    scores = [record.score for record in rows if record.score is not None]
    lowers = [
        record.rigorous_lower
        for record in rows
        if record.rigorous_lower is not None
    ]

    envelope = {
        "fiber_count": len(rows),
        "rational_parameter_count": len(rational),
        "parameter_min": None,
        "parameter_max": None,
        "log_height_min": None,
        "log_height_max": None,
        "log_denominator_min": None,
        "log_denominator_max": None,
        "score_min": min(scores) if scores else None,
        "score_max": max(scores) if scores else None,
        "rigorous_lower_min": min(lowers) if lowers else None,
        "rigorous_lower_max": max(lowers) if lowers else None,
    }
    if rational:
        ordered = sorted(rational, key=lambda rec: rec.value)
        envelope.update(
            {
                "parameter_min": str(ordered[0].value),
                "parameter_max": str(ordered[-1].value),
                "log_height_min": min(rec.log_height for rec in rational),
                "log_height_max": max(rec.log_height for rec in rational),
                "log_denominator_min": min(rec.log_denominator for rec in rational),
                "log_denominator_max": max(rec.log_denominator for rec in rational),
            }
        )

    return {
        "source": "fiber_atlas",
        "kind": "fiber_selection",
        "family": str(family),
        "curve_ids": [int(record.curve_id) for record in rows],
        "parameters": parameters,
        "selection": {
            "view": str(view),
            "axis": {
                "x": str(x_metric),
                "y": str(y_metric),
                "color": str(color_metric),
            },
            "filters": dict(filters or {}),
            "family_baseline": (
                {
                    "value": rows[0].family_baseline,
                    "kind": rows[0].family_baseline_kind,
                    "source": rows[0].family_baseline_source,
                }
                if rows
                else {"value": None, "kind": None, "source": None}
            ),
            "envelope": envelope,
        },
    }


def picker_order(records: Iterable[FiberRecord]) -> list[FiberRecord]:
    """Put the most interesting stored fibers first without calling it proof."""
    return sorted(
        records,
        key=lambda r: (
            -(r.rank_jump if r.rank_jump is not None else -1),
            -(r.rigorous_lower if r.rigorous_lower is not None else -1),
            -r.exact_discoveries,
            -r.quartic_hits,
            -r.covering_mapped_points,
            -(r.score if r.score is not None else -1e300),
            r.curve_id,
        ),
    )


def parameter_display(record: FiberRecord) -> str:
    p = record.rational_parameter
    if p is None:
        return record.parameter or "—"
    if p.denominator == 1:
        return str(p.numerator)
    return f"{p.numerator}/{p.denominator}"
