# Rank Hunter Plugin Guide

Rank Hunter has three plugin shapes:

- **Family** — supplies elliptic-curve family mathematics and, optionally, family/target search commands.
- **Feature** — adds a small contribution at a core-owned hook, or transforms a search command before it launches.
- **Workspace** — adds a full Streamlit page. The manifest type is called `extension`; the UI calls these Workspaces.

All three use `plugin.json` schema version 1.

## Where plugins live

At runtime Rank Hunter scans `<rank-hunter>/plugins/`.

A plugin can be installed flat:

```text
plugins/my_plugin/plugin.json
```

or under one category directory:

```text
plugins/families/my_family/plugin.json
plugins/extensions/my_workspace/plugin.json
plugins/features/my_feature/plugin.json
```

The repository may group Features under `extensions/`; the manifest `plugin_type` decides what the plugin actually is.

## Common manifest fields

Every new plugin should declare these fields explicitly:

```json
{
  "schema_version": 1,
  "plugin_type": "family",
  "id": "my_plugin",
  "name": "My Plugin",
  "version": "0.1.0",
  "description": "One useful sentence.",
  "enabled_by_default": false,
  "icon": ":material/science:"
}
```

`plugin_type` must be `family`, `feature`, or `extension`.

The icon is optional. If present, use a Material symbol in Rank Hunter's form:

```text
:material/science:
```

Use a stable plugin id. Lowercase snake_case is the normal convention. Treat the id as persistent data: jobs, plugin state, provenance, and stored curves may refer to it.

Use normal semantic versions for `version`. Rank Hunter stores the version with provenance, so bump it whenever behavior changes in a way that matters to a saved search or result.

## Pick the right plugin type

Use a **Family** when the code answers questions such as:

- what is the curve at parameter `t`?
- how do I reduce this family modulo `p`?
- what generic sections are known?
- how should Rank Hunter search this family or one stored specialization?

Use a **Feature** when you want to add behavior to an existing Rank Hunter surface without owning a page. Features are deliberately narrow. They should not replace core pages or silently take ownership of core state.

Use a **Workspace** when the plugin needs its own page, controls, charts, tables, or research tool. A Workspace should be self-contained and should not require a new core route.

## Discovery and validation

From the Rank Hunter project root:

```bash
sage -python -m rank42.plugin_validate --project-root . --db rank42.db --plugin my_plugin
```

Validation checks the manifest and imports the plugin. Family validation also loads the family mathematics and checks the declared validation specialization. A successful validation records the plugin as ready and enabled in the selected database.

Keep plugin tests inside the plugin directory:

```text
my_plugin/
  plugin.json
  ...
  tests/
```

Run them with the same Python/Sage environment Rank Hunter uses.

## A few rules that save trouble

1. **Do not fake proof state.** Heuristics, numerical independence screens, chart novelty, and search scores are not rank certificates.
2. **Keep family mathematics in the Family plugin.** Core owns generic scheduling, persistence, validation, and common arithmetic.
3. **Do not depend on generated Streamlit CSS class names.** Workspaces should use Rank Hunter's semantic theme tokens.
4. **Do not write a Feature for a whole page.** That is a Workspace.
5. **Do not write a Workspace to patch a Family search.** Put the search logic in the Family adapter or a narrow Feature hook.
6. **Expect plugins to be disabled.** A plugin must not be required for Rank Hunter to boot.
7. **Use unique Streamlit keys.** Prefix them with the plugin id.
8. **Keep provenance with the code.** Papers, formulas, claim boundaries, and external sources belong in the manifest or plugin README.

## Guides

- [Writing a Family plugin](FAMILY_PLUGINS.md)
- [Writing a Feature plugin](FEATURE_PLUGINS.md)
- [Writing a Workspace plugin](WORKSPACE_PLUGINS.md)
