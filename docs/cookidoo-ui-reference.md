# Cookidoo UI Reference

Compact reference for repeated Cookidoo work in in-app browser.

## Assumptions

- Normal Chrome login not visible to Codex. Cookidoo must be logged in inside Codex in-app browser.
- Cookidoo session persists in in-app browser when direct Cookidoo URLs open.
- Cookidoo notes attach to recipe, not recipe list. Be careful when recipe appears in multiple lists.

## URLs

- Suche: `https://cookidoo.de/search/de-DE`
- Meine Rezepte: `https://cookidoo.de/organize/de-DE/my-recipes`
- Einkaufsliste: `https://cookidoo.de/shopping/de-DE`
- Meine Woche: `https://cookidoo.de/planning/de-DE/my-week`

Useful search filters as URL params:

```text
languages=de&tmv=TM6&difficulty=easy&preparationTime=1800
```

Example:

```text
https://cookidoo.de/search/de-DE?languages=de&tmv=TM6&difficulty=easy&preparationTime=1800&query=Lachs
```

## Low-Context Verification

- After big navigation, one broad snapshot for orientation. Then targeted checks: list title, recipe count, note substring, `Nach Rezepten N`, planning date, concrete pantry terms.
- Shopping list: check active section before `Bereits vorhandene Artikel` separately. Otherwise checked pantry items look like open shopping items.
- Repeated recipe actions: use small browser helpers, e.g. open recipe page, open context menu, click menu item, confirm dialog. Saves context versus repeated full snapshots.
- If UI state only visually clear, screenshot exact area, then return to targeted DOM checks.

## Recipe Lists

Create list:

1. Open `Meine Rezepte`.
2. Click `Rezeptliste erstellen`.
3. Enter title.
4. `Speichern`.
5. New list appears under `Meine Rezeptlisten`.

Add recipe to list:

1. Open recipe page.
2. Open context menu next to save icon.
3. `Zur Rezeptliste hinzufügen`.
4. Select target list.

Remove recipe from list:

1. Open recipe list.
2. Open context menu on recipe card.
3. `Entfernen`.

In-app browser note: narrow/responsive view can show only left list navigation on direct custom-list URL. Click target list in navigation; Cookidoo jumps to same URL with `#main` and shows recipe cards.

## Shopping List

Clear shopping list:

1. Open `https://cookidoo.de/shopping/de-DE`.
2. Open three-dot menu.
3. `Alle löschen`.
4. Confirm `Alle löschen`.
5. Success state: `Deine Einkaufsliste ist leer`.

Add recipe to shopping list:

1. Open recipe page.
2. Open context menu next to save icon.
3. `Auf die Einkaufsliste`.
4. Shopping list then shows added recipe count at `Nach Rezepten`, e.g. `Nach Rezepten 3`.

Pantry cleanup:

1. After adding recipes, open shopping list.
2. Check ingredients against `data/pantry.json`. Read `cookidoo_name` as UI wording and `name` as actual pantry item.
3. Remove Wasser, Olivenoel, Oel/Rapsoel, Butter/ungesalzene Butter, Essig/weissen Essig, Pfeffer/schwarzen Pfeffer, Salz, unless special variant required.
4. Do not remove Sonnenblumenoel when specifically requested.
5. Remove spices/sauces only when in `pantry.json` and not expired by first cooking date, e.g. Cookidoo `Gewuerzpaste fuer Gemuesebruehe, selbst gemacht` as pantry `Vegeta`.
6. Unknown expiry: mark manual review or leave on list.

## Week Plan

Add recipe to `Meine Woche`:

1. Open recipe page.
2. Open context menu next to save icon.
3. `Zu Meine Woche hinzufügen`.
4. Pick day in calendar.
5. `Speichern`.

Check directly:

```text
https://cookidoo.de/planning/de-DE/my-week?date=YYYY-MM-DD
```

Opening e.g. `date=2026-05-09` shows week around that day. More reliable than checking current week from `date=today`.

## Notes

New note:

1. Open recipe page.
2. `Notiz hinzufügen`.
3. Fill textbox `Füge deine Tipps, Tricks oder Variationen hinzu`.
4. `Bestätigen`.

Proven portion note:

```text
600-800-kcal-Mahlzeit: ca. 0,9-1,2 Cookidoo-Portionen. Cookidoo: 693 kcal, 42 g Eiweiß pro Portion.
```

Proven week note:

```text
KW 19-20 (09.-15.05.): Samstag Fisch. 4 Cookidoo-Portionen kochen -> 3 Wochenportionen.

Nährwerte geschätzt (BLS/REWE, Salz grob), je Wochenportion:
Energie 3134 kJ / 749 kcal
Fett 34,3 g
  davon gesättigte Fettsäuren 10,8 g
Kohlenhydrate 53,2 g
  davon Zucker 6,3 g
Ballaststoffe 9,0 g
Eiweiß 51,9 g
Salz 2,8 g

Einfrieren: eher nicht ideal; Fisch zuerst/zeitnah essen.
```

Cookidoo notes accept line breaks and render them visually. DOM snapshot normalizes text to one line; verify with normalized whitespace or screenshot.

Existing notes: `Notiz hinzufügen` not always clear in DOM. Visually, trash and pencil icons appear in `Meine Notizen`. Notes are recipe-wide; before overwrite, check whether existing note should remain.

## Recipe Selection Criteria

Good filters:

- Sprache: Deutsch
- Geraet: TM6
- Schwierigkeit: einfach
- Arbeitszeit: `<= 30 Min`
- Ziel: ca. 600-800 kcal pro echte Mahlzeit
- Protein-Ziel: moeglichst mindestens 40 g Eiweiss pro echter Portion
- 30-39 g Eiweiss pro echter Portion acceptable when recipe otherwise fits
- Unter 25 g Eiweiss only deliberate exception, e.g. seasonal dish, and mark in note

Weekly cooking Saturday through Friday:

- 3 recipes for Saturday, Sunday, Monday.
- Monday prefers lowest effort: short active time, little chopping, little cleanup, no nested side steps.
- Monday category not fixed; after picking 1x fish, 1x meat, 1x vegetarian, place easiest recipe on Monday when possible.
- Plan about 3 real weekly portions per recipe.
- If Cookidoo defaults to 4 portions, often practical: cook 4 Cookidoo portions, split into 3 real meals.
- Calculation: `kcal je Cookidoo-Portion * Cookidoo-Portionen / echte Mahlzeiten`.
- At least one fish, one meat, one vegetarian meal for variety.
- Fish first or soon.

## Known Pitfalls

- Search results and recipe lists partly lazy-loaded. If recipe not in DOM, scroll list or reload page.
- `Meine Woche` with current date does not always show all later entries. For verification, open cooking week with `?date=YYYY-MM-DD`.
- Shopping list has `Nach Kategorie` and `Nach Rezepten`. For content check, `Nach Rezepten N` is fastest sanity check.
- For recipes with sauce or separate sides, mention in note whether side must be calculated separately.
- Do not copy Cookidoo nutrition blindly. If ingredients/amounts exist, use local calculation from `bin/nutrition.py` as primary; mention Cookidoo only as comparison. Explain product match and portions when values differ.
