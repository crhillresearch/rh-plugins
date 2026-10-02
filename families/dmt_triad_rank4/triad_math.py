"""Exact pure-Python mathematics for DMT-001 REA CURVE2 / Triad Family."""
from __future__ import annotations
from fractions import Fraction
from math import isqrt

LABELS = ("a", "b", "c", "d", "e", "f")
SELECTED_TRIPLES = ("ace", "acf", "bde", "bdf", "bef", "cef")
REGULAR_QUADRUPLES = (("a", "b", "e", "f"), ("a", "d", "e", "f"), ("c", "d", "e", "f"))
REGULAR_QUINTUPLES = (("a", "b", "c", "d", "e"), ("a", "b", "c", "d", "f"))
PAPER_SECTIONS = {
    "ace": ("P", "R", "E_d", "E_f"),
    "acf": ("P", "R", "E_d", "E_e"),
    "bde": ("P", "R", "E_c", "E_f"),
    "bdf": ("P", "R", "E_c", "E_e"),
    "bef": ("P", "R", "E_c", "E_d"),
    "cef": ("P", "R", "E_a", "E_b"),
}

def piezas_values(t):
    t = Fraction(t); t2 = t*t
    a = ((t2-2*t-1)*(t2+2*t+3)*(3*t2-2*t+1))/(4*t*(t2-1)*(t2+2*t-1))
    b = (4*t*(t2-1)*(t2-2*t-1))/((t2+2*t-1)**3)
    c = (4*t*(t2-1)*(t2+2*t-1))/((t2-2*t-1)**3)
    d = ((t2+2*t-1)*(t2-2*t+3)*(3*t2+2*t+1))/(4*t*(t2-1)*(t2-2*t-1))
    e = (-t*(t2+4*t+1)*(t2-4*t+1))/((t-1)*(t+1)*(t2+2*t-1)*(t2-2*t-1))
    f = ((t-1)*(t+1)*(3*t2-1)*(t2-3))/(4*t*(t2+2*t-1)*(t2-2*t-1))
    return dict(zip(LABELS,(a,b,c,d,e,f)))

def rational_sqrt(value):
    value=Fraction(value)
    if value<0: raise ValueError("negative rational is not a square")
    n,d=value.numerator,value.denominator; rn,rd=isqrt(n),isqrt(d)
    if rn*rn!=n or rd*rd!=d: raise ValueError(f"not a rational square: {value}")
    return Fraction(rn,rd)

def is_rational_square(value):
    try: rational_sqrt(value); return True
    except ValueError: return False

def is_diophantine_sextuple(values):
    vals=[values[k] for k in LABELS]
    if any(v==0 for v in vals) or len(set(vals))!=6: return False
    return all(is_rational_square(vals[i]*vals[j]+1) for i in range(6) for j in range(i+1,6))

def regular_quadruple_residual(p,q,r,s):
    return (p-q-r+s)**2-4*(p*s+1)*(q*r+1)

def regular_quintuple_residual(p,q,r,s,z):
    lhs=(p*q*r*s*z+2*p*q*r+p+q+r-s-z)**2
    rhs=4*(p*q+1)*(p*r+1)*(q*r+1)*(s*z+1)
    return lhs-rhs

def verify_paper_regularity(values):
    return all(regular_quadruple_residual(*(values[k] for k in labels))==0 for labels in REGULAR_QUADRUPLES) and all(regular_quintuple_residual(*(values[k] for k in labels))==0 for labels in REGULAR_QUINTUPLES)

def triple_values(values,triple):
    if triple not in SELECTED_TRIPLES: raise ValueError(f"unknown DMT selected triad {triple!r}")
    return tuple(values[k] for k in triple)

def split_roots(values,triple):
    u,v,w=triple_values(values,triple); return (-u*v,-u*w,-v*w)

def curve_a_invariants(values,triple):
    u,v,w=triple_values(values,triple); uv,uw,vw=u*v,u*w,v*w
    return (Fraction(0),uv+uw+vw,Fraction(0),uv*uw+uv*vw+uw*vw,uv*uw*vw)

def curve_rhs(values,triple,x):
    u,v,w=triple_values(values,triple); x=Fraction(x)
    return (x+u*v)*(x+u*w)*(x+v*w)

def p_point(values,triple):
    u,v,w=triple_values(values,triple); return Fraction(0),u*v*w

def r_point(values,triple):
    u,v,w=triple_values(values,triple)
    r=rational_sqrt(u*v+1); s=rational_sqrt(u*w+1); q=rational_sqrt(v*w+1)
    return r*s+r*q+s*q+1,(r+s)*(r+q)*(s+q)

def ez_point(values,triple,z_label):
    if z_label not in LABELS or z_label in triple: raise ValueError(f"{z_label!r} is not an ambient fourth label for {triple}")
    u,v,w=triple_values(values,triple); z=values[z_label]
    return u*v*w*z, u*v*w*rational_sqrt(u*z+1)*rational_sqrt(v*z+1)*rational_sqrt(w*z+1)

def ambient_points(values,triple):
    result={"P":p_point(values,triple),"R":r_point(values,triple)}
    for label in LABELS:
        if label not in triple: result[f"E_{label}"]=ez_point(values,triple,label)
    return result

def paper_section_coordinates(t,triple):
    values=piezas_values(t); points=ambient_points(values,triple)
    return [points[label] for label in PAPER_SECTIONS[triple]]

def good_selected_fiber(t):
    try: values=piezas_values(t)
    except ZeroDivisionError: return False
    if not is_diophantine_sextuple(values) or not verify_paper_regularity(values): return False
    return all(len(set(split_roots(values,triple)))==3 for triple in SELECTED_TRIPLES)
