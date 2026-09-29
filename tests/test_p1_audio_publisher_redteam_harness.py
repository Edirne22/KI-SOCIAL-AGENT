"""Isolated P1 Audio -> Racing-QM -> Approval -> Publisher contract harness.

No Pipecat/Postiz dependency: this tests the boundary contract before integration.
Fixtures are derived from real 2026-09-29 acceptance cases.
"""
from dataclasses import dataclass, replace
import re

@dataclass(frozen=True)
class Fixture:
    key: str
    rider: str
    source_title: str
    transcript: str
    source_id: str = "run-morning-2026-09-29"
    approved: bool = True
    target: str = "instagram:edirnelibuelent"

FIXTURES = {
    "morbidelli": Fixture(
        "morbidelli", "Franco Morbidelli",
        "Franco Morbidelli ağzından kaçırdı: 2027’de WorldSBK’ye geliyor",
        "Franco Morbidelli hat für 2027 ein starkes Signal Richtung WorldSBK gegeben.",
    ),
    "oncu": Fixture(
        "oncu", "Can Öncü",
        "Can Öncü Cremona WorldSSP",
        "Can Öncü fährt in Cremona in der WorldSSP.",
    ),
    "lecuona": Fixture(
        "lecuona", "Iker Lecuona",
        "Iker Lecuona Cremona Superpole 1:27.253",
        "Iker Lecuona fuhr in der Cremona-Superpole 1:27.253.",
    ),
    "bulega": Fixture(
        "bulega", "Nicolò Bulega",
        "Bulega Lecuona Cremona",
        "Nicolò Bulega und Iker Lecuona fahren in Cremona.",
    ),
    "agius": Fixture(
        "agius", "Senna Agius",
        "Tech3 signs Agius for MotoGP debut from 2027",
        "Agius startet ab 2027 bei Tech3 in der MotoGP.",
    ),
}

BAD_GERMAN = (
    "ein enger schnitt für den nationalen sportler",
    "wie einschätzen ihr",
    "nächsten wochenende",
    "werkswagen",
    "duble",
    "double-wochenende",
)

def audio_boundary(f: Fixture):
    errors=[]
    if not f.source_id.strip(): errors.append("provenance_missing")
    if not f.transcript.strip(): errors.append("transcript_missing")
    if any(x in f.transcript.lower() for x in BAD_GERMAN): errors.append("language_gate")
    # Audio/transcript is untrusted input. Obvious entity mismatch is fail-closed.
    rider=f.rider.casefold(); transcript=f.transcript.casefold(); surname=rider.split()[-1]\n    if rider not in transcript and not (len(surname)>=4 and re.search(r"(?<![a-zà-ž])"+re.escape(surname)+r"(?![a-zà-ž])",transcript)): errors.append("rider_mismatch")
    return not errors, errors

def approval_boundary(f: Fixture):
    errors=[]
    if not f.approved: errors.append("approval_missing")
    if not f.target.startswith(("instagram:","facebook:","tiktok:")): errors.append("target_invalid")
    return not errors, errors

def publisher_sim(f: Fixture, *, events=1, status=200, platform_results=None):
    ok, errors=approval_boundary(f)
    if not ok: return {"ok":False,"errors":errors,"posts":[]}
    if status in (401,429) or status >= 500:
        return {"ok":False,"errors":[f"provider_{status}"],"posts":[]}
    # Idempotency contract: same approval/source/target yields exactly one external publish.
    idem=f"{f.source_id}|{f.key}|{f.target}"
    posts=[idem] if events >= 1 else []
    result={"ok":True,"errors":[],"posts":posts}
    if platform_results is not None:
        failed=[p for p,s in platform_results.items() if not s]
        result["platform_results"]=platform_results
        if failed:
            result["ok"]=False
            result["errors"].append("partial_failure:"+",".join(sorted(failed)))
    return result

def claim_strength_attack_blocked(f: Fixture, generated: str):
    """Conservative simulation of the existing rule: generated text cannot upgrade a
    future/transfer source that is not explicit confirmation."""
    title=f.source_title.lower()
    future=bool(re.search(r"\b20\d{2}\b", title)) and any(x in title for x in ("worldsbk","motogp","moto2","moto3"))
    explicit=bool(re.search(r"\b(signs?|signed|confirmed|officially confirmed|announces?|will join|will race|has signed)\b", title))
    generated_definitive=any(x in generated.lower() for x in ("bestätigt","steht fest","wird 2027","startet 2027"))
    return bool(future and not explicit and generated_definitive)

def run_redteam():
    results={}
    # Positive controls
    for key in ("oncu","lecuona","bulega","agius"):
        f=FIXTURES[key]
        a,_=audio_boundary(f); p=publisher_sim(f,events=2)
        results[f"positive_{key}"]=a and p["ok"] and len(p["posts"])==1

    m=FIXTURES["morbidelli"]
    results["attack_morbidelli_certainty"]=claim_strength_attack_blocked(
        m, "Franco Morbidelli hat bestätigt, dass er 2027 in der WorldSBK startet."
    )
    results["attack_bad_german"]=not audio_boundary(replace(FIXTURES["oncu"], transcript="Ein enger Schnitt für den nationalen Sportler. Wie einschätzen ihr die Chancen?"))[0]
    results["attack_chantra_grammar"]=not audio_boundary(replace(FIXTURES["oncu"], transcript="Can Öncü fährt am nächsten Wochenende."))[0]
    results["attack_rider_swap"]=not audio_boundary(replace(FIXTURES["lecuona"], transcript="Toprak Razgatlıoğlu fuhr in Cremona 1:27.253."))[0]
    results["attack_provenance_loss"]=not audio_boundary(replace(FIXTURES["lecuona"], source_id=""))[0]
    results["attack_approval_bypass"]=not publisher_sim(replace(FIXTURES["lecuona"], approved=False))["ok"]
    results["attack_wrong_target"]=not publisher_sim(replace(FIXTURES["lecuona"], target="unknown:wrong"))["ok"]
    results["attack_retry_duplicate"]=len(publisher_sim(FIXTURES["lecuona"],events=3)["posts"])==1
    results["attack_429"]=not publisher_sim(FIXTURES["lecuona"],status=429)["ok"]
    results["attack_500"]=not publisher_sim(FIXTURES["lecuona"],status=500)["ok"]
    partial=publisher_sim(FIXTURES["lecuona"],platform_results={"instagram":True,"facebook":False})
    results["attack_partial_failure"]=(not partial["ok"] and partial["platform_results"]["instagram"] and not partial["platform_results"]["facebook"])
    return results

def main():
    r=run_redteam()
    for k,v in r.items(): print(("PASS" if v else "FAIL"), k)
    failed=[k for k,v in r.items() if not v]
    print(f"SUMMARY {len(r)-len(failed)}/{len(r)} PASS")
    if failed: raise SystemExit("FAILED: "+", ".join(failed))

if __name__=="__main__":
    main()
