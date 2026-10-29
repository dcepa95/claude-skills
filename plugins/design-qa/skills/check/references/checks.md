# What to check, and Figma vs CSS traps

## Review order

Go through each region in this order. Problems early in the list cause the ones later, so fixing in this order avoids chasing symptoms.

1. **Context**: right viewport, right state, fonts loaded, right data (copy length, image ratio).
2. **Layering and clipping**: z-order, overflow, cropped focus rings, shadows cut off by a parent.
3. **Geometry**: position, width and height, padding, gap, alignment, the last item in a row or list.
4. **Sizing behaviour**: what stretches, what's fixed, min and max widths, wrapping. Check one width between breakpoints too.
5. **Typography**: family, weight, size, line height, letter spacing, case, wrapping and truncation.
6. **Surfaces**: background, border (width, colour, side), radius per corner, shadow, opacity, blur.
7. **States**: hover, focus-visible, active, disabled, selected, error, loading, empty.

## Classify before you compare

- **Axes**: for each element, is width (and height) fixed, set by its content, fluid, or clamped by min and max? A Figma frame width is the capture condition, not a width the element must have: set the viewport to the frame width, and don't force the component to the frame's pixel width.
- **Content**: real copy, prices and images often differ from the design. Different text is never an excuse for wrong padding, type or wrapping. Compare the styling, and note content differences separately.
- **Dynamic regions** (carousels, timers, videos, user data, live prices): hide or mask them in both images, or exclude them from the pixel check, and say so.

## Units and traps

| Figma | CSS | Note |
|---|---|---|
| Letter spacing `5%` | `0.05em` | Percent of the font size. Compare in px: `font-size × %`. |
| Letter spacing `0` px | `normal` | Same thing. |
| Line height `Auto` | `normal` | Depends on the font's metrics; compare the rendered text box height instead. |
| Line height `150%` | `1.5` or `font-size × 1.5` px | Computed style gives px. |
| Font weight name (`Medium`) | number (`500`) | compare.py maps names to numbers. Also check the font file for that weight actually loaded (`stabilize.js` lists them); otherwise the browser fakes bold. |
| Stroke inside / centre / outside | `border` is always inside the box | Centre and outside strokes change the element's outer size; outside ones match `outline` or `box-shadow: 0 0 0 Npx`, which take no layout space. |
| Fill with layer opacity | `opacity` on the element | Opacity on a parent changes children too. A grey that's really a translucent white looks right on one background and wrong on another: compare the colour **as rendered**, and mark opacity `NOT_PROVEN` unless the backdrop matches the design. |
| Auto layout gap | `gap`, or margins | "Space between" in Figma is `justify-content: space-between`, not a fixed gap. |
| Auto layout padding | `padding` | Hug contents = width from content; fill container = `flex: 1` or `width: 100%`. |
| Text box trim / vertical trim | half-leading | CSS adds half the leading above and below text; Figma with trim doesn't. A 1–3px vertical offset of text inside a button is often this, not wrong padding. |
| Corner radius per corner | `border-*-radius` | Pill shapes in Figma are often a large number: any radius ≥ half the height looks the same. |
| Drop shadow `x y blur spread` | `box-shadow: x y blur spread` | Figma blur equals CSS blur radius. |
| Layer blur / background blur | `filter: blur()` / `backdrop-filter` | Can't be judged on a plain backdrop: `NOT_PROVEN` unless the backdrop matches. |
| Variables / styles | CSS custom properties, SCSS variables | Map colours and sizes back to tokens with `get_variable_defs`; a raw value equal to a token's value should use the token. |

## Severity

- **Blocker**: broken layout, unreadable or overlapping content, missing element, wrong component.
- **High**: visibly wrong at a glance: wrong colour, size, weight or spacing on primary elements, wrong state.
- **Medium**: noticeable when compared side by side: 2–4px spacing, slightly wrong line height, radius.
- **Nit**: sub-pixel, anti-aliasing, or invisible at 100% zoom.

## Ledger row

Each finding has: region, property, expected (with token name), actual, delta, verdict (`PASS`, `MISMATCH`, `NOT_PROVEN`), severity, where to fix (`file:line`), and evidence (measurement, crop or heatmap region). Things the design doesn't settle (missing state, conflicting frames, a value that isn't a token) are `DESIGN_AMBIGUOUS`: list them for the designer instead of guessing.
