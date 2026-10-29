# design-qa

Install it:

```
/plugin install design-qa --marketplace dcepa95/claude-skills
```

Run `/design-qa:check <figma link> [page url] [what on the page]` to check a built page or component against its Figma design. You get every difference with numbers and the file to change, not "looks a bit off".

It runs two checks, and it's only done when both pass:

- **Property check.** It measures the computed styles in the browser and compares them with the Figma values: sizes, padding, gap, radius per corner, borders, colours (mapped back to your tokens), shadows, opacity and the full type spec. Geometry gets ±0.5px; radius, borders and type must match exactly. Whatever can't be judged (like a blur over a plain background) is reported as not proven, never as a pass.
- **Pixel check.** It screenshots the component and the Figma node at the same 2× scale and diffs them pixel by pixel. You get a heatmap, and it zooms into the regions that differ. A size difference is reported first, because it means the geometry is off.

Before capturing, it waits for fonts and images and freezes animations. Each screenshot is taken twice to make sure nothing is still moving. It checks the hover, focus and other states the design shows, at each Figma frame width. It knows the usual Figma-to-CSS traps: letter spacing in %, strokes inside vs outside, line height `Auto`, text trim, and a grey that's really a translucent white.

The report groups differences by severity (blocker, high, medium, nit) with expected, actual, delta and `file:line`. Anything the design doesn't settle becomes a question for the designer. In "Report and fix" mode, it fixes the differences in up to 3 rounds and re-checks after each. Then a separate reviewer, who hasn't seen the earlier findings, compares the final screenshots, so nothing gets waved through. Nothing is committed without asking.

Needs the Chrome DevTools plugin, the Figma plugin and Python 3. The pixel diff uses macOS `sips`, or Pillow if it's installed, so there's nothing else to install. It's meant for full component checks; for a one-line CSS tweak, checking by eye is faster.

`/design-qa:check help` lists the arguments.

See the [plugin README](../../README.md) to install or update.
