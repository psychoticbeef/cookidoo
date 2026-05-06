# Cookidoo Wochenplanung

Dieses Repository sammelt meinen Cookidoo-Mealprep-Workflow: Rezepte suchen,
Nährwerte realistischer nachrechnen, Notizen in Cookidoo schreiben, Einkaufsliste
aufräumen und den Wochenplan befüllen.

Die Grundidee: Ich koche Samstag, Sonntag und Montag je ein Gericht. Jedes
Gericht soll drei echte Mealprep-Portionen ergeben. Damit entstehen neun
Portionen für Samstag bis Freitag.

## Nächste Woche planen

Dieses Repo enthält einen lokalen Codex-Skill:

```text
$cookidoo-week
```

Wichtig: Den Ordner dieses Repos als Workspace öffnen, sonst sieht Codex den
lokalen Skill nicht.

Der Skill macht den kompletten Wochenworkflow:

1. drei neue Cookidoo-Rezepte suchen
2. genau ein Fischgericht, ein Fleischgericht und ein vegetarisches Gericht
3. keine Wiederholung aus dem bisherigen Jahr verwenden
4. einfache Rezepte mit wenig Vorbereitung bevorzugen
5. Bewertungen prüfen und schwach bewertete Rezepte aussortieren
6. grob 600-800 kcal pro echter Portion anpeilen
7. Nährwerte lokal aus Zutaten schätzen, statt Cookidoo-Werte blind zu kopieren
8. Notizen mit Portionen, Nährwerten und Einfrier-Hinweis schreiben
9. neue Cookidoo-Liste anlegen
10. Rezepte in Wochenplan und Einkaufsliste eintragen
11. Einkaufsliste gegen Vorräte/Pantry bereinigen

## Meine Regeln

- Die Cookidoo-Woche läuft von Samstag bis Freitag.
- Gekocht wird Samstag, Sonntag und Montag.
- Montag bevorzugt das Rezept mit dem wenigsten Aufwand, weil Arbeit/Sport den
  Abend knapper machen: kurze aktive Arbeitszeit, wenig Schnippeln, wenig
  Abwasch, keine verschachtelten Zusatzschritte.
- Pro Gericht werden drei echte Wochenportionen geplant.
- Wenn vier Cookidoo-Portionen gut zu drei echten Portionen passen, ist das
  völlig okay. Die Cookidoo-Portionszahl muss dann in die Notiz.
- Rezepte sollen `einfach` sein und möglichst wenig aktive Arbeitszeit haben.
- Protein-Ziel: möglichst mindestens 40 g Eiweiß pro echter Portion.
- 30-39 g Eiweiß pro Portion sind akzeptabel, wenn das Rezept sonst gut passt.
- Unter 25 g Eiweiß nur bewusst als Ausnahme, z. B. als saisonales Gericht, und
  dann in der Notiz kennzeichnen.
- Es soll proteinreicher sein, aber keine reine Fitness-Mahlzeit werden.
- Saisonale Gerichte sind willkommen, aber nicht erzwungen.
- Cookidoo-Nährwerte sind nur Vergleichswerte. Die eigentliche Notiz basiert auf
  der lokalen Zutatenrechnung.

## Vorräte

Die Einkaufsliste wird gegen `data/pantry.json` geprüft.

Immer da sind zum Beispiel:

- Wasser
- Olivenöl
- Rapsöl, wenn Cookidoo nur allgemein `Öl` verlangt
- ungesalzene Butter
- weißer Essig
- schwarzer Pfeffer
- Salz
- einige Gewürze und Saucen mit Ablaufdatum

Sonnenblumenöl ist nicht automatisch vorhanden. Wenn ein Rezept ausdrücklich
Sonnenblumenöl oder ein anderes spezielles Öl verlangt, soll es auf der
Einkaufsliste bleiben.

## Nährwerte

Die Nährwerte werden mit `bin/nutrition.py` aus der lokalen Produktdatenbank
geschätzt. Die Daten kommen aus einer zusammengeführten DB mit unter anderem
REWE, Edeka, dm und BLS.

Für generische Zutaten werden bevorzugt BLS-Werte genutzt. Für konkrete Produkte
oder produktartige Zutaten werden eher Supermarktprodukte verwendet.

Beispiel:

```sh
bin/nutrition.py search "broccoli roh" --source bls
bin/nutrition.py search "tortilla 20cm" --source rewe
bin/nutrition.py calc recipes/kw19-20-2026.json --markdown
```

Einzelne Einkaufsliste-Einträge gegen die Pantry prüfen:

```sh
bin/nutrition.py pantry-check "Paprika edelsüß" --date 2026-05-09
bin/nutrition.py pantry-check "Sonnenblumenöl" --date 2026-05-09
```

## Was hier liegt

- `.agents/skills/cookidoo-week/`: der lokale Codex-Skill für die Wochenplanung
- `bin/nutrition.py`: kleines CLI für Suche, Nährwertrechnung und Pantry-Check
- `data/products_harmonized.json`: lokale Nährwertdatenbank
- `data/products.store`: SQLite/SwiftData-Kopie der Produktdaten
- `data/ingredient-defaults.json`: feste Zuordnungen für schwierige Zutaten
- `data/pantry.json`: Vorräte, Gewürze und Ablaufdaten
- `docs/cookidoo-ui-reference.md`: Bediennotizen zur Cookidoo-Weboberfläche
- `docs/meal-plan-history-2026.md`: Jahres-History gegen Wiederholungen
- `docs/nutrition-workflow.md`: Regeln für Nährwertberechnung und Notizen
- `recipes/`: ausgewählte Rezept-Artefakte mit Zutaten und Produktmatches
- `reports/`: berechnete Labels und Cookidoo-Notiztexte

## Public-Hinweis

Der Ordner enthält keine Cookidoo-Zugangsdaten. Der Login bleibt im Browser.

Enthalten sind aber persönliche Präferenzen, Vorräte, Gewürzliste, ausgewählte
Rezepte und lokale Produktdaten. Das ist nicht geheim im Passwort-Sinn, aber
persönlich.

## Für Agenten

Der Einstieg für wiederholte Planung ist der Skill:

```text
.agents/skills/cookidoo-week/SKILL.md
```

Bei Änderungen an der Cookidoo-Oberfläche bitte die UI-Notizen in
`docs/cookidoo-ui-reference.md` aktualisieren. Bei neuen Nährwert-Learnings bitte
`docs/nutrition-workflow.md` ergänzen.
