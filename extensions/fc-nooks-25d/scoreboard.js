(() => {
  'use strict';
  const api = globalThis.FCN25D;
  const empty = () => ({ home: 'HOME', away: 'AWAY', score: '—', clock: 'AWAITING MFL', found: false });
  const clean = el => (el?.innerText || el?.textContent || '').trim().replace(/\s+/g, ' ');
  function readScoreboard() {
    const containers = [...document.querySelectorAll('header,nav,[class*="score"],[class*="Score"],[class*="header"],[class*="Header"],[data-testid*="score"]')]
      .filter(el => !el.closest('[data-fcn25d]'));
    const nodes = [...new Set(containers.flatMap(el => [el, ...[...el.querySelectorAll('span,strong,div')].slice(0,50)]))];
    let result = null, shortest = Infinity;
    for (const el of nodes) {
      const text = clean(el);
      if (text.length > 180 || text.length < 7) continue;
      // Preserve v1.5's abbreviation pattern; allow a full-name header as fallback.
      const m = text.match(/^(?:(\d{1,3}:\d{2}(?:\s*\+\s*\d{1,2})?)\s+)?([A-Z][A-Z0-9]{1,7})\s+(\d{1,2})\s*[-–:]\s*(\d{1,2})\s+([A-Z][A-Z0-9]{1,7})(?:\s+(\d{1,3}:\d{2}))?$/)
        || text.match(/^(?:(\d{1,3}:\d{2})\s+)?([\p{L}][\p{L}\p{N} .&'’-]{1,45}?)\s+(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([\p{L}][\p{L}\p{N} .&'’-]{1,45}?)(?:\s+(\d{1,3}:\d{2}))?$/u);
      if (m && text.length < shortest) { shortest = text.length; result = { home:m[2], away:m[5], score:`${m[3]} – ${m[4]}`, clock:m[1] || m[6] || '', found:true }; }
    }
    if (!result) return empty();
    if (!result.clock) {
      const clocks = [...document.querySelectorAll('[data-testid*="clock"],[data-testid*="timer"],[class*="clock"],[class*="Clock"],[class*="timer"],[class*="Timer"]'), ...nodes];
      const clock = clocks.filter(el => !el.closest('[data-fcn25d]')).map(clean).find(t => /^(?:\d{1,3}:\d{2}(?:\s*\+\s*\d{1,2})?|HT|FT|HALF TIME|FULL TIME)$/.test(t));
      result.clock = clock || 'CLOCK UNAVAILABLE';
    }
    return result;
  }
  api.readScoreboard = readScoreboard;
  api.emptyScoreboard = empty;
})();
