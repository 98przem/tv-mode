(() => {
  'use strict';
  if (window.__tvModeNetflixFocus) return;
  const style = document.createElement('style');
  style.textContent = `
    .handleNext, .handlePrev, .slider-button, [class*="handleNext"], [class*="handlePrev"],
    [data-uia="carousel-hawkins-right-button"], [data-uia="carousel-hawkins-left-button"] { opacity: 0 !important; }
    .button-nfplayerBack, .button-nfplayerFullscreen, .nfplayer-back, .nfplayer-fullscreen,
    [data-uia="control-nav-back"],
    [data-uia="nfplayer-exit"], [data-uia*="fullscreen" i], [aria-label*="fullscreen" i],
    [aria-label*="full screen" i], [aria-label="Back" i], [aria-label="Wstecz" i] {
      display: none !important;
    }
    [data-tv-mode-focus="true"] {
      outline: 2px solid #ffffff !important;
      outline-offset: 3px !important;
      box-shadow: 0 0 0 4px rgba(20, 124, 255, 0.75), 0 0 12px rgba(20, 124, 255, 0.9) !important;
      border-radius: 6px !important;
    }
    [data-tv-mode-focus="true"][data-uia="timeline-knob"] {
      outline: 3px solid #ffffff !important;
      box-shadow: 0 0 0 5px rgba(20, 124, 255, 0.9), 0 0 14px rgba(20, 124, 255, 1) !important;
      border-radius: 50% !important;
    }
  `;
  document.documentElement.append(style);
  let selected = null;
  let playerMode = null;
  let carouselBusyUntil = 0;
  const selector = 'button:not([disabled]), [role="button"]:not([aria-disabled="true"]), [role="option"], [role="combobox"], a[href], .sub-menu-link, input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';
  const visible = element => {
    const style = getComputedStyle(element), box = element.getBoundingClientRect();
    return style.display !== 'none' && style.visibility !== 'hidden' && box.width > 8 && box.height > 8 && box.bottom > 0 && box.right > 0 && box.top < innerHeight && box.left < innerWidth;
  };
  const rendered = element => {
    const style = getComputedStyle(element), box = element.getBoundingClientRect();
    return style.display !== 'none' && style.visibility !== 'hidden' && box.width > 8 && box.height > 8;
  };
  const modalRoot = () => [...document.querySelectorAll(
    '[role="dialog"], [role="alertdialog"], [role="alert"], [aria-modal="true"], [role="menu"], ' +
    '.previewModal--container, .detail-modal, [data-uia*="modal"], [data-uia*="dialog"], ' +
    '[data-uia*="interrupter"], [data-uia*="error"], [data-uia*="alert"], [data-uia*="concurrency"], ' +
    '[data-uia^="selector-"], .track-list, .audio-subtitle-selector, .episode-selector, ' +
    '.interrupter-actions, .concurrency-interrupter, .nf-modal, .modal-container, .error-container, ' +
    '.watch-video--playback-error, .playback-error-overlay, [data-uia="playback-error"]'
  )].filter(visible).sort((a, b) => {
    const aa = a.getBoundingClientRect(), bb = b.getBoundingClientRect();
    return bb.width * bb.height - aa.width * aa.height;
  })[0] || null;
  const isHero = element => Boolean(
    element && (
      element.matches('[data-uia="play-video-button"], [data-uia="billboard-play-button"], [data-uia*="billboard-play"], [data-uia="billboard-more-info"], [data-uia*="billboard-info"], [data-uia*="billboard"], .billboard-row button, .billboard-row a.playLink') ||
      element.closest('[data-uia*="billboard"], .billboard, .billboard-row')
    )
  );
  const heroTargets = () => {
    if (modalRoot()) return [];
    return [...document.querySelectorAll(
      '[data-uia="play-video-button"], [data-uia="billboard-play-button"], [data-uia*="billboard-play"], [data-uia="billboard-more-info"], [data-uia*="billboard-info"], .billboard-row button, .billboard-row a.playLink'
    )].filter(visible);
  };
  const isLogo = element => Boolean(
    element.closest('.logo, .brand-logo, .netflix-logo') ||
    element.querySelector('.svg-icon-netflix-logo, [data-uia="netflix-logo"]')
  );
  const isCarouselArrow = element => Boolean(element.closest(
    '.handle, .handleNext, .handlePrev, .slider-button, [class*="handleNext"], [class*="handlePrev"], [data-uia*="carousel-next"], [data-uia*="carousel-prev"], [data-uia="carousel-hawkins-right-button"], [data-uia="carousel-hawkins-left-button"]'
  ));
  const isTopBar = element => {
    return element.matches('[data-uia^="nav-"], [data-uia^="navigation+"]') || Boolean(element.closest(
      'header, [role="navigation"], .main-header, .pinning-header, .tabbed-primary-navigation, .secondary-navigation'
    ));
  };
  const fullyVisibleHorizontally = element => {
    const box = element.getBoundingClientRect();
    return box.left >= 12 && box.right <= innerWidth - 12;
  };
  const targets = () => {
    const scope = modalRoot() || document;
    const all = [...scope.querySelectorAll(selector)].filter(element =>
      visible(element) && !isLogo(element) && !isCarouselArrow(element) && (scope !== document || !isTopBar(element))
    );
    return all.filter(element => !all.some(other =>
      other !== element && element.contains(other) && visible(other)
    ));
  };
  const cardSelector = '[data-uia$="-card"], .slider-item a, .slider-item [tabindex], .slider-item [role="button"], a.slider-refocus, .title-card a, .title-card-container a, .title-card-container [tabindex], [data-uia*="title-card"] a, [data-uia*="title-card"][tabindex]';
  const allCardTargets = () => modalRoot() ? [] : [...new Set(document.querySelectorAll(cardSelector))].filter(rendered);
  const cardTargets = () => allCardTargets().filter(visible);
  const navigationTargets = () => {
    if (modalRoot()) return [];
    const explicit = [...document.querySelectorAll(
      '[data-uia^="nav-"], .tabbed-primary-navigation a, .navigation-tab a, .secondary-navigation a, .main-header a[href^="/browse"], header a[href], [role="navigation"] a[href]'
    )].filter(element => visible(element) && !isLogo(element));
    const candidates = explicit.length ? explicit : [...document.querySelectorAll('a[href]')].filter(element => {
      if (!visible(element)) return false;
      const box = element.getBoundingClientRect();
      return box.top >= 0 && box.bottom <= 110 && !isLogo(element);
    });
    const seen = new Set();
    return candidates.filter(element => {
      const key = new URL(element.href, location.href).pathname;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };
  const topActionTargets = () => {
    if (modalRoot()) return [];
    const candidates = [...document.querySelectorAll(
      '[data-uia^="navigation+actions+"], [data-uia="navigation+profile-menu+trigger"], [data-uia="notification-bell"], header button, .main-header button'
    )].map(element => element.closest('button, a, [role="button"]') || element)
      .filter(element => visible(element) && !isLogo(element));
    return [...new Set(candidates)].filter(element => !candidates.some(other =>
      other !== element && element.contains(other)
    ));
  };
  const filterTargets = () => modalRoot() ? [] : [...document.querySelectorAll(
    'select:not([disabled]), [role="combobox"], .label[role="button"][aria-haspopup="true"], [aria-haspopup="listbox"]'
  )].filter(element => visible(element) && !isTopBar(element) && element.getBoundingClientRect().top >= 70);
  const inPlayer = () => location.pathname.startsWith('/watch/') || Boolean(document.querySelector('.watch-video'));
  const center = box => ({x: box.left + box.width / 2, y: box.top + box.height / 2});
  const initialTarget = all => {
    if (modalRoot()) {
      const retryBtn = all.find(e =>
        e.matches('[data-uia*="retry"], [data-uia*="action-retry"], [data-uia*="confirm"], [data-uia*="primary"]') ||
        /ponów|retry|spróbuj|ok|kontynuuj|dalej|tak|wznów/i.test(e.textContent || e.getAttribute('aria-label') || '')
      );
      if (retryBtn) return retryBtn;
      if (all.includes(document.activeElement)) return document.activeElement;
      return all[0];
    }
    const hero = all.find(element => element.matches(
      '[data-uia="play-video-button"], [data-uia="billboard-play-button"], [data-uia="billboard-more-info"]'
    ));
    if (hero) return hero;
    if (all.includes(document.activeElement)) return document.activeElement;
    const preferred = cardTargets()[0];
    if (preferred && all.includes(preferred)) return preferred;
    return all.find(element => element.getBoundingClientRect().top > 140) || all[0];
  };
  function select(element) {
    if (selected === element) return;
    document.querySelectorAll('[data-tv-mode-focus="true"]').forEach(item =>
      item.removeAttribute('data-tv-mode-focus')
    );
    selected = element;
    if (!selected) return;
    selected.setAttribute('data-tv-mode-focus', 'true');
    selected.focus({preventScroll: true});
    if (isHero(selected)) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      if (document.scrollingElement) {
        document.scrollingElement.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } else {
      const box = selected.getBoundingClientRect();
      selected.scrollIntoView({
        block: box.top < 0 || box.bottom > innerHeight ? 'center' : 'nearest',
        inline: box.left < 0 || box.right > innerWidth ? 'center' : 'nearest',
      });
    }
  }
  function move(direction, heldMs = 0) {
    if ((direction === 'ArrowLeft' || direction === 'ArrowRight') && seekPlayer(direction, heldMs)) return true;
    const topActions = topActionTargets();
    if (selected && topActions.includes(selected)) {
      if (direction === 'ArrowDown') {
        const heroes = heroTargets();
        if (heroes.length) {
          select(heroes[0]);
          return true;
        }
        const filters = filterTargets();
        select(filters[0] || initialTarget(targets()));
        return true;
      }
      if (direction === 'ArrowUp') return true;
      const change = direction === 'ArrowLeft' ? -1 : direction === 'ArrowRight' ? 1 : 0;
      if (!change) return true;
      const index = topActions.indexOf(selected);
      select(topActions[(index + change + topActions.length) % topActions.length]);
      return true;
    }
    const all = targets();
    if (!all.length) return false;
    if (!selected || !all.includes(selected)) { select(initialTarget(all)); return true; }
    const navigation = navigationTargets();
    if (navigation.includes(selected)) {
      if (direction === 'ArrowDown') { select(initialTarget(all.filter(item => !navigation.includes(item)))); return true; }
      return false;
    }
    const cards = allCardTargets();
    const selectedIsCard = cards.includes(selected) || Boolean(selected.closest(
      '[data-uia$="-card"], .slider-item, .title-card, .title-card-container, [data-uia*="title-card"]'
    ));
    const pool = selectedIsCard ? cards : all.filter(item => !navigation.includes(item));
    const from = selected.getBoundingClientRect();
    const origin = center(from);
    const horizontal = direction === 'ArrowLeft' || direction === 'ArrowRight';
    const sign = direction === 'ArrowLeft' || direction === 'ArrowUp' ? -1 : 1;
    if (selected.matches('select')) {
      const next = Math.max(0, Math.min(selected.options.length - 1, selected.selectedIndex + sign));
      if (next !== selected.selectedIndex) {
        selected.selectedIndex = next;
        selected.dispatchEvent(new Event('input', {bubbles: true}));
        selected.dispatchEvent(new Event('change', {bubbles: true}));
      }
      return true;
    }
    if (horizontal) {
      if (performance.now() < carouselBusyUntil) return true;
      if (selectedIsCard) {
        const carousel = selected.closest('[data-uia="carousel-scroller"], [data-uia^="carousel-row-section"], .carousel-row, .lolomoRow, .rowContainer, .slider');
        const rowCards = carousel ? [...carousel.querySelectorAll(cardSelector)].filter(rendered) : [];
        const currentIndex = rowCards.indexOf(selected);
        const nextCard = currentIndex >= 0 ? rowCards[currentIndex + sign] : null;
        if (!nextCard) return true;
        if (fullyVisibleHorizontally(nextCard)) { select(nextCard); return true; }
        return advanceCarousel(sign, origin.y, nextCard);
      }
      const row = pool.filter(item => {
        if (item === selected) return false;
        const point = center(item.getBoundingClientRect());
        return sign * (point.x - origin.x) > 6 && Math.abs(point.y - origin.y) < Math.max(70, from.height * 0.55);
      });
      row.sort((a, b) => {
        const aa = center(a.getBoundingClientRect()), bb = center(b.getBoundingClientRect());
        return Math.abs(aa.x - origin.x) - Math.abs(bb.x - origin.x) || Math.abs(aa.y - origin.y) - Math.abs(bb.y - origin.y);
      });
      if (row[0] && (modalRoot() || fullyVisibleHorizontally(row[0]))) { select(row[0]); return true; }
      return false;
    }
    const candidates = pool.map(item => ({item, point: center(item.getBoundingClientRect())}))
      .filter(candidate => candidate.item !== selected && sign * (candidate.point.y - origin.y) > 12);
    if (candidates.length) {
      const nearestY = Math.min(...candidates.map(candidate => Math.abs(candidate.point.y - origin.y)));
      const nextRow = candidates.filter(candidate => Math.abs(candidate.point.y - origin.y) <= nearestY + 70);
      nextRow.sort((a, b) => Math.abs(a.point.x - origin.x) - Math.abs(b.point.x - origin.x));
      select(nextRow[0].item);
      return true;
    }
    if (selectedIsCard && sign < 0) {
      const heroes = heroTargets();
      if (heroes.length) {
        heroes.sort((a, b) => Math.abs(center(a.getBoundingClientRect()).x - origin.x) - Math.abs(center(b.getBoundingClientRect()).x - origin.x));
        select(heroes[0]);
        return true;
      }
      const upper = filterTargets().length ? filterTargets() : topActions;
      if (upper.length) {
        upper.sort((a, b) => Math.abs(center(a.getBoundingClientRect()).x - origin.x) - Math.abs(center(b.getBoundingClientRect()).x - origin.x));
        select(upper[0]);
      }
      return true;
    }
    if (isHero(selected) && sign < 0) {
      const upper = filterTargets().length ? filterTargets() : topActions;
      if (upper.length) {
        upper.sort((a, b) => Math.abs(center(a.getBoundingClientRect()).x - origin.x) - Math.abs(center(b.getBoundingClientRect()).x - origin.x));
        select(upper[0]);
      }
      return true;
    }
    if (selectedIsCard) return scrollCards(sign, origin.x);
    return false;
  }
  function advanceCarousel(change, preferredY, nextCard) {
    const row = selected.closest('[data-uia="carousel-scroller"], [data-uia^="carousel-row-section"], .carousel-row, .lolomoRow, .rowContainer, .slider') || document;
    const selector = change > 0
      ? '[data-uia="carousel-hawkins-right-button"], .handleNext, [class*="handleNext"], [data-uia*="carousel-next"], button[aria-label="Next"]'
      : '[data-uia="carousel-hawkins-left-button"], .handlePrev, [class*="handlePrev"], [data-uia*="carousel-prev"], button[aria-label="Previous"]';
    let control = [...row.querySelectorAll(selector)].find(visible);
    if (!control) control = [...document.querySelectorAll(selector)].find(element => {
      if (!visible(element)) return false;
      const point = center(element.getBoundingClientRect());
      return Math.abs(point.y - preferredY) < 120;
    });
    if (!control) return false;
    carouselBusyUntil = performance.now() + 750;
    control.click();
    setTimeout(() => {
      if (nextCard && rendered(nextCard)) { select(nextCard); return; }
      const cards = cardTargets().filter(card => {
        const point = center(card.getBoundingClientRect());
        return Math.abs(point.y - preferredY) < 120;
      });
      cards.sort((a, b) => change > 0
        ? a.getBoundingClientRect().left - b.getBoundingClientRect().left
        : b.getBoundingClientRect().right - a.getBoundingClientRect().right);
      if (cards[0]) select(cards[0]);
    }, 700);
    return true;
  }
  function moveSection(change) {
    const sections = navigationTargets();
    if (!sections.length) return false;
    let current = sections.indexOf(selected);
    if (current < 0) current = sections.findIndex(element =>
      element.getAttribute('aria-current') === 'page' ||
      element.closest('.active, .current, .navigation-tab-active') ||
      new URL(element.href, location.href).pathname === location.pathname
    );
    const index = current < 0 ? (change > 0 ? -1 : 0) : current;
    const next = sections[(index + change + sections.length) % sections.length];
    select(next);
    setTimeout(() => next.click(), 80);
    return true;
  }
  function scrollCards(change, preferredX) {
    const scrolling = document.scrollingElement || document.documentElement;
    const before = scrolling.scrollTop;
    window.scrollBy({top: change * Math.round(innerHeight * 0.76), behavior: 'smooth'});
    setTimeout(() => {
      const cards = cardTargets();
      if (!cards.length) return;
      cards.sort((a, b) => {
        const aa = center(a.getBoundingClientRect()), bb = center(b.getBoundingClientRect());
        const targetY = change > 0 ? innerHeight * 0.68 : innerHeight * 0.32;
        return Math.abs(aa.x - preferredX) + Math.abs(aa.y - targetY) * 0.45
          - Math.abs(bb.x - preferredX) - Math.abs(bb.y - targetY) * 0.45;
      });
      if (scrolling.scrollTop !== before) select(cards[0]);
    }, 340);
    return true;
  }
  function activate() {
    if (modalRoot()) {
      const all = targets();
      if (!selected || !all.includes(selected)) {
        select(initialTarget(all));
      }
      if (selected) {
        selected.click();
        try {
          selected.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
        } catch (_) {}
        return true;
      }
      return false;
    }
    const active = document.activeElement;
    const profileTile = [selected, active].find(element =>
      element?.matches?.('[data-uia^="profile-selector+tile-"]')
    );
    if (profileTile) {
      select(profileTile);
      return 'Space';
    }
    const topActions = topActionTargets();
    if (selected && topActions.includes(selected)) {
      selected.click();
      return true;
    }
    const all = targets();
    if (!selected || !all.includes(selected)) select(all[0]);
    if (!selected) return false;
    selected.click();
    return true;
  }
  function back() {
    const modal = modalRoot();
    if (modal) {
      const closeBtn = modal.querySelector(
        '[data-uia*="close"], [aria-label*="Close" i], [aria-label*="Zamknij" i], button.close, .modal-close'
      );
      if (closeBtn && visible(closeBtn)) {
        closeBtn.click();
        return true;
      }
      return 'b';
    }
    const notification = document.querySelector('[data-uia="notification-bell"][aria-expanded="true"]');
    if (notification) return 'b';
    const profileMenu = document.querySelector('[data-uia="navigation+profile-menu+trigger"][aria-expanded="true"]');
    if (profileMenu) return 'b';
    const searchInput = [...document.querySelectorAll(
      '[data-uia*="search"] input, input[type="search"], input[placeholder*="Search"], input[placeholder*="Szukaj"]'
    )].find(visible);
    if (searchInput) return 'b';
    if (inPlayer()) {
      return 'PlayerBack';
    }
    const candidates = [
      '[data-uia="player-back-button"]', '.button-nfplayerBack',
      '[data-uia="previewModal-closebtn"]', '.previewModal--close',
      'button[aria-label="Back"]', 'button[aria-label="Close"]',
    ];
    for (const candidate of candidates) {
      const element = document.querySelector(candidate);
      if (element && visible(element)) { element.click(); return true; }
    }
    return false;
  }
  const playerPlayButton = () => {
    const candidates = [
      '[data-uia="control-play-pause"]',
      '[data-uia*="play-pause"]',
      '[data-uia*="player-play"]',
      '[data-uia*="play-button"]',
      'button[aria-label*="Play" i]',
      'button[aria-label*="Odtwórz" i]',
      'button[data-uia*="play" i]',
      '[role="button"][aria-label*="Play" i]',
      '[role="button"][aria-label*="Odtwórz" i]',
      '.button-nfplayerPlay',
      '.nf-big-play',
      '.play-button',
      'button.play',
    ];
    for (const sel of candidates) {
      const el = document.querySelector(sel);
      if (el && visible(el)) return el;
    }
    return null;
  };
  const playerTimeline = () => {
    const element = document.querySelector(
      '[data-uia="timeline-knob"], [role="slider"][data-uia*="timeline"], [role="slider"]'
    );
    return element && visible(element) ? element : null;
  };
  const playerTimelineTrack = () => {
    const element = document.querySelector('[data-uia="timeline"]');
    return element && visible(element) ? element : null;
  };
  const playerControls = () => {
    if (!inPlayer()) return [];
    const selectors = [
      '[data-uia^="control-play-pause"]',
      '[data-uia="control-back10"]',
      '[data-uia="control-forward10"]',
      '[data-uia="control-volume-high"]',
      '[data-uia="control-volume-low"]',
      '[data-uia="control-volume-muted"]',
      '[data-uia="control-next"]',
      '[data-uia="control-episodes"]',
      '[data-uia="control-audio-subtitle"]',
      '[data-uia="control-speed"]',
    ];
    const explicit = selectors.flatMap(selector => [...document.querySelectorAll(selector)]);
    const generic = [...document.querySelectorAll(
      '.watch-video button, .watch-video [role="button"], .PlayerControlsNeo button, .PlayerControlsNeo [role="button"]'
    )];
    const controls = [...explicit, ...generic]
      .map(element => element.closest('button, [role="button"]') || element)
      .filter((element, index, all) => {
        if (!visible(element) || all.indexOf(element) !== index) return false;
        const uia = element.getAttribute('data-uia') || '';
        const label = element.getAttribute('aria-label') || element.textContent || '';
        return !/nav-back|fullscreen|full screen|player-back|control-back(?!10)|\bback\b|\bwstecz\b/i.test(`${uia} ${label}`);
      });
    return controls;
  };
  const playerTarget = () => {
    const timeline = playerTimeline();
    const controls = playerControls();
    if (timeline && (selected === timeline || playerMode === 'timeline')) return timeline;
    if (selected && controls.includes(selected)) return selected;
    const play = playerPlayButton();
    return play || controls[0] || timeline;
  };
  function movePlayer(direction) {
    const timeline = playerTimeline();
    const controls = playerControls();
    if (!timeline && !controls.length) return false;
    const current = playerTarget();
    if (direction === 'ArrowUp') {
      if (current !== timeline && timeline) {
        playerMode = 'timeline';
        select(timeline);
        return true;
      }
      if (current === timeline && controls.length) {
        playerMode = 'controls';
        select(playerPlayButton() || controls[0]);
        return true;
      }
      return true;
    }
    if (direction === 'ArrowDown') {
      if (current === timeline) {
        playerMode = 'controls';
        select(playerPlayButton() || controls[0]);
        return true;
      }
      if (controls.length) {
        const index = controls.indexOf(current);
        if (index >= 0) {
          playerMode = 'controls';
          select(controls[index]);
          return true;
        }
      }
      return true;
    }
    if (direction !== 'ArrowLeft' && direction !== 'ArrowRight') return false;
    if (current === timeline) {
      select(timeline);
      return direction === 'ArrowLeft' ? 'TimelineLeft' : 'TimelineRight';
    }
    if (!controls.length) return true;
    let index = controls.indexOf(current);
    if (index < 0) index = 0;
    index += direction === 'ArrowLeft' ? -1 : 1;
    index = (index + controls.length) % controls.length;
    playerMode = 'controls';
    select(controls[index]);
    return true;
  }
  function activatePlayer() {
    const timeline = playerTimeline();
    const current = playerTarget();
    if (timeline && current === timeline) {
      playerMode = 'timeline';
      const video = document.querySelector('video');
      return video && !video.paused ? 'PlayerPause' : true;
    }
    if (!current) return false;
    if (current.matches('[data-uia="player-blocked-play"]')) return 'PlayButton';
    current.click();
    try {
      current.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    } catch (_) {}
    return true;
  }
  function seekPlayer(direction, heldMs = 0) {
    if (!inPlayer()) return false;
    const result = movePlayer(direction);
    if (result !== 'TimelineLeft' && result !== 'TimelineRight') return result;
    const timeline = playerTimeline();
    const track = playerTimelineTrack();
    const video = document.querySelector('video');
    if (!timeline || !track || !video || !Number.isFinite(video.duration) || video.duration <= 0) return result;
    const box = track.getBoundingClientRect();
    const step = heldMs >= 2500 ? 15 : heldMs >= 1200 ? 10 : 5;
    const change = result === 'TimelineLeft' ? -step : step;
    const target = Math.max(0, Math.min(video.duration, video.currentTime + change));
    return `TimelineClick:${box.left + box.width * target / video.duration}:${box.top + box.height / 2}`;
  }
  const direction = {up: 'ArrowUp', down: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight'};
  window.__tvModeNetflixFocus = {
    handle(action, heldMs = 0) {
      const modal = modalRoot();
      if (modal) {
        if (direction[action]) return move(direction[action], heldMs);
        if (action === 'a') return activate();
        if (action === 'b') return back();
        return false;
      }
      if (inPlayer()) {
        if (action === 'a') return activatePlayer();
        if (action === 'up' || action === 'down' || action === 'left' || action === 'right') {
          return seekPlayer(direction[action], heldMs);
        }
        if (action === 'x') return 'KeyM';
        if (action === 'lb' || action === 'rb') return true;
        if (action === 'b') return back();
      }
      if (direction[action]) return move(direction[action], heldMs);
      if (action === 'a') return activate();
      if (action === 'lb') return moveSection(-1);
      if (action === 'rb') return moveSection(1);
      if (action === 'b') return back();
      return false;
    },
  };
})();
