"""C2 rank-11 family over the paired-cover genus-one parameter curve."""
from __future__ import annotations

import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, QQ, sage_eval


HERE = Path(__file__).resolve().parent
SOURCE = json.loads((HERE / 'data/source_family.json').read_text())
PAIR = json.loads((HERE / 'data/paired_cover.json').read_text())
PAIRED_SECTIONS = json.loads((HERE / 'data/paired_sections.json').read_text())['source_sections']
CERTIFICATE_PATH = HERE / 'data/rank11_certificate.json'
CERTIFICATE_SHA256 = '3fecff8ae7ebe4cd85d5dcae5a5145d3ac4b8ae0708d84e797836412b0ed0c85'
FAMILY_NAME = 'Hill C2 rank ≥11 genus-one-base family'
BASE_QUARTIC = PolynomialRing(QQ, 's')(PAIR['quartic'])
BASE_E = EllipticCurve(QQ, PAIR['auxiliary_a_invariants'])
BASE_GENERATOR = BASE_E(*PAIR['auxiliary_point'])
BASE_N = PolynomialRing(QQ, 's')(PAIR['parent_numerator'])
BASE_D = PolynomialRing(QQ, 's')(PAIR['parent_denominator'])
ROOT10 = PolynomialRing(QQ, 's')(PAIR['first_root_numerator'])
CERTIFICATE = json.loads(CERTIFICATE_PATH.read_text())

candidate_denominator_mode = 'family_owned'
MAX_AUTOMATIC_SELECTOR = 12


def name():
    return FAMILY_NAME


def generic_rank():
    return 11


def candidate_seed_parameters():
    return (1, -1, 2, -2)


def _selector(value):
    q = QQ(value)
    if not q.is_integer() or not q:
        raise ValueError('selector must be a nonzero integer multiple of the certified base point')
    return int(q)


def parameter_point(index, base=QQ):
    """Map n times the certified Jacobian point to (s,v) on the quartic base."""
    n = _selector(index)
    H = EllipticCurve(base, [base(QQ(a)) for a in PAIR['auxiliary_a_invariants']])
    P = H(base(QQ(PAIR['auxiliary_point'][0])), base(QQ(PAIR['auxiliary_point'][1])))
    Q = n * P
    if Q.is_zero():
        raise ValueError('the selected auxiliary multiple is the point at infinity')
    X, Y = Q.xy()
    F = [base(c) for c in PAIR['quartic']]
    e = F[0].sqrt()
    d, c, b, a = F[1], F[2], F[3], F[4]
    denominator = X**2 - 4 * e**2 * a
    if not denominator:
        raise ValueError('the auxiliary point lies in the omitted birational chart')
    s = (2 * e * Y + X * d + 2 * e**2 * b) / denominator
    v = (X * s**2 - d * s) / (2 * e) - e
    if v**2 != sum(F[i] * s**i for i in range(5)):
        raise ArithmeticError('the Jacobian-to-quartic map failed exact replay')
    return s, v


def parent_parameter(index, base=QQ):
    s, _v = parameter_point(index, base=base)
    N = sum(base(PAIR['parent_numerator'][i]) * s**i for i in range(3))
    D = sum(base(PAIR['parent_denominator'][i]) * s**i for i in range(3))
    if not D:
        raise ValueError('the selected base point maps to infinity on the parent parameter line')
    return N / D


def _evaluate(expression, parameter, variable='t'):
    numerator_coeffs, denominator_coeffs = _expression_coefficients(str(expression), variable)
    base = parameter.parent()
    numerator = sum(base(c) * parameter**i for i, c in enumerate(numerator_coeffs))
    denominator = sum(base(c) * parameter**i for i, c in enumerate(denominator_coeffs))
    return numerator / denominator


@lru_cache(maxsize=128)
def _expression_coefficients(expression, variable):
    ring = PolynomialRing(QQ, variable)
    function_field = ring.fraction_field()
    z = function_field.gen()
    value = function_field(sage_eval(str(expression).replace('^', '**'), locals={variable: z}))
    return tuple(value.numerator()), tuple(value.denominator())


def _a_invariants(t):
    return [_evaluate(value, t) for value in SOURCE['a_invariants']]


def curve(index):
    try:
        t = parent_parameter(index)
        E = EllipticCurve(QQ, _a_invariants(t))
        return E if E.discriminant() else None
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def curve_mod_p(index, p):
    try:
        field = GF(int(p))
        t = parent_parameter(index, base=field)
        E = EllipticCurve(field, _a_invariants(t))
        return E if E.discriminant() else None
    except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
        return None


def generic_section_points(index):
    """Return all eleven exact points on the selected rational fiber."""
    t = parent_parameter(index)
    s, v = parameter_point(index)
    E = curve(index)
    if E is None:
        raise ValueError('the selected family fiber is singular')
    points = [E(_evaluate(row['x'], t), _evaluate(row['y'], t)) for row in SOURCE['sections']]
    D = sum(QQ(PAIR['parent_denominator'][i]) * s**i for i in range(3))
    root10 = sum(QQ(PAIR['first_root_numerator'][i]) * s**i for i in range(3)) / D
    roots = [root10, v / D]
    a2 = _evaluate(SOURCE['a_invariants'][1], t)
    for row, root in zip(PAIRED_SECTIONS, roots):
        px = _evaluate(row['trace_x'], t, variable='U')
        py = _evaluate(row['trace_y'], t, variable='U')
        slope = _evaluate(row['slope'], t, variable='U')
        multiplier = _evaluate(row['square_multiplier'], t, variable='U')
        x_short = (slope**2 - px + multiplier * root) / 2
        y = slope * (x_short - px) - py
        points.append(E(x_short - a2 / 3, y))
    if len(points) != 11 or any(P.is_zero() for P in points):
        raise ArithmeticError('the eleven sections did not specialize to finite points')
    return points


def torsion_points(index):
    E = curve(index)
    if E is None:
        raise ValueError('the selected family fiber is singular')
    T = E(0, 0)
    if 2 * T != E(0):
        raise ArithmeticError('the visible C2 section is not 2-torsion')
    return [T]


def validate_specialization(index):
    E = curve(index)
    if E is None:
        raise ValueError('the selected family fiber is singular')
    points = generic_section_points(index)
    if any(P.curve() != E for P in points):
        raise ArithmeticError('a displayed section left the specialized curve')
    torsion = E.torsion_subgroup().invariants()
    if list(map(int, torsion)) != [2]:
        raise ArithmeticError(f'validation specialization has torsion {torsion}, expected C2')
    return {'verified': True, 'selector': str(index), 'point_count': len(points),
            'torsion_invariants': [2], 'rank_claim': 'the family-level certificate is over Q(C)'}


def validate_generic_rank_claim():
    """Replay the packaged exact Gram and paired-deck certificate receipt."""
    raw = CERTIFICATE_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CERTIFICATE_SHA256:
        raise ArithmeticError('packaged rank-11 certificate hash mismatch')
    receipt = json.loads(raw)
    if (receipt.get('status') != 'certified_generic_rank_lower_bound_over_genus_one_base'
            or int(receipt.get('rank_lower_bound') or 0) < 11
            or receipt.get('torsion_subgroup') != 'C2'
            or receipt.get('parameter_base_genus') != 1
            or receipt.get('nonisotrivial') is not True
            or len(receipt.get('cover_receipts') or []) != 2):
        raise ArithmeticError('rank-11 genus-one family receipt is incomplete')
    for cover in receipt['cover_receipts']:
        from sage.all import matrix
        H = matrix(QQ, cover['corrected_gram'])
        if (H.nrows() != 10 or not H.is_positive_definite()
                or str(H.det()) != str(cover['determinant'])
                or H.det() != 11040
                or QQ(cover['new_section_residual_height']) != 3
                or QQ(cover['anti_invariant_height']) != 12
                or cover.get('parent_sections_deck_invariant') is not True
                or cover.get('new_section_not_deck_invariant') is not True):
            raise ArithmeticError('a correction-aware cover Gram failed exact replay')
    if (int(receipt.get('auxiliary_torsion_order_multiple') or 0) != 2
            or not any(QQ(x) for x in receipt.get('auxiliary_point_multiple_nonzero') or [])):
        raise ArithmeticError('the genus-one base positive-rank witness is missing')
    return {'verified': True, 'lower_bound': 11,
            'method': 'two exact correction-aware Shioda Grams plus deck anti-invariant independence',
            'base_genus': 1, 'torsion_subgroup': 'C2',
            'certificate_sha256': CERTIFICATE_SHA256}


def generate_rank42_candidate_rows(*, a_min, a_max, b_min, b_max, top,
                                   prime_bound, stage_bounds=None,
                                   stage_keeps=None, excluded_parameters=()):
    """Score integer multiples of the genus-one base point by finite fields."""
    from sage.all import prime_range
    excluded = set()
    for raw in excluded_parameters or ():
        try:
            excluded.add(int(raw[0] if isinstance(raw, (tuple, list)) else raw))
        except (TypeError, ValueError):
            continue
    bounds = [int(bound) for bound in (stage_bounds or [prime_bound])]
    keeps = [int(keep) for keep in (stage_keeps or [top])]
    if len(bounds) != len(keeps):
        raise ValueError('candidate stage bounds and keeps must have the same length')
    low = max(int(a_min), -MAX_AUTOMATIC_SELECTOR)
    high = min(int(a_max), MAX_AUTOMATIC_SELECTOR)
    if low != int(a_min) or high != int(a_max):
        print(f'[family scoring] exact-size guard: selectors limited to '
              f'{low}..{high} (requested {a_min}..{a_max})', flush=True)
    selectors = [n for n in range(low, high + 1)
                 if n != 0 and n not in excluded]
    rows = []
    for stage_index, bound in enumerate(bounds):
        primes = list(map(int, prime_range(17, bound)))
        print(f'[family scoring] stage {stage_index + 1}/{len(bounds)} · '
              f'{len(selectors)} selectors · primes < {bound}', flush=True)
        scored = []
        for index, n in enumerate(selectors, 1):
            total = 0.0
            used = 0
            for p in primes:
                E = curve_mod_p(n, p)
                if E is None:
                    continue
                ap = p + 1 - int(E.cardinality())
                total -= ap * math.log(p) / p
                used += 1
            if used:
                scored.append({'family': name(), 'a': n, 'b': 1, 't': str(n),
                               'score': total, 'prime_bound': bound, 'prime_terms': used,
                               'ranking_kind': 'mestre_nagao', 'ranking_value': total,
                               'score_provenance': {'algorithm': 'genus_one_auxiliary_multiple_nagao_v1',
                                                    'selector_is_auxiliary_multiple': True,
                                                    'parameter_base_genus': 1}})
            if index % 50 == 0 or index == len(selectors):
                print(f'[family scoring] stage {stage_index + 1}/{len(bounds)} · '
                      f'{index}/{len(selectors)} selectors scored', flush=True)
        scored.sort(key=lambda row: (row['score'], -abs(row['a']), -row['a']), reverse=True)
        rows = scored[:keeps[stage_index]]
        selectors = [row['a'] for row in rows]
    return rows[:max(1, int(top))]
