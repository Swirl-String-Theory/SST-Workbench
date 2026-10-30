# A075-v0.2.8 — uitvoeren met Framework v1.1.0

De nieuwe versie staat naast v0.2.4 en gebruikt een **eigen complete, gehashte Framework v1.1.0-runtime**. Er wordt niet teruggevallen op een oudere frameworkmap of een globale installatie.

1. Activeer de reeds werkende `.venv-a075-xpu` en installeer de bijgevoegde `requirements.txt`.
2. Voer `python -m pytest -q tests`, `python tools\preflight_contract.py`, `run_all.cmd BACKEND_PREFLIGHT` en `run_all.cmd GPU_PROBE` uit.
3. Voer `python tools\prepare_private.py` uit voor nieuwe private commits; kopieer geen oude private bestanden.
4. Voer vervolgens `run_all.cmd FREEZE`, `run_all.cmd BASIC --grid 80 --grid-up 112 --threads 12 --allow-expensive` uit.
5. Start `FULL` pas na beoordeling van BASIC en het rekenplan (`--plan`).

De regel uit Framework v1.1.0 vereist minimaal **2 van 3 werkelijk uitgevoerde** wetenschappelijke implementaties. Geen successtatus op basis van een deviceprobe. PyTorch XPU gebruikt op Arc A770 float32: dit is diagnostisch, geen IEEE float64-pariteit. C++ is een hybride kernel en is geen volledig onafhankelijke Fourieroplosser. Domeinonafhankelijkheid blijft optioneel via `--domain-study`; `--boundary free-space` wordt correct geweigerd.

Na de frameworkrun: bekijk `AUTO_BACKEND_MATRIX.json`, de energiematrices per stap, de gate-ledger en het PDF-rapport. De fysische conclusie blijft UNRESOLVED totdat bronvertrek, vele onafhankelijke klokcycli, tijd-, ruimte-, finite-core- en domeinconvergentie sluitend zijn vastgesteld.
