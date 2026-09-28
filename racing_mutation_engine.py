"""Deterministic Racing mutation engine for adversarial tests. Test-only: never used in production generation."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Mutation:
    id: str
    kind: str
    needle: str
    replacement: str

DEFAULT_MUTATIONS=(
 Mutation("session-superpole-race","session","Superpole Race","Superpole"),
 Mutation("place-barcelona","place","Cremona","Barcelona"),
 Mutation("team-phoenix","team","Ducati","Phoenix-Werksteam"),
 Mutation("number-gap","number","0,365","9,999"),
 Mutation("series-motogp","series","WorldSSP","MotoGP"),
 Mutation("language-renne","language","vor dem Rennen","vor dem Renne"),
)

def apply_mutation(text, mutation):
    if mutation.needle not in text:
        raise ValueError("mutation needle missing: "+mutation.id)
    return text.replace(mutation.needle,mutation.replacement,1)
