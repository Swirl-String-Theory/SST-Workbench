# SSTcore ↔ Node-route

## Aanbevolen volgorde

1. Maak SSTcore-functies zuiver en deel Python-bindings en CLI dezelfde C++ core.
2. Definieer versieerbare JSON/binaire request/response-contracten.
3. Bouw eerst een `sstcore` CLI/daemon-adapter voor Node-procesisolatie.
4. Voeg pas daarna een Node-API-addon toe voor bewezen hotspots.

## Niet doen

- Pythonfuncties handmatig één voor één herschrijven in TypeScript.
- De Pythoninterpreter direct in de frontend embedden.
- Verschillende formules onderhouden in Python, JavaScript en C++.

De canonical implementation hoort één gedeelde core te zijn; Python en Node zijn adapters.
