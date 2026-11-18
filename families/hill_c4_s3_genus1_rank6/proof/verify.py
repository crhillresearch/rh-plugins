#!/usr/bin/env python3
"""Independent exact verification of the C4 S3 genus-one rank >=6 construction.

Dependencies: Python >=3.10 and sympy. No Sage/Magma/network needed.
The rank >=4 of the inherited Elkies--Klagsbrun sections is a cited theorem.
"""
from __future__ import annotations
import json
from fractions import Fraction as Q
from math import gcd, isqrt, lcm
from pathlib import Path
import sympy as S

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'data' / 'construction.json').read_text())
U,t,w = S.symbols('u t w')

def check(label, test):
    if not bool(test):
        raise AssertionError(label)
    print('PASS:', label, flush=True)

def rational_sqrt(z):
    z=Q(z)
    if z<0:return None
    a,b=isqrt(z.numerator),isqrt(z.denominator)
    return Q(a,b) if a*a==z.numerator and b*b==z.denominator else None

def rational_sym(z):
    z=S.cancel(z)
    if z.free_symbols: raise ValueError('expected rational constant')
    return Q(int(S.numer(z)),int(S.denom(z)))

def reduced(z,p):
    z=Q(z)
    return (z.numerator%p)*pow(z.denominator,-1,p)%p

def add(P,Q0,a2,a4,mod=None):
    if P is None:return Q0
    if Q0 is None:return P
    x,y=P; X,Y=Q0
    if mod is None:
        if x==X and y==-Y:return None
        if x==X:
            if y==0:return None
            m=(3*x*x+2*a2*x+a4)/(2*y)
        else:m=(Y-y)/(X-x)
        xr=m*m-a2-x-X
        return (xr,-m*(xr-x)-y)
    p=mod; x%=p;y%=p;X%=p;Y%=p;a2%=p;a4%=p
    if x==X and (y+Y)%p==0:return None
    if x==X:
        if y==0:return None
        m=(3*x*x+2*a2*x+a4)*pow(2*y,-1,p)%p
    else:m=(Y-y)*pow(X-x,-1,p)%p
    xr=(m*m-a2-x-X)%p
    return (xr,(-m*(xr-x)-y)%p)

def times(P,n,a2,a4,mod=None):
    R=None
    while n:
        if n&1:R=add(R,P,a2,a4,mod)
        P=add(P,P,a2,a4,mod);n//=2
    return R

def elliptic_order(a2,a4,a6,p):
    vs=[Q(z) for z in (a2,a4,a6)]
    assert all(z.denominator%p for z in vs)
    A,B,C=[reduced(z,p) for z in vs]
    # discriminant of y^2=x^3+A x^2+B x+C
    discr=16*(A*A*B*B-4*B**3-4*A**3*C-27*C*C+18*A*B*C)
    assert discr%p, f'bad reduction: {p}'
    squares={v*v%p for v in range(p)}
    return 1+sum(1 if (v:=(x*x*x+A*x*x+B*x+C)%p)==0 else (2 if v in squares else 0) for x in range(p))

# Parent K3, four inherited sections. These four are known independent by
# Elkies--Klagsbrun, 2020, section 11; the verifier checks their identities only.
a=(8*t-1)*(32*t+7)
g=(15*t-8)*(31*t-7)
b=8*(t+1)*g
A=S.expand(a*a-8*b);B=S.expand(16*b*b)
Xi=[-S.Rational(15,4)*(t+1)*(31*t-7)*(32*t+7),
    (8*t-1)*(15*t-8)*(31*t-7)*(32*t+7),
    -(t+1)*(8*t-1)*(15*t-8)*(32*t+7),
    -4*(t+1)*(2*t+5)*(15*t-8)*(32*t+7)]
Zi=[S.Rational(19,4)*(t+1)*(31*t-7)*(32*t+7)*(127*t-44),
    (8*t-1)*(15*t-8)*(16*t+1)*(31*t-7)*(32*t+7)*(46*t-15),
    (t+1)*(8*t-1)*(14*t-9)*(15*t-8)*(16*t-7)*(32*t+7),
    4*(t+1)*(8*t+7)*(15*t-8)*(32*t+7)*(56*t*t+8*t-57)]
for i,(x,z) in enumerate(zip(Xi,Zi),1):
    check(f'inherited section {i} on parent surface', S.expand(z*z-(x+b)*(4*x*x+a*a*(x+b)))==0)
check('explicit C4 torsion model', S.expand((4*a*b)**2-(4*b)**3-A*(4*b)**2-B*(4*b))==0)

# Cubic map from the 2-neighbor fibration.
N=14907321*U**3-392116761*U**2+3433897552*U-9026551296
K=31965219*U**2-66155603*U-1665613632
D=24*K
tmap=N/D
H=888912877588164*U**5-10646406622659951*U**4-960018782069421396*U**3+12164159827914309855*U**2-9247249925793225856*U-202923579084549844992
V=U*(U-9)*H/(9*K**2)
F=U**2*a*a+4*U*g*(U-8*(t+1))**2
check('cubic 2-neighbor section identity', S.cancel(F.subs(t,tmap)-V**2)==0)
check('cubic map generically degree 3', S.degree(N,U)==3 and S.gcd(N,D)==1)

poly_disc=S.discriminant(N-t*D,U)
branch=1682330950211090408678592*t**4+2032853295795148379391696*t**3+53691289761921871193523*t**2+1391585322280210990012*t-132998306248524640756
check('exact cubic discriminant', S.expand(poly_disc-43796088116928*branch)==0)
check('four simple branch values',S.gcd(branch,S.diff(branch,t))==1)

# Galois closure: for a chosen root U, the other two cubic roots are
# rational over the quartic curve w^2=G(U).
cs=[3*378971104359372914995200,
    -3*198772910377722356658560,
    3*33956711603623770472443,
    -3*2452798658271489135894,
    3*70581401878625698203]
G=S.expand(sum(cs[i]*U**i for i in range(5)))
check('quartic data match archive', [str(v) for v in cs]==DATA['galois_quartic_low_to_high'])
check('quartic squarefree',S.degree(S.gcd(G,S.diff(G,U)),U)==0)
z=S.symbols('z')
A3=14907321
A2=-392116761-767165256*t
A1=3433897552+1587734472*t
A0=-9026551296+39974727168*t
B2=S.cancel(A2.subs(t,tmap)+A3*U)
C2=S.cancel(A1.subs(t,tmap)+A2.subs(t,tmap)*U+A3*U**2)
check('quadratic residual discriminant equals square in w',
      S.cancel(B2**2-4*A3*C2-(477603**2)*G/K**2)==0)

# Auxiliary Jacobian and its exact non-torsion rational point.
e=isqrt(cs[0]); check('quartic has rational point (0,e)', e*e==cs[0])
c0,c1,c2,c3,c4=cs
J2=c2
J4=c3*c1-4*c4*e*e
J6=e*e*c3*c3+c4*c1*c1-4*c4*c2*e*e
XX=(2*e*(w+e)+c1*U)/U**2
YY=(((XX**2-4*c4*e*e)*U-(XX*c1+2*e*e*c3)))/(2*e)
relation=S.together(YY**2-XX**3-J2*XX**2-J4*XX-J6).as_numer_denom()[0]
check('quartic-to-Jacobian birational identity', S.Poly(relation,w).rem(S.Poly(w*w-G,w)).is_zero)

def jacobian_point(u0,w0):
    X=(2*e*(w0+e)+c1*u0)/(u0*u0)
    Y=((X*X-4*c4*e*e)*u0-(X*c1+2*e*e*c3))/(2*e)
    return (X,Y)

def inverse_jacobian(P):
    X,Y=P
    den=X*X-4*c4*e*e
    u0=(2*e*Y+X*c1+2*e*e*c3)/den
    w0=(X*u0*u0-c1*u0)/(2*e)-e
    return u0,w0

seed_u=Q(7288,837)
seed_w=-Q(4303028078006840,25947)  # crucial NEGATIVE sign
check('quartic seed on curve', seed_w*seed_w==sum(cs[i]*seed_u**i for i in range(5)))
R=jacobian_point(seed_u,seed_w)
check('seed Jacobian point exact', R[1]**2==R[0]**3+J2*R[0]**2+J4*R[0]+J6)
check('seed Jacobian coordinates match archived witness',
      [str(v) for v in R]==DATA['seed_jacobian_point_XY'])
orders={p:elliptic_order(J2,J4,J6,p) for p in (31,37)}
check('auxiliary good-reduction orders',orders=={31:27,37:48})
redR=(reduced(R[0],37),reduced(R[1],37))
check('3R nonzero modulo 37',times(redR,3,J2,J4,37)==(16,14))
check('Jacobian point non-torsion', gcd(*orders.values())==3)

# Smooth rational fiber and all three rational cubic roots from 2R.
Q0=times(R,2,J2,J4)
u0,w0=inverse_jacobian(Q0)
check('2R gives another rational quartic point',w0*w0==sum(cs[i]*u0**i for i in range(5)))
t0=Q(N.subs(U,S.Rational(u0.numerator,u0.denominator)),D.subs(U,S.Rational(u0.numerator,u0.denominator)))
check('smooth specialized t0 as archived',str(t0)==DATA['smooth_fiber_t'])
kv=Q(K.subs(U,S.Rational(u0.numerator,u0.denominator)))
bb2=Q(-392116761)-767165256*t0+A3*u0
rt=Q(477603)*w0/kv
roots=[u0,(-bb2+rt)/(2*A3),(-bb2-rt)/(2*A3)]
check('three distinct rational cubic roots',len(set(roots))==3)
for r in roots:
    check('specialized cubic root',A3*r**3+(-392116761-767165256*t0)*r*r+(3433897552+1587734472*t0)*r-9026551296+39974727168*t0==0)

av=Q(a.subs(t,S.Rational(t0.numerator,t0.denominator)))
gv=Q(g.subs(t,S.Rational(t0.numerator,t0.denominator)))
bv=Q(b.subs(t,S.Rational(t0.numerator,t0.denominator)))
av2=av*av-8*bv;bv4=16*bv*bv
points=[]
for r in roots:
    v=Q(V.subs(U,S.Rational(r.numerator,r.denominator)))
    P=(4*r*gv,4*gv*v)
    check('specialized cubic point on C4 curve',P[1]*P[1]==P[0]**3+av2*P[0]**2+bv4*P[0])
    points.append(P)
tors=(4*bv,4*av*bv)
check('specialized torsion point order four',times(tors,2,av2,bv4)==(Q(0),Q(0)) and times(tors,4,av2,bv4) is None)
E_orders={p:elliptic_order(av2,bv4,0,p) for p in (43,59,73)}
check('good-reduction orders of smooth C4 fiber',E_orders=={43:56,59:72,73:76})
check('exact rational torsion C4 at smooth fiber',gcd(*E_orders.values())==4)
redP=[(reduced(x,43),reduced(y,43)) for x,y in points]
negative=lambda P:(P[0],-P[1]%43)
red_diff=add(redP[0],negative(redP[1]),reduced(av2,43),reduced(bv4,43),43)
red4=times(red_diff,4,reduced(av2,43),reduced(bv4,43),43)
check('fourfold difference of cubic points is nonzero modulo 43',red4==(9,38))

# Infinite progression retaining torsion C4: n*360R + 2R.
J_orders={p:elliptic_order(J2,J4,J6,p) for p in (43,59,73)}
check('Jacobian reduction orders for progression',J_orders=={43:45,59:72,73:72})
M=lcm(*J_orders.values())
check('progression step 360',M==360)
invden=Q0[0]**2-4*c4*e*e
for p in (43,59,73):
    for label,obj in [('JX',Q0[0]),('JY',Q0[1]),('u',u0),('w',w0),('t',t0),('K',kv),('invden',invden)]:
        check(f'progression regular: {label} mod {p}',Q(obj).denominator%p!=0)
    check(f'progression map regular and finite mod {p}',
          reduced(u0,p)!=0 and reduced(kv,p)!=0 and reduced(invden,p)!=0)
WITNESS=json.loads((ROOT/'data'/'witness.json').read_text())
check('archive 2R coordinates', [str(v) for v in Q0]==WITNESS['point_in_jacobian_2R_XY'])
check('archive quartic 2R point', [str(v) for v in (u0,w0)]==WITNESS['quartic_rational_point_2R_uw'])
check('archive cubic roots', [str(v) for v in roots]==WITNESS['cubic_roots_at_smooth_t'])
check('archive 3 point coordinates', [[str(x),str(y)] for x,y in points]==WITNESS['three_cubic_section_points_XY'])
check('nonconstant j-invariant', b.subs(t,-1)==0 and a.subs(t,-1)!=0 and b.subs(t,0)!=0)

print('\nCERTIFIED relative to published EK2020 rank-4 parent theorem:',flush=True)
print('  Rank >= 6 over positive-rank genus-one S3 splitting-field base.')
print('  Exact generic C4 torsion; infinitely many distinct rational C4 fibers rank >= 6.')
print('  Generic exact rank and bibliographic novelty NOT claimed.')
print('  R (non-torsion):',str(R))
print('  t(2R):',str(t0))
print('  4*(P1-P2) mod 43:',str(red4))
