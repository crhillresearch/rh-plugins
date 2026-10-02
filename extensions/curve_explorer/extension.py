from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import streamlit as st


def _load_backend():
    path = Path(__file__).with_name("backend.py")
    spec = importlib.util.spec_from_file_location("rank42_curve_explorer_backend", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


B = _load_backend()

_THEME_TOKEN_KEYS = (
    "rh-bg",
    "rh-card",
    "rh-card-2",
    "rh-surface-hover",
    "rh-surface-active",
    "rh-border",
    "rh-border-strong",
    "rh-control-border",
    "rh-text",
    "rh-text-secondary",
    "rh-muted",
    "rh-muted-2",
    "rh-primary",
    "rh-primary-deep",
    "rh-success",
    "rh-warning",
    "rh-danger",
    "rh-text-on-accent",
)

_THEME_FALLBACKS = {
    "light": {
        "rh-bg": "#f4f7fb",
        "rh-card": "#ffffff",
        "rh-card-2": "#eef3f8",
        "rh-surface-hover": "#e8f0f8",
        "rh-surface-active": "#dbeafe",
        "rh-border": "#d6dee8",
        "rh-border-strong": "#a9b7c8",
        "rh-control-border": "#a9b7c8",
        "rh-text": "#162033",
        "rh-text-secondary": "#46566d",
        "rh-muted": "#6f7e92",
        "rh-muted-2": "#94a1b2",
        "rh-primary": "#1677c8",
        "rh-primary-deep": "#0f5f9f",
        "rh-success": "#23855b",
        "rh-warning": "#a76b16",
        "rh-danger": "#bd4050",
        "rh-text-on-accent": "#ffffff",
    },
    "dark": {
        "rh-bg": "#0b0f16",
        "rh-card": "#111722",
        "rh-card-2": "#171e2b",
        "rh-surface-hover": "#202a39",
        "rh-surface-active": "#163247",
        "rh-border": "#273142",
        "rh-border-strong": "#354257",
        "rh-control-border": "#354257",
        "rh-text": "#edf2f7",
        "rh-text-secondary": "#b7c1cc",
        "rh-muted": "#8d99a8",
        "rh-muted-2": "#68778a",
        "rh-primary": "#58c7ff",
        "rh-primary-deep": "#2e7da7",
        "rh-success": "#55dfa6",
        "rh-warning": "#ffbd66",
        "rh-danger": "#ff775c",
        "rh-text-on-accent": "#ffffff",
    },
}


def _runtime_appearance(context):
    value = st.session_state.get("_rh_appearance")
    if not value:
        setting = getattr(context, "setting", None)
        if callable(setting):
            try:
                value = setting("ui_appearance", "")
            except Exception:
                value = ""
    if not value:
        try:
            value = st.get_option("theme.base")
        except Exception:
            value = ""
    value = str(value or "light").strip().lower()
    return value if value in {"light", "dark"} else "light"


def _safe_css_token(value, fallback):
    value = str(value or "").strip()
    if not value or any(char in value for char in "{};"):
        return fallback
    return value


def _runtime_theme_css(context):
    appearance = _runtime_appearance(context)
    fallback = _THEME_FALLBACKS[appearance]
    runtime = st.session_state.get("_rh_theme_palette")
    runtime = runtime if isinstance(runtime, dict) else {}

    lines = [":root {", f"  color-scheme: {appearance};"]
    for key in _THEME_TOKEN_KEYS:
        value = _safe_css_token(runtime.get(key), fallback[key])
        lines.append(f"  --{key}: {value};")
    lines.append("}")
    return "\n".join(lines)


def _curve_label(row):
    vals = [row[k] for k in ("exact_rank", "descent_lower", "generic_lower") if k in row and row[k] is not None]
    rank = f"≥{max(int(v) for v in vals)}" if vals else "rank ?"
    score = f" · Nagao {float(row['score']):.3f}" if row.get("score") is not None else ""
    return f"#{row['id']} · {row.get('family','curve')} · t={row.get('parameter','—')} · {rank}{score}"


def _point_label(p):
    badge = "✓" if p.exact_verified else "·"
    return f"{badge} {p.label} {p.compact()}"


HTML_TEMPLATE = r'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
__THEME_CSS__
:root {
  --paper:var(--rh-card); --paper2:var(--rh-bg); --raised:var(--rh-card-2); --ink:var(--rh-text); --muted:var(--rh-muted);
  --border:var(--rh-border); --border-strong:var(--rh-border-strong); --grid:color-mix(in srgb,var(--rh-border) 72%,transparent); --axis:var(--rh-muted-2); --curve:var(--rh-primary);
  --stored:var(--rh-success); --p:var(--rh-warning); --q:color-mix(in srgb,var(--rh-primary) 46%,var(--rh-danger) 54%); --third:var(--rh-primary-deep);
  --sum:var(--rh-danger); --line:var(--rh-text-secondary); --shadow:0 18px 42px color-mix(in srgb,var(--rh-text) 18%,transparent);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:transparent;color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.shell{background:var(--paper);border:1px solid var(--border);border-radius:18px;overflow:hidden;box-shadow:var(--shadow)}
.head{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:13px 16px 11px 18px;border-bottom:1px solid var(--border);background:linear-gradient(180deg,var(--rh-card-2),var(--rh-card))}
.title{min-width:0}.eyebrow{font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);font-weight:750;margin-bottom:3px}.eq{font-family:Cambria,"Times New Roman",serif;font-size:20px;line-height:1.1;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.controls,.filterbar,.selectionbar{display:flex;align-items:center;gap:6px;flex-wrap:wrap}.controls{flex:none}
button{height:31px;padding:0 10px;display:inline-grid;place-items:center;border:1px solid var(--rh-control-border);background:var(--raised);color:var(--rh-text-secondary);border-radius:9px;font-size:11px;font-weight:700;cursor:pointer;box-shadow:0 1px 1px color-mix(in srgb,var(--rh-text) 12%,transparent)}
button.icon{width:33px;padding:0;font-size:15px}button:hover{background:var(--rh-surface-hover);border-color:var(--rh-border-strong);color:var(--rh-text)}button.active{background:var(--rh-surface-active);border-color:var(--rh-primary);color:var(--rh-primary)}button:disabled{opacity:.38;cursor:default}
.toolrow{display:flex;justify-content:space-between;gap:12px;padding:8px 16px;border-bottom:1px solid var(--border);background:var(--rh-card);align-items:center;min-height:48px}
.filterbar button{border-radius:999px;height:28px}.selectionbar{justify-content:flex-end;color:var(--muted);font-size:11px}.pick{padding:5px 9px;border-radius:999px;background:var(--rh-card-2);border:1px solid var(--border);white-space:nowrap}.pick strong{color:var(--rh-text)}.pick.p strong{color:var(--p)}.pick.q strong{color:var(--q)}
.canvas-wrap{position:relative;background:var(--paper)}svg{display:block;width:100%;height:680px;background:var(--paper);cursor:grab;touch-action:none}svg.dragging{cursor:grabbing}
.legend{position:absolute;left:17px;top:14px;display:flex;gap:6px;flex-wrap:wrap;max-width:70%;pointer-events:none}.chip{display:flex;align-items:center;gap:5px;padding:4px 7px;border:1px solid color-mix(in srgb,var(--rh-border) 78%,transparent);border-radius:999px;background:color-mix(in srgb,var(--rh-card) 88%,transparent);backdrop-filter:blur(7px);color:var(--rh-text-secondary);font-size:10px;box-shadow:0 3px 10px color-mix(in srgb,var(--rh-text) 12%,transparent)}.swatch{width:8px;height:8px;border-radius:50%;display:inline-block}
.readout{position:absolute;right:15px;bottom:15px;min-width:235px;max-width:48%;background:color-mix(in srgb,var(--rh-card) 96%,transparent);border:1px solid var(--border-strong);border-radius:12px;padding:9px 11px;box-shadow:0 8px 24px color-mix(in srgb,var(--rh-text) 18%,transparent);font-size:11px;line-height:1.45;display:none;color:var(--rh-text-secondary)}.readout .name{font-weight:760;color:var(--rh-text)}.readout .coords{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10px;color:var(--rh-text-secondary);word-break:break-all}.readout .math{margin-top:4px;color:var(--rh-text-secondary)}
.foot{display:flex;justify-content:space-between;gap:15px;padding:9px 16px 10px 18px;border-top:1px solid var(--border);color:var(--muted);font-size:10px;background:var(--rh-card)}.tooltip{position:fixed;display:none;pointer-events:none;z-index:50;background:var(--rh-card-2);color:var(--rh-text);border:1px solid var(--rh-border-strong);border-radius:8px;padding:7px 9px;font-size:10px;box-shadow:0 9px 26px color-mix(in srgb,var(--rh-text) 20%,transparent);white-space:nowrap}
@media(max-width:760px){.head{align-items:flex-start;flex-direction:column}.toolrow{align-items:flex-start;flex-direction:column}.selectionbar{justify-content:flex-start}.eq{font-size:17px}svg{height:610px}.readout{max-width:70%}}
</style>
</head>
<body>
<div class="shell">
  <div class="head">
    <div class="title"><div class="eyebrow">Real locus over ℝ · exact click constructions over ℚ</div><div class="eq" id="eq"></div></div>
    <div class="controls">
      <button class="icon" id="out" title="Zoom out">−</button><button class="icon" id="in" title="Zoom in">+</button>
      <button id="smart" title="Smart initial framing">Smart</button><button id="fitShown">Fit shown</button><button id="fitAll">Fit all</button><button id="shape">Curve</button>
    </div>
  </div>
  <div class="toolrow">
    <div class="filterbar"><button class="active" data-filter="all">All points</button><button data-filter="generators">Generators</button><button data-filter="subgroup">Selected subgroup</button></div>
    <div class="selectionbar">
      <span class="pick p"><strong>P</strong>: <span id="pPick">click a point</span></span><span class="pick q"><strong>Q</strong>: <span id="qPick">click next</span></span>
      <button id="tangent" disabled>Tangent at P</button><button id="play" disabled>▶ Construct</button><button id="fitConstruction" disabled>Fit construction</button><button id="clear" disabled>Clear</button>
    </div>
  </div>
  <div class="canvas-wrap">
    <svg id="plot" viewBox="0 0 1000 680" role="img" aria-label="Elliptic curve real locus with exact rational points"></svg>
    <div class="legend"><span class="chip"><i class="swatch" style="background:var(--curve)"></i>curve</span><span class="chip"><i class="swatch" style="background:var(--stored)"></i>stored ℚ-points</span><span class="chip"><i class="swatch" style="background:var(--p)"></i>P</span><span class="chip"><i class="swatch" style="background:var(--q)"></i>Q</span><span class="chip"><i class="swatch" style="background:var(--third)"></i>R</span><span class="chip"><i class="swatch" style="background:var(--sum)"></i>−R = P+Q</span></div>
    <div class="readout" id="readout"><div class="name" id="rname"></div><div class="coords" id="rcoords"></div><div class="math" id="rmath"></div><div id="rmeta"></div></div>
  </div>
  <div class="foot"><span id="hint">click a point for P · click another for Q · click P twice for a tangent · hover for exact coordinates</span><span id="cache"></span></div>
</div>
<div class="tooltip" id="tip"></div>
<script>
const DATA=__DATA__;
const svg=document.getElementById('plot'),tip=document.getElementById('tip'),readout=document.getElementById('readout');
const rname=document.getElementById('rname'),rcoords=document.getElementById('rcoords'),rmath=document.getElementById('rmath'),rmeta=document.getElementById('rmeta');
const pPick=document.getElementById('pPick'),qPick=document.getElementById('qPick'),hint=document.getElementById('hint');
const tangentBtn=document.getElementById('tangent'),playBtn=document.getElementById('play'),fitConstructionBtn=document.getElementById('fitConstruction'),clearBtn=document.getElementById('clear');
document.getElementById('eq').textContent=DATA.equation;
document.getElementById('cache').textContent=DATA.pair_cache_points>=DATA.point_count?`${DATA.point_count} exact interactive point${DATA.point_count===1?'':'s'}`:`precomputed exact cache ${DATA.pair_cache_points}/${DATA.point_count} · uncached pairs computed exactly on selection`;
const NS='http://www.w3.org/2000/svg',W=1000,H=680,PAD={l:64,r:28,t:30,b:54};
const byId=Object.fromEntries(DATA.points.map(p=>[String(p.id),p]));
let view=null,initial=null,drag=null,filterMode='all',selection={p:null,q:null},constructionStep=3,playTimers=[];
const dynamicPairCache={};
function el(t,a={}){const e=document.createElementNS(NS,t);Object.entries(a).forEach(([k,v])=>v!==null&&v!==undefined&&e.setAttribute(k,v));return e}
function finite(v){return Number.isFinite(v)&&Math.abs(v)<1e290}
function discr(x){const[a1,a2,a3,a4,a6]=DATA.ainv,L=a1*x+a3;return L*L+4*(x*x*x+a2*x*x+a4*x+a6)}
function branches(x){const[a1,,a3]=DATA.ainv,d=discr(x);if(!(d>=0)||!finite(d))return null;const r=Math.sqrt(d),L=a1*x+a3;return[(-L+r)/2,(-L-r)/2]}
function pairKey(a,b){return[String(a),String(b)].sort().join('|')}
function bgcd(a,b){a=a<0n?-a:a;b=b<0n?-b:b;while(b!==0n){const t=a%b;a=b;b=t}return a||1n}
function rat(n,d=1n){n=BigInt(n);d=BigInt(d);if(d===0n)throw new Error('zero rational denominator');if(d<0n){n=-n;d=-d}const g=bgcd(n,d);return{n:n/g,d:d/g}}
function qparse(value){const s=String(value).trim();const parts=s.split('/');return rat(BigInt(parts[0]),parts.length>1?BigInt(parts[1]):1n)}
function qadd(a,b){return rat(a.n*b.d+b.n*a.d,a.d*b.d)}
function qsub(a,b){return rat(a.n*b.d-b.n*a.d,a.d*b.d)}
function qmul(a,b){return rat(a.n*b.n,a.d*b.d)}
function qdiv(a,b){if(b.n===0n)throw new Error('division by zero');return rat(a.n*b.d,a.d*b.n)}
function qneg(a){return{n:-a.n,d:a.d}}
function qeq(a,b){return a.n===b.n&&a.d===b.d}
function qzero(a){return a.n===0n}
function qsquare(a){return qmul(a,a)}
function qcube(a){return qmul(qsquare(a),a)}
function qtext(a){return a.d===1n?a.n.toString():`${a.n}/${a.d}`}
function qfloat(a){if(a.n===0n)return 0;const sign=a.n<0n?-1:1,ns=(a.n<0n?-a.n:a.n).toString(),ds=a.d.toString(),take=16,nLead=Number(ns.slice(0,take)),dLead=Number(ds.slice(0,take)),exp=(ns.length-Math.min(take,ns.length))-(ds.length-Math.min(take,ds.length));const v=sign*(nLead/dLead)*(10**Math.max(-300,Math.min(300,exp)));if(!Number.isFinite(v))return sign*1e290;return Math.max(-1e290,Math.min(1e290,v))}
function exactConstruction(P,Q){
  const [a1,a2,a3,a4,a6]=DATA.ainv_exact.map(qparse),x1=qparse(P.x_exact),y1=qparse(P.y_exact),x2=qparse(Q.x_exact),y2=qparse(Q.y_exact);
  const sameX=qeq(x1,x2),vertical=sameX&&qzero(qadd(qadd(y1,y2),qadd(qmul(a1,x1),a3)));
  if(vertical)return{p:String(P.id),q:String(Q.id),vertical:true,x_vertical:P.x,line:null,result:null,third:null,dynamic:true};
  let lam,nu;
  if(!sameX){lam=qdiv(qsub(y2,y1),qsub(x2,x1));nu=qdiv(qsub(qmul(y1,x2),qmul(y2,x1)),qsub(x2,x1))}
  else{
    const den=qadd(qadd(qmul(rat(2n),y1),qmul(a1,x1)),a3);
    if(qzero(den))return{p:String(P.id),q:String(Q.id),vertical:true,x_vertical:P.x,line:null,result:null,third:null,dynamic:true};
    lam=qdiv(qsub(qadd(qadd(qmul(rat(3n),qsquare(x1)),qmul(qmul(rat(2n),a2),x1)),a4),qmul(a1,y1)),den);
    nu=qdiv(qsub(qadd(qadd(qneg(qcube(x1)),qmul(a4,x1)),qmul(rat(2n),a6)),qmul(a3,y1)),den)
  }
  const x3=qsub(qsub(qsub(qadd(qsquare(lam),qmul(a1,lam)),a2),x1),x2);
  const y3=qsub(qsub(qneg(qmul(qadd(lam,a1),x3)),nu),a3);
  const yThird=qsub(qsub(qneg(y3),qmul(a1,x3)),a3);
  return{
    p:String(P.id),q:String(Q.id),vertical:false,x_vertical:null,dynamic:true,
    line:{lambda:qfloat(lam),nu:qfloat(nu),lambda_exact:qtext(lam),nu_exact:qtext(nu)},
    result:{x:qfloat(x3),y:qfloat(y3),x_exact:qtext(x3),y_exact:qtext(y3)},
    third:{x:qfloat(x3),y:qfloat(yThird),x_exact:qtext(x3),y_exact:qtext(yThird)}
  }
}
function currentPair(){
  if(selection.p===null||selection.q===null)return null;
  const key=pairKey(selection.p,selection.q);
  if(DATA.pair_constructions[key])return DATA.pair_constructions[key];
  if(dynamicPairCache[key])return dynamicPairCache[key];
  const P=byId[String(selection.p)],Q=byId[String(selection.q)];
  if(!P||!Q)return null;
  try{dynamicPairCache[key]=exactConstruction(P,Q);return dynamicPairCache[key]}
  catch(err){console.error('exact construction failed',err);return null}
}
function pointVisible(p){if(String(p.id)===String(selection.p)||String(p.id)===String(selection.q))return true;if(filterMode==='generators')return !!p.is_generator;if(filterMode==='subgroup')return !!p.in_subgroup;return true}
function shownPoints(){return DATA.points.filter(pointVisible)}
function visibleY(xmin,xmax,pts=shownPoints()){let vals=[];const n=1300;for(let i=0;i<=n;i++){const x=xmin+(xmax-xmin)*i/n,b=branches(x);if(b)for(const y of b)if(finite(y))vals.push(y)}for(const p of pts)if(p.x>=xmin&&p.x<=xmax&&finite(p.y))vals.push(p.y);const pair=currentPair();if(pair){for(const k of ['third','result']){const p=pair[k];if(p&&p.x>=xmin&&p.x<=xmax&&finite(p.y))vals.push(p.y)}}if(!vals.length)return[-5,5];let lo=Math.min(...vals),hi=Math.max(...vals);if(lo===hi){lo-=1;hi+=1}const span=hi-lo,pad=Math.max(.5,span*.10);return[lo-pad,hi+pad]}
function setInitial(xmin,xmax){const yr=visibleY(xmin,xmax,DATA.points);initial={xmin,xmax,ymin:yr[0],ymax:yr[1]};view={...initial};draw()}
function map(){const iw=W-PAD.l-PAD.r,ih=H-PAD.t-PAD.b,sx=iw/(view.xmax-view.xmin),sy=ih/(view.ymax-view.ymin);return{X:x=>PAD.l+(x-view.xmin)*sx,Y:y=>PAD.t+(view.ymax-y)*sy,sx,sy}}
function niceStep(span,target=10){const raw=Math.max(span/target,1e-300),p=10**Math.floor(Math.log10(raw)),r=raw/p;return(r<1.5?1:r<3.5?2:r<7.5?5:10)*p}
function fmtTick(v,step){if(Math.abs(v)<Math.abs(step)*1e-8)return'0';const av=Math.abs(v);if(av>=1e5||(av>0&&av<1e-3))return v.toExponential(1).replace('+','');const d=Math.max(0,Math.min(6,-Math.floor(Math.log10(Math.abs(step)))+1));return(+v.toFixed(d)).toString()}
function curvePath(M,branch){let d='',open=false,py=null;const N=Math.max(1400,DATA.samples);for(let i=0;i<=N;i++){const x=view.xmin+(view.xmax-view.xmin)*i/N,b=branches(x);if(!b){open=false;py=null;continue}const y=b[branch];if(!finite(y)){open=false;continue}const X=M.X(x),Y=M.Y(y);if(Y<PAD.t-160||Y>H-PAD.b+160){open=false;py=null;continue}if(py!==null&&Math.abs(Y-py)>180)open=false;d+=(open?'L':'M')+X.toFixed(2)+','+Y.toFixed(2)+' ';open=true;py=Y}return d}
function text(g,x,y,s,attrs={}){const t=el('text',{x,y,fill:'var(--muted)','font-size':'11','font-family':'Inter,system-ui,sans-serif',...attrs});t.textContent=s;g.appendChild(t);return t}
function drawAxes(M){const g=el('g'),xs=niceStep(view.xmax-view.xmin,11),ys=niceStep(view.ymax-view.ymin,9);for(let x=Math.ceil(view.xmin/xs)*xs;x<=view.xmax+xs*1e-8;x+=xs){const X=M.X(x);g.appendChild(el('line',{x1:X,y1:PAD.t,x2:X,y2:H-PAD.b,stroke:'var(--grid)','stroke-width':'1'}));text(g,X,H-PAD.b+22,fmtTick(x,xs),{'text-anchor':'middle'})}for(let y=Math.ceil(view.ymin/ys)*ys;y<=view.ymax+ys*1e-8;y+=ys){const Y=M.Y(y);g.appendChild(el('line',{x1:PAD.l,y1:Y,x2:W-PAD.r,y2:Y,stroke:'var(--grid)','stroke-width':'1'}));text(g,PAD.l-11,Y+4,fmtTick(y,ys),{'text-anchor':'end'})}if(view.xmin<=0&&view.xmax>=0){const X=M.X(0);g.appendChild(el('line',{x1:X,y1:PAD.t,x2:X,y2:H-PAD.b,stroke:'var(--axis)','stroke-width':'1.35'}))}if(view.ymin<=0&&view.ymax>=0){const Y=M.Y(0);g.appendChild(el('line',{x1:PAD.l,y1:Y,x2:W-PAD.r,y2:Y,stroke:'var(--axis)','stroke-width':'1.35'}))}text(g,W-PAD.r-2,H-PAD.b+38,'x',{'text-anchor':'end','font-size':'13','font-style':'italic',fill:'var(--muted)'});text(g,PAD.l-35,PAD.t+3,'y',{'text-anchor':'middle','font-size':'13','font-style':'italic',fill:'var(--muted)'});svg.appendChild(g)}
function showPoint(p,kind='stored point'){readout.style.display='block';rname.textContent=`${kind} · ${p.label||''}`;rcoords.textContent=`(${p.x_exact}, ${p.y_exact})`;rmath.textContent='';rmeta.textContent=`${p.role||''}${p.independence?' · '+p.independence:''}`}
function showConstruction(){const pair=currentPair(),P=selection.p!==null?byId[String(selection.p)]:null,Q=selection.q!==null?byId[String(selection.q)]:null;if(!P){readout.style.display='none';return}readout.style.display='block';if(!Q){rname.textContent=`P = ${P.label}`;rcoords.textContent=`(${P.x_exact}, ${P.y_exact})`;rmath.textContent='Choose Q, or click P again for the tangent.';rmeta.textContent='exact stored rational point';return}rname.textContent=`${P.label} + ${Q.label}`;rcoords.textContent=pair&&pair.result?`(${pair.result.x_exact}, ${pair.result.y_exact})`:'O';if(pair&&pair.third)rmath.textContent=`line meets R = (${pair.third.x_exact}, ${pair.third.y_exact}); negate R to get P + Q`;else if(pair&&pair.vertical)rmath.textContent='vertical secant/tangent: P + Q = O';else rmath.textContent='exact construction not cached for this pair';rmeta.textContent=pair?'construction precomputed exactly over Q':'use Server exact tools below for this uncached pair'}
function marker(g,p,M,kind='stored',labelText=null){if(!finite(p.x)||!finite(p.y)||p.x<view.xmin||p.x>view.xmax||p.y<view.ymin||p.y>view.ymax)return;const colors={stored:'var(--stored)',P:'var(--p)',Q:'var(--q)',third:'var(--third)',sum:'var(--sum)'},c=colors[kind]||colors.stored,r=kind==='stored'?4.7:7.1;const halo=el('circle',{cx:M.X(p.x),cy:M.Y(p.y),r:r+5,fill:'transparent',stroke:'transparent','stroke-width':'2','pointer-events':'all'});const dot=el('circle',{cx:M.X(p.x),cy:M.Y(p.y),r,fill:c,stroke:'var(--paper)','stroke-width':kind==='stored'?1.5:2});const hoverText=()=>`${labelText||p.label||kind} = (${p.x_exact}, ${p.y_exact})${p.interactive===false?' · exact playback computed on selection':''}`;const enter=e=>{tip.style.display='block';tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+10)+'px';tip.textContent=hoverText()};const move=e=>{tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+10)+'px'};const leave=()=>tip.style.display='none';const click=e=>{e.stopPropagation();if(kind==='stored'||kind==='P'||kind==='Q'){selectPoint(String(p.id));if(p.interactive===false){hint.textContent='P/Q selected. This pair was outside the precomputed cache, so exact playback was computed on selection.'}return}showPoint({...p,label:labelText||kind},kind)};for(const target of [halo,dot]){target.style.cursor='pointer';target.addEventListener('mouseenter',enter);target.addEventListener('mousemove',move);target.addEventListener('mouseleave',leave);target.addEventListener('click',click)}g.appendChild(halo);g.appendChild(dot);if(kind!=='stored')text(g,M.X(p.x)+9,M.Y(p.y)-9,labelText||kind,{fill:c,'font-weight':'760','font-size':'12'})}
function drawConstruction(body,M,pair){if(!pair||constructionStep<1)return;if(pair.vertical){const X=M.X(pair.x_vertical);body.appendChild(el('line',{x1:X,y1:PAD.t,x2:X,y2:H-PAD.b,stroke:'var(--line)','stroke-width':'1.8','stroke-dasharray':'7 6',opacity:'.82'}));if(constructionStep>=3)text(body,X+8,PAD.t+20,'P + Q = O',{fill:'var(--sum)','font-weight':'750','font-size':'12'});return}if(pair.line){const y1=pair.line.lambda*view.xmin+pair.line.nu,y2=pair.line.lambda*view.xmax+pair.line.nu;body.appendChild(el('line',{x1:M.X(view.xmin),y1:M.Y(y1),x2:M.X(view.xmax),y2:M.Y(y2),stroke:'var(--line)','stroke-width':'1.8','stroke-dasharray':'7 6',opacity:'.80'}))}if(constructionStep>=2&&pair.third)marker(body,{...pair.third,label:'R',role:'third intersection',independence:'derived exactly',interactive:false},M,'third','R');if(constructionStep>=3&&pair.third&&pair.result){body.appendChild(el('line',{x1:M.X(pair.third.x),y1:M.Y(pair.third.y),x2:M.X(pair.result.x),y2:M.Y(pair.result.y),stroke:'var(--sum)','stroke-width':'1.7','stroke-dasharray':'3 5',opacity:'.8'}));marker(body,{...pair.result,label:'P + Q',role:'exact sum',independence:'derived exactly',interactive:false},M,'sum','−R = P + Q')}}
function draw(){svg.innerHTML='';svg.appendChild(el('rect',{x:0,y:0,width:W,height:H,fill:'var(--paper)'}));const M=map();drawAxes(M);const clip=el('clipPath',{id:'plotclip'});clip.appendChild(el('rect',{x:PAD.l,y:PAD.t,width:W-PAD.l-PAD.r,height:H-PAD.t-PAD.b}));const defs=el('defs');defs.appendChild(clip);svg.appendChild(defs);const body=el('g',{'clip-path':'url(#plotclip)'});const cg=el('g',{fill:'none',stroke:'var(--curve)','stroke-width':'3.15','stroke-linejoin':'round','stroke-linecap':'round'});cg.appendChild(el('path',{d:curvePath(M,0)}));cg.appendChild(el('path',{d:curvePath(M,1)}));body.appendChild(cg);const pg=el('g');for(const p of DATA.points){if(!pointVisible(p))continue;let kind='stored',label=null;const isP=String(p.id)===String(selection.p),isQ=String(p.id)===String(selection.q);if(isP&&isQ){kind='P';label='P = Q'}else if(isP){kind='P';label='P'}else if(isQ){kind='Q';label='Q'}marker(pg,p,M,kind,label)}body.appendChild(pg);drawConstruction(body,M,currentPair());svg.appendChild(body);svg.appendChild(el('rect',{x:PAD.l,y:PAD.t,width:W-PAD.l-PAD.r,height:H-PAD.t-PAD.b,fill:'none',stroke:'var(--border-strong)','stroke-width':'1'}))}
function zoom(f,cx=(view.xmin+view.xmax)/2,cy=(view.ymin+view.ymax)/2){const wx=(view.xmax-view.xmin)*f/2,wy=(view.ymax-view.ymin)*f/2;view={xmin:cx-wx,xmax:cx+wx,ymin:cy-wy,ymax:cy+wy};draw()}
function fitList(pts){pts=pts.filter(p=>p&&finite(p.x)&&finite(p.y));if(!pts.length){view={...initial};draw();return}let xs=pts.map(p=>p.x),ys=pts.map(p=>p.y),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys),sx=xmax-xmin,sy=ymax-ymin;if(!sx)sx=Math.max(2,Math.abs(xmin)*.35);if(!sy)sy=Math.max(2,Math.abs(ymin)*.35);view={xmin:xmin-sx*.30,xmax:xmax+sx*.30,ymin:ymin-sy*.25,ymax:ymax+sy*.25};draw()}
function fitShown(){fitList(shownPoints())}function fitAll(){fitList(DATA.points)}
function fitShape(){const[xmin,xmax]=DATA.shape_bounds,yr=visibleY(xmin,xmax,[]);view={xmin,xmax,ymin:yr[0],ymax:yr[1]};draw()}
function fitConstruction(){const pts=[];if(selection.p!==null)pts.push(byId[String(selection.p)]);if(selection.q!==null)pts.push(byId[String(selection.q)]);const pair=currentPair();if(pair){if(pair.third)pts.push(pair.third);if(pair.result)pts.push(pair.result)}fitList(pts)}
function constructionOutside(){const pts=[];if(selection.p!==null)pts.push(byId[String(selection.p)]);if(selection.q!==null)pts.push(byId[String(selection.q)]);const pair=currentPair();if(pair){if(pair.third)pts.push(pair.third);if(pair.result)pts.push(pair.result)}return pts.some(p=>p&&(p.x<view.xmin||p.x>view.xmax||p.y<view.ymin||p.y>view.ymax))}
function updateSelectionUI(){const P=selection.p!==null?byId[String(selection.p)]:null,Q=selection.q!==null?byId[String(selection.q)]:null;pPick.textContent=P?P.label:'click a point';qPick.textContent=Q?Q.label:'click next';tangentBtn.disabled=!P;playBtn.disabled=!(P&&Q&&currentPair());fitConstructionBtn.disabled=!(P||Q);clearBtn.disabled=!(P||Q);showConstruction();draw()}
function selectPoint(id){if(selection.p===null){selection={p:id,q:null}}else if(selection.q===null){selection={p:selection.p,q:id}}else{selection={p:id,q:null}}constructionStep=3;updateSelectionUI();if(selection.p!==null&&selection.q!==null&&constructionOutside())fitConstruction()}
function clearSelection(){selection={p:null,q:null};constructionStep=3;readout.style.display='none';hint.textContent='click a point for P · click another for Q · click P twice for a tangent · hover for exact coordinates';updateSelectionUI()}
function playConstruction(){const pair=currentPair();if(!pair)return;playTimers.forEach(clearTimeout);playTimers=[];constructionStep=0;draw();[1,2,3].forEach((step,i)=>playTimers.push(setTimeout(()=>{constructionStep=step;draw();showConstruction()},350+i*520)))}
for(const b of document.querySelectorAll('[data-filter]'))b.addEventListener('click',()=>{filterMode=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));fitShown();draw()});
tangentBtn.onclick=()=>{if(selection.p!==null){selection.q=selection.p;constructionStep=3;updateSelectionUI();if(constructionOutside())fitConstruction()}};playBtn.onclick=playConstruction;fitConstructionBtn.onclick=fitConstruction;clearBtn.onclick=clearSelection;
document.getElementById('smart').onclick=()=>{view={...initial};draw()};document.getElementById('fitShown').onclick=fitShown;document.getElementById('fitAll').onclick=fitAll;document.getElementById('shape').onclick=fitShape;document.getElementById('in').onclick=()=>zoom(.82);document.getElementById('out').onclick=()=>zoom(1.22);
svg.addEventListener('wheel',e=>{e.preventDefault();const r=svg.getBoundingClientRect(),mx=view.xmin+(e.clientX-r.left)/r.width*(view.xmax-view.xmin),my=view.ymax-(e.clientY-r.top)/r.height*(view.ymax-view.ymin);zoom(e.deltaY>0?1.16:.86,mx,my)},{passive:false});svg.addEventListener('dblclick',e=>{const r=svg.getBoundingClientRect(),mx=view.xmin+(e.clientX-r.left)/r.width*(view.xmax-view.xmin),my=view.ymax-(e.clientY-r.top)/r.height*(view.ymax-view.ymin);zoom(.72,mx,my)});svg.addEventListener('pointerdown',e=>{if(e.target.tagName==='circle')return;svg.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY,v:{...view}};svg.classList.add('dragging')});svg.addEventListener('pointermove',e=>{if(!drag)return;const r=svg.getBoundingClientRect(),dx=(e.clientX-drag.x)/r.width*(drag.v.xmax-drag.v.xmin),dy=(e.clientY-drag.y)/r.height*(drag.v.ymax-drag.v.ymin);view={xmin:drag.v.xmin-dx,xmax:drag.v.xmax-dx,ymin:drag.v.ymin+dy,ymax:drag.v.ymax+dy};draw()});svg.addEventListener('pointerup',()=>{drag=null;svg.classList.remove('dragging')});
setInitial(DATA.xmin,DATA.xmax);updateSelectionUI();
</script>
</body>
</html>'''


def _plot_html(payload, context):
    data = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    return (
        HTML_TEMPLATE
        .replace("__THEME_CSS__", _runtime_theme_css(context))
        .replace("__DATA__", data)
    )


def _status_line(row, lower, npoints):
    exact = row.get("exact_rank")
    score = row.get("score")
    bits = [f"rigorous lower ≥ {lower}" if lower is not None else "rigorous lower unknown"]
    if exact is not None:
        bits.append(f"exact rank {exact}")
    bits.append(f"{npoints} stored exact point{'s' if npoints != 1 else ''}")
    if score is not None:
        bits.append(f"Nagao {float(score):.3f}")
    return "  ·  ".join(bits)


def render(context):
    #st.caption("Click rational points directly on the curve to build exact secant/tangent constructions over Q.")

    rows = [dict(r) for r in context.db.execute(
        """SELECT * FROM curves WHERE a_invariants_json IS NOT NULL AND TRIM(a_invariants_json)<>''
           ORDER BY COALESCE(exact_rank,descent_lower,generic_lower,-1) DESC,
           COALESCE(score,-1e99) DESC,id DESC LIMIT 5000"""
    ).fetchall()]
    if not rows:
        st.info("No stored curves with a-invariants are available yet.")
        return

    preferred = st.session_state.get("curves_selected_id") or st.session_state.get("analysis_curve_id") or st.session_state.get("target_curve_id")
    index = next((i for i, r in enumerate(rows) if preferred and int(r["id"]) == int(preferred)), 0)
    row = st.selectbox("Curve", rows, index=index, format_func=_curve_label, key="rh-ext-curve-explorer-curve")
    st.session_state["curve_explorer_curve_id"] = int(row["id"])

    try:
        row, model = B.load_curve(context.db, int(row["id"]))
        points = B.load_points(context.db, int(row["id"]), model)
    except Exception as exc:
        st.error(str(exc))
        return

    lower = B.rigorous_lower(row)
    st.caption(_status_line(row, lower, len(points)))

    xmin, xmax = B.choose_bounds(model, points, mode="Smart")
    payload = B.plot_payload(model, points, bounds=(xmin, xmax), samples=2800, pair_cache_points=96)
    st.iframe(_plot_html(payload, context), width="stretch", height=815)

    if not points:
        st.info("The real locus is available, but this curve has no exact stored rational points to overlay yet.")
        return

    with st.expander("Server exact tools", expanded=False):
        st.caption("The graph's clickable constructions are precomputed here in Python over Q. These controls are for explicit arithmetic and multiples outside the bounded click cache.")
        ids = [str(p.id) for p in points]
        by_id = {str(p.id): p for p in points}
        opts = [None] + ids
        c1, c2 = st.columns(2)
        p_id = c1.selectbox("Point P", opts, format_func=lambda x: "Select P" if x is None else _point_label(by_id[x]), key="rh-ext-curve-explorer-server-p")
        q_id = c2.selectbox("Point Q", opts, format_func=lambda x: "Select Q" if x is None else _point_label(by_id[x]), key="rh-ext-curve-explorer-server-q")
        if p_id is not None and q_id is not None:
            try:
                P, Qp = by_id[p_id], by_id[q_id]
                result = model.add(P.point, Qp.point)
                third = B.INF if result is B.INF else model.negate(result)
                if result is B.INF:
                    st.code(f"{P.label} + {Qp.label} = O", language="text")
                else:
                    st.code(
                        f"R = ({B.qstr(third[0])}, {B.qstr(third[1])})\n"
                        f"-R = {P.label} + {Qp.label} = ({B.qstr(result[0])}, {B.qstr(result[1])})",
                        language="text",
                    )
            except Exception as exc:
                st.warning(f"Exact addition could not be computed: {exc}")

        if p_id is not None:
            nmax = st.slider("Compute through nP", 1, 20, 8, key="rh-ext-curve-explorer-multiples")
            rows_out = []
            for n in range(1, nmax + 1):
                try:
                    result = model.mul(n, by_id[p_id].point)
                    rows_out.append({"n": n, "nP": "O" if result is B.INF else f"({B.qstr(result[0])}, {B.qstr(result[1])})"})
                except Exception as exc:
                    rows_out.append({"n": n, "nP": f"error: {exc}"})
                    break
            st.dataframe(rows_out, width="stretch", hide_index=True)

    with st.expander("Point ledger", expanded=False):
        st.dataframe([
            {
                "point": p.label,
                "x": B.qstr(p.x),
                "y": B.qstr(p.y),
                "role": p.role,
                "generator": p.is_generator,
                "selected subgroup": p.in_selected_subgroup,
                "exact verified": p.exact_verified,
                "rigorous independent": p.rigorous_independent,
                "independence": p.independence_status,
                "source": p.source,
            }
            for p in points
        ], width="stretch", hide_index=True)
