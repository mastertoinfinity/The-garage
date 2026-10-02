/* ─── Navigation toggle ─────────────────────────────────────────────────────── */
const navToggle = document.querySelector('.nav-toggle');
const nav = document.querySelector('.main-nav');

if (navToggle && nav) {
  navToggle.addEventListener('click', () => {
    const open = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!open));
    nav.classList.toggle('is-open', !open);
  });
}

/* ─── Date input min = today ────────────────────────────────────────────────── */
const today = new Date();
const localToday = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
document.querySelectorAll('input[type="date"]').forEach((input) => {
  input.min = localToday;
});

/* ─── Scroll-reveal (IntersectionObserver) ──────────────────────────────────── */
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.service-card, .review, .catalog-item, .booking-row, .why-card, .step-item, .location-pill').forEach((item) => {
  item.classList.add('reveal');
  revealObserver.observe(item);
});

/* ─── Count-up animation for trust strip numbers ─────────────────────────────── */
function animateCount(el) {
  const target = parseInt(el.dataset.target, 10);
  const decimal = el.dataset.decimal || '';
  const duration = 1400;
  const start = performance.now();

  function tick(now) {
    const elapsed = Math.min(now - start, duration);
    const progress = elapsed / duration;
    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(eased * target);
    el.textContent = current + decimal;
    if (elapsed < duration) requestAnimationFrame(tick);
    else el.textContent = target + decimal;
  }
  requestAnimationFrame(tick);
}

const countObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      animateCount(entry.target);
      countObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.count-up').forEach((el) => countObserver.observe(el));

/* ─── Car hotspot keyboard accessibility ─────────────────────────────────────── */
document.querySelectorAll('.car-hotspot').forEach((hotspot) => {
  const dot = hotspot.querySelector('.hotspot-dot');
  if (dot) {
    dot.setAttribute('tabindex', '0');
    dot.setAttribute('role', 'button');
    dot.setAttribute('aria-label', hotspot.dataset.label || 'Car feature');
    dot.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        hotspot.classList.toggle('is-focused');
        e.preventDefault();
      }
    });
  }
});

/* ─── UPI copy-to-clipboard button ──────────────────────────────────────────── */
const copyBtn = document.querySelector('.copy-upi-btn');
if (copyBtn) {
  copyBtn.addEventListener('click', () => {
    const upiId = copyBtn.closest('.upi-id-box')?.querySelector('strong')?.textContent?.trim();
    if (upiId && navigator.clipboard) {
      navigator.clipboard.writeText(upiId).then(() => {
        const orig = copyBtn.textContent;
        copyBtn.textContent = 'Copied ✓';
        setTimeout(() => { copyBtn.textContent = orig; }, 2000);
      });
    }
  });
}