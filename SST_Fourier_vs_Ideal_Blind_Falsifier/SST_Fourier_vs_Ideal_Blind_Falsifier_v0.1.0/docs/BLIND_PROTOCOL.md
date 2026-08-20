# Blind protocol

## Separation

`prepare` may read source labels/topology solely to construct matched pairs. It writes source identity only under `private/`.

`run` reads only:

- `blind_catalog/pairs_public.csv`;
- anonymous `geometry/CAND_*.npz`;
- the numerical preset.

It does not import or open files under `private/`.

## Public candidate content

Anonymous geometry files contain only `points` and `offsets`. The public pair table contains anonymous IDs and component count. No `ideal`, `fseries`, `relaxed`, topology ID, source path, ropelength or SST particle label occurs in the blind input.

## Commitment and seal

Before dynamics, `manifest_public.json` stores SHA-256 of the private identity key. After blind scoring, `SEALED_MANIFEST.json` hashes:

- every blind result file;
- numerical config;
- the complete anonymous public catalog tree (manifest, pair table, and geometry files);
- all code/document/config/CMD files relevant to the campaign.

Reveal refuses changed blind results, changed code/config, or a private key that no longer matches the pre-run commitment.

## Non-negotiable exclusions

The blind stage does not use:

- visual quality labels;
- ropelength target values;
- SST particle identity;
- alpha or other fitted SST targets;
- artificial damping or auto-relax;
- post-hoc metric selection;
- topology-specific tuning.
