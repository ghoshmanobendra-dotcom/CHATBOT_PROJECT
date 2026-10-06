/* ================================================================
   GCECT IT Assistant — Landing Page JavaScript
   Particle canvas · typed text · scroll animations · navbar
   ================================================================ */

/* ── 1. PARTICLE CANVAS ─────────────────────────────────────── */
(function initParticles() {
  const canvas  = document.getElementById('particle-canvas');
  const ctx     = canvas.getContext('2d');
  let W, H, particles = [], raf;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function Particle() {
    this.reset();
  }
  Particle.prototype.reset = function () {
    this.x  = Math.random() * W;
    this.y  = Math.random() * H;
    this.r  = Math.random() * 1.6 + 0.4;
    this.vx = (Math.random() - 0.5) * 0.35;
    this.vy = (Math.random() - 0.5) * 0.35;
    this.life  = 0;
    this.maxLife = Math.random() * 200 + 80;
    const hue = Math.random() > 0.5 ? 230 : 265;   // blue or violet
    this.color = `hsla(${hue},80%,70%,`;
  };
  Particle.prototype.update = function () {
    this.x  += this.vx;
    this.y  += this.vy;
    this.life++;
    if (this.life > this.maxLife
        || this.x < 0 || this.x > W
        || this.y < 0 || this.y > H) {
      this.reset();
    }
  };
  Particle.prototype.draw = function () {
    const progress = this.life / this.maxLife;
    const alpha = progress < 0.1
      ? progress / 0.1
      : progress > 0.8
      ? (1 - progress) / 0.2
      : 1;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.fillStyle = this.color + (alpha * 0.75) + ')';
    ctx.fill();
  };

  // Connection lines
  function drawLines() {
    const maxDist = 120;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d  = Math.sqrt(dx*dx + dy*dy);
        if (d < maxDist) {
          const alpha = (1 - d / maxDist) * 0.12;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(91,127,255,${alpha})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
  }

  function loop() {
    ctx.clearRect(0, 0, W, H);
    drawLines();
    particles.forEach(p => { p.update(); p.draw(); });
    raf = requestAnimationFrame(loop);
  }

  function init() {
    resize();
    particles = Array.from({ length: 110 }, () => new Particle());
    if (raf) cancelAnimationFrame(raf);
    loop();
  }

  window.addEventListener('resize', () => { resize(); });
  init();
})();

/* ── 2. NAVBAR SCROLL EFFECT ────────────────────────────────── */
(function initNavbar() {
  const nav = document.getElementById('navbar');
  function onScroll() {
    if (window.scrollY > 40) nav.classList.add('scrolled');
    else nav.classList.remove('scrolled');
  }
  window.addEventListener('scroll', onScroll, { passive: true });
})();

/* ── 3. TYPED TEXT ANIMATION ────────────────────────────────── */
(function initTyped() {
  const words  = ['College Guide', 'IT Assistant', 'Academic Helper', 'Study Partner'];
  const target = document.getElementById('typed-word');
  if (!target) return;

  let wIdx = 0, cIdx = 0, deleting = false;
  const DELAY_TYPE = 90, DELAY_DEL = 50, DELAY_PAUSE = 1800;

  function tick() {
    const word = words[wIdx];
    if (!deleting) {
      target.textContent = word.slice(0, cIdx + 1);
      cIdx++;
      if (cIdx === word.length) {
        deleting = true;
        setTimeout(tick, DELAY_PAUSE);
        return;
      }
      setTimeout(tick, DELAY_TYPE);
    } else {
      target.textContent = word.slice(0, cIdx - 1);
      cIdx--;
      if (cIdx === 0) {
        deleting = false;
        wIdx = (wIdx + 1) % words.length;
        setTimeout(tick, 300);
        return;
      }
      setTimeout(tick, DELAY_DEL);
    }
  }
  // Add blinking cursor via CSS injected class
  target.style.borderRight = '3px solid #8b5cf6';
  target.style.paddingRight = '4px';
  target.style.animation = 'cursor-blink 1s step-end infinite';

  // Inject cursor-blink keyframe
  const style = document.createElement('style');
  style.textContent = `
    @keyframes cursor-blink {
      0%,100% { border-right-color: #8b5cf6; }
      50%      { border-right-color: transparent; }
    }
  `;
  document.head.appendChild(style);

  setTimeout(tick, 1200);
})();

/* ── 4. SCROLL REVEAL ───────────────────────────────────────── */
(function initReveal() {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;

  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const d = entry.target.style.getPropertyValue('--d') || '0ms';
        setTimeout(() => entry.target.classList.add('visible'), parseInt(d) || 0);
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  els.forEach(el => io.observe(el));
})();

/* ── 5. ORB MOUSE PARALLAX ──────────────────────────────────── */
(function initOrbParallax() {
  const orb = document.getElementById('orb-body');
  if (!orb) return;
  document.addEventListener('mousemove', (e) => {
    const cx = window.innerWidth / 2;
    const cy = window.innerHeight / 2;
    const dx = (e.clientX - cx) / cx;
    const dy = (e.clientY - cy) / cy;
    orb.style.transform = `translateY(0px) rotateX(${-dy * 12}deg) rotateY(${dx * 12}deg)`;
  });
  document.addEventListener('mouseleave', () => {
    orb.style.transform = '';
  });
})();

/* ── 6. BUBBLE CLICK INTERACTION ────────────────────────────── */
(function initBubbles() {
  const questions = [
    '📚 3rd Sem Subjects?',
    '🎓 HOD Details',
    '💰 Fees & Scholarships',
    '🏢 Placement Cell',
    '⚙️ OS Topics',
    '🗄️ DBMS Syllabus',
    '🤖 AI Subject',
    '🕸️ Computer Networks',
    '📅 Exam Schedule',
    '🏅 Bytemonk Club',
    '🎒 Admission Docs',
    '💡 DSA Topics',
  ];

  const bubbles = document.querySelectorAll('.float-bubble');
  let idx = 4;

  function rotateBubble(b) {
    b.style.opacity = '0';
    b.style.transition = 'opacity 0.4s';
    setTimeout(() => {
      b.querySelector('span').textContent = questions[idx % questions.length];
      idx++;
      b.style.opacity = '1';
    }, 400);
  }

  bubbles.forEach((b, i) => {
    // Stagger initial rotation
    setInterval(() => rotateBubble(b), 4000 + i * 1200);
    b.addEventListener('click', () => rotateBubble(b));
    b.style.cursor = 'pointer';
    b.title = 'Click to cycle topics';
  });
})();

/* ── 7. SMOOTH SCROLL FOR ANCHOR LINKS ─────────────────────── */
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const id = a.getAttribute('href').slice(1);
    const el = document.getElementById(id);
    if (el) {
      e.preventDefault();
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

/* ── 8. COUNTER ANIMATION for stat badges ───────────────────── */
(function initCounters() {
  const nums = document.querySelectorAll('.stat-num');
  if (!nums.length) return;

  const io = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el  = entry.target;
      const raw = el.textContent.replace(/\D/g, '');
      const end = parseInt(raw, 10);
      if (isNaN(end)) return;
      const suffix = el.textContent.replace(/[0-9]/g, '');
      let start = 0; const dur = 800; const step = dur / end;
      const timer = setInterval(() => {
        start++;
        el.textContent = start + suffix;
        if (start >= end) clearInterval(timer);
      }, step);
      io.unobserve(el);
    });
  }, { threshold: 1 });

  nums.forEach(n => io.observe(n));
})();
