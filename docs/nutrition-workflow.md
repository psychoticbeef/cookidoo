# Nutrition workflow

Goal: estimate a German-style nutrition label for Cookidoo mealprep portions and
write a compact, auditable summary into the recipe notes.

## Data sources

- Primary database: `data/products_harmonized.json`
- SQLite/SwiftData copy: `data/products.store`
- Default ingredient matches:
  `data/ingredient-defaults.json`
- Pantry/shopping defaults: `data/pantry.json`
- Built from REWE, Edeka, dm, BLS 2025, and a few restaurant/product sources.
- CLI helper: `bin/nutrition.py`

## Portion rule

For the current mealprep setup, most recipes are cooked as 4 Cookidoo portions
and divided into 3 real weekly meals.

Formula:

```text
per real meal = total recipe nutrition / real meal count
per Cookidoo portion = total recipe nutrition / Cookidoo portion count
```

## Protein target

For weekly mealprep, prefer at least 40 g protein per real meal. Treat 30-39 g
as acceptable when the recipe otherwise fits well. Recipes below 25 g protein
per real meal should be deliberate exceptions only, e.g. seasonal dishes, and the
Cookidoo note should mark that exception.

Do not turn the workflow into fitness-recipe optimization. The target is normal,
satisfying food with meaningfully higher protein than a typical easy dinner.

## Cookidoo values

Treat Cookidoo nutrition values as comparison data, not as the primary estimate,
when ingredient amounts are available. The primary note should come from the
local ingredient calculation in `bin/nutrition.py`; Cookidoo values are useful
for sanity checks and can be mentioned as comparison when they diverge.

Reason: Cookidoo values can be hard to reconcile with visible ingredients. For
example, `r251327` (Corn Chowder) showed 685 kcal per Cookidoo portion, while a
local calculation with regular `Bacon in Streifen` matched to REWE Tulip
Baconstreifen gives about 497 kcal per Cookidoo portion. Even a very fatty
Pancetta/Bauchspeck match stayed below Cookidoo. In such cases:

1. Pick the ingredient match that reflects the likely real purchase, not the one
   that best forces the Cookidoo total.
2. State the important assumption in the note, e.g. "Bacon als regulaere
   Baconstreifen, ausgelassenes Fett bleibt im Gericht".
3. Adjust `real_portions` so the actual meal lands in the 600-800 kcal target.
4. Keep Cookidoo values only as comparison text when that helps explain a
   discrepancy.

## Matching rules

1. Use BLS for generic raw or common ingredients.
2. Use supermarket products when the ingredient is product-like or branded.
3. Ignore water and tiny herb/spice garnish unless it materially affects the
   recipe.
4. Model explicit salt separately with BLS table salt.
5. Treat broth paste/cubes as rough salt estimates; brands and homemade paste
   vary heavily.
6. Check `data/ingredient-defaults.json` for known ambiguous ingredients.
7. When Cookidoo says vegetable broth paste/cube and no exact product is given,
   use `rewe:2082415` (`Podravka Vegeta Oryginalna 500g`) as the default model.
   Assume `1 geh. TL` is roughly `10 g` unless the recipe gives a weight.
8. Record every match by `source` and `id` in the recipe JSON.

## Pantry and shopping-list rules

Before finalizing a Cookidoo shopping list, compare the ingredient list against
`data/pantry.json`.

Always available unless explicitly overridden:

- Wasser
- Olivenöl
- Öl (pantry: Rapsöl)
- Butter (pantry: ungesalzene Butter)
- Essig (pantry: weißer Essig)
- Pfeffer (pantry: schwarzer Pfeffer)
- Salz

Do not treat Sonnenblumenöl as a pantry default. If a recipe explicitly asks for
Sonnenblumenöl or another non-standard oil, leave it on the shopping list.

Use Cookidoo's shopping-list wording in `cookidoo_name` and the actual pantry
item in `name`. This keeps the UI cleanup simple while preserving substitutions
such as `Öl -> Rapsöl` and `Gewürzpaste für Gemüsebrühe, selbst gemacht ->
Vegeta`.

For dated spices/sauces:

1. If the ingredient is listed and `expires` is after the first cooking date of
   the week, remove it from the shopping list.
2. If `expires` is before the cooking date, keep it and mark it as `nachkaufen`.
3. If `expires` is `null`, keep or flag it for manual review instead of blindly
   removing it.
4. Preserve exact recipe requirements when substitution would change the dish
   materially, e.g. Reisessig is not the same as weißer Essig.

Current expiry parsing convention:

- `27` means `2027-12-31`.
- `08/28` means `2028-08-31`.
- `ende 26` means `2026-12-31`.
- `?` means unknown/manual review.

Use the CLI for quick checks:

```sh
bin/nutrition.py pantry-check "Paprika edelsüß" --date 2026-05-09
bin/nutrition.py pantry-check "Sonnenblumenöl" --date 2026-05-09
bin/nutrition.py pantry-check "Reisessig" --date 2026-05-09
```

## Note format

Use a short Cookidoo note like:

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

Keep the full ingredient-match table in `reports/`, not in Cookidoo.

## Caveats

- Cookidoo gives only a subset of label values. Sugar, saturated fat, and salt
  are local estimates.
- Salt is usually the weakest estimate because broth paste, stock cubes, canned
  products, and "to taste" additions differ a lot.
- The estimate should be used to sanity-check meal size, not as medical-grade
  nutrition tracking.
