"""Kihara specialization rank-claim helpers for current Rank Hunter.

The published generic-rank theorem is historical metadata.  A stored
``generic_lower`` is specialization evidence and is written only after the
core exact lower-bound certificate verifies the fourteen specialized sections.
"""
from __future__ import annotations

from rank42.db import get_curve, log_event, update_curve
from rank42.exact_lb import (
    ExactCertificateFailure, ExactCertificateTimeout, run_exact_certificate,
)
from rank42.points import upsert_point

PLUGIN_ID = "kihara2001_rank14"
HISTORICAL_GENERIC_RANK_LOWER = 14
BASELINE_SEARCH_REF = "family:exact-baseline"


def _supported_baseline_count(db, curve_id):
    row = db.execute(
        """SELECT COUNT(*) AS n FROM points
           WHERE curve_id=? AND exact_verified=1 AND rigorous_independent=1
             AND (role='generic_section' OR search_ref=?)""",
        (int(curve_id), BASELINE_SEARCH_REF),
    ).fetchone()
    return int(row["n"] or 0)


def reconcile_specialization_lower(db, curve_id):
    """Drop unsupported legacy Kihara ``generic_lower`` values conservatively.

    v1.1.0 could write ``generic_lower=14`` after only a numerical height
    screen.  Current core treats that column as rigorous specialization
    evidence.  Preserve a value only when the point ledger contains enough
    exact rigorous family-baseline witnesses to support it.
    """
    row = get_curve(db, int(curve_id))
    if row is None or row["generic_lower"] is None:
        return {"cleared": False, "supported": 0}
    lower = int(row["generic_lower"])
    supported = _supported_baseline_count(db, curve_id)
    if lower <= 0 or supported >= lower:
        return {"cleared": False, "supported": supported}
    update_curve(db, int(curve_id), generic_lower=None)
    log_event(
        db, int(curve_id), "warn",
        f"cleared unsupported legacy Kihara generic_lower={lower}; "
        f"rigorous family-baseline witnesses={supported}",
    )
    return {"cleared": True, "supported": supported, "previous_lower": lower}


def certify_specialized_sections(db, *, curve_id, E, basis, parameter, timeout=120):
    """Certify the specialized fourteen-section subgroup exactly.

    Returns the core certificate object with ``rigorous_lower`` when verified.
    Timeouts/failures/inconclusive results never write ``generic_lower``.
    """
    reconcile_specialization_lower(db, curve_id)
    current = get_curve(db, int(curve_id))
    supported = _supported_baseline_count(db, curve_id)
    if (
        current is not None
        and current["generic_lower"] is not None
        and int(current["generic_lower"]) >= HISTORICAL_GENERIC_RANK_LOWER
        and supported >= int(current["generic_lower"])
    ):
        return {
            "status": "cached_certified", "independent": True, "cached": True,
            "rigorous_lower": int(current["generic_lower"]),
        }

    points = [P for P in basis if not P.is_zero()]
    if len(points) != HISTORICAL_GENERIC_RANK_LOWER:
        msg = (
            f"Kihara specialization produced {len(points)} nonzero sections; "
            f"expected {HISTORICAL_GENERIC_RANK_LOWER}"
        )
        log_event(db, int(curve_id), "warn", msg)
        return {"status": "invalid_baseline", "independent": False, "error": msg}

    try:
        cert = run_exact_certificate(
            E.a_invariants(),
            [[str(P[0]), str(P[1])] for P in points],
            timeout=int(timeout),
        )
    except ExactCertificateTimeout as exc:
        log_event(db, int(curve_id), "warn", f"Kihara exact section certificate timed out: {exc}")
        return {"status": "timeout", "independent": False, "error": str(exc)}
    except ExactCertificateFailure as exc:
        log_event(db, int(curve_id), "warn", f"Kihara exact section certificate failed: {exc}")
        return {"status": "error", "independent": False, "error": str(exc)}

    if not cert.get("independent"):
        status = str(cert.get("status") or "inconclusive")
        level = "warn" if status == "dependent" else "info"
        log_event(db, int(curve_id), level, f"Kihara exact section certificate {status}")
        return cert

    lower = int(cert.get("rank_lower_bound") or 0)
    if lower < len(points):
        msg = f"exact certificate reported independence but lower bound {lower} < {len(points)}"
        log_event(db, int(curve_id), "error", msg)
        return {**cert, "status": "invalid_certificate", "independent": False, "error": msg}

    for idx, P in enumerate(points):
        upsert_point(
            db,
            curve_id=int(curve_id), x=P[0], y=P[1],
            source="family_generic_section", role="generic_section",
            exact_verified=True, independence_status="rigorous_independent",
            rigorous_independent=True, search_ref=BASELINE_SEARCH_REF,
            plugin_id=PLUGIN_ID,
            metadata={
                "section_index": idx,
                "family": "Kihara 2001",
                "parameter": str(parameter),
                "claim_class": "exact_specialization_lower_bound",
                "historical_generic_rank_lower": HISTORICAL_GENERIC_RANK_LOWER,
                "certificate": cert.get("certificate"),
            },
        )
    update_curve(db, int(curve_id), generic_lower=lower)
    log_event(db, int(curve_id), "info", f"exact specialized Kihara section lower bound {lower}")
    return {**cert, "rigorous_lower": lower}
