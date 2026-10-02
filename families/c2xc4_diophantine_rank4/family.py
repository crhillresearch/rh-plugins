"""Dujella-Peral C2 x C4 Diophantine-triple family of exact generic rank 4."""
from __future__ import annotations
from sage.all import EllipticCurve, GF, QQ, ZZ

generic_rank=4
historical_generic_rank_lower=4
CONTROL_PARAMETER=QQ(15)

def name():
    return "Dujella-Peral C2 x C4 Diophantine-triple rank 4"

def _pA(t):
    return (
        87671889*t**24 + 854321688*t**23 + 3766024692*t**22
        + 9923033928*t**21 + 17428851514*t**20 + 21621621928*t**19
        + 19950275060*t**18 + 15200715960*t**17 + 11789354375*t**16
        + 10470452464*t**15 + 8925222696*t**14 + 5984900048*t**13
        + 2829340620*t**12 + 820299856*t**11 + 59930952*t**10
        - 66320528*t**9 - 35768977*t**8 - 9381000*t**7 - 1017244*t**6
        + 262760*t**5 + 159130*t**4 + 41096*t**3 + 6468*t**2 + 600*t + 25
    )

def _f1(t): return t**2-2*t-1
def _f2(t): return 69*t**4+148*t**3+78*t**2+4*t+1
def _f3(t): return 13*t**2-2*t-1
def _f4(t): return 9*t**4+28*t**3+18*t**2+4*t+1
def _f5(t): return 11*t**4+12*t**3+2*t**2-4*t-1
def _f6(t): return 9*t**2+14*t+7
def _f7(t): return 31*t**4+52*t**3+22*t**2-4*t-1
def _f8(t): return 3*t**2+2*t+1

def _a_raw(t): return 2*_pA(t)

def _b_raw(t):
    return _f1(t)**2*_f2(t)**2*_f3(t)**2*_f4(t)**2*_f5(t)**2*_f6(t)**2*_f7(t)**2*_f8(t)**2

def a_coeff(t):
    t=QQ(t); return QQ(_a_raw(t))

def b_coeff(t):
    t=QQ(t); return QQ(_b_raw(t))

def _x_sections(t):
    t=QQ(t)
    return [
        _f4(t)**2*_f5(t)**2*_f2(t)**2,
        _f8(t)*_f6(t)**2*_f3(t)*_f4(t)*_f5(t)**2*_f7(t),
        _f8(t)*_f6(t)**2*_f3(t)*_f4(t)**2*_f5(t)*_f2(t),
        -_f8(t)**2*_f6(t)**2*_f5(t)**2*_f7(t)**2,
    ]

def _sqrt_qq(value):
    value=QQ(value)
    if value<0: raise ArithmeticError("expected rational square, got negative value")
    n=ZZ(value.numerator()); d=ZZ(value.denominator())
    if not n.is_square() or not d.is_square(): raise ArithmeticError("expected an exact rational square")
    return QQ(n.sqrt())/QQ(d.sqrt())

def curve(t):
    try:
        t=QQ(t); E=EllipticCurve(QQ,[0,a_coeff(t),0,b_coeff(t),0])
        return None if E.discriminant()==0 else E
    except (ArithmeticError,TypeError,ValueError,ZeroDivisionError): return None

def curve_mod_p(r0,p0):
    try:
        p=int(p0)
        if p==2: return None
        K=GF(p); t=K(int(r0)); E=EllipticCurve(K,[0,_a_raw(t),0,_b_raw(t),0])
        return None if E.discriminant()==0 else E
    except (ArithmeticError,TypeError,ValueError,ZeroDivisionError): return None

def generic_section_points(t):
    t=QQ(t); E=curve(t)
    if E is None: raise ArithmeticError(f"singular specialization t={t}")
    A=a_coeff(t); B=b_coeff(t); out=[]
    for xx in _x_sections(t):
        x=QQ(xx); y=_sqrt_qq(x**3+A*x**2+B*x); out.append(E(x,y))
    if len(out)!=4 or any(P.is_zero() for P in out): raise ArithmeticError("construction did not produce four nonzero sections")
    return out

def construction_check(t=CONTROL_PARAMETER):
    t=QQ(t); E=curve(t)
    if E is None: raise ArithmeticError(f"undefined specialization t={t}")
    pts=generic_section_points(t)
    return {"parameter":str(t),"sections":len(pts),"distinct_nonzero":len({(QQ(P[0]),QQ(P[1])) for P in pts}),"torsion_invariants":[int(v) for v in E.torsion_subgroup().invariants()],"a_invariants":[str(a) for a in E.a_invariants()]}

def validate_generic_rank_claim():
    from rank42.exact_lb import run_exact_certificate
    E=curve(CONTROL_PARAMETER)
    if E is None: raise RuntimeError("control t=15 is singular")
    pts=generic_section_points(CONTROL_PARAMETER)
    exact=run_exact_certificate(E.a_invariants(),[[P[0],P[1]] for P in pts],timeout=240)
    lower=int(exact.get("rank_lower_bound") or 0)
    return {"verified":bool(exact.get("independent") is True and lower>=4),"lower_bound":lower,"method":"four published free generators + Rank Hunter exact independence certificate at t=15","certificate_version":"c2xc4-diophantine-rank4-generic-lower-v0.1.0","details":{"control_parameter":"15","section_count":len(pts),"specialization_certificate":exact,"paper_independence_control":"2","paper_exact_rank_control":"15","paper_generic_rank":4}}
