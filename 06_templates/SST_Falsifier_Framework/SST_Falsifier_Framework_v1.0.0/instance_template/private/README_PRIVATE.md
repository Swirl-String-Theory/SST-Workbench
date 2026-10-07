# PRIVATE — never include in blind package

`new_falsifier.py` creates:

- `OPAQUE_ID_KEY.bin` — HMAC-SHA256 secret for opaque discovery IDs.
- `REVEAL_NONCE.bin` — random nonce for reveal commitment.

Place reveal mappings/targets here only. Do not commit this directory to public/blind archives.

- `reveal.json` — exact private mappings/targets committed at FREEZE and disclosed only in REVEAL.
- `blind_forbidden_terms.txt` — private lexical contamination scan list, committed at FREEZE.
