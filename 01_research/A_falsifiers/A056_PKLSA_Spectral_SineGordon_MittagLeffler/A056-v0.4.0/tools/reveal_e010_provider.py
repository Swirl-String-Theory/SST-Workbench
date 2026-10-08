from pathlib import Path
import argparse, json, hashlib, shutil


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _framework_reveal_verified(out: Path) -> tuple[bool, str]:
    decision_p = out / "REVEAL_DECISION.json"
    summary_p = out / "RUN_SUMMARY_REVEALED.json"
    verify_p = out / "REVEAL_VERIFICATION.json"
    if not decision_p.exists():
        return False, "REVEAL_DECISION.json is absent"
    decision = json.loads(decision_p.read_text(encoding="utf-8"))
    if decision.get("performed") is not True:
        return False, f"framework reveal was not performed: {decision.get('reason', 'unspecified')}"
    if not summary_p.exists() or not verify_p.exists():
        return False, "canonical framework revealed summary/verification is absent"
    verification = json.loads(verify_p.read_text(encoding="utf-8"))
    if verification.get("reveal_ok") is not True or verification.get("blind_terms_ok") is not True:
        return False, "canonical framework reveal commitment verification is not PASS"
    return True, "canonical framework reveal verified"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--require-framework-revealed", action="store_true")
    a = ap.parse_args()
    inp = Path(a.input_dir)
    out = Path(a.output_dir)
    if a.require_framework_revealed:
        ok, reason = _framework_reveal_verified(out)
        if not ok:
            print(json.dumps({"status": "SKIP", "reason": reason}, indent=2))
            return 0

    priv = inp.parent / "private" / (inp.name + "_reveal")
    reveal = json.loads((priv / "provider_reveal.json").read_text(encoding="utf-8"))
    nonce = (priv / "NONCE.bin").read_bytes()
    actual = hashlib.sha256(nonce + canon(reveal)).hexdigest()
    expected = json.loads((inp / "PROVIDER_REVEAL_COMMITMENT.json").read_text(encoding="utf-8"))["sha256"]
    if actual != expected:
        raise SystemExit("provider reveal commitment mismatch")
    rd = out / "revealed"
    rd.mkdir(parents=True, exist_ok=True)
    shutil.copy2(priv / "provider_reveal.json", rd / "A056_PROVIDER_REVEAL.json")
    (rd / "A056_PROVIDER_REVEAL_VERIFICATION.json").write_text(
        json.dumps({"schema": "A056-PROVIDER-REVEAL-VERIFICATION-1", "pass": True, "expected": expected, "actual": actual}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "cases": len(reveal.get("cases", [])), "commitment": actual}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
