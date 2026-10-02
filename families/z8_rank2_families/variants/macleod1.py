"""MacLeod I Z/8 rank-2 family from Dujella-Kazalicki-Peral (2021)."""
from __future__ import annotations
from sage.all import EllipticCurve, GF, QQ, ZZ
generic_rank=2
historical_generic_rank_lower=2
CONTROL_PARAMETER=QQ("17")
VARIANT_ID="macleod1"

def name(): return "Z/8 rank-2 · MacLeod I"
def _a_raw(u): return 1058387660788345388204032-141209336315730168643584*u+7118408590330053918720*u**2+46091099527055278080*u**3-20521534612217970688*u**4+473831305485189120*u**5+19585996741025792*u**6-545185218600960*u**7-18026420955648*u**8+234415749120*u**9+22250170880*u**10-242597376*u**11-14269120*u**12+276096*u**13+1632*u**14-96*u**15+u**16
def _b_raw(u): return 4096*(u-63)**4*(u-28)**4*(u-14)**4*(u+2)**4*(u+28)**4*(u+42)**4*(3*u-98)**4
def a_coeff(u):
    u=QQ(u); return QQ(_a_raw(u))
def b_coeff(u):
    u=QQ(u); return QQ(_b_raw(u))
def _x_sections(u):
    u=QQ(u)
    return [(16*(u-63)*(u-28)**3*(u-14)**3*(u+2)**3*(u+28)**3*(u+42)*(3*u-98)*(u**4+24*u**3-2744*u**2-61152*u+3133648)**2)/((3*u**4-24*u**3-3080*u**2+4704*u+1103088)**2),(-1024*(u-63)**2*(u-28)**3*(u-14)**2*(u+2)**2*(u+28)**3*(u+42)**3*(3*u-98)**3)/((u**2-28*u+980)**2)]
def _sqrt_qq(value):
    value=QQ(value)
    if value<0: raise ArithmeticError("expected rational square, got negative value")
    n=ZZ(value.numerator()); d=ZZ(value.denominator())
    if not n.is_square() or not d.is_square(): raise ArithmeticError("expected an exact rational square")
    return QQ(n.sqrt())/QQ(d.sqrt())
def curve(u):
    try:
        u=QQ(u); E=EllipticCurve(QQ,[0,a_coeff(u),0,b_coeff(u),0]); return None if E.discriminant()==0 else E
    except (ArithmeticError,TypeError,ValueError,ZeroDivisionError): return None
def curve_mod_p(r0,p0):
    try:
        p=int(p0)
        if p==2: return None
        K=GF(p); u=K(int(r0)); E=EllipticCurve(K,[0,_a_raw(u),0,_b_raw(u),0]); return None if E.discriminant()==0 else E
    except (ArithmeticError,TypeError,ValueError,ZeroDivisionError): return None
def generic_section_points(u):
    u=QQ(u); E=curve(u)
    if E is None: raise ArithmeticError(f"singular MacLeod I specialization u={u}")
    A=a_coeff(u); B=b_coeff(u); out=[]
    for xx in _x_sections(u):
        x=QQ(xx); y=_sqrt_qq(x**3+A*x**2+B*x); out.append(E(x,y))
    if len(out)!=2 or any(P.is_zero() for P in out): raise ArithmeticError("MacLeod I did not produce two nonzero sections")
    return out
def construction_check(u=CONTROL_PARAMETER):
    u=QQ(u); E=curve(u)
    if E is None: raise ArithmeticError(f"undefined MacLeod I specialization u={u}")
    pts=generic_section_points(u); tors=E.torsion_subgroup().invariants()
    return {"variant":VARIANT_ID,"parameter":str(u),"sections":len(pts),"distinct_nonzero":len({(QQ(P[0]),QQ(P[1])) for P in pts}),"torsion_invariants":[int(x) for x in tors],"a_invariants":[str(a) for a in E.a_invariants()]}
def validate_generic_rank_claim():
    from rank42.exact_lb import run_exact_certificate
    E=curve(CONTROL_PARAMETER)
    if E is None: raise RuntimeError("MacLeod I control specialization is singular")
    pts=generic_section_points(CONTROL_PARAMETER)
    exact=run_exact_certificate(E.a_invariants(),[[P[0],P[1]] for P in pts],timeout=180)
    lower=int(exact.get("rank_lower_bound") or 0)
    return {"verified":bool(exact.get("independent") is True and lower>=2),"lower_bound":lower,"method":"two published full free generators + Rank Hunter exact independence certificate","certificate_version":"z8-rank2-macleod1-generic-lower-v0.1.0","details":{"variant":VARIANT_ID,"control_parameter":str(CONTROL_PARAMETER),"section_count":len(pts),"specialization_certificate":exact,"paper_generic_rank":2}}
