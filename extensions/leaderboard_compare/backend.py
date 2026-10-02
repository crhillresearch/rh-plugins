from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Iterable


LOCAL_SOURCE = "rank_hunter"
ICARM_SOURCE = "icarm"

TORSION_LABEL_ORDER = (
    "Trivial",
    "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C12",
    "C2 × C2", "C2 × C4", "C2 × C6", "C2 × C8",
)

METRICS = {
    "conductor": {
        "label": "log conductor",
        "axis": "size (log conductor) →",
        "help": "Natural log of the recorded conductor N.",
    },
    "naive": {
        "label": "naive height",
        "axis": "size (naive height) →",
        "help": "ICARM's imported naive height. Rank Hunter local rows do not currently persist this metric.",
    },
    "faltings": {
        "label": "Faltings height",
        "axis": "size (Faltings height) →",
        "help": "ICARM's imported stable Faltings height. Rank Hunter local rows do not currently persist this metric.",
    },
    "disc": {
        "label": "log |Δ|",
        "axis": "size (log |Δ|) →",
        "help": "Natural log of the absolute recorded discriminant.",
    },
}


@dataclass(frozen=True)
class ChartPoint:
    source: str
    source_label: str
    source_id: str
    rank_lower: int
    rank_evidence: str
    family: str
    parameter: str
    conductor: str | None
    discriminant: str | None
    naive_height: float | None
    faltings_height: float | None
    torsion_label: str | None = None
    url: str | None = None
    submitter: str | None = None
    updated_at: str | None = None

    def metric(self, key: str) -> float | None:
        if key == "conductor":
            return log_big_int(self.conductor)
        if key == "naive":
            return finite_float(self.naive_height)
        if key == "faltings":
            return finite_float(self.faltings_height)
        if key == "disc":
            return log_big_int(self.discriminant)
        raise KeyError(key)

    @property
    def label(self) -> str:
        if self.source == LOCAL_SOURCE:
            return f"Rank Hunter #{self.source_id}"
        if self.source == ICARM_SOURCE:
            return f"ICARM #{self.source_id}"
        return f"{self.source_label} #{self.source_id}"

    @property
    def detail(self) -> str:
        if self.source == LOCAL_SOURCE:
            parameter = self.parameter or "—"
            return f"{self.family} · parameter={parameter}"
        if self.submitter:
            return f"submitted by {self.submitter}"
        return "ICARM leaderboard"


def torsion_label_from_factors(values) -> str | None:
    """Convert source-provided invariant factors to Rank Hunter's display label."""
    if values is None:
        return None
    try:
        factors = tuple(int(value) for value in values if int(value) > 1)
    except (TypeError, ValueError):
        return None
    if not factors:
        return "Trivial"
    return " × ".join(f"C{value}" for value in factors)


def icarm_torsion_label(raw_json) -> str | None:
    """Read ICARM's source-provided torsion invariant factors without recomputation."""
    if raw_json is None:
        return None
    try:
        payload = json.loads(str(raw_json) or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or "torsion" not in payload:
        return None
    torsion = payload.get("torsion")
    if not isinstance(torsion, list):
        return None
    return torsion_label_from_factors(torsion)


def torsion_groups(points: Iterable[ChartPoint]) -> list[str]:
    """Known torsion labels present in the current comparison population."""
    labels = {str(p.torsion_label) for p in points if p.torsion_label}
    order = {label: i for i, label in enumerate(TORSION_LABEL_ORDER)}
    return sorted(labels, key=lambda label: (order.get(label, len(order)), label))


def filter_torsion(points: Iterable[ChartPoint], torsion_label: str | None) -> list[ChartPoint]:
    """Restrict to one known torsion group; None means no torsion restriction."""
    pts = list(points)
    if torsion_label is None:
        return pts
    wanted = str(torsion_label)
    return [p for p in pts if p.torsion_label == wanted]


def torsion_metadata_counts(points: Iterable[ChartPoint]) -> tuple[int, int]:
    pts = list(points)
    known = sum(1 for p in pts if p.torsion_label)
    return known, len(pts) - known


def finite_float(value) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return out if math.isfinite(out) else None


def abs_big_int(value) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text[0] in "+-":
        text = text[1:]
    if not text or not text.isdigit():
        return None
    text = text.lstrip("0")
    if not text:
        return None
    return int(text)


def log_big_int(value) -> float | None:
    """Natural log of |n| for an arbitrarily large decimal integer string."""
    n = abs_big_int(value)
    if n is None:
        return None
    text = str(n)
    k = min(15, len(text))
    return math.log(float(text[:k])) + (len(text) - k) * math.log(10.0)


def metric_order_value(point: ChartPoint, metric_key: str):
    """Exact ordering key when possible; logs are monotone so bigint ordering is exact."""
    if metric_key == "conductor":
        return abs_big_int(point.conductor)
    if metric_key == "disc":
        return abs_big_int(point.discriminant)
    return point.metric(metric_key)


def _table_exists(db, name: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (name,),
    ).fetchone()
    return row is not None


def _table_columns(db, name: str) -> set[str]:
    if not _table_exists(db, name):
        return set()
    return {str(row["name"]) for row in db.execute(f"PRAGMA table_info({name})")}


def _local_rank_expr() -> str:
    # Keep this aligned with rank42.db.proven_lower().
    return (
        "MAX(COALESCE(exact_rank,0),"
        " COALESCE(descent_lower,0),"
        " COALESCE(generic_lower,0))"
    )


def rank_extent(db) -> tuple[int, int]:
    mins: list[int] = []
    maxs: list[int] = []

    if _table_exists(db, "curves"):
        expr = _local_rank_expr()
        row = db.execute(
            f"SELECT MIN({expr}) AS lo, MAX({expr}) AS hi FROM curves WHERE {expr}>0"
        ).fetchone()
        if row is not None:
            if row["lo"] is not None:
                mins.append(int(row["lo"]))
            if row["hi"] is not None:
                maxs.append(int(row["hi"]))

    if _table_exists(db, "external_curves"):
        row = db.execute(
            """
            SELECT MIN(rank_lower_bound) AS lo, MAX(rank_lower_bound) AS hi
            FROM external_curves
            WHERE source=? AND active=1 AND rank_lower_bound>0
            """,
            (ICARM_SOURCE,),
        ).fetchone()
        if row is not None:
            if row["lo"] is not None:
                mins.append(int(row["lo"]))
            if row["hi"] is not None:
                maxs.append(int(row["hi"]))

    if not maxs:
        return (1, 1)
    return (max(1, min(mins or [1])), max(maxs))


def list_local_families(db, min_rank: int, max_rank: int) -> list[str]:
    if not _table_exists(db, "curves"):
        return []
    expr = _local_rank_expr()
    rows = db.execute(
        f"""
        SELECT DISTINCT family
        FROM curves
        WHERE {expr} BETWEEN ? AND ?
          AND family IS NOT NULL
          AND TRIM(family)<>''
        ORDER BY family COLLATE NOCASE
        """,
        (int(min_rank), int(max_rank)),
    ).fetchall()
    return [str(row["family"]) for row in rows]


def load_local_points(
    db,
    *,
    min_rank: int,
    max_rank: int,
    families: Iterable[str] | None = None,
) -> list[ChartPoint]:
    if not _table_exists(db, "curves"):
        return []

    expr = _local_rank_expr()
    params: list[object] = [int(min_rank), int(max_rank)]
    family_clause = ""
    chosen = [str(x) for x in (families or []) if str(x)]
    if chosen:
        marks = ",".join("?" for _ in chosen)
        family_clause = f" AND family IN ({marks})"
        params.extend(chosen)

    curve_columns = _table_columns(db, "curves")
    torsion_select = "torsion_label" if "torsion_label" in curve_columns else "NULL AS torsion_label"
    rows = db.execute(
        f"""
        SELECT id, family, parameter, conductor, discriminant,
               exact_rank, descent_lower, generic_lower, updated_at,
               {torsion_select},
               {expr} AS rank_lower
        FROM curves
        WHERE {expr} BETWEEN ? AND ?
        {family_clause}
        ORDER BY rank_lower ASC, id ASC
        """,
        params,
    ).fetchall()

    out: list[ChartPoint] = []
    for row in rows:
        rank_lower = int(row["rank_lower"] or 0)
        exact = row["exact_rank"]
        if exact is not None and int(exact) == rank_lower:
            rank_evidence = f"rank = {rank_lower}"
        else:
            rank_evidence = f"rank ≥ {rank_lower}"
        out.append(
            ChartPoint(
                source=LOCAL_SOURCE,
                source_label="Rank Hunter",
                source_id=str(row["id"]),
                rank_lower=rank_lower,
                rank_evidence=rank_evidence,
                family=str(row["family"] or "curve"),
                parameter=str(row["parameter"] or ""),
                conductor=str(row["conductor"]) if row["conductor"] is not None else None,
                discriminant=str(row["discriminant"]) if row["discriminant"] is not None else None,
                naive_height=None,
                faltings_height=None,
                torsion_label=str(row["torsion_label"]) if row["torsion_label"] else None,
                updated_at=str(row["updated_at"]) if row["updated_at"] is not None else None,
            )
        )
    return out


def load_icarm_points(db, *, min_rank: int, max_rank: int) -> list[ChartPoint]:
    if not _table_exists(db, "external_curves"):
        return []
    external_columns = _table_columns(db, "external_curves")
    raw_select = "raw_json" if "raw_json" in external_columns else "NULL AS raw_json"
    rows = db.execute(
        f"""
        SELECT source_id, rank_lower_bound, conductor, discriminant,
               naive_height, faltings_height, source_url, submitter,
               source_updated_at, {raw_select}
        FROM external_curves
        WHERE source=? AND active=1
          AND rank_lower_bound BETWEEN ? AND ?
        ORDER BY rank_lower_bound ASC, CAST(source_id AS INTEGER) ASC
        """,
        (ICARM_SOURCE, int(min_rank), int(max_rank)),
    ).fetchall()

    out: list[ChartPoint] = []
    for row in rows:
        rank_lower = int(row["rank_lower_bound"])
        out.append(
            ChartPoint(
                source=ICARM_SOURCE,
                source_label="ICARM",
                source_id=str(row["source_id"]),
                rank_lower=rank_lower,
                rank_evidence=f"rank ≥ {rank_lower}",
                family="ICARM leaderboard",
                parameter="",
                conductor=str(row["conductor"]) if row["conductor"] is not None else None,
                discriminant=str(row["discriminant"]) if row["discriminant"] is not None else None,
                naive_height=finite_float(row["naive_height"]),
                faltings_height=finite_float(row["faltings_height"]),
                torsion_label=icarm_torsion_label(row["raw_json"]),
                url=str(row["source_url"]) if row["source_url"] else None,
                submitter=str(row["submitter"]) if row["submitter"] else None,
                updated_at=str(row["source_updated_at"]) if row["source_updated_at"] else None,
            )
        )
    return out


def icarm_catalog_status(db) -> dict | None:
    if not _table_exists(db, "external_catalogs"):
        return None
    row = db.execute(
        """
        SELECT source_url, curve_count, best_rank_lower, snapshot_path,
               raw_sha256, fetched_at, updated_at
        FROM external_catalogs
        WHERE source=?
        """,
        (ICARM_SOURCE,),
    ).fetchone()
    return dict(row) if row is not None else None


def with_metric(points: Iterable[ChartPoint], metric_key: str) -> list[ChartPoint]:
    return [p for p in points if p.metric(metric_key) is not None]


def best_per_rank(points: Iterable[ChartPoint], metric_key: str) -> list[ChartPoint]:
    """Lowest metric at each rank, separately for each source. Ties are kept."""
    pts = with_metric(points, metric_key)
    minima: dict[tuple[str, int], object] = {}
    for p in pts:
        key = (p.source, p.rank_lower)
        value = metric_order_value(p, metric_key)
        assert value is not None
        prev = minima.get(key)
        if prev is None or value < prev:
            minima[key] = value
    return [
        p
        for p in pts
        if metric_order_value(p, metric_key) == minima[(p.source, p.rank_lower)]
    ]


def record_frontier(points: Iterable[ChartPoint], metric_key: str) -> list[ChartPoint]:
    """Per-source records: no equal-or-higher rank has a smaller metric."""
    best = best_per_rank(points, metric_key)
    by_source: dict[str, list[ChartPoint]] = {}
    for p in best:
        by_source.setdefault(p.source, []).append(p)

    keep: list[ChartPoint] = []
    for source_points in by_source.values():
        rank_min: dict[int, object] = {}
        for p in source_points:
            v = metric_order_value(p, metric_key)
            assert v is not None
            prev = rank_min.get(p.rank_lower)
            rank_min[p.rank_lower] = v if prev is None else min(v, prev)
        frontier: dict[int, object] = {}
        best_higher = None
        for rank in sorted(rank_min, reverse=True):
            value = rank_min[rank]
            frontier[rank] = value if best_higher is None else min(value, best_higher)
            best_higher = value if best_higher is None else min(best_higher, value)
        for p in source_points:
            value = metric_order_value(p, metric_key)
            assert value is not None
            if value <= frontier[p.rank_lower]:
                keep.append(p)
    return keep


def best_at_or_above(
    points: Iterable[ChartPoint],
    metric_key: str,
    *,
    min_rank: int,
    source: str,
) -> ChartPoint | None:
    eligible = [
        p
        for p in points
        if p.source == source
        and p.rank_lower >= int(min_rank)
        and p.metric(metric_key) is not None
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda p: (
            metric_order_value(p, metric_key),
            -p.rank_lower,
            int(p.source_id) if p.source_id.isdigit() else p.source_id,
        ),
    )
