# Türkische Namen: Aussprache und Identitätsabgleich

Status: Konzept und Testanforderung; keine Änderung an produktiver ASR.

- Offizielle Personennamen, Schreibvarianten, regionale Aussprachen und Spitznamen getrennt speichern.
- Beispiele wie Ahmet/Ahmed oder Mehmet/Memo sind **keine** allgemeingültigen Identitätsgleichsetzungen. Memo ist eine mögliche Kurzform, aber kein Beweis für Mehmet.
- Türkische Zeichen (ı/i/İ/I, ğ, ş, ç, ö, ü) und Unicode-Normalisierung erhalten. Akzent- oder ASCII-Vergleich ausschließlich zur Kandidatensuche; offizielle Schreibweise nicht überschreiben.
- Aussprachevarianten aus unterschiedlichen Regionen als mögliche Erkennungshinweise führen, ohne Menschen anhand der Region zu klassifizieren oder eine feste regionale Aussprache zu unterstellen.
- Automatischer Identitätsabgleich erfordert zusätzliche Merkmale: Nachname, datierte Rennklasse, Team und belegte Quelle. Bei Mehrdeutigkeit keine automatische Zuordnung.
- Transkript muss das tatsächlich Gesagte wiedergeben; kanonische Namen nur in separat gekennzeichneten Metadaten. Keine nachträgliche stille Textersetzung.
- Vergleichstests mit synthetischer DE/TR-Aussprache, Code-Switching, Spitznamen und Negativfällen (verschiedene Personen mit ähnlichem Namen). Falsche Einfügungen und falsche Zusammenführungen getrennt messen.
