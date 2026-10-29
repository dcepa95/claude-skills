(root) => {
  root = root || window.__designQaRoot || document.body;
  root.scrollIntoView({ block: 'nearest' });
  const KEEP = [
    'display', 'position', 'flex-direction', 'flex-wrap', 'justify-content', 'align-items', 'gap',
    'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
    'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
    'border-top-width', 'border-right-width', 'border-bottom-width', 'border-left-width',
    'border-top-style', 'border-top-color', 'border-right-color', 'border-bottom-color', 'border-left-color',
    'border-top-left-radius', 'border-top-right-radius', 'border-bottom-right-radius', 'border-bottom-left-radius',
    'outline-width', 'outline-style', 'outline-color', 'outline-offset',
    'background-color', 'background-image', 'box-shadow', 'opacity', 'mix-blend-mode', 'backdrop-filter', 'filter',
    'color', 'font-family', 'font-size', 'font-weight', 'font-style', 'line-height', 'letter-spacing',
    'text-transform', 'text-align', 'text-decoration-line', 'white-space', 'overflow', 'object-fit', 'fill', 'stroke',
  ];
  const DEFAULTS = new Set(['none', 'normal', 'auto', '0px', 'rgba(0, 0, 0, 0)', 'static', 'visible', 'start', 'nowrap', 'row', 'stretch', 'baseline']);
  const SKIP = { opacity: '1', 'object-fit': 'fill', fill: 'rgb(0, 0, 0)' };
  const inherited = new Set(['color', 'font-family', 'font-size', 'font-weight', 'font-style', 'line-height', 'letter-spacing', 'text-transform', 'text-align', 'white-space']);
  const base = root.getBoundingClientRect();
  const r2 = (n) => Math.round(n * 100) / 100;
  const label = (el) => {
    const cls = [...el.classList].slice(0, 2).map((c) => '.' + c.replace(/__[a-zA-Z0-9]{4,}$/, '')).join('');
    return el.tagName.toLowerCase() + cls;
  };
  const out = [];
  const walk = (el, path, parentStyle, depth) => {
    if (out.length >= 200 || depth > 12) return;
    const cs = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    if (cs.display === 'none' || cs.visibility === 'hidden' || (rect.width === 0 && rect.height === 0)) return;
    const styles = {};
    for (const p of KEEP) {
      const v = cs.getPropertyValue(p);
      if (!v || DEFAULTS.has(v) || SKIP[p] === v) continue;
      if (parentStyle && inherited.has(p) && parentStyle.getPropertyValue(p) === v) continue;
      if (p.endsWith('-color') && p.startsWith('border') && cs.getPropertyValue(p.replace('-color', '-width')) === '0px') continue;
      if (p.startsWith('outline') && cs.getPropertyValue('outline-style') === 'none') continue;
      styles[p] = v;
    }
    const text = [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).join(' ').slice(0, 60);
    const before = getComputedStyle(el, '::before').content;
    const after = getComputedStyle(el, '::after').content;
    out.push({
      path,
      figma: el.dataset.figmaNode || undefined,
      text: text || undefined,
      box: { x: r2(rect.left - base.left), y: r2(rect.top - base.top), w: r2(rect.width), h: r2(rect.height) },
      pseudo: [before, after].some((c) => c && c !== 'none') ? { before, after } : undefined,
      styles,
    });
    let i = 0;
    for (const child of el.children) walk(child, `${path} > ${label(child)}:${i++}`, cs, depth + 1);
  };
  walk(root, label(root), null, 0);
  return { url: location.href, viewport: `${innerWidth}x${innerHeight}`, dpr: devicePixelRatio, rootBox: { x: r2(base.left), y: r2(base.top), w: r2(base.width), h: r2(base.height) }, rootFontSize: getComputedStyle(document.documentElement).fontSize, count: out.length, truncated: out.length >= 200, nodes: out };
}
