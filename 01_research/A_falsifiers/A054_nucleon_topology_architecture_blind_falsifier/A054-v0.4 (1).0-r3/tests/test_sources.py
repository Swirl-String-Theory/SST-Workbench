import json
from pathlib import Path
from experiment.source_loader import load_manifest_cases
ROOT=Path(__file__).resolve().parents[1]
def test_discovery_72(): assert len(load_manifest_cases(ROOT,'data/discovery/DISCOVERY_MANIFEST.json','data/discovery'))==72
def test_confirmation_7(): assert len(load_manifest_cases(ROOT,'data/confirmation/CONFIRMATION_MANIFEST.json','data/confirmation'))==7
