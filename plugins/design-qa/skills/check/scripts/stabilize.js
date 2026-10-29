async () => {
  if (!document.getElementById('design-qa-freeze')) {
    const style = document.createElement('style');
    style.id = 'design-qa-freeze';
    style.textContent = '*,*::before,*::after{animation-duration:0s!important;animation-delay:0s!important;transition:none!important;caret-color:transparent!important;scroll-behavior:auto!important}';
    document.head.appendChild(style);
  }
  await document.fonts.ready;
  await Promise.all([...document.images].filter((img) => !img.complete).map((img) => img.decode().catch(() => {})));
  await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  const fonts = [...document.fonts];
  const name = (f) => `${f.family.replace(/"/g, '')} ${f.weight} ${f.style}`;
  return {
    viewport: `${innerWidth}x${innerHeight}`,
    dpr: devicePixelRatio,
    fontsLoaded: [...new Set(fonts.filter((f) => f.status === 'loaded').map(name))],
    fontsFailed: [...new Set(fonts.filter((f) => f.status === 'error').map(name))],
    brokenImages: [...document.images].filter((img) => img.complete && !img.naturalWidth).map((img) => img.currentSrc || img.src),
  };
}
