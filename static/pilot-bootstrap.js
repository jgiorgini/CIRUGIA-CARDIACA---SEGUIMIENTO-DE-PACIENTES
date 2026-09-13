(() => {
  const PILOT_VERSION = 'RCV-V1.0-PILOT-001';
  document.title = PILOT_VERSION;

  function patchVersionLabels() {
    document.querySelectorAll('.version').forEach(el => {
      const txt = el.textContent || '';
      if (txt.includes('RCV-V1.0-LOCAL-004')) {
        el.textContent = txt
          .replace('RCV-V1.0-LOCAL-004', PILOT_VERSION)
          .replace('datos locales SQLite', 'backend central');
      }
    });
  }

  patchVersionLabels();
  const obs = new MutationObserver(patchVersionLabels);
  obs.observe(document.documentElement, {subtree: true, childList: true});
})();
