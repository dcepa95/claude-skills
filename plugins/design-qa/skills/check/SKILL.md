---
name: check
description: Check a built page or component against its Figma design and report every difference with numbers, not impressions. Measures computed styles in the browser and compares them with the Figma values (spacing, sizes, type, colours and tokens, borders, radius, shadows), pixel-diffs matching screenshots at the same scale, covers hover/focus/disabled states and breakpoints, and says which file and line to change. Can fix the differences in rounds until the check is clean. Use this whenever the user asks to compare an implementation with Figma, "does this match the design", design QA, pixel-perfect check, visual review against a Figma link, or when a component keeps not quite matching the design after several tweaks. Not for quick single-value CSS tweaks the user will check themselves. Also `help`.
---

# Design QA

Compare what the browser renders with what Figma specifies, and report the differences as a ledger the user can act on: what, how far off, where to fix it.

Three rules matter most:
- **Numbers before eyes.** Measured properties decide; screenshots catch what measurements miss. A diff percentage alone proves nothing.
- **Done means both checks pass**: no `MISMATCH` in the property ledger, and no unexplained region in the pixel diff. Anything that can't be judged is `NOT_PROVEN`, never `PASS`.
- **Don't guess the design.** When Figma doesn't settle something (missing state, two frames disagree), it's `DESIGN_AMBIGUOUS` and goes on a list for the designer.

Scripts are in `${CLAUDE_SKILL_DIR}/scripts`, and `references/checks.md` has the review order, the Figma-vs-CSS unit traps and the severity scale; read it at the start of every run. Work files (screenshots, measurements, heatmaps) go in `<scratchpad>/design-qa/<run>/`. The skill runs as `/design-qa:check` when installed as a plugin, or `/check` as a personal skill.

## How to ask

Every decision is an `AskUserQuestion` call with 2–4 concrete options: real node names, URLs, widths and states from this run. Bundle independent questions into one call. Don't ask what the request already answers. If the user answers in prose, go with it.

## Arguments

```
/design-qa:check <figma link> [<page url or route>] [<what on the page>]
/design-qa:check help
```

Several Figma links mean several states or breakpoints of the same thing (e.g. a 375 and a 1440 frame, or default and hover variants).

## 0. Tools

This needs the Chrome DevTools tools (`navigate_page`, `emulate`, `take_snapshot`, `take_screenshot`, `evaluate_script`) and the Figma tools (`get_screenshot`, `get_metadata`, `get_design_context`, `get_variable_defs`). If either set is missing, say which plugin provides it and stop. Follow the Figma server's instructions: create a session for the file first, and load the Figma skills its tools require (such as `figma-design-to-code` before `get_design_context`).

## 1. Scope

From the Figma link take the file key and node id (`node-id=12-34` → `12:34`). Call `get_metadata` on the node: it gives the frame size, its children and any variants (states) and sibling frames at other widths.

Then settle, in one call where possible:
- **Page**: the URL to open. Use the argument, else the project's dev URL from `CLAUDE.md`, `package.json` scripts or `.env` (`localhost:3000`…). Check it answers with `curl -sk -o /dev/null -w '%{http_code}'`. If nothing is running, ask `Start the dev server` · `I'll start it` · `Use a preview URL` (via Other). If you start it, run it in the background and stop it at the end.
- **What on the page**: `The whole page` · a component, found by its text, role or selector. Find it with `take_snapshot` and keep its `uid`.
- **States and widths** (multiSelect): the variants and frame widths `get_metadata` found, plus `Hover`, `Focus` for anything interactive. Recommend the ones the design actually shows; states without a design go to `DESIGN_AMBIGUOUS` unless the user wants them checked against the default.
- **Mode**: `Report only (Recommended)` · `Report and fix`: fix in rounds until the check is clean (at most 3 rounds, then report what's left).

To reach a state that needs a flow (an open modal, a filled cart, a logged-in view), ask the user how to get there, or drive it with clicks. Don't hardcode data in the app for it; if there's no other way, ask first, and mark the change with a `TEMP:` comment.

## 2. Capture the design

For each Figma node in scope:
1. `get_screenshot` with `maxDimension` = the node's longer edge × 2, so it's at 2× scale, matching the page captured at device pixel ratio 2. Download it with the curl command the tool gives to `design-<state>-<width>.png`. If the image came back smaller than 2× (clamped), note the real scale and pass it to the diff.
2. `get_design_context` on the node. When the response says it's sparse or truncated, call it on the child nodes in parallel.
3. `get_variable_defs` for the tokens the node uses.

From these, write down the expected values per region: size, padding, gap, alignment, radius per corner, border, fill, shadow, opacity, and the full type spec. Keep token names next to their values.

## 3. Capture the page

For each state and width:
1. `emulate` with `viewport: "<frame width>x<frame height or 900>x2"` (add `,mobile,touch` for frames under 768 wide). The Figma frame width sets the viewport; it isn't a width the component has to have.
2. `navigate_page` to the URL, or reload after changing the viewport.
3. Run `scripts/stabilize.js` with `evaluate_script` (pass the file's contents as `function`). It freezes animations and transitions, waits for fonts and images, and returns the loaded and failed fonts. A design font that didn't load makes every type check meaningless: stop and report it.
4. Put the component in the state: `hover` on its uid; `press_key` Tab until it has focus, for `:focus-visible`; disabled or selected via the app's own controls.
5. Run `scripts/measure.js` with `evaluate_script`, `args: [<uid>]` and `filePath` set to `measure-<state>-<width>.json`. It scrolls the component into view and returns every visible element under it with its box (relative to the component), the computed styles that differ from defaults, and `rootBox`, the component's box in the viewport. The snapshot often only lists interactive elements, not their wrapping `div`. Then first set the root from a child it does list, `(el) => { window.__designQaRoot = el.closest('<selector>'); return !!window.__designQaRoot }` with `args: [<child uid>]`, or from a selector with `() => …document.querySelector(…)`, and run `measure.js` without `args`.
6. Screenshot the component: `take_screenshot` with its `uid` and `filePath` set to `page-<state>-<width>.png`. Without a uid for it, take the viewport and crop it to `rootBox`: `pixeldiff.py crop viewport.png page-<s>.png <x> <y> <w> <h> --scale 2`. Take it twice and compare with `cmp`. If the files differ, something is still moving: wait a second and retry, up to 3 times, then find and mask the moving part, and say so.

## 4. Property check

Match Figma nodes to DOM elements: by a `data-figma-node` attribute if the project has one, otherwise by text, role and order. Write `pairs.json`, one row per property worth checking, with `region`, `property`, `expected` (Figma, converted with the traps in `references/checks.md`), `actual` (from the measurement), `token`, and `severity`. Include every property from the review order that the design specifies, not just suspicious ones. Missing data on either side stays `null`, which makes the row `NOT_PROVEN`.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/compare.py pairs.json --rem <root font size from measure.json>
```

It prints the ledger, mismatches first. Geometry gets ±0.5px; radius, border and type must match exactly.

For each mismatch, find where to fix it: search the component's styles for its class, then the raw value or the wrong variable (`grep -rn`). When the expected value is a token and the code has a raw value equal to it, or another token, say which token to use.

## 5. Pixel check

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/pixeldiff.py design-<s>.png page-<s>.png --scale 2 --out heat-<s>.png
```

- A **size mismatch** comes first: it means geometry is off, and the rest of the diff is approximate until it's fixed. Connect it to the ledger (which width, padding or line height explains it).
- Look at the heatmap with `Read`, then crop each of the biggest regions from both images (`pixeldiff.py crop <in> <out> X Y W H --scale 2`) and look at the pair. Always also crop the tricky spots: corners and borders, shadows, the first and last item of a repeated row, focus rings, text that might wrap.
- Each region either matches a ledger row, becomes a new row, or is explained (different copy or image, anti-aliasing). Unexplained regions mean the check isn't done.

## 6. Report

Show:
1. One line: what was checked (component, states, widths) and the result (`4 mismatches, 1 not proven, 23 pass`).
2. The mismatches, grouped by severity (Blocker, High, Medium, Nit): region, property, expected (token), actual, delta, `file:line` to change.
3. `NOT_PROVEN` items and why (blur on a plain backdrop, state not reachable).
4. `DESIGN_AMBIGUOUS` items, written as questions for the designer.
5. Paths to the screenshots and heatmaps.

## 7. Fix rounds (Report and fix)

Fix one batch of related mismatches at a time (same element or same cause), then capture and measure again only the affected states, and re-run both checks. Show a round counter (`Round 2 of 3: 1 mismatch left`). Don't touch `DESIGN_AMBIGUOUS` items. After 3 rounds, stop and report what's left.

Before calling it clean, run a fresh check that isn't anchored on yours: launch a read-only subagent (`Agent`, general-purpose) with only the final design and page screenshot paths, the crops, and the Figma link, asking for every visible difference with its location. Anything it finds that isn't in the ledger goes back through steps 4–5.

At the end, show the diff of the changes and ask `Commit` · `I'll review first`. Stop the dev server if you started it.
