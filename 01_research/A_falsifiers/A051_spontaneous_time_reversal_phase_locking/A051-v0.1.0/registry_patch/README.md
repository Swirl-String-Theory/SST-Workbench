# Registry integration

These are additive candidate entries only. Do not overwrite canonical index files with these snippets.

On 2026-10-02, `family_hierarchy.json` is ahead of `catalog_index.json`: the hierarchy contains A050 and declares A051 next, while the catalog index does not yet contain A050. Re-run the repository's canonical registry/index generator after placing the family, then verify both indices and `falsifier_registry.yaml` converge on the physical tree.
