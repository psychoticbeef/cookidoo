# Cookidoo Browser Helpers

Use this file only when actively automating Cookidoo in the in-app browser.
Copy or adapt the smallest helper needed for the next action; do not paste the
whole file into browser context.

## Page Text Helpers

These snippets are useful in page-evaluate style browser calls when a selector is
unstable but the visible German UI text is stable.

```js
const textOf = (node) =>
  (node?.innerText || node?.textContent || "").replace(/\s+/g, " ").trim();

const norm = (value) =>
  String(value || "")
    .normalize("NFKD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();

const controls = () =>
  Array.from(document.querySelectorAll("button, a, input, textarea, [role='button'], [role='menuitem']"));

const findControl = (label) =>
  controls().find((node) => norm(textOf(node) || node.getAttribute("aria-label")).includes(norm(label)));

const clickControl = (label) => {
  const node = findControl(label);
  if (!node) return false;
  node.click();
  return true;
};
```

## Targeted Verification Patterns

Prefer boolean/count checks over full snapshots once the page is loaded.

```js
const bodyText = textOf(document.body);

const includesAll = (needles) =>
  needles.every((needle) => norm(bodyText).includes(norm(needle)));

const visibleRecipeCount = () =>
  Array.from(document.querySelectorAll("a[href*='/recipes/'], [data-testid*='recipe']"))
    .map(textOf)
    .filter(Boolean).length;
```

For note verification, normalize whitespace and check distinctive substrings
instead of the full note:

```js
includesAll([
  "KW 22 (23.-29.05.)",
  "4 Cookidoo-Portionen kochen -> 3 Wochenportionen",
  "Nährwerte geschätzt",
]);
```

For shopping-list cleanup, inspect the active/open section before already-owned
items:

```js
const shoppingText = textOf(document.body);
const openShoppingText = shoppingText.split(/Bereits vorhandene Artikel/i)[0];
const stillOpen = (labels) =>
  labels.filter((label) => norm(openShoppingText).includes(norm(label)));
```

## Repeated Cookidoo Actions

Use these as action patterns, not as guaranteed selectors. Cookidoo markup
changes often; visible text and `aria-label` are usually more stable.

```js
const openRecipeMenu = () =>
  clickControl("Weitere Optionen") ||
  clickControl("Mehr") ||
  clickControl("Optionen");

const confirmDialog = () =>
  clickControl("Speichern") ||
  clickControl("Bestätigen") ||
  clickControl("Alle löschen");
```

Typical flow:

1. Navigate directly to the recipe/list/shopping/week URL.
2. Take one broad observation only if orientation is needed.
3. Use text helpers to click the next stable control.
4. Verify with a targeted substring, count, or absence check.
5. If a helper fails, take a small snapshot/screenshot of the current dialog and
   adjust only that step.
