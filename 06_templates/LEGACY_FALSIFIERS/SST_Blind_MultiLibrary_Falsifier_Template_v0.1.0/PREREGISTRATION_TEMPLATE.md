# Preregistration template

Freeze this document **before inspecting scientific campaign values**.

## 1. Question and primary null
Define one falsifiable question and an explicit null. No target values may enter discovery code.

## 2. Immutable lane order
`G0 provenance -> G1 admissibility -> G2 discovery -> G3 independent confirmation -> G4 numerical certification -> G5 cross-source replication -> G6 mechanism/physics -> REVEAL`.

Every gate ends in `PASS`, `FAIL`, `UNRESOLVED`, or `NOT_RUN_PREREQUISITE`. Later scientific claims require all stated predecessors to be `PASS`.

## 3. Independence unit
Declare the primary independent unit (topology, carrier, experiment, source family, etc.). Multiple meshes, seeds, source variants, parameter scans, or GPU replicas of one unit are not independent observations.

## 4. Blind boundary
List reveal-only symbols, numerical targets, historical mappings, experimental constants and labels. Commit a SHA-256 of the private reveal file. The blind output archive must not contain the reveal file or its contents.

## 5. CPU/GPU authority
GPU may screen. CPU is the reference implementation. A GPU result cannot promote a scientific candidate unless CPU↔GPU parity passes on a preregistered sample and every finalist is CPU-certified.

## 6. Controls and multiplicity
Preregister negative controls, nuisance controls, permutation/null construction, multiple-testing correction and stopping rules.

## 7. Allowed conclusions
State exactly which combinations of gate outcomes permit `SUPPORTED`, `FALSIFIED`, or `UNRESOLVED`. Never turn a prerequisite failure into support.
