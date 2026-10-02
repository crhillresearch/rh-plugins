"""Rank Hunter Fermigier rank-12 search adapter.  It only maps UI options to CLIs.

The runners are launched by plugin-local file path rather than by a ``plugins.*``
module path so the adapter works in both flat runtime installs and current Rank Hunter
``plugins/Families/<plugin>`` discovery layout.
"""

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent

def _native(python,db,src_flag,src_value,o):
    cmd=[str(python),str(PLUGIN_ROOT/'native_search.py'),'--db',str(db),src_flag,str(src_value)]
    for key,flag in [('limit','--limit'),('mode','--mode'),('stages','--stages'),('timeout','--timeout'),('construction_timeout','--construction-timeout'),('subgroup_scan','--subgroup-scan'),('exact_candidates','--exact-candidates'),('certificate_timeout','--certificate-timeout')]:
        if o.get(key) is not None: cmd += [flag,str(o[key])]
    if o.get('ratpoints'): cmd += ['--ratpoints',str(o['ratpoints'])]
    if o.get('force'): cmd.append('--force')
    return cmd

def _pgl2(python,db,src_flag,src_value,o):
    cmd=[str(python),str(PLUGIN_ROOT/'chart_search.py'),'--db',str(db),src_flag,str(src_value)]
    for key,flag in [('limit','--limit'),('mode','--mode'),('charts','--charts'),('chart_strategy','--chart-strategy'),('anchor_pool','--anchor-pool'),('discovered_anchor_pool','--discovered-anchor-pool'),('free_bound','--free-bound'),('stages','--stages'),('timeout','--timeout'),('construction_timeout','--construction-timeout'),('subgroup_scan','--subgroup-scan'),('exact_candidates','--exact-candidates'),('certificate_timeout','--certificate-timeout')]:
        if o.get(key) is not None: cmd += [flag,str(o[key])]
    if o.get('ratpoints'): cmd += ['--ratpoints',str(o['ratpoints'])]
    if o.get('force'): cmd.append('--force')
    return cmd

def _build(python,db,src_flag,src_value,o):
    return (_native if o.get('adapter')=='native' else _pgl2)(python,db,src_flag,src_value,o)

def build_family_search_command(*, python, db, candidate_file, options):
    return _build(python,db,'--input',candidate_file,options)

def build_target_search_command(*, python, db, curve_id, options):
    opts=dict(options); opts['limit']=1
    return _build(python,db,'--id',curve_id,opts)
