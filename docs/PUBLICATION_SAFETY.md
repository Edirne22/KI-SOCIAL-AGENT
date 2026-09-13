# Veröffentlichungs-Schutz

## Ablauf

Ein freigegebener Beitrag wird nicht mehr direkt an eine Plattform gesendet:

1. Der Workflow reserviert einen **vollständigen**, freigegebenen Block mit `Publication-Claim: BEREIT` und speichert ihn in Git.
2. Derselbe Workflow markiert ihn mit einem eindeutigen Lauf-Token als `Publication-Claim: IN_BEARBEITUNG …` und speichert auch diesen Zustand in Git.
3. Nur genau dieser Workflow-Lauf darf den Block veröffentlichen.
4. Bei Erfolg ersetzt der Publisher den Header durch `[GEPOSTET … | ID: …]`.

Dadurch führt ein unbekannter Abbruch nach einem Plattform-Aufruf nicht zu einem automatischen Doppelpost.

## Sicheres Fehlerverhalten

Ein Block mit `Publication-Claim: IN_BEARBEITUNG …` wird nicht automatisch wiederholt.

- Erst auf Instagram/Facebook prüfen, ob der Beitrag dort erschienen ist.
- Wenn erschienen: den Block mit Zeitpunkt und Plattform-ID als `[GEPOSTET …]` markieren.
- Wenn nicht erschienen: Claim-Zeile entfernen; der Status `FREIGEGEBEN` bleibt erhalten. Erst dann kann ein späterer Lauf neu reservieren.

## Duplikate

Gleiche, noch unveröffentlichte Texte derselben Plattform werden nicht automatisch reserviert. Sie erscheinen in `memory/PUBLICATION_DUPLICATES.md`; Bülent entscheidet, welcher Entwurf bleibt.

## Voraussetzung

Alle Publisher verarbeiten ausschließlich Blöcke mit:

```markdown
Status: FREIGEGEBEN
```

Medien-Generatoren folgen derselben Regel. Entwürfe bleiben damit technisch von Veröffentlichung und kostenpflichtiger Medien-Erzeugung getrennt.
