#!/usr/bin/env python3
"""Seeded PGL2 search wrapper for the Mestre/Fermigier sextuple family.

This wrapper enriches PGL2 search geometry from exact persisted sources:

* mapped native-quartic fibres already discovered on a stored Mestre curve;
* native-quartic fibres attached to stored rigorous elliptic generators in the
  exact point/search ledger; and
* exact elliptic->quartic inversion as a fallback when a rigorous generator has
  no persisted source fibre.

An optional seed curve may contribute the same kinds of x-coordinates as
search geometry for other specializations.  Elliptic points, independence and
rank evidence are never transported between fibres.  Every search hit is still
inverse-mapped and checked exactly by ``chart_search.py`` and every rank
increase still requires the normal exact certificate path.
"""
from __future__ import annotations

import json
import sys

import chart_search as cs


# The core subgroup-chart planner enumerates ordered triples of
# base+discovered anchors. Feeding dozens of seed fibres into that cubic
# enumeration can dominate the entire search before ratpoints ever starts.
# Seeded neighbour searches therefore use a bounded mixed bank. Target search
# is stricter: once rigorous non-base source fibres are recoverable, the
# discovered-anchor bank contains only those rigorous fibres. Together with the
# twelve structural base fibres this makes every subgroup chart genuinely
# rank-basis-informed instead of letting easier dependent rediscoveries win the
# chart-quality ranking.
SEEDED_FAMILY_ANCHOR_CAP = 16
RIGOROUS_TARGET_ANCHOR_CAP = 16


def _pop_seed_curve_id(argv):
    seed = 0
    out = [argv[0]]
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == "--seed-curve-id":
            if i + 1 >= len(argv):
                raise SystemExit("--seed-curve-id requires an integer")
            seed = int(argv[i + 1])
            i += 2
            continue
        if arg.startswith("--seed-curve-id="):
            seed = int(arg.split("=", 1)[1])
            i += 1
            continue
        out.append(arg)
        i += 1
    return seed, out


def _spread(values, limit):
    values = sorted(set(values), key=lambda x: (cs.rational_height_bits(x), x))
    limit = int(limit)
    if limit <= 0 or len(values) <= limit:
        return values
    if limit == 1:
        return [values[len(values) // 2]]
    idxs = []
    for i in range(limit):
        idx = round(i * (len(values) - 1) / (limit - 1))
        if idx not in idxs:
            idxs.append(idx)
    return [values[i] for i in idxs]


def _priority_spread(priority, others, limit):
    """Keep exact priority anchors, then fill the remaining bank by spread."""
    limit = int(limit)
    priority = sorted(set(priority), key=lambda x: (cs.rational_height_bits(x), x))
    priority_set = set(priority)
    others = [x for x in set(others) if x not in priority_set]
    others.sort(key=lambda x: (cs.rational_height_bits(x), x))
    if limit <= 0:
        return priority + others
    if len(priority) >= limit:
        return _spread(priority, limit)
    return priority + _spread(others, limit - len(priority))


def _stored_basis_on_current_model(row, E):
    """Return stored rigorous generators transported to ``E`` when possible.

    Older Mestre rows may contain witnesses on an earlier but isomorphic model.
    Those coordinates must not be interpreted directly on the current model.
    If the stored model is available and isomorphic, transport the points by an
    exact Sage isomorphism.  If anything is incompatible, decline to use those
    generators as chart geometry; the stored rank evidence itself is untouched.
    """
    lower = int(row["descent_lower"] or 0)
    if lower <= 0:
        return [], "no_descent_basis"
    try:
        raw = json.loads(row["generators_json"] or "[]")
    except Exception:
        return [], "bad_generators_json"
    if not raw:
        return [], "no_generators"

    source_curve = E
    transport = None
    mode = "current_model"
    try:
        stored_ainvs = json.loads(row["a_invariants_json"] or "null")
    except Exception:
        stored_ainvs = None
    if stored_ainvs:
        try:
            stored_ainvs = [cs.QQ(str(a)) for a in stored_ainvs]
            current_ainvs = [cs.QQ(a) for a in E.a_invariants()]
            if stored_ainvs != current_ainvs:
                source_curve = cs.family.EllipticCurve(cs.QQ, stored_ainvs)
                if not source_curve.is_isomorphic(E):
                    return [], "stored_model_not_isomorphic"
                transport = source_curve.isomorphism_to(E)
                mode = "exact_isomorphic_transport"
        except Exception:
            return [], "stored_model_unusable"

    points = []
    seen = set()
    for xy in raw:
        if not isinstance(xy, (list, tuple)) or len(xy) < 2:
            continue
        try:
            P0 = source_curve(cs.QQ(str(xy[0])), cs.QQ(str(xy[1])))
            P = transport(P0) if transport is not None else P0
        except Exception:
            continue
        if P.is_zero():
            continue
        key = cs._point_key(P)
        if key in seen:
            continue
        seen.add(key)
        points.append(P)
        if len(points) >= lower:
            break
    if len(points) < lower:
        return [], f"incomplete_{mode}"
    return points, mode


def _native_x_from_ledger_record(rec):
    """Return an exact native x-coordinate from one persisted quartic row."""
    try:
        pmeta = json.loads(rec["point_meta"] or "{}")
    except Exception:
        pmeta = {}
    try:
        smeta = json.loads(rec["search_meta"] or "{}")
    except Exception:
        smeta = {}
    source = str(smeta.get("source") or "")
    raw_x = pmeta.get("native_x")
    if raw_x is None and source == "mestre_sextuple_native_quartic":
        raw_x = rec["chart_x"]
    if raw_x is None:
        return None
    try:
        return cs._fq(raw_x)
    except Exception:
        return None


def _ledger_basis_native_x(db, curve_id, E, basis):
    """Match rigorous generators to their exact persisted quartic source rows.

    Mestre rank growth is stored after an exact quartic point has already been
    mapped to the deterministic elliptic model. For those generators the most
    reliable inverse map is therefore not symbolic inversion at all: reuse the
    exact ``native_x`` that produced the stored elliptic point, but only after
    matching ``mapped_point_json`` exactly on ``E``. This is provenance
    recovery, not transported rank evidence.
    """
    wanted = {cs._point_key(P) for P in basis if not P.is_zero()}
    if not wanted:
        return {}
    rows = db.execute(
        """
        SELECT qp.x AS chart_x, qp.metadata_json AS point_meta,
               qp.mapped_point_json AS mapped_point,
               qs.metadata_json AS search_meta
        FROM quartic_points qp
        JOIN quartic_searches qs ON qs.id=qp.search_id
        WHERE qs.curve_id=? AND qp.exact_verified=1
          AND qp.mapped_point_json IS NOT NULL
        ORDER BY qp.id ASC
        """,
        (int(curve_id),),
    ).fetchall()
    matched = {}
    for rec in rows:
        try:
            raw_point = json.loads(rec["mapped_point"] or "null")
        except Exception:
            raw_point = None
        if not isinstance(raw_point, (list, tuple)) or len(raw_point) < 2:
            continue
        try:
            P = E(cs.QQ(str(raw_point[0])), cs.QQ(str(raw_point[1])))
        except Exception:
            continue
        if P.is_zero():
            continue
        key = cs._point_key(P)
        if key not in wanted or key in matched:
            continue
        native_x = _native_x_from_ledger_record(rec)
        if native_x is not None:
            matched[key] = native_x
    return matched


def _exact_quartic_preimage(bundle, P):
    """Return ``(native_x, recovery_mode)`` for an elliptic point, exactly.

    First use the closed-form inverse obtained directly from the forward map.
    If that route does not round-trip, recover the preimage algebraically from
    the elliptic X-coordinate. Substituting

        v = (X*u^2 - D*u)/Q - y0,   x = x0 + u

    into ``v^2=f(x)`` gives a polynomial over Q whose rational nonzero roots
    contain every affine quartic preimage compatible with X. A root is accepted
    only after the quartic equation and the full forward map both check exactly.
    This fallback changes search geometry only; it cannot create or alter rank
    evidence.
    """
    if P.is_zero():
        return None

    data = bundle["map_data"]
    x0 = cs.QQ(data["x0"])
    y0 = cs.QQ(data["y0"])
    Q = cs.QQ(data["Q"])
    C = cs.QQ(data["C"])
    D = cs.QQ(data["D"])
    coeffs = [cs.QQ(c) for c in bundle["quartic_coefficients"]]
    coeffs_f = [cs._fq(c) for c in coeffs]

    try:
        X0, Y0 = P.xy()
        X = cs.QQ(X0)
        Y = cs.QQ(Y0)
    except Exception:
        X = cs.QQ(P[0])
        Y = cs.QQ(P[1])

    def accept_u(u, mode):
        u = cs.QQ(u)
        if u == 0:
            return None
        xq = x0 + u
        yq = (X * u**2 - D * u) / Q - y0

        # ``rank42.mobius_quartic.evaluate`` deliberately returns a stdlib
        # Fraction. Do the quartic equality in that same exact domain instead
        # of relying on mixed Sage-QQ/Fraction rich comparison.
        xq_f = cs._fq(xq)
        yq_f = cs._fq(yq)
        if yq_f * yq_f != cs.evaluate(coeffs_f, xq_f):
            return None
        try:
            back = cs.family.map_native_quartic_point(bundle, xq, yq)
        except Exception:
            return None
        if back != P:
            return None
        return xq_f, mode

    # Fast path: algebraic elimination using both elliptic coordinates.
    if Y != 0:
        try:
            direct_u = (Q**2 * (X + C) - D**2) / (Q * Y)
            hit = accept_u(direct_u, "closed_form")
            if hit is not None:
                return hit
        except Exception:
            pass

    # Robust exact fallback: use X only, solve the defining preimage equation
    # over QQ, then require an exact forward round-trip to P.
    try:
        R = cs.family.PolynomialRing(cs.QQ, "u")
        u = R.gen()
        xpoly = x0 + u
        vpoly = (X * u**2 - D * u) / Q - y0
        fpoly = sum((coeffs[i] * xpoly**i for i in range(len(coeffs))), R.zero())
        preimage_poly = vpoly**2 - fpoly
        for root, _mult in preimage_poly.roots(ring=cs.QQ):
            hit = accept_u(root, "algebraic_x")
            if hit is not None:
                return hit
    except Exception:
        pass
    return None


def _rigorous_basis_native_x(db, curve_id):
    """Recover exact native-quartic anchors for stored rigorous generators.

    Persisted exact point provenance is used first. Elliptic->quartic inversion
    is only a fallback for generators without a matching ledger row. Every
    inverse-derived anchor is verified on the native quartic and by an exact
    quartic->elliptic round-trip. Failure to recover a witness never aborts
    discovery and never changes stored rigorous rank evidence.
    """
    row = cs.get_curve(db, int(curve_id))
    if row is None or str(row["family"] or "") != cs.family.name():
        return [], {"mode": "not_mestre", "basis": 0, "skipped": 0}
    if int(row["descent_lower"] or 0) <= 0:
        return [], {"mode": "no_descent_basis", "basis": 0, "skipped": 0}

    try:
        t = cs._canonical_parameter(cs.QQ(str(row["parameter"])))
        bundle = cs.family.direct_search_bundle(t)
    except Exception:
        return [], {"mode": "model_construction_failed", "basis": 0, "skipped": 0}
    E = bundle["curve"]
    basis, mode = _stored_basis_on_current_model(row, E)
    if not basis:
        return [], {"mode": mode, "basis": 0, "skipped": 0}

    # Internal positive control. These eleven points are produced by the very
    # quartic map being inverted here, so all non-exceptional ones must recover.
    generic_total = len(bundle.get("basis") or [])
    generic_recovered = 0
    for P0 in bundle.get("basis") or []:
        if _exact_quartic_preimage(bundle, P0) is not None:
            generic_recovered += 1

    ledger = _ledger_basis_native_x(db, curve_id, E, basis)
    values = []
    seen = set()
    matched_basis = 0
    ledger_count = 0
    closed_form = 0
    algebraic = 0
    for P in basis:
        key = cs._point_key(P)
        if key in ledger:
            hit = (ledger[key], "ledger")
        else:
            hit = _exact_quartic_preimage(bundle, P)
        if hit is None:
            continue
        matched_basis += 1
        xq, recovery_mode = hit
        if recovery_mode == "ledger":
            ledger_count += 1
        elif recovery_mode == "closed_form":
            closed_form += 1
        elif recovery_mode == "algebraic_x":
            algebraic += 1
        if xq in seen:
            continue
        seen.add(xq)
        values.append(xq)

    return values, {
        "mode": mode,
        "basis": len(basis),
        "matched_basis": matched_basis,
        "skipped": max(0, len(basis) - matched_basis),
        "ledger": ledger_count,
        "closed_form": closed_form,
        "algebraic": algebraic,
        "generic_recovered": generic_recovered,
        "generic_total": generic_total,
    }


def _install_seed(seed_curve_id):
    seed_curve_id = int(seed_curve_id)
    original = cs._load_discovered_native_x
    basis_cache = {}
    seed_row = None

    def rigorous_values(db, curve_id):
        cid = int(curve_id)
        if cid not in basis_cache:
            basis_cache[cid] = _rigorous_basis_native_x(db, cid)
            values, meta = basis_cache[cid]
            if values or meta.get("skipped") or meta.get("basis"):
                print(
                    f"[mestre basis anchors] curve #{cid}: anchors={len(values)} "
                    f"matched={int(meta.get('matched_basis') or 0)}/"
                    f"{int(meta.get('basis') or 0)} "
                    f"ledger={int(meta.get('ledger') or 0)} "
                    f"closed_form={int(meta.get('closed_form') or 0)} "
                    f"algebraic={int(meta.get('algebraic') or 0)} "
                    f"generic_control={int(meta.get('generic_recovered') or 0)}/"
                    f"{int(meta.get('generic_total') or 0)} mode={meta.get('mode')}",
                    flush=True,
                )
        return basis_cache[cid][0]

    def seeded_loader(db, curve_id, base_x, *, limit=256):
        nonlocal seed_row
        current = original(db, curve_id, base_x, limit=max(int(limit), 1) * 4)

        # During a seeded family hunt, do not inspect each candidate's legacy
        # rigorous basis before reaching the seed. Old candidate rows can use
        # earlier model coordinates and are irrelevant to the seed geometry.
        current_basis = []
        if seed_curve_id <= 0 or int(curve_id) == seed_curve_id:
            current_basis = rigorous_values(db, curve_id)

        priority = list(current_basis)
        ordinary = list(current)
        seeded_neighbor = seed_curve_id > 0 and int(curve_id) != seed_curve_id
        if seeded_neighbor:
            if seed_row is None:
                seed_row = cs.get_curve(db, seed_curve_id)
                if seed_row is None:
                    raise ValueError(f"Mestre seed curve #{seed_curve_id} not found")
                if str(seed_row["family"] or "") != cs.family.name():
                    raise ValueError(
                        f"seed curve #{seed_curve_id} belongs to {seed_row['family']!r}, "
                        f"not {cs.family.name()!r}"
                    )

            seed_t = cs._canonical_parameter(cs.QQ(str(seed_row["parameter"])))
            seed_base = {
                cs._fq(x)
                for x, _y in cs.family.native_quartic_known_points(seed_t)
            }
            seed_discovered = original(
                db,
                seed_curve_id,
                seed_base,
                limit=max(int(limit), 1) * 8,
            )
            seed_basis = rigorous_values(db, seed_curve_id)
            priority.extend(seed_basis)
            ordinary.extend(seed_discovered)

        target_base = {cs._fq(x) for x in base_x}
        priority = [cs._fq(x) for x in priority if cs._fq(x) not in target_base]
        ordinary = [cs._fq(x) for x in ordinary if cs._fq(x) not in target_base]

        requested_limit = int(limit)
        if priority and not seeded_neighbor:
            # Same-fibre target search: the structural base fibres already carry
            # the generic rank-11 geometry. Use only rigorous non-base source
            # fibres here so every subgroup chart contains a certified
            # exceptional direction. Dependent rediscoveries are intentionally
            # excluded from chart planning once these anchors exist.
            effective_limit = min(requested_limit, RIGOROUS_TARGET_ANCHOR_CAP)
            reduced = _spread(priority, effective_limit)
            print(
                f"[mestre basis] curve #{int(curve_id)} using {len(reduced)} exact "
                "rigorous non-base anchor fibre(s); ordinary dependent fibres excluded",
                flush=True,
            )
            return reduced

        if seeded_neighbor:
            effective_limit = min(requested_limit, SEEDED_FAMILY_ANCHOR_CAP)
            reduced = _priority_spread(priority, ordinary, effective_limit)
            total_unique = len(set(priority) | set(ordinary))
            if total_unique > len(reduced):
                print(
                    f"[mestre seed] candidate #{int(curve_id)} anchor bank capped "
                    f"{total_unique}->{len(reduced)} with "
                    f"{len(set(priority) & set(reduced))} priority anchor(s) reserved "
                    "before PGL2 planning",
                    flush=True,
                )
            return reduced

        # No rigorous source fibre is recoverable yet: retain the original
        # discovered-fibre behaviour rather than inventing rank geometry.
        return _spread(ordinary, requested_limit)

    cs._load_discovered_native_x = seeded_loader
    if seed_curve_id > 0:
        print(
            f"[mestre seed] borrowing exact anchor geometry from curve #{seed_curve_id}; "
            f"neighbor anchor bank capped at {SEEDED_FAMILY_ANCHOR_CAP}; "
            "persisted rigorous source fibres are preferred, and no rank evidence is transported",
            flush=True,
        )
    else:
        print(
            "[mestre basis anchors] exact persisted source fibres for rigorous generators "
            "are preferred; verified elliptic->quartic inversion is the fallback",
            flush=True,
        )


def main():
    seed_curve_id, argv = _pop_seed_curve_id(sys.argv)
    sys.argv[:] = argv
    _install_seed(seed_curve_id)
    cs.main()


if __name__ == "__main__":
    main()
