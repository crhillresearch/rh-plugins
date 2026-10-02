# Writing a Feature plugin

A Feature is a narrow contribution to a Rank Hunter surface. It does not own a route. Use it for a small UI block, a status panel, or a controlled search-command transformation.

If you need a full page, write a Workspace instead.

## Layout

```text
extensions/my_feature/
  plugin.json
  feature_ui.py
  feature.py           # optional functional hook implementation
  README.md
  tests/
```

The directory can live under `features/` or `extensions/`. The manifest decides the plugin type.

## Minimal render Feature

```json
{
  "schema_version": 1,
  "plugin_type": "feature",
  "id": "my_feature",
  "name": "My Feature",
  "version": "0.1.0",
  "description": "Adds a compact research status block.",
  "enabled_by_default": false,
  "icon": ":material/extension:",
  "entrypoint": "feature_ui.py",
  "hooks": [
    "analysis.work_center.after_header"
  ]
}
```

The entrypoint must define:

```python
import streamlit as st

def render(context):
    st.caption("Feature content")
```

Even a Feature that only uses a functional command hook should keep a valid render entrypoint, because Feature validation imports it and expects `render(context)`.

## Public render hooks

Current public hook ids are:

```text
dashboard.after_header
search.after_header
target.after_header
curves.after_header
curves.actions
candidates.after_header
points.after_header
manage.jobs.results.after_header
data.catalogs.after_header
analysis.work_center.after_header
analysis.descent.after_header
analysis.mw_geometry.after_header
analysis.quartics.after_header
analysis.independence.after_header
analysis.saturation.after_header
manage.campaigns.after_header
manage.jobs.after_header
```

Use the canonical names above for new plugins.

Compatibility aliases still accepted by current core are:

```text
results.after_header           -> manage.jobs.results.after_header
external_catalog.after_header  -> data.catalogs.after_header
analysis.analyze.after_header  -> analysis.work_center.after_header
analysis.lattices.after_header -> analysis.mw_geometry.after_header
```

Do not start new code on an alias.

### System hooks are not public extension points

`settings.after_header` and `database.after_header` are privileged compatibility hooks. A manifest cannot grant itself access. Core requires both a declared privilege and a hard-coded allowlist entry.

For third-party plugin work, treat Settings and Database insertion as unavailable.

## FeatureContextV1

Render hooks receive a `FeatureContextV1` object.

Useful fields:

```text
context.project_root
context.db_path
context.db
context.plugin_id
context.plugin_version
context.hook_id
context.payload
context.science_python
```

Helpers:

```python
value = context.setting("science_python", "")
curve_id = context.get("curve_id")
```

`payload` is read-only. The host decides what each hook receives.

Rank Hunter failure-isolates render Features: an exception in a Feature should not bring down the host page. Still, handle expected errors locally and show a useful message.

## Keep render hooks small

A render Feature lives inside somebody else's page. Do not build a second application inside that slot.

Good Feature content:

- one compact status block;
- a small action group;
- a narrow visualization;
- a context-aware helper.

Bad Feature content:

- a full dashboard;
- a second navigation system;
- a long-running search launched during render;
- page-wide CSS that changes unrelated Rank Hunter controls.

The Dashboard hook has a bounded compact-status contract. Rank Hunter may limit contributions and height there.

## Functional search-command hook

Features can also transform a command immediately before Rank Hunter enqueues a search.

Manifest:

```json
{
  "schema_version": 1,
  "plugin_type": "feature",
  "id": "my_command_feature",
  "name": "My Command Feature",
  "version": "0.1.0",
  "entrypoint": "feature_ui.py",
  "hooks": [
    {
      "name": "search_command",
      "entrypoint": "feature.py",
      "function": "on_search_command",
      "priority": 100
    }
  ]
}
```

Callback:

```python
def on_search_command(context):
    command = list(context.get("command") or [])
    family = context.get("family_plugin") or {}
    kind = context.get("kind") or ""
    metadata = context.get("metadata") or {}

    if not command:
        return None

    # Return None when this Feature does not apply.
    if family.get("id") != "my_family":
        return None

    replacement = command + ["--extra-safe-mode"]

    return {
        "command": replacement,
        "note": "extra safe mode enabled",
        "metadata": {
            "mode": "extra-safe"
        }
    }
```

The command hook context is a plain mapping, not `FeatureContextV1`. Current keys are:

```text
project_root
command
family_plugin
kind
metadata
```

`family_plugin` contains basic identity metadata when the launch belongs to a Family.

Return either:

- `None` — no change;
- a mapping containing a non-empty `command` list/tuple.

Optional `note` and `metadata` are recorded in the Feature audit trail.

Command hooks run in ascending `priority`, with plugin id as the tie-breaker. Keep transforms deterministic. A later Feature receives the command produced by earlier Features.

If a command hook fails, Rank Hunter records the error and preserves the current command instead of taking down the launch.

## A Feature is not a proof boundary

A command transform may change search geometry or scheduling, but it does not gain authority to mark a point independent, change an exact rank, or create a rigorous upper bound without the normal core validation path.

This distinction matters for Features such as symmetry reduction: removing provably duplicate search regions is valid; declaring the surviving points independent because they came from distinct regions is not.

## Streamlit keys and CSS

Prefix every widget key with the plugin id:

```python
st.checkbox("Enabled", key="my-feature-enabled")
```

Avoid global CSS. If a Feature needs local styling, scope selectors to a plugin-owned container/key.

Do not depend on Streamlit's generated Emotion class names.

## Testing

Useful tests for a render Feature:

- manifest parses and hook ids are supported;
- entrypoint exports `render`;
- render code uses stable plugin-scoped keys;
- pure helper functions are tested without Streamlit where possible.

Useful tests for a command Feature:

- unrelated commands return `None`;
- supported commands are transformed exactly once;
- transformed command preserves all required original arguments;
- plugin/family mismatch is a no-op;
- metadata/note are stable;
- repeated runs are deterministic.

Validate with:

```bash
sage -python -m rank42.plugin_validate --project-root . --db rank42.db --plugin my_feature
```
