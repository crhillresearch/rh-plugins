# Writing a Family plugin

A Family plugin owns family-specific mathematics. At minimum it tells Rank Hunter how to construct a specialization over `Q` and how to evaluate the same family over finite fields. Most useful Family plugins also expose search options and commands.

## Minimal layout

A small module-backed Family usually looks like this:

```text
families/my_family/
  plugin.json
  family.py
  search_adapter.py        # optional unless search capabilities need it
  README.md
  tests/
```

A data-only formula family can use `family.json` instead of `family.py`.

## Minimal manifest

```json
{
  "schema_version": 1,
  "plugin_type": "family",
  "id": "my_family",
  "name": "My Family",
  "version": "0.1.0",
  "description": "One-parameter elliptic family used for rank searches.",
  "enabled_by_default": false,
  "family": {
    "kind": "module",
    "spec": "my_family",
    "file": "family.py"
  },
  "validation_parameter": "1"
}
```

`validation_parameter` should be a rational specialization where the curve is defined and nonsingular.

## Family source contract

Rank Hunter requires these callables from a loaded family:

```python
def name():
    return "My Family"

def curve(t):
    # Return a Sage EllipticCurve over QQ, or None at a pole/singular fibre.
    ...

def curve_mod_p(r, p):
    # Return the corresponding Sage EllipticCurve over GF(p), or None
    # when this specialization is not valid modulo p.
    ...
```

If your family supplies generic sections, also provide:

```python
def generic_section_points(t):
    # Return exact Sage points on curve(t).
    return [...]
```

Keep these exact. If a section is only numerically plausible, do not return it as a generic section.

### JSON formula families

For a straightforward Weierstrass family, Rank Hunter can load the mathematics from JSON:

```json
{
  "name": "Example family",
  "generic_rank": 2,
  "parameter": "t",
  "a_invariants": [
    "0",
    "0",
    "0",
    "t^2 + 1",
    "t"
  ],
  "sections": [
    {"x": "0", "y": "t"}
  ]
}
```

Then point the manifest at it:

```json
"family": {
  "kind": "json",
  "file": "family.json"
}
```

The five `a_invariants` expressions and section coordinates are evaluated as trusted local Sage expressions. Rational functions are allowed. Poles and singular fibres are treated as undefined specializations.

For more complicated constructions, use a Python module.

## Capabilities

A Family may declare any of these current capabilities:

```text
candidate_generation
family_search
target_search
known_subgroup
quartic_search
pgl2_search
free_search
pipeline_transform
constructive_family
```

Only declare what the plugin really supports.

If you declare `family_search` or `target_search`, provide `search_adapter`.

If you declare charts, `pgl2_search` is required.

Example:

```json
{
  "search_adapter": "search_adapter.py",
  "capabilities": [
    "candidate_generation",
    "family_search",
    "target_search",
    "known_subgroup"
  ]
}
```

## Search adapter

The adapter translates Rank Hunter controls into an executable command. The command is launched by core; the plugin should not start long-running work during page rendering.

Existing module-style adapters are supported. New code can also export a `FamilyAdapterV1` instance.

### Runtime command signatures

The current Family-search host calls:

```python
def build_family_search_command(*, python, db, candidate_file, options):
    return [
        str(python),
        "my_worker.py",
        "--db", str(db),
        "--input", str(candidate_file),
    ]
```

The current Target-search host calls:

```python
def build_target_search_command(*, python, db, curve_id, options):
    return [
        str(python),
        "my_target_worker.py",
        "--db", str(db),
        "--curve-id", str(curve_id),
    ]
```

Return a command as a list/tuple of arguments. Do not return a shell command string.

Rank Hunter runs Family and Target geometry work against a temporary database copy and validates what is allowed back into live scientific state. Code that assumes direct writes to the live database will not behave the way you expect.

### Search options

A plugin can describe controls in `plugin.json`:

```json
"search_options": {
  "family": [
    {
      "key": "timeout",
      "type": "int",
      "label": "Seconds per stage",
      "default": 30,
      "min": 1,
      "max": 3600,
      "help": "Hard runtime budget for one search stage."
    },
    {
      "key": "mode",
      "type": "choice",
      "label": "Search mode",
      "default": "both",
      "choices": ["integer", "both", "rational"]
    },
    {
      "key": "use_extra_charts",
      "type": "bool",
      "label": "Use extra charts",
      "default": true
    }
  ],
  "target": []
}
```

Supported option types are:

```text
int
bool
choice
str
```

Supported presentation fields include:

```text
key, type, label, default, min, max, choices, help,
group, group_help, group_columns, group_expanded
```

Do not declare core orchestration keys such as `limit` or `target_lower` as plugin-owned search options.

The same schema may instead come from the adapter's `search_options(...)` method. Manifest options take precedence when present.

### Presets

Use `search_presets` for named profiles:

```json
"search_presets": [
  {
    "id": "scan",
    "label": "Scan",
    "description": "Routine search.",
    "candidate": {
      "a_min": -1000,
      "a_max": 1000,
      "b_min": 1,
      "b_max": 100,
      "engine": "sieve",
      "stage_bounds": "500,2000",
      "stage_keeps": "5000,500",
      "top": 500
    },
    "family": {
      "timeout": 30,
      "mode": "both"
    },
    "target": {
      "timeout": 60,
      "mode": "rational"
    }
  }
]
```

A preset may contain any useful combination of `candidate`, `family`, and `target`.

Current candidate preset keys are:

```text
a_min, a_max, b_min, b_max, stage_bounds, stage_keeps,
top, engine, sample_count, sample_seed
```

Candidate engines currently accepted by the manifest validator are `sieve`, `scalar`, and `sampled`.

## Variants

One plugin can own several related families:

```json
{
  "default_variant": "odd",
  "variants": [
    {
      "id": "odd",
      "name": "Odd family",
      "validation_parameter": "3",
      "family": {
        "kind": "module",
        "spec": "my_family_odd",
        "file": "odd_family.py"
      }
    },
    {
      "id": "even",
      "name": "Even family",
      "validation_parameter": "5/2",
      "family": {
        "kind": "module",
        "spec": "my_family_even",
        "file": "even_family.py"
      }
    }
  ]
}
```

Every variant needs `id`, `name`, and `family`. Variant metadata can override family-level rank, torsion, presets, options, and validation metadata.

If there is no `variants` list, Rank Hunter creates a single synthetic `default` variant.

## Generic-rank claims

Treat published, reconstructed, and verified claims separately.

Current claim states are:

```text
historical_record
reconstructed_model
sections_verified
generic_lower_bound_verified
exact_constant_curve_control
```

A legacy `verified_exact` state is still accepted for old manifests, but do not use it for new work.

For a published claim that Rank Hunter has not independently verified:

```json
{
  "historical_generic_rank_lower": 11,
  "generic_rank_claim_state": "historical_record"
}
```

For an operational verified generic lower bound:

```json
{
  "verified_generic_rank_lower": 2,
  "generic_rank_claim_state": "generic_lower_bound_verified"
}
```

If you declare `verified_generic_rank_lower`, the family source must provide:

```python
def validate_generic_rank_claim():
    return {
        "verified": True,
        "lower_bound": 2,
        # include useful certificate/provenance fields
    }
```

The validator requires the returned lower bound to be at least the manifest value.

`generic_rank` remains accepted for older plugins, but new plugins should not use it as a shortcut around claim state.

## Torsion metadata

A Family or variant can declare exact rational torsion targets:

```json
{
  "torsion_groups": ["C2 × C4"],
  "torsion_provider_role": "canonical_universal"
}
```

Current provider roles are:

```text
canonical_universal
prescribed_subfamily
general
```

A provider role requires `torsion_groups`.

During validation Rank Hunter computes the exact torsion group at the validation specialization and checks that it matches the declaration.

For record-hunt families, optional `torsion_record` metadata can include:

```json
{
  "rank_lower": 9,
  "goal_rank": 10,
  "source": {
    "name": "Reference name",
    "url": "https://example.org"
  },
  "secondary_family_search_recommended": false
}
```

## PGL2 charts

Advanced Family plugins may publish exact chart metadata:

```json
"charts": [
  {
    "id": "native",
    "label": "Native chart",
    "variant": "default",
    "native_variant": "default",
    "matrix": ["1", "0", "0", "1"],
    "candidate_defaults": {},
    "symmetry_matrices": []
  }
],
"default_chart": "native"
```

Each matrix is exact `[A,B,C,D]` for the Möbius map. Rank Hunter rejects singular matrices and validates referenced variants. Declaring charts requires `pgl2_search`.

## Plugin-owned corpora

A Family can declare read-only research corpora:

```json
"corpora": [
  {
    "id": "published_curves",
    "name": "Published curves",
    "cache_file": "published_curves.db",
    "builder": "build_corpus.py",
    "description": "Local searchable copy of the published corpus.",
    "variant_family_keys": {
      "default": "my_family"
    }
  }
]
```

`cache_file` must be a plain filename. The optional builder lives inside the plugin. Core owns discovery/read-only access; the plugin owns how the corpus is built and how variants map to family keys.

## Returning exact geometry results

A modern worker can emit a typed result instead of relying only on sandbox database writes.

Rank Hunter sets:

```text
RANK42_PLUGIN_GEOMETRY_RESULT_PATH
```

If your worker writes JSON there, the current schema is:

```json
{
  "schema": "rank42.plugin_geometry_result.v1",
  "status": "completed",
  "engine": "my-engine",
  "engine_version": "1.0",
  "algorithm": "exact mapped point search",
  "points": [
    ["1/2", "3/4"]
  ],
  "rigorous_upper_certificate": null,
  "artifacts": [],
  "metadata": {}
}
```

Allowed statuses are `completed`, `partial`, and `inconclusive`.

Point coordinates are strings and are checked by core before promotion. A plugin does not get to promote rank merely by putting a number in its result file.

## Pipeline research hooks

Family adapters may optionally provide these advanced hooks:

```text
derive_pipeline_coverings
derive_pipeline_transform
run_pipeline_higher_descent
run_pipeline_padic_covering_search
```

These are capability-discovered by the Pipeline. Do not invent lookalike results: each hook has a core-owned exact/typed contract and is treated as unsupported when absent.

Use these only when the family genuinely has family-specific mathematics that core cannot derive generically.

## Provenance

Put the source of the family in the manifest:

```json
"provenance": {
  "author": "Author Name",
  "paper": "Paper title",
  "journal": "Journal details",
  "claim_boundary": "What is proved, what is only used as search guidance."
}
```

The most useful provenance sentence is usually the claim boundary. Say exactly what the plugin may treat as evidence.

## Validation checklist

Before shipping a Family plugin:

- `plugin.json` loads.
- The validation specialization is nonsingular.
- `curve(t)` and `curve_mod_p(r,p)` agree with the same family.
- Every declared generic section is exactly on the specialized curve.
- Verified generic rank metadata has a real validator/certificate.
- Declared torsion matches the exact validation specialization.
- Search options validate for every variant.
- Every preset only uses declared/host-owned fields.
- Search commands return argument lists, not shell strings.
- Family and target workers tolerate a temporary database path.
- Heuristic screens never write rigorous rank evidence.
- Tests include at least one known specialization and one failure/singular case.

Run:

```bash
sage -python -m rank42.plugin_validate --project-root . --db rank42.db --plugin my_family
```
