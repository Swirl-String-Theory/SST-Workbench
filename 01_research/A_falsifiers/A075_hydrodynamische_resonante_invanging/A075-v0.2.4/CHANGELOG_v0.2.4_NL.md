# A075-v0.2.4 — GPU-probe / domeinonafhankelijkheid

- GPU_PROBE stageert gecontroleerd `instance_template/native/cpp/sycl_worker.cpp` naar de instance-lokale `native/cpp/sycl_worker.cpp`, waarna de onveranderde framework-API `probe_worker(instance_root)` gebruikt wordt. **Er wordt niets gewijzigd in Framework v1.0.10.**
- Het echte device-type wordt in de diagnostiek vastgelegd; een Biot–Savart-SYCL-deviceprobe wordt nooit gelijkgesteld aan een volledige A075 Euler-GPU-run.
- Nieuwe `--domain-study` en `--domain-study-only` opties, plus `--domains 10:80,15:120,20:160`.
- Physicale `dx`, `core`, `dt`-cap en fysieke eindtijd blijven gelijk over boxgroottes. Resultatenmatrix met late lokale energie-observabele, fluxresidu, energiebehoud en vorticiteitsinhoud aan periodieke randen.
- `--boundary free-space` is expres fail-closed: dit pakket bevat nog géén fysisch correcte open-rand-Euler-provider. Een grotere periodieke doos is alleen een eindige-box-convergentietest.
- Blinde/preregistratie en gates blijven **UNRESOLVED** totdat daadwerkelijke domein-, kern-, klok- en fluxchecks zijn geslaagd. Bestaande bevroren versies worden niet aangepast.
