# Writing a Workspace plugin

The UI calls these **Workspaces**. The manifest type is still `extension`.

A Workspace owns a full Streamlit page registered in Rank Hunter navigation. Use it for an interactive research tool, visualization, comparison page, explorer, or other self-contained surface.

## Layout

```text
extensions/my_workspace/
  plugin.json
  extension.py
  backend.py            # optional; useful for keeping UI thin
  README.md
  tests/
```

## Minimal manifest

```json
{
  "schema_version": 1,
  "plugin_type": "extension",
  "id": "my_workspace",
  "name": "My Workspace",
  "version": "0.1.0",
  "description": "Interactive workspace for ...",
  "enabled_by_default": false,
  "icon": ":material/insights:",
  "menu": {
    "id": "my_workspace",
    "label": "My Workspace",
    "icon": ":material/insights:"
  },
  "entrypoint": "extension.py"
}
```

The entrypoint must define:

```python
def render(context):
    ...
```

Rank Hunter owns the application-level page header. New Workspaces should render the body, not add a duplicate top-level `st.title()`.

## Navigation

There is one public navigation section for Workspace plugins: **Workspaces**.

Rank Hunter creates that sidebar section only when at least one Workspace is enabled. If no Workspace is enabled, the **Workspaces** section is not shown at all.

Every enabled Workspace page is listed under **Workspaces**. A Workspace does not choose between Search, Data, Analysis, Manage, or Plugins. Those are core navigation areas.

The current manifest loader still accepts the older `menu.section` field for compatibility with existing plugins. It does **not** control where a Workspace appears in the sidebar. New Workspace plugins should simply omit `section`.

A Workspace can register more than one page by making `menu` a list:

```json
"menu": [
  {
    "id": "overview",
    "label": "My Overview",
    "entrypoint": "overview.py",
    "icon": ":material/insights:"
  },
  {
    "id": "compare",
    "label": "My Compare Tool",
    "entrypoint": "compare.py",
    "icon": ":material/compare_arrows:"
  }
]
```

Each enabled page appears in the **Workspaces** sidebar section. Each page id must be unique inside the plugin. Page-level `entrypoint` overrides the top-level entrypoint.

## ExtensionContextV1

`render(context)` receives an `ExtensionContextV1` object.

Fields:

```text
context.project_root
context.db_path
context.db
context.plugin_id
context.plugin_version
context.page_id
context.page_label
context.science_python
```

Settings helper:

```python
ratpoints = context.setting("ratpoints_cpu", "")
```

`context.db` is Rank Hunter's live database connection. It is fine for a Workspace to query it. Be cautious with writes: direct writes couple the plugin to internal schema and bypass the normal scientific evidence boundaries. Prefer core-owned actions and APIs when changing Rank Hunter state.

## Basic workspace example

```python
import streamlit as st

def render(context):
    rows = context.db.execute(
        """
        SELECT id, family, parameter,
               COALESCE(exact_rank, descent_lower, generic_lower, 0) AS lower
        FROM curves
        ORDER BY lower DESC, id DESC
        LIMIT 200
        """
    ).fetchall()

    st.caption(f"{len(rows)} curves")
    st.dataframe(
        [dict(row) for row in rows],
        hide_index=True,
        width="stretch",
    )
```

Keep expensive work out of the render path. A page reruns often. Database queries should be bounded and indexed; searches and long arithmetic belong in Jobs/Pipeline or a dedicated worker.

## Theme support

A Workspace must work in both Light and Dark appearance.

Use Rank Hunter's semantic CSS tokens instead of a fixed dark palette. Common tokens include:

```text
--rh-bg
--rh-card
--rh-card-2
--rh-border
--rh-border-strong
--rh-control-border
--rh-text
--rh-text-secondary
--rh-muted
--rh-muted-2
--rh-primary
--rh-surface-active
```

Example:

```python
st.markdown(
    """
    <style>
    div[class*="st-key-my-workspace-"] {
        color: var(--rh-text);
    }

    .my-workspace-card {
        background: var(--rh-card);
        color: var(--rh-text);
        border: 1px solid var(--rh-border);
        border-radius: 14px;
        padding: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
```

Scope custom CSS to your Workspace. Do not override the whole application.

Do not depend on generated Streamlit/Emotion class names or DOM child positions. Semantic `rh-*` tokens and plugin-owned selectors are the stable contract.

For native Streamlit inputs, prefer the normal widgets first. Add CSS only when a custom surface genuinely needs it.

## Widget keys

Every interactive widget should have a stable plugin-prefixed key:

```python
st.selectbox(
    "Curve",
    options,
    key="my-workspace-curve",
)
```

Duplicate Streamlit keys crash the page. Do not derive two different widgets from the same key template in one render.

## Local modules

Workspace entrypoints are loaded as standalone modules. Avoid generic sibling imports that can collide with another plugin's module name.

A safe pattern for a local backend is:

```python
from pathlib import Path
import importlib.util
import sys

HERE = Path(__file__).resolve().parent

def _load_backend():
    name = "rank42_extension_my_workspace_backend"
    module = sys.modules.get(name)
    if module is not None:
        return module

    path = HERE / "backend.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

B = _load_backend()
```

This prevents a generic name such as `backend` or `engine` from colliding with another loaded Workspace.

## Iframes and custom HTML

Custom HTML/JS is fine when Streamlit cannot provide the interaction you need. Keep the boundary clean:

- generate data in Python;
- serialize only the data the page needs;
- escape user/database text before inserting it into HTML;
- keep exact mathematical values as strings when JavaScript number precision is not enough;
- use semantic Rank Hunter theme values for colors;
- do not let browser-only arithmetic silently become scientific evidence.

If the browser performs an exact visualization calculation, treat it as presentation unless core separately validates and stores the result.

## Error handling

Rank Hunter catches Workspace render exceptions and shows an error block instead of crashing the whole app. That is a last line of defense, not the normal UX.

Handle expected errors close to the control that caused them:

```python
try:
    data = load_something()
except ValueError as exc:
    st.error(str(exc))
    return
```

## Keep the page self-contained

A Workspace may read shared Rank Hunter state, but it should not require edits to unrelated pages just to function.

If the page needs new core behavior, ask whether the behavior really belongs in:

- a Family adapter;
- a Feature hook;
- a reusable core API.

Do not monkey-patch Rank Hunter modules from the Workspace.

## Testing

At minimum test:

- manifest id, type, version, menu, and entrypoint;
- enabled Workspace pages appear under the single **Workspaces** navigation section;
- disabling the last Workspace removes the **Workspaces** section from the sidebar;
- `render(context)` exists;
- all local module paths resolve;
- unique/stable widget-key prefixes;
- Light/Dark theme contract uses semantic tokens;
- no fixed-color regression if the Workspace has custom HTML/CSS;
- backend pure functions separately from Streamlit;
- empty database state;
- malformed/missing source data;
- one realistic populated state.

Validate with:

```bash
sage -python -m rank42.plugin_validate --project-root . --db rank42.db --plugin my_workspace
```

## Reference examples in this repository

The RELEASE branch currently contains useful examples:

- `extensions/curve_explorer` — interactive curve visualization, iframe/JavaScript, exact rational construction display, theme-aware custom rendering.
- `extensions/leaderboard_compare` — database-backed comparison UI with scoped Light/Dark styling and filters.
- `extensions/symmetry_reducer` — a Feature rather than a Workspace, but useful for the local-module loading pattern and plugin-scoped tooling.

Copy structure, not assumptions. A plugin should only depend on the parts of the host API it actually needs.
