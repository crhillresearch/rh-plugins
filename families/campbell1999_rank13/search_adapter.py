"""Campbell 1999 search adapter. No Sage work runs in the Rank Hunter UI process."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
NATIVE = HERE / "campbell_quartic_search.py"
PGL2 = HERE / "campbell_chart_search.py"


def search_options(context="family"):
    target = str(context) == "target"
    return [
        {"key":"adapter","type":"choice","label":"Search adapter","default":"pgl2" if target else "native","choices":["native","pgl2"]},
        {"key":"limit","type":"int","label":"Candidates","default":20,"min":1,"max":5000},
        {"key":"mode","type":"choice","label":"ratpoints x mode","default":"both" if target else "integer","choices":["integer","both","rational"]},
        {"key":"charts","type":"int","label":"PGL2 charts","default":24 if target else 12,"min":1,"max":256},
        {"key":"chart_strategy","type":"choice","label":"Chart strategy","default":"hybrid","choices":["base","subgroup","free","hybrid"]},
        {"key":"anchor_pool","type":"int","label":"Base anchor pool","default":13,"min":3,"max":64},
        {"key":"discovered_anchor_pool","type":"int","label":"Discovered anchor pool","default":20 if target else 12,"min":0,"max":128},
        {"key":"free_bound","type":"int","label":"Free PGL2 entry bound","default":3,"min":1,"max":20},
        {"key":"stages","type":"str","label":"ratpoints height stages","default":"1000,10000,100000" if not target else "1000,10000,100000,1000000"},
        {"key":"timeout","type":"int","label":"Seconds per stage","default":15 if not target else 30,"min":1,"max":3600},
        {"key":"construction_timeout","type":"int","label":"Exact construction timeout","default":120,"min":10,"max":7200},
        {"key":"subgroup_scan","type":"int","label":"Subgroup novelty scan","default":128 if not target else 512,"min":0,"max":10000},
        {"key":"exact_candidates","type":"int","label":"Exact candidates","default":8 if not target else 16,"min":0,"max":256},
        {"key":"certificate_timeout","type":"int","label":"Exact certificate timeout","default":90 if not target else 180,"min":1,"max":7200},
        {"key":"include_known_fibers","type":"bool","label":"Include exact involution controls","default":False},
    ]


def _base(script, *, python, db, src_flag, src_value, options):
    branch=str(options.get('plugin_variant') or 'c1').lower()
    cmd=[str(python),str(script),'--branch',branch,'--db',str(db),src_flag,str(src_value)]
    mapping=[
        ('limit','--limit'),('mode','--mode'),('stages','--stages'),('timeout','--timeout'),
        ('construction_timeout','--construction-timeout'),('subgroup_scan','--subgroup-scan'),
        ('exact_candidates','--exact-candidates'),('certificate_timeout','--certificate-timeout'),
    ]
    if script == PGL2:
        mapping += [
            ('charts','--charts'),('chart_strategy','--chart-strategy'),('anchor_pool','--anchor-pool'),
            ('discovered_anchor_pool','--discovered-anchor-pool'),('free_bound','--free-bound'),
        ]
    for key,flag in mapping:
        if options.get(key) is not None:
            cmd += [flag,str(options[key])]
    if options.get('ratpoints'):
        cmd += ['--ratpoints',str(options['ratpoints'])]
    if options.get('include_known_fibers'):
        cmd.append('--include-known-fibers')
    if options.get('force'):
        cmd.append('--force')
    return cmd


def _build(*, python, db, src_flag, src_value, options):
    script = NATIVE if options.get('adapter') == 'native' else PGL2
    return _base(script,python=python,db=db,src_flag=src_flag,src_value=src_value,options=options)


def build_family_search_command(*, python, db, candidate_file, options):
    return _build(python=python,db=db,src_flag='--input',src_value=candidate_file,options=options)


def build_target_search_command(*, python, db, curve_id, options):
    opts=dict(options); opts['limit']=1
    return _build(python=python,db=db,src_flag='--id',src_value=curve_id,options=opts)
