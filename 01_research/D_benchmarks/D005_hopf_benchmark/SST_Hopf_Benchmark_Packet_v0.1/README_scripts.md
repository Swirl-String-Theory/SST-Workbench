# SST Hopf Python Scripts v0.1

Dit pakket bevat één uitvoerbaar Python-script voor ieder van de acht `.md`-deelplannen uit **SST Hopf Benchmark Packet v0.1**.

## Belangrijkste statusregel

De scripts maken onderscheid tussen:

- `PASS`: de betreffende numerieke gate voldoet aan de ingevoerde criteria;
- `DEMONSTRATION`: alleen een mathematische/numerieke identity-test, geen SST-afleiding;
- `INDETERMINATE`: de vereiste SST-dynamica of externe certificatie ontbreekt;
- `FAIL`: een expliciete test of guard faalt.

De scripts sluiten H6–H10 dus niet kunstmatig met synthetische invoer.

## Bestanden

| Stap | Script | Gates |
|---|---|---|
| 1 | `01_definieer_sst_orderparameter.py` | H4 |
| 2 | `02_analytische_hopf_benchmark.py` | H0–H3 |
| 3 | `03_toroflux_spinorveld.py` | H4 |
| 4 | `04_hopf_lading_numeriek.py` | H1–H3 |
| 5 | `05_heliciteitsbridge.py` | H5 |
| 6 | `06_effectieve_spinactie.py` | H6–H8 |
| 7 | `07_vier_pi_configuratieruimte.py` | H9 |
| 8 | `08_trefoil_integratie.py` | H10 |

Gemeenschappelijke numeriek staat in `sst_hopf_common.py`. De oorspronkelijke plannen staan ongewijzigd onder `docs/`.

## Installatie

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

python -m pip install -r requirements.txt
```

## Snelle benchmarkroute

### Stap 1

```bash
python 01_definieer_sst_orderparameter.py \
  --output results/step01
```

De default is een synthetische, nergens nul orderparameter om H4-infrastructuur te testen. Voor een echte SST-kandidaat:

```bash
python 01_definieer_sst_orderparameter.py \
  --input-npz sst_fields.npz \
  --output results/step01_sst
```

`sst_fields.npz` moet `phi1` en `phi2` bevatten.

### Stap 2

```bash
python 02_analytische_hopf_benchmark.py \
  --resolutions 24 32 48 64 \
  --output results/step02
```

Voor publiceerbare convergentie zijn grotere grids nodig; `256^3` vraagt veel geheugen.

### Stap 3

```bash
python 03_toroflux_spinorveld.py \
  --m 1 --n-winding 1 \
  --profile regularized \
  --output results/step03
```

`--profile source` reproduceert de profieloriëntatie uit het plan, maar markeert voor `n != 0` terecht een as-singulariteit. De default `regularized` verwisselt de profieloriëntatie zodat de hoekafhankelijke component op de kern verdwijnt en de director buiten de buis constant wordt. Deze correctie wordt expliciet in evidence vastgelegd.

### Stap 4

Op de benchmark van stap 2:

```bash
python 04_hopf_lading_numeriek.py \
  results/step02/analytic_hopf_benchmark.npz \
  --output results/step04
```

### Stap 5

Identity-benchmark:

```bash
python 05_heliciteitsbridge.py \
  results/step02/analytic_hopf_benchmark.npz \
  --circulation 1.0 \
  --output results/step05
```

Dit geeft `DEMONSTRATION`. Voor een echte H5-test moet `--sst-fields` een NPZ met `velocity` en `vorticity` leveren.

### Stap 6

Synthetische fitdemonstratie:

```bash
python 06_effectieve_spinactie.py --output results/step06
```

Een echte H6-test gebruikt:

```bash
python 06_effectieve_spinactie.py \
  --trajectory reduced_action_trajectory.npz \
  --metadata reduction_metadata.json \
  --sector-table sector_energies.json \
  --output results/step06_sst
```

Trajectoryvelden:

```text
time, theta, phi, lagrangian_first_order
```

De metadata moet aantoonbaar uit een volledige SST-actiereductie komen. Het script behandelt een metadataflag niet als zelfstandig bewijs; de provenance blijft onderdeel van de beoordeling.

### Stap 7

```bash
python 07_vier_pi_configuratieruimte.py \
  --output results/step07
```

Dit demonstreert `SU(2) -> SO(3)`, maar H9 blijft `INDETERMINATE` zonder extern configuratieruimte-/Finkelstein–Rubinstein-certificaat.

### Stap 8

```bash
python 08_trefoil_integratie.py \
  --output results/step08
```

De standaard `T(2,3)`-curve is een bekende parametervoorstelling maar geen onafhankelijke knotcertificatie. H10 blijft daarom `INDETERMINATE` zonder upstream evidence en provenance.

## Smoke-test

```bash
python tests/run_smoke.py
```

De smoke-test gebruikt kleine grids en controleert uitvoering, bestanden en JSON. Hij is geen hoge-resolutie topologische certificatie.

## Numerieke opmerkingen

1. Finite differences op een eindig kubisch domein convergeren langzaam naar `Q_H=1`; het script rapporteert dit als convergentie-evidence.
2. De director/FFT-route veronderstelt periodieke numeriek en een nagenoeg constante director aan de grens.
3. Preimage-linking in stap 2 gebruikt analytische Hopf-vezels; willekeurige preimage-extractie uit voxeldata is nog niet inbegrepen.
4. De toroflux- en trefoilvelden zijn ansätze. Ze worden niet voorgesteld als uit de SST-actie afgeleid.
5. H9 vereist topologie van de volledige configuratieruimte, niet alleen het spinorteken na een rotatie.

## Python

Getest met Python 3.11+ en NumPy.
