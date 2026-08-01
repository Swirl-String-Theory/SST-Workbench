# Architectuurgrens

## Nu: M1

`apps/web/src/legacy/vortexlab-runtime.js` is bewust nog één classic script. Dat behoudt de globale lexical environment en uitvoeringsvolgorde van de monoliet.

## M2 extractievolgorde

1. `config/canon` en immutable constants
2. catalog loader en provenance
3. pure geometry utilities
4. reach/DCSD
5. Biot–Savart/LIA/integratie
6. benchmark registries en gates
7. rendering
8. controls/HUD
9. bootstrap/runtime composition root

Iedere stap vereist referentie-JSON-pariteit voordat de volgende stap start.

## Engine boundary

De browser praat later alleen met een `EngineClient`. De eerste externe adapter gebruikt een SSTcore CLI-proces met JSON via stdin/stdout. Pas na protocolstabilisatie volgt eventueel Node-API.
