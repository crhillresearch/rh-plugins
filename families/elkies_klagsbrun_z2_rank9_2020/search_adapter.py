from __future__ import annotations


def build_family_search_command(*, python, db, candidate_file, options):
    cmd = [
        str(python), '-m', 'rank42.auto_analyze',
        '--db', str(db),
        '--input', str(candidate_file),
        '--family', str(options['family_spec']),
        '--limit', str(int(options.get('limit', 20))),
        '--quick-timeout', str(int(options.get('quick_timeout', 120))),
        '--strong-timeout', str(int(options.get('strong_timeout', 600))),
        '--quick-strategy', str(options.get('quick_strategy', 'pari')),
        '--generic-certificate-timeout', str(int(options.get('generic_certificate_timeout', 120))),
        '--strong-certificate-timeout', str(int(options.get('strong_certificate_timeout', 120))),
    ]
    if options.get('fast_screen'):
        cmd.append('--fast-screen')
    if options.get('quick_only'):
        cmd.append('--quick-only')
    if options.get('strong_on_timeout'):
        cmd.append('--strong-on-timeout')
    return cmd


def build_target_search_command(*, python, db, curve_id, options):
    cmd = [
        str(python), '-m', 'rank42.fixed_curve_search',
        '--db', str(db),
        '--curve-id', str(int(curve_id)),
        '--stages', str(options.get('stages', '1000,10000,100000')),
        '--timeout', str(int(options.get('timeout', 20))),
        '--exact-candidates', str(int(options.get('exact_candidates', 8))),
        '--certificate-timeout', str(int(options.get('certificate_timeout', 120))),
    ]
    if options.get('ratpoints'):
        cmd += ['--ratpoints', str(options['ratpoints'])]
    return cmd
