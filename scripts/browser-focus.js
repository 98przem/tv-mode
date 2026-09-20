(() => {
  'use strict';
  if (window.__tvModeBrowserFocus) return;
  const style = document.createElement('style');
  style.textContent = `
    [data-tv-mode-focus="true"] {
      outline: 4px solid #ffffff !important;
      outline-offset: 5px !important;
      box-shadow: 0 0 0 8px rgba(20, 124, 255, 0.75), 0 0 22px rgba(20, 124, 255, 0.9) !important;
      border-radius: 6px !important;
    }
  `;
  document.documentElement.append(style);
  let selected = null;
  const visible = element => {
    const style = getComputedStyle(element), box = element.getBoundingClientRect();
    return style.display !== 'none' && style.visibility !== 'hidden' &&
      box.width > 8 && box.height > 8 && box.bottom > 0 && box.right > 0 &&
      box.top < innerHeight && box.left < innerWidth;
  };
  const selector = 'button:not([disabled]), a[href], [role="button"], [role="link"], ' +
    '[role="option"], [role="menuitem"], input:not([disabled]), textarea:not([disabled]), ' +
    'select:not([disabled]), [contenteditable="true"]';
  const all = () => [...document.querySelectorAll(selector)].filter(visible);
  const modal = () => [...document.querySelectorAll(
    '[role="dialog"], [role="alertdialog"], [aria-modal="true"], [id*="cookie" i], ' +
    '[class*="cookie" i], [class*="consent" i], [data-testid*="cookie" i], ' +
    'iframe[src*="commerce" i], iframe[title*="sign" i], iframe[title*="login" i]'
  )].filter(visible).sort((a, b) => {
    const aa = a.getBoundingClientRect(), bb = b.getBoundingClientRect();
    return bb.width * bb.height - aa.width * aa.height;
  })[0] || null;
  const scoped = () => {
    const root = modal();
    if (!root) return all();
    const items = [...root.querySelectorAll(selector)].filter(visible);
    return items.length ? items : [root];
  };
  const text = element => `${element.textContent || ''} ${element.getAttribute('aria-label') || ''}`;
  const initial = items => items.find(item =>
    /sign in|log in|zaloguj/i.test(text(item))
  ) || items.find(item => item.matches('input, textarea, [contenteditable="true"]')) ||
    items.find(item =>
      /accept|agree|allow|consent|continue|ok|zaakceptuj|zgadzam|zezwól|kontynuuj|dalej/i.test(text(item))
    ) ||
    items.find(item => item.matches('button, [role="button"]')) || items[0];
  const focusResult = () => {
    if (!selected) return true;
    if (selected.matches('input, textarea, iframe, [contenteditable="true"]')) {
      const box = selected.getBoundingClientRect();
      return `InputFocus:${box.x},${box.y},${box.width},${box.height}`;
    }
    return true;
  };
  const select = element => {
    if (!element) return;
    document.querySelectorAll('[data-tv-mode-focus="true"]').forEach(item =>
      item.removeAttribute('data-tv-mode-focus')
    );
    selected = element;
    selected.setAttribute('data-tv-mode-focus', 'true');
    selected.focus({preventScroll: true});
    selected.scrollIntoView({block: 'nearest', inline: 'nearest'});
  };
  const activate = () => {
    const items = scoped();
    if (!selected || !items.includes(selected)) select(initial(items));
    if (!selected) return false;
    selected.click();
    setTimeout(() => {
      const root = modal();
      if (root) select(root);
    }, 80);
    return true;
  };
  const back = () => {
    const root = modal();
    if (root) {
      const close = [...root.querySelectorAll('button, [role="button"]')].find(item =>
        visible(item) && /close|cancel|reject|zamknij|anuluj|odrzuć/i.test(text(item))
      );
      if (close) { close.click(); return true; }
    }
    history.back();
    return true;
  };
  const move = action => {
    const items = scoped();
    if (!items.length) return false;
    if (!selected || !items.includes(selected)) { select(initial(items)); return true; }
    const from = selected.getBoundingClientRect();
    const horizontal = action === 'left' || action === 'right';
    const sign = action === 'left' || action === 'up' ? -1 : 1;
    const candidates = items.filter(item => {
      if (item === selected) return false;
      const box = item.getBoundingClientRect();
      const dx = box.left + box.width / 2 - (from.left + from.width / 2);
      const dy = box.top + box.height / 2 - (from.top + from.height / 2);
      return sign * (horizontal ? dx : dy) > 8 &&
        Math.abs(horizontal ? dy : dx) < (horizontal ? Math.max(80, from.height) : Math.max(140, from.width));
    });
    candidates.sort((a, b) => {
      const aa = a.getBoundingClientRect(), bb = b.getBoundingClientRect();
      const ax = Math.abs((aa.left + aa.width / 2) - (from.left + from.width / 2));
      const ay = Math.abs((aa.top + aa.height / 2) - (from.top + from.height / 2));
      const bx = Math.abs((bb.left + bb.width / 2) - (from.left + from.width / 2));
      const by = Math.abs((bb.top + bb.height / 2) - (from.top + from.height / 2));
      return (horizontal ? ax + ay * 0.5 : ay + ax * 0.5) -
        (horizontal ? bx + by * 0.5 : by + bx * 0.5);
    });
    if (candidates[0]) select(candidates[0]);
    return true;
  };
  window.__tvModeBrowserFocus = {
    handle(action) {
      if (action === 'a') return activate();
      if (action === 'b') return back();
      if (['up', 'down', 'left', 'right'].includes(action)) {
        move(action);
        return focusResult();
      }
      return true;
    },
  };
})();
