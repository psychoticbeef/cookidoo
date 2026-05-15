# Cookidoo UI Reference

Kurze Referenz fuer wiederholte Cookidoo-Arbeiten im In-App-Browser.

## Grundannahmen

- Der normale Chrome-Login ist fuer Codex nicht sichtbar. Cookidoo muss im Codex-In-App-Browser eingeloggt sein.
- Die Cookidoo-Session bleibt im In-App-Browser erhalten, wenn direkte Cookidoo-URLs geoeffnet werden.
- Cookidoo-Notizen haengen am Rezept, nicht an einer Rezeptliste. Daher vorsichtig sein, wenn ein Rezept in mehreren Listen verwendet wird.

## Wichtige URLs

- Suche: `https://cookidoo.de/search/de-DE`
- Meine Rezepte: `https://cookidoo.de/organize/de-DE/my-recipes`
- Einkaufsliste: `https://cookidoo.de/shopping/de-DE`
- Meine Woche: `https://cookidoo.de/planning/de-DE/my-week`

Nuetzliche Suchfilter als URL-Parameter:

```text
languages=de&tmv=TM6&difficulty=easy&preparationTime=1800
```

Beispiel:

```text
https://cookidoo.de/search/de-DE?languages=de&tmv=TM6&difficulty=easy&preparationTime=1800&query=Lachs
```

## Kontextarme Verifikation

- Nach einem grossen Seitenwechsel reicht ein breiter Snapshot zur Orientierung.
  Danach gezielte Checks verwenden: Listentitel, Rezeptanzahl, Notiz-Substring,
  `Nach Rezepten N`, Planungsdatum und konkrete Pantry-Begriffe.
- Bei der Einkaufsliste den aktiven Bereich vor `Bereits vorhandene Artikel`
  getrennt pruefen. Sonst wirken bereits abgehakte Vorratsartikel wie offene
  Einkaufspositionen.
- Fuer wiederholte Rezeptaktionen kleine Browser-Helfer verwenden, z. B.
  Rezeptseite oeffnen, Kontextmenue oeffnen, Menuepunkt klicken, Dialog
  bestaetigen. Das spart Kontext gegenueber mehrfachen Vollsnapshots.
- Wenn ein UI-Zustand nur visuell eindeutig ist, einen Screenshot fuer genau
  diesen Bereich nutzen und danach wieder zu gezielten DOM-Pruefungen wechseln.

## Rezeptlisten

Liste erstellen:

1. `Meine Rezepte` oeffnen.
2. `Rezeptliste erstellen` anklicken.
3. Titel eingeben.
4. `Speichern`.
5. Die neue Liste erscheint unter `Meine Rezeptlisten`.

Rezept zu Liste hinzufuegen:

1. Rezeptseite oeffnen.
2. Kontextmenue neben dem Merken-Icon oeffnen.
3. `Zur Rezeptliste hinzufügen`.
4. Ziel-Liste auswaehlen.

Rezept aus Liste entfernen:

1. Rezeptliste oeffnen.
2. Kontextmenue am Rezept-Card oeffnen.
3. `Entfernen`.

Hinweis zur In-App-Browser-Ansicht: Bei schmaler/responsiver Ansicht kann eine
direkte Custom-List-URL zunaechst nur die linke Listen-Navigation zeigen. Dann
die Ziel-Liste in der Navigation anklicken; Cookidoo springt auf dieselbe URL mit
`#main` und zeigt die Rezeptkarten.

## Einkaufsliste

Einkaufsliste leeren:

1. `https://cookidoo.de/shopping/de-DE` oeffnen.
2. Drei-Punkte-Menue oeffnen.
3. `Alle löschen`.
4. Im Dialog nochmal `Alle löschen`.
5. Erfolgszustand: `Deine Einkaufsliste ist leer`.

Rezept zur Einkaufsliste hinzufuegen:

1. Rezeptseite oeffnen.
2. Kontextmenue neben dem Merken-Icon oeffnen.
3. `Auf die Einkaufsliste`.
4. Danach zeigt die Einkaufsliste bei `Nach Rezepten` die Anzahl der hinzugefuegten Rezepte, z. B. `Nach Rezepten 3`.

Pantry-Bereinigung:

1. Nach dem Hinzufuegen der Rezepte Einkaufsliste oeffnen.
2. Zutaten gegen `data/pantry.json` pruefen. Dabei `cookidoo_name` als UI-Wortlaut und `name` als tatsaechlichen Vorrat lesen.
3. Wasser, Olivenoel, Oel/Rapsoel, Butter/ungesalzene Butter, Essig/weissen Essig, Pfeffer/schwarzen Pfeffer und Salz entfernen, sofern keine besondere Variante verlangt ist.
4. Sonnenblumenoel nicht entfernen, wenn es konkret verlangt wird.
5. Gewuerze/Saucen nur entfernen, wenn sie in `pantry.json` stehen und zum ersten Kochdatum der Woche noch nicht abgelaufen sind, z. B. Cookidoo `Gewuerzpaste fuer Gemuesebruehe, selbst gemacht` als Vorrat `Vegeta`.
6. Eintraege mit unbekanntem Ablaufdatum fuer manuelle Pruefung markieren oder auf der Liste lassen.

## Wochenplan

Rezept in `Meine Woche` eintragen:

1. Rezeptseite oeffnen.
2. Kontextmenue neben dem Merken-Icon oeffnen.
3. `Zu Meine Woche hinzufügen`.
4. Im Kalender den Tag waehlen.
5. `Speichern`.

Direkt pruefen:

```text
https://cookidoo.de/planning/de-DE/my-week?date=YYYY-MM-DD
```

Wenn man z. B. `date=2026-05-09` oeffnet, zeigt Cookidoo die Woche um diesen Tag herum. Das ist zuverlaessiger als nur die aktuelle Woche ab `date=today` zu pruefen.

## Notizen

Neue Notiz:

1. Rezeptseite oeffnen.
2. `Notiz hinzufügen`.
3. Textbox `Füge deine Tipps, Tricks oder Variationen hinzu` fuellen.
4. `Bestätigen`.

Bewaehrtes Format fuer Portionen:

```text
600-800-kcal-Mahlzeit: ca. 0,9-1,2 Cookidoo-Portionen. Cookidoo: 693 kcal, 42 g Eiweiß pro Portion.
```

Bewaehrtes Format fuer eine Wochenplanung:

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

Cookidoo-Notizen akzeptieren Zeilenumbrueche und zeigen sie visuell an. Der
DOM-Snapshot normalisiert den Text aber zu einer Zeile; beim Verifizieren also
Whitespace normalisieren oder per Screenshot pruefen.

Wichtig: Bei existierenden Notizen ist `Notiz hinzufügen` im DOM nicht immer eindeutig sichtbar. Visuell gibt es dann Papierkorb- und Stift-Icons im Bereich `Meine Notizen`. Da Notizen rezeptweit sind, vor dem Ueberschreiben pruefen, ob eine bestehende Notiz erhalten bleiben soll.

## Rezeptauswahl-Kriterien

Bisher gut passende Filter:

- Sprache: Deutsch
- Geraet: TM6
- Schwierigkeit: einfach
- Arbeitszeit: `<= 30 Min`
- Ziel: ca. 600-800 kcal pro echte Mahlzeit
- Protein-Ziel: moeglichst mindestens 40 g Eiweiss pro echter Portion
- 30-39 g Eiweiss pro echter Portion sind akzeptabel, wenn das Rezept sonst gut passt
- Unter 25 g Eiweiss nur bewusst als Ausnahme, z. B. als saisonales Gericht, und in der Notiz kennzeichnen

Fuer Wochenkochen Samstag bis Freitag:

- 3 Rezepte fuer Samstag, Sonntag, Montag.
- Montag bevorzugt das Rezept mit dem geringsten Aufwand: kurze aktive Arbeitszeit, wenig Schnippeln, wenig Abwasch, keine verschachtelten Zusatzschritte.
- Kategorie nicht fest an Montag binden; nach Auswahl von 1x Fisch, 1x Fleisch und 1x vegetarisch das einfachste Rezept moeglichst auf Montag legen.
- Pro Rezept ca. 3 echte Wochenportionen einplanen.
- Wenn Cookidoo standardmaessig 4 Portionen anbietet, ist oft praktikabel: 4 Cookidoo-Portionen kochen und in 3 echte Mahlzeiten teilen.
- Rechnung: `kcal je Cookidoo-Portion * Cookidoo-Portionen / echte Mahlzeiten`.
- Mindestens eine Mahlzeit Fisch, eine Fleisch, eine vegetarisch fuer Abwechslung.
- Fisch zuerst oder zeitnah essen.

## Bekannte Stolperstellen

- Die Suchergebnisse und Rezeptlisten sind teils lazy-loaded. Wenn ein Rezept nicht im DOM auffindbar ist, Liste scrollen oder die Seite neu laden.
- `Meine Woche` mit dem aktuellen Datum zeigt nicht immer alle spaeteren Eintraege. Fuer Kontrolle gezielt mit `?date=YYYY-MM-DD` auf die Kochwoche gehen.
- Einkaufsliste hat zwei Ansichten: `Nach Kategorie` und `Nach Rezepten`. Fuer Inhaltskontrolle ist `Nach Rezepten N` der schnellste Plausibilitaetscheck.
- Bei Rezepten mit Sauce oder separaten Beilagen in der Notiz erwaehnen, ob Beilage separat einberechnet werden muss.
- Cookidoo-Naehwerte nicht blind uebernehmen. Wenn Zutaten/Mengen vorhanden sind, lokale Rechnung aus `bin/nutrition.py` als primaeren Wert verwenden; Cookidoo nur zum Vergleich nennen. Bei Abweichungen Produktmatch und Portionierung in der Notiz erklaeren.
