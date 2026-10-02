"""Exact shared engine for Campbell's six 1999 rank-13 quartic families.

Campbell starts with a sextuple ``A=(a_1,...,a_6)`` and

    p_A(x,u) = prod_i ((x-a_i)^2-u^2) = G_A(x,u)^2 - u^2 r_A(x,u).

For the six published examples ``r_A`` has degree four in x.  Campbell also
exhibits one additional affine point, giving thirteen finite rational points
on ``y^2=r_A``.  Its leading coefficient is ``a^2*u^2+c``.  We make the
published rational-leading-coefficient trick explicit using a well-conditioned
parameter ``t``:

    u(t) = (N-M*t^2)/(2*a*t),
    b(t) = (N+M*t^2)/(2*t),        M*N = c,

so ``a^2*u(t)^2+c=b(t)^2``.  Dividing y by b produces the monic native
quartic used by Rank Hunter.  This is an exact Q(t)-birational normalization;
it does not change the x-fibres searched by ratpoints.

The literature declares the thirteen displayed points independent.  Rank
Hunter nevertheless keeps its proof boundary: a specialization gets a stored
rigorous lower bound only after ``rank42.exact_lb`` certifies the specialized
points.  The family metadata is therefore provenance, not an automatic rank
promotion.
"""

from __future__ import annotations

import sys

from sage.all import QQ, GF, EllipticCurve, PolynomialRing


BRANCH_DATA = {
    "c1": {
        "sextuple": (0, 87, 164, 264, 375, 452),
        "extra_x": (7, 31, 10848, 31),
        "leading_sqrt": 47520,
        "leading_const": 261856625817600,
        "parameter_M": 16159680,
        "parameter_N": 16204320,
        "quartic_z_coefficients": ((407636871790807296000000, 11464201682375270400, -383676814540800, 2258150400), (-9212285252051481600000, -126225579713587200, 2020291891200), (72339159689682969600, 740277402163200, -4516300800), (-232601719837132800, -2020291891200), (261856625817600, 2258150400)),
        "g_z_coefficients": ((0, -9550870704, 224545, -1), (-638464464000, 132790416, -1342), (16765277904, -900482, 3), (-157659216, 2684), (675937, -3), (-1342,), (1,)),
        "extra_y_coefficients": ('-38941499520', '-2367607983840/961', '-2604127680/961', '43338240/961'),
    },
    "c2": {
        "sextuple": (0, 55, 146, 255, 260, 346),
        "extra_x": (-7, 27, 6920, 27),
        "leading_sqrt": 23400,
        "leading_const": 52956717840000,
        "parameter_M": 7264296,
        "parameter_N": 7290000,
        "quartic_z_coefficients": ((33932069273080836000000, 1443043240329600000, -55409908320000, 547560000), (-968787350572298400000, -19604105604720000, 387672480000), (9500686829398440000, 122040537840000, -1095120000), (-37908878707440000, -387672480000), (52956717840000, 547560000)),
        "g_z_coefficients": ((0, -3944532700, 138341, -1), (-184206594000, 68060520, -1062), (6574154500, -563922, 3), (-78996120, 2124), (425581, -3), (-1062,), (1,)),
        "extra_y_coefficients": ('-661206000', '-48242799800/81', '77932400/81', '1768000/81'),
    },
    "c3": {
        "sextuple": (0, 355, 602, 910, 1580, 1827),
        "extra_x": (19, 89, 127890, 89),
        "leading_sqrt": 764400,
        "leading_const": 953429511303360000,
        "parameter_M": 976010490,
        "parameter_N": 976864000,
        "quartic_z_coefficients": ((315154666331369181138276000000, 575165414208250756800000, -1613394156890880000, 584307360000), (-1865017295814872569406400000, -1672112287971740160000, 2054424677760000), (3847310690868724191840000, 2854531937799360000, -1168614720000), (-3249364531473889920000, -2054424677760000), (953429511303360000, 584307360000)),
        "g_z_coefficients": ((0, -2132312062300, 3575429, -1), (-561386378826000, 7797627180, -5274), (3793393775500, -13907538, 3), (-9279034380, 10548), (10332109, -3), (-5274,), (1,)),
        "extra_y_coefficients": ('-56297612826000', '-5695086205645200/7921', '-1442454904800/7921', '5778864000/7921'),
    },
    "c4": {
        "sextuple": (0, 97, 104, 129, 500, 532),
        "extra_x": (1, 23, 9804, 23),
        "leading_sqrt": 43680,
        "leading_const": 207916115097600,
        "parameter_M": 14412996,
        "parameter_N": 14425600,
        "quartic_z_coefficients": ((119826490826375424000000, 1485804450699878400, -449877554380800, 1907942400), (-3561273124498252800000, -26005937955379200, 1732411699200), (37373283642638361600, 562686556723200, -3815884800), (-158238908168140800, -1732411699200), (207916115097600, 1907942400)),
        "g_z_coefficients": ((0, -5779542064, 284945, -1), (-346159632000, 108342096, -1362), (10923517264, -927522, 3), (-126250896, 2724), (642577, -3), (-1362,), (1,)),
        "extra_y_coefficients": ('-30262202880', '-2454185391840/529', '-400370880/529', '23063040/529'),
    },
    "c5": {
        "sextuple": (0, 42, 47, 82, 152, 175),
        "extra_x": (1, 21, 410, 3),
        "leading_sqrt": 7200,
        "leading_const": 746807040000,
        "parameter_M": 864000,
        "parameter_N": 864360,
        "quartic_z_coefficients": ((18538956042445440000, 3677189241600000, -1296322560000, 51840000), (-1171402250376960000, -116836715520000, 17210880000), (26028542816640000, 2241596160000, -103680000), (-237057891840000, -17210880000), (746807040000, 51840000)),
        "g_z_coefficients": ((0, -163536436, 32213, -1), (-4305688800, 6441612, -498), (299566036, -124002, 3), (-7742412, 996), (91789, -3), (-498,), (1,)),
        "extra_y_coefficients": ('-110896800', '-61234400', '-36800', '352000/49'),
    },
    "c6": {
        "sextuple": (0, 37, 62, 110, 180, 205),
        "extra_x": (7, 23, 1271, 23),
        "leading_sqrt": 6600,
        "leading_const": 1705199760000,
        "parameter_M": 1302400,
        "parameter_N": 1309275,
        "quartic_z_coefficients": ((86701164331716000000, 10471139236800000, -1461350880000, 43560000), (-4741490089274400000, -282611442960000, 17249760000), (89014750620840000, 3220216560000, -87120000), (-665142120720000, -17249760000), (1705199760000, 43560000)),
        "g_z_coefficients": ((0, -329032300, 45869, -1), (-9311346000, 11179080, -594), (583640500, -176418, 3), (-13040280, 1188), (130549, -3), (-594,), (1,)),
        "extra_y_coefficients": ('-411041400', '-30169576800/529', '92954400/529', '3168000/529'),
    },
}


def _eval_coeff_poly(coeffs, z):
    out = 0 * z
    power = 1 + 0 * z
    for c in coeffs:
        out += c * power
        power *= z
    return out


def _poly_from_coefficients(R, coeffs):
    x = R.gen()
    return sum((coeffs[i] * x**i for i in range(len(coeffs))), R.zero())


def _quartic_invariants_from_coefficients(coeffs):
    e, d, c, b, a = coeffs
    I = 12 * a * e - 3 * b * d + c**2
    J = 72 * a * c * e + 9 * b * c * d - 27 * a * d**2 - 27 * b**2 * e - 2 * c**3
    return I, J


class CampbellBranch:
    historical_generic_rank_lower = 13
    generic_rank = None
    parameter_symmetry = "sign"

    def __init__(self, key):
        key = str(key).lower()
        if key not in BRANCH_DATA:
            raise ValueError(f"unknown Campbell 1999 branch {key!r}")
        self.key = key
        self.data = BRANCH_DATA[key]

    @property
    def label(self):
        return self.key.upper()

    def name(self):
        return f"Campbell 1999 {self.label}, generic rank >=13"

    def canonical_parameter(self, t):
        tq = QQ(t)
        return -tq if tq < 0 else tq

    def parameter_orbit_key(self, t):
        return str(self.canonical_parameter(t))

    def _parameter_data(self, t):
        tq = QQ(t)
        if tq == 0:
            raise ZeroDivisionError("Campbell parameter t=0 is excluded by the rational base change")
        a = QQ(self.data["leading_sqrt"])
        M = QQ(self.data["parameter_M"])
        N = QQ(self.data["parameter_N"])
        u = (N - M * tq**2) / (2 * a * tq)
        b = (N + M * tq**2) / (2 * tq)
        if b == 0:
            raise ZeroDivisionError("Campbell leading-square normalization has b(t)=0")
        if a**2 * u**2 + QQ(self.data["leading_const"]) != b**2:
            raise ArithmeticError("Campbell rational leading-square identity failed")
        return tq, u, b

    def _quartic_coefficients_u(self, u):
        z = u * u
        return [_eval_coeff_poly(row, z) for row in self.data["quartic_z_coefficients"]]

    def _g_coefficients_u(self, u):
        z = u * u
        return [_eval_coeff_poly(row, z) for row in self.data["g_z_coefficients"]]

    def _extra_x(self, u):
        an, ad, bn, bd = self.data["extra_x"]
        return QQ(an) / QQ(ad) * u + QQ(bn) / QQ(bd)

    def _extra_y_u(self, u):
        coeffs = [QQ(c) for c in self.data["extra_y_coefficients"]]
        return sum(coeffs[i] * u**i for i in range(len(coeffs)))

    def _native_data(self, t):
        tq, u, b = self._parameter_data(t)
        if u == 0:
            raise ZeroDivisionError("Campbell shift u(t)=0 degenerates the displayed finite sections")
        R = PolynomialRing(QQ, "x")
        quartic_u = _poly_from_coefficients(R, [QQ(c) for c in self._quartic_coefficients_u(u)])
        G = _poly_from_coefficients(R, [QQ(c) for c in self._g_coefficients_u(u)])
        quartic = quartic_u / (b * b)

        roots = [QQ(a) + u for a in self.data["sextuple"]] + [QQ(a) - u for a in self.data["sextuple"]]
        if len(set(roots)) != 12:
            raise ArithmeticError("specialization has colliding Campbell base fibres")
        points = []
        for xx in roots:
            yy = QQ(G(xx) / (u * b))
            if yy**2 != quartic(xx):
                raise ArithmeticError("Campbell square-completion point failed the normalized quartic")
            points.append((xx, yy))

        extra_x = QQ(self._extra_x(u))
        extra_y = QQ(self._extra_y_u(u) / b)
        if extra_y**2 != quartic(extra_x):
            raise ArithmeticError("Campbell published extra point failed the normalized quartic")
        if extra_x in set(roots):
            raise ArithmeticError("Campbell extra point collided with a constructed base fibre")
        extra = (extra_x, extra_y)
        return R, quartic, roots, points, extra, tq, u, b, G

    @staticmethod
    def _choose_origin(points):
        for index, (_, yy) in enumerate(points):
            if yy != 0:
                return index
        raise ArithmeticError("all Campbell base points have y=0; no finite origin is usable")

    @staticmethod
    def _map_quartic_point(E, data, xq, yq):
        x0, y0, Q = data["x0"], data["y0"], data["Q"]
        C, D = data["C"], data["D"]
        u = QQ(xq) - x0
        v = QQ(yq)
        if u == 0:
            if v == y0:
                return E(0)
            T = data.get("involution_translation")
            if v == -y0 and T is not None:
                return T
            raise ArithmeticError("point above chosen Campbell origin needs exceptional map")
        X = (Q * (v + y0) + D * u) / u**2
        Y = (Q**3 * (v + y0) + Q**2 * (D*u + C*u**2) - D**2*u**2) / (Q*u**3)
        return E(QQ(X), QQ(Y))

    def _rational_model(self, t):
        native = self._native_data(t)
        R, quartic, roots, points, extra, tq, shift_u, lead_b, G = native
        origin_index = self._choose_origin(points)
        x0, y0 = points[origin_index]
        s = R.gen()
        rt = quartic(s + x0)
        A, B, C, D = (QQ(rt[4]), QQ(rt[3]), QQ(rt[2]), QQ(rt[1]))
        if A != 1:
            raise ArithmeticError("normalized Campbell quartic is not monic")
        if QQ(rt[0]) != y0**2:
            raise ArithmeticError("translated Campbell quartic lost its rational origin")
        Q = 2*y0
        a1 = D/y0
        a2 = C - (D/Q)**2
        a3 = B*Q
        a4 = -A*Q**2
        a6 = a2*a4
        E = EllipticCurve(QQ, [a1,a2,a3,a4,a6])
        if E.discriminant() == 0:
            raise ArithmeticError("singular Campbell specialization")
        data = {
            "x0":x0,"y0":y0,"Q":Q,"A":A,"B":B,"C":C,"D":D,
            "origin_index":int(origin_index),"involution_translation":None,
            "parameter_t":tq,"shift_u":shift_u,"leading_square_b":lead_b,
        }
        for index,(xx,yy) in enumerate(points):
            if index == origin_index:
                continue
            P=self._map_quartic_point(E,data,xx,yy)
            Pi=self._map_quartic_point(E,data,xx,-yy)
            data["involution_translation"] = P+Pi
            break
        if data["involution_translation"] is None:
            raise ArithmeticError("could not determine Campbell quartic involution translation")
        return E,data,native

    def curve(self,t):
        try:
            return self._rational_model(t)[0]
        except (ArithmeticError,ValueError,ZeroDivisionError,TypeError):
            return None

    def screen_curve(self,t):
        try:
            coeffs=self.quartic_search_coefficients(t)
            I,J=_quartic_invariants_from_coefficients(coeffs)
            E=EllipticCurve(QQ,[0,0,0,-27*I,-27*J])
            return None if E.discriminant()==0 else E
        except (ArithmeticError,ValueError,ZeroDivisionError,TypeError):
            return None

    def screen_model_name(self):
        return "binary_quartic_jacobian"

    def curve_mod_p(self,r0,p0):
        try:
            p=int(p0)
            if p in (2,3): return None
            K=GF(p); t=K(int(r0))
            if t==0: return None
            a=K(self.data["leading_sqrt"]); M=K(self.data["parameter_M"]); N=K(self.data["parameter_N"])
            if 2*a*t==0 or 2*t==0: return None
            u=(N-M*t*t)/(2*a*t); b=(N+M*t*t)/(2*t)
            if b==0 or u==0: return None
            coeffs=[_eval_coeff_poly(row,u*u)/(b*b) for row in self.data["quartic_z_coefficients"]]
            I,J=_quartic_invariants_from_coefficients(coeffs)
            E=EllipticCurve(K,[0,0,0,-27*I,-27*J])
            return None if E.discriminant()==0 else E
        except (ArithmeticError,ValueError,ZeroDivisionError,TypeError):
            return None

    def quartic_search_coefficients(self,t):
        tq,u,b=self._parameter_data(t)
        if u==0:
            raise ZeroDivisionError("Campbell shift u(t)=0 degenerates the displayed finite sections")
        return [QQ(c)/(b*b) for c in self._quartic_coefficients_u(u)]

    def native_quartic_known_points(self,t):
        native=self._native_data(QQ(t))
        return [*native[3], native[4]]

    def native_quartic_known_x(self,t):
        return [P[0] for P in self.native_quartic_known_points(t)]

    def _basis_candidates_from_model(self,E,data,native):
        points=native[3]; extra=native[4]; origin_index=int(data["origin_index"])
        finite=[]
        for index,(xx,yy) in enumerate(points):
            if index==origin_index: continue
            P=self._map_quartic_point(E,data,xx,yy)
            if P.is_zero(): raise ArithmeticError("non-origin Campbell base point mapped to identity")
            finite.append(P)
        finite.append(self._map_quartic_point(E,data,*extra))
        if len(finite)!=12:
            raise ArithmeticError("Campbell finite transformed section set has wrong size")
        # For a monic quartic, the two rational infinities map to (+/-Q,0).
        inf_plus=E(QQ(data["Q"]),QQ(0))
        inf_minus=E(QQ(-data["Q"]),QQ(0))
        return [[inf_plus,*finite],[inf_minus,*finite]]

    def generic_section_points(self,t):
        E,data,native=self._rational_model(t)
        return self._basis_candidates_from_model(E,data,native)[0]

    def direct_search_bundle(self,t):
        tq=QQ(t); E,data,native=self._rational_model(tq)
        candidates=self._basis_candidates_from_model(E,data,native)
        return {
            "curve":E,
            "basis":candidates[0],
            "basis_candidates":candidates,
            "map_data":data,
            "quartic_coefficients":[QQ(native[1][i]) for i in range(5)],
            "native_points":[*native[3],native[4]],
            "constructed_points":list(native[3]),
            "published_extra_point":native[4],
            "branch":self.key,
            "published_declared_rank":13,
        }

    def map_native_quartic_point(self,bundle,x,y):
        return self._map_quartic_point(bundle["curve"],bundle["map_data"],QQ(str(x)),QQ(str(y)))

    def native_quartic_involution_translation(self,bundle,t):
        T=bundle["map_data"].get("involution_translation")
        if T is None: raise ArithmeticError("quartic involution translation was not initialized")
        for xq,yq in self.native_quartic_known_points(t):
            P=self.map_native_quartic_point(bundle,xq,yq); Pi=self.map_native_quartic_point(bundle,xq,-yq)
            if P+Pi!=T: raise ArithmeticError("Campbell quartic involution failed exact P -> T-P check")
        return T

    def native_quartic_involution_controls(self,bundle,t):
        T=self.native_quartic_involution_translation(bundle,t); out=[]
        for index,(xq,yq) in enumerate(self.native_quartic_known_points(t),1):
            P=self.map_native_quartic_point(bundle,xq,yq); Pi=self.map_native_quartic_point(bundle,xq,-yq)
            if Pi!=T-P: raise ArithmeticError(f"Campbell involution relation failed on known fibre {index}")
            out.append({"index":index,"native_point":(QQ(xq),QQ(yq)),"published_image":P,"opposite_image":Pi,"translation":T})
        return out

    def covering_map_expressions_from_native(self,bundle,native_x="u",native_y="v"):
        d=bundle["map_data"]; x0,y0,Q,C,D=(d[k] for k in ("x0","y0","Q","C","D"))
        w=f"(({native_x})-({x0}))"; vv=f"({native_y})"
        xexpr=f"(({Q})*({vv}+({y0}))+({D})*{w})/({w}^2)"
        yexpr=(f"(({Q})^3*({vv}+({y0}))+({Q})^2*(({D})*{w}+({C})*({w}^2))" f"-({D})^2*({w}^2))/(({Q})*({w}^3))")
        return {"x":xexpr,"y":yexpr}

    def covering_map_expressions(self,bundle):
        return self.covering_map_expressions_from_native(bundle,"u","v")

    def construction_check(self,t=QQ(1)):
        tq=QQ(t); bundle=self.direct_search_bundle(tq); E=bundle["curve"]; coeffs=bundle["quartic_coefficients"]
        for xx,yy in bundle["native_points"]:
            rhs=sum(coeffs[i]*xx**i for i in range(5))
            if yy**2!=rhs: raise ArithmeticError("known Campbell point failed normalized quartic equation")
        screen=self.screen_curve(tq)
        if screen is None or screen.j_invariant()!=E.j_invariant():
            raise ArithmeticError("Campbell quartic Jacobian and finite-origin model disagree on j")
        if coeffs[4] != 1:
            raise ArithmeticError("Campbell native quartic leading coefficient is not one")
        return {
            "family":self.name(),"branch":self.key,"parameter":str(tq),
            "known_affine_points":len(bundle["native_points"]),"basis_candidates":len(bundle["basis_candidates"]),
            "sections_per_basis":len(bundle["basis"]),"quartic_monic":True,
            "j_invariant":str(E.j_invariant()),"t_sign_quartic_symmetry":coeffs==self.quartic_search_coefficients(-tq),
            "claim_scope":"exact specialization construction/on-curve checks; rank requires exact certificate",
        }

    def validate_symbolically(self):
        T=PolynomialRing(QQ,"t"); K=T.fraction_field(); t=K(T.gen())
        U=PolynomialRing(K,"u"); # only used to retain an exact fraction-field parent
        a=K(self.data["leading_sqrt"]); M=K(self.data["parameter_M"]); N=K(self.data["parameter_N"])
        shift=(N-M*t**2)/(2*a*t); b=(N+M*t**2)/(2*t)
        if a**2*shift**2+K(self.data["leading_const"]) != b**2:
            raise ArithmeticError("symbolic Campbell leading-square parameterization failed")
        R=PolynomialRing(K,"x"); x=R.gen()
        quartic_u=_poly_from_coefficients(R,[K(c) for c in self._quartic_coefficients_u(shift)])
        G=_poly_from_coefficients(R,[K(c) for c in self._g_coefficients_u(shift)])
        q=quartic_u/(b*b)
        p=R.one()
        for ai in self.data["sextuple"]:
            p*=((x-K(ai))**2-shift**2)
        if G*G-p != shift**2*quartic_u:
            raise ArithmeticError("symbolic Campbell square-completion identity failed")
        roots=[K(ai)+shift for ai in self.data["sextuple"]]+[K(ai)-shift for ai in self.data["sextuple"]]
        for xx in roots:
            yy=G(xx)/(shift*b)
            if yy**2!=q(xx): raise ArithmeticError("symbolic Campbell constructed point failed")
        ex=self._extra_x(shift); ey=self._extra_y_u(shift)/b
        if ey**2!=q(ex): raise ArithmeticError("symbolic Campbell published extra point failed")
        if q[4]!=1: raise ArithmeticError("symbolic Campbell native quartic is not monic")
        return {
            "family":self.name(),"branch":self.key,"identity_verified":True,
            "constructed_affine_points_verified":12,"published_extra_point_verified":True,
            "rational_infinities":2,"displayed_section_candidates":13,
            "claim_scope":"exact Q(t) identities and on-curve verification only; generic independence remains literature provenance until independently certified",
        }


def _branch_from_argv(default="c1"):
    try:
        index=sys.argv.index("--branch")
    except ValueError:
        return default
    if index+1 >= len(sys.argv):
        return default
    value=str(sys.argv[index+1]).lower()
    return value if value in BRANCH_DATA else default


# Plugin-local branch selected by the v0.8.1 variant-aware adapter.
family = CampbellBranch(_branch_from_argv())
