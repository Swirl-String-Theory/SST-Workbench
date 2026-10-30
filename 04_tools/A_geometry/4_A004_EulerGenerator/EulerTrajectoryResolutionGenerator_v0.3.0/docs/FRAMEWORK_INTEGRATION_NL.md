# Framework 1.1.0 integratiegrens

De volledige byte-identieke release-runtime van A077-v0.1.2 is overgenomen uit de canonical frozen release, inclusief `_sst_runtime/instance_template` en `RUNTIME_SNAPSHOT_MANIFEST.json`. `framework_bootstrap.py` voert voor gebruik een integriteitscontrole uit over 142 bestanden. De Tool is niet ingeschreven als nieuw A-falsifier-catalogusnummer; bestaande families A075/A077 worden niet veranderd.

`FRAMEWORK_DIAGNOSTIC_GATE_LEDGER.json` gebruikt **TG0–TG5** voor lokale toolcontroles, expliciet gescheiden van G0–G10 uit geregistreerde falsifiers. Er zijn geen per-provider twee-van-drie-wetenschappelijke backendclaims. GPU/DD32 alleen op echte Intel XPU uitvoer, niet op CPU-simulatie. Het originele `instance_template` is aanwezig als bron voor eventuele formele toekomstige falsifier-instanties. Een schijn-PASS via `G10` of `CERTIFY` is verboden.

De runtime heeft wél een echte `sycl-dd32` Biot–Savart-worker met FMA/TwoSum en bronhash-gates. Hij is **niet** het numerieke FFT-Euler-veld in deze tool. Het XPU-veld draait voorlopig met complex64/fp32 en apart gecompenseerde tracers.
