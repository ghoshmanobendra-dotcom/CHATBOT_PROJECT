/**
 * scroll-locked-video-hero.js
 * ─────────────────────────────────────────────────────────────
 * Vanilla JS port of the MetroHero React component by
 * guglielmogiannattasio.exe, customised for GCECT IT Dept.
 *
 * Usage — drop one <div id="metro-hero-mount"></div> on your
 * page and then call:
 *
 *   import { mountMetroHero } from './components/ui/scroll-locked-video-hero.js';
 *   mountMetroHero('#metro-hero-mount', {
 *     videoSrc:      'https://…',
 *     title:         'KNOWLEDGE OPENS',
 *     tagline:       'Every answer about GCECT is within reach.',
 *     taglineSub:    'AI-powered · 53+ topics · Subjects, Faculty, Fees…',
 *     ctaHref:       '/landing',
 *     ctaLabel:      'Enter the Assistant',
 *     scrubDistance: 3200,
 *     exitThreshold: 320,
 *   });
 *
 * The mount element becomes a full-viewport hero. Body is pinned
 * with position:fixed (same technique modal libraries use) while
 * the hero is active. Wheel / touch input drives video.currentTime.
 * After the video ends + extra scroll input, the page is unlocked
 * and the browser navigates to ctaHref.
 * ─────────────────────────────────────────────────────────────
 */

const DEFAULT_VIDEO = "https://cdn.21st.dev/assets/mirror/21/21a77eac28eacbb7e142016eefeaa0b4a766619e51113629a3bc6df6af066c0f.mp4";

/** @param {number} v @param {number} min @param {number} max */
function clamp(v, min, max) { return Math.min(max, Math.max(min, v)); }

/**
 * @param {string|HTMLElement} selector
 * @param {Partial<MetroHeroOptions>} [opts]
 */
export function mountMetroHero(selector, opts = {}) {
  const container = typeof selector === 'string'
    ? document.querySelector(selector)
    : selector;
  if (!container) throw new Error(`[MetroHero] Mount target not found: ${selector}`);

  const {
    videoSrc      = DEFAULT_VIDEO,
    title         = 'KNOWLEDGE OPENS',
    tagline       = 'Every answer about GCECT is already within reach.',
    taglineSub    = 'AI-powered · 53+ topics · Subjects, Faculty, Fees, Placements & more',
    ctaHref       = '/landing',
    ctaLabel      = 'Enter the Assistant',
    scrubDistance = 3200,
    exitThreshold = 320,
    badgeName     = 'GCECT IT',
    badgeSub      = 'Dept. of Information Technology',
    signature     = { label: 'adapted from guglielmogiannattasio.exe', url: 'https://www.guglielmogiannattasio.it' },
  } = opts;

  // ── Inject styles once ──────────────────────────────────────
  if (!document.getElementById('metro-hero-styles')) {
    const style = document.createElement('style');
    style.id = 'metro-hero-styles';
    style.textContent = `
      .mh-root {
        position: relative; height: 100dvh; width: 100%;
        overflow: hidden; background: #05070d; touch-action: none;
        --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      }
      .mh-video {
        position: absolute; inset: 0; width: 100%; height: 100%;
        object-fit: cover; opacity: 0; transform-origin: center;
        will-change: transform; transition: opacity .6s ease;
        touch-action: none; pointer-events: none;
      }
      .mh-video.ready { opacity: 1; }
      .mh-overlay {
        position: absolute; inset: 0; pointer-events: none;
        background: linear-gradient(180deg,
          rgba(5,7,13,.38)  0%,  rgba(5,7,13,0)    30%,
          rgba(5,7,13,.12)  70%, rgba(5,7,13,.6)   100%);
      }
      .mh-badge {
        position: absolute; top: clamp(14px,2.5vw,26px); left: clamp(14px,2.5vw,26px);
        display: flex; align-items: center; gap: 10px;
        background: rgba(8,11,24,.65); backdrop-filter: blur(14px);
        border: 1px solid rgba(91,127,255,.28); border-radius: 12px;
        padding: 9px 14px; z-index: 5;
      }
      .mh-badge-orb {
        width: 26px; height: 26px; border-radius: 7px; flex-shrink: 0;
        background: linear-gradient(135deg, #5b7fff, #8b5cf6);
      }
      .mh-badge-name { font-family: var(--sans); font-weight: 700; font-size: 12.5px; color: #f2f4f8; }
      .mh-badge-sub  { font-family: var(--sans); font-size: 10px; color: rgba(190,200,230,.6); font-weight: 500; }
      .mh-title {
        position: absolute; inset: 0; display: flex; align-items: center;
        justify-content: center; padding: 0 6%; text-align: center;
        pointer-events: none; will-change: transform, filter, opacity;
      }
      .mh-title span {
        font-family: var(--sans); font-weight: 800;
        font-size: clamp(28px, 6.8vw, 92px); line-height: 1;
        letter-spacing: -.025em; color: #f2f4f8;
        text-shadow: 0 4px 30px rgba(0,0,0,.55); display: inline-block;
      }
      .mh-tagline {
        position: absolute; inset: 0; display: flex; flex-direction: column;
        align-items: center; justify-content: center; gap: 18px;
        padding: 0 8%; text-align: center; opacity: 0;
        will-change: transform, filter, opacity;
      }
      .mh-tagline-main {
        font-family: var(--sans); font-weight: 700;
        font-size: clamp(20px, 3.2vw, 42px); line-height: 1.2;
        letter-spacing: -.015em; color: #f2f4f8;
        text-shadow: 0 4px 24px rgba(0,0,0,.55); pointer-events: none;
      }
      .mh-tagline-sub {
        font-family: var(--sans); font-size: clamp(12px, 1.5vw, 18px);
        color: rgba(210,224,248,.65); font-weight: 500; pointer-events: none;
      }
      .mh-cta {
        display: inline-flex; align-items: center; gap: 10px;
        padding: 13px 30px; margin-top: 10px;
        background: linear-gradient(135deg, #5b7fff, #8b5cf6);
        border-radius: 13px; color: #fff; font-family: var(--sans);
        font-weight: 700; font-size: clamp(13px, 1.5vw, 17px);
        letter-spacing: .01em; text-decoration: none;
        box-shadow: 0 6px 26px rgba(91,127,255,.45);
        transition: transform .2s, box-shadow .2s; cursor: pointer;
      }
      .mh-cta:hover { transform: translateY(-2px); box-shadow: 0 10px 36px rgba(91,127,255,.55); }
      .mh-cta svg { width: 18px; height: 18px; }
      .mh-hint {
        position: absolute; left: 50%; bottom: clamp(20px, 6vh, 48px);
        transform: translateX(-50%); display: flex; flex-direction: column;
        align-items: center; gap: 8px; color: rgba(240,244,248,.72);
        font-family: var(--sans); font-size: clamp(10px,1.3vw,12px);
        font-weight: 600; letter-spacing: .3em;
        transition: opacity .4s ease; pointer-events: none;
      }
      @keyframes mh-bounce { 0%,100%{transform:translateY(0);opacity:.5} 50%{transform:translateY(6px);opacity:1} }
      .mh-hint svg { animation: mh-bounce 1.6s ease-in-out infinite; }
      .mh-progress-track {
        position: absolute; left: 0; right: 0; bottom: 0;
        height: 2px; background: rgba(255,255,255,.1);
      }
      .mh-progress-fill {
        height: 100%; width: 100%;
        background: linear-gradient(90deg, rgba(255,255,255,.45), rgba(255,255,255,.95));
        transform: scaleX(0); transform-origin: left center; will-change: transform;
      }
      .mh-sig {
        position: absolute; right: clamp(12px,2.5vw,22px); bottom: clamp(10px,2vw,18px);
        font-family: var(--sans); font-size: clamp(10px,1.2vw,12px);
        font-weight: 500; letter-spacing: .01em; color: rgba(210,218,238,.5); z-index: 5;
      }
      .mh-sig a { color: inherit; text-decoration: none; transition: color .2s; }
      .mh-sig a:hover { color: #f2f4f8; }
      .mh-loader {
        position: absolute; inset: 0; display: flex; align-items: center;
        justify-content: center; pointer-events: none; z-index: 10;
        transition: opacity .5s ease;
      }
      .mh-loader.hidden { opacity: 0; }
      .mh-loader-ring {
        width: 40px; height: 40px;
        border: 2px solid rgba(255,255,255,.1);
        border-top-color: rgba(91,127,255,.8);
        border-radius: 50%; animation: mh-spin .8s linear infinite;
      }
      @keyframes mh-spin { to { transform: rotate(360deg); } }
    `;
    document.head.appendChild(style);
  }

  // ── Build DOM ────────────────────────────────────────────────
  container.innerHTML = `
    <div class="mh-root" id="mh-root">
      <div class="mh-loader" id="mh-loader"><div class="mh-loader-ring"></div></div>
      <video class="mh-video" id="mh-video" src="${videoSrc}" muted playsinline preload="auto"></video>
      <div class="mh-overlay"></div>
      <div class="mh-badge">
        <div class="mh-badge-orb"></div>
        <div>
          <div class="mh-badge-name">${badgeName}</div>
          <div class="mh-badge-sub">${badgeSub}</div>
        </div>
      </div>
      <div class="mh-title" id="mh-title"><span>${title}</span></div>
      <div class="mh-tagline" id="mh-tagline">
        <span class="mh-tagline-main">${tagline}</span>
        <span class="mh-tagline-sub">${taglineSub}</span>
        <a href="${ctaHref}" class="mh-cta" id="mh-cta">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          ${ctaLabel}
        </a>
      </div>
      <div class="mh-hint" id="mh-hint">
        <span>SCROLL</span>
        <svg width="14" height="18" viewBox="0 0 14 18" fill="none">
          <path d="M7 1L7 17M2 12L7 17L12 12" stroke="currentColor" stroke-width="1.5"
                stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div class="mh-progress-track"><div class="mh-progress-fill" id="mh-fill"></div></div>
      ${signature ? `<div class="mh-sig">adapted from <a href="${signature.url}" target="_blank" rel="noopener">${signature.label}</a></div>` : ''}
    </div>
  `;

  // ── Refs ─────────────────────────────────────────────────────
  const root      = document.getElementById('mh-root');
  const vid       = document.getElementById('mh-video');
  const titleEl   = document.getElementById('mh-title');
  const taglineEl = document.getElementById('mh-tagline');
  const hintEl    = document.getElementById('mh-hint');
  const fillEl    = document.getElementById('mh-fill');
  const loaderEl  = document.getElementById('mh-loader');
  const ctaEl     = document.getElementById('mh-cta');

  // ── State ─────────────────────────────────────────────────────
  let duration           = 0;
  let targetProgress     = 0;
  let currentProgress    = 0;
  let rafId              = 0;
  let hasStarted         = false;
  let isSeeking          = false;
  let pendingTime        = null;
  let locked             = false;
  let lockedScrollY      = 0;
  let touchStartY        = 0;
  let overflowAccum      = 0;
  let exiting            = false;

  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  // ── Lock / unlock ─────────────────────────────────────────────
  function engageLock() {
    if (locked) return; locked = true;
    lockedScrollY = window.scrollY;
    Object.assign(document.body.style, {
      position: 'fixed', top: `-${lockedScrollY}px`,
      left: '0', right: '0', width: '100%', height: '100%',
      overscrollBehavior: 'none',
    });
  }
  function releaseLock() {
    if (!locked) return; locked = false;
    const y = lockedScrollY;
    ['position','top','left','right','width','height','overscrollBehavior']
      .forEach(k => { document.body.style[k] = ''; });
    window.scrollTo(0, y);
  }

  // ── Seek queue ────────────────────────────────────────────────
  function seekTo(t) {
    if (isSeeking) { pendingTime = t; return; }
    isSeeking = true;
    vid.currentTime = t;
  }
  vid.addEventListener('seeked', () => {
    isSeeking = false;
    if (pendingTime !== null) {
      const t = pendingTime; pendingTime = null;
      isSeeking = true; vid.currentTime = t;
    }
  });

  // ── Video ready ───────────────────────────────────────────────
  vid.addEventListener('loadeddata', () => {
    duration = vid.duration || 0;
    vid.classList.add('ready');
    loaderEl.classList.add('hidden');
    if (reduceMotion) vid.currentTime = duration * 0.92;
  });
  // iOS Safari kickstart
  (() => { const p = vid.play(); if (p?.then) p.then(() => vid.pause()).catch(()=>{}); else vid.pause(); })();

  // ── Exit ──────────────────────────────────────────────────────
  function triggerExit() {
    if (exiting) return; exiting = true;
    root.style.transition = 'opacity .45s ease';
    root.style.opacity = '0';
    cleanup();
    setTimeout(() => { releaseLock(); window.location.href = ctaHref; }, 460);
  }
  ctaEl.addEventListener('click', e => { e.preventDefault(); triggerExit(); });

  // ── Input ─────────────────────────────────────────────────────
  function addDelta(dy) {
    if (exiting) return;
    targetProgress = clamp(targetProgress + dy / scrubDistance, 0, 1);
    if (targetProgress > 0.001) hasStarted = true;
    if (targetProgress >= 0.9999 && dy > 0) {
      overflowAccum += dy;
      if (overflowAccum >= exitThreshold) triggerExit();
    }
    if (dy < 0) overflowAccum = 0;
  }

  const onWheel = e => { addDelta(e.deltaY); e.preventDefault(); };
  const onTouchStart = e => { touchStartY = e.touches[0]?.clientY ?? 0; };
  const onTouchMove = e => {
    const y = e.touches[0]?.clientY ?? touchStartY;
    addDelta(touchStartY - y);
    touchStartY = y;
    e.preventDefault();
  };

  window.addEventListener('wheel',      onWheel,      { passive: false });
  window.addEventListener('touchstart', onTouchStart, { passive: true  });
  window.addEventListener('touchmove',  onTouchMove,  { passive: false });
  root.addEventListener('touchstart',   onTouchStart, { passive: true,  capture: true });
  root.addEventListener('touchmove',    onTouchMove,  { passive: false, capture: true });

  function cleanup() {
    window.removeEventListener('wheel',      onWheel);
    window.removeEventListener('touchstart', onTouchStart);
    window.removeEventListener('touchmove',  onTouchMove);
    root.removeEventListener('touchstart',   onTouchStart, true);
    root.removeEventListener('touchmove',    onTouchMove,  true);
    cancelAnimationFrame(rafId);
  }

  // ── RAF loop ──────────────────────────────────────────────────
  function frame() {
    currentProgress += (targetProgress - currentProgress) * 0.18;
    if (duration > 0) seekTo(currentProgress * duration);

    vid.style.transform = `scale(${1 + currentProgress * 0.065})`;

    const tT = 1 - clamp(currentProgress / 0.35, 0, 1);
    titleEl.style.opacity   = tT;
    titleEl.style.transform = `translateY(${(1-tT)*-26}px) scale(${0.96+tT*0.04})`;
    titleEl.style.filter    = `blur(${(1-tT)*11}px)`;

    hintEl.style.opacity = hasStarted ? '0' : '1';

    const tg = clamp((currentProgress - 0.82) / 0.18, 0, 1);
    taglineEl.style.opacity   = tg;
    taglineEl.style.transform = `translateY(${(1-tg)*22}px) scale(${0.97+tg*0.03})`;
    taglineEl.style.filter    = `blur(${(1-tg)*9}px)`;

    fillEl.style.transform = `scaleX(${currentProgress})`;
    rafId = requestAnimationFrame(frame);
  }

  // ── Boot ──────────────────────────────────────────────────────
  engageLock();
  if (!reduceMotion) rafId = requestAnimationFrame(frame);
  else {
    taglineEl.style.opacity = '1';
    taglineEl.style.filter = taglineEl.style.transform = '';
    titleEl.style.opacity = '0';
    fillEl.style.transform = 'scaleX(1)';
  }

  // Return a teardown handle
  return { destroy: () => { cleanup(); releaseLock(); container.innerHTML = ''; } };
}
