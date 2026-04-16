// ─── VotingBox Main JS ───────────────────────────────────────────

// ─── Toast System ────────────────────────────────────────────────
function showToast(message, type = 'success', duration = 3000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? '✓' : '✗';
  toast.innerHTML = `<span style="color:${type==='success'?'var(--accent)':'#EF4444'};font-weight:700;">${icon}</span><span>${message}</span>`;
  container.appendChild(toast);
  requestAnimationFrame(() => { requestAnimationFrame(() => { toast.classList.add('show'); }); });
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 400);
  }, duration);
}

// ─── Fade-in on Scroll ───────────────────────────────────────────
function initFadeIn() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('visible'); }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
}

// ─── Accordion ───────────────────────────────────────────────────
function initAccordion() {
  document.querySelectorAll('.accordion-header').forEach(btn => {
    btn.addEventListener('click', () => {
      const item = btn.closest('.accordion-item');
      const body = item.querySelector('.accordion-body');
      const isOpen = item.classList.contains('open');
      document.querySelectorAll('.accordion-item').forEach(i => {
        i.classList.remove('open');
        i.querySelector('.accordion-body').style.maxHeight = '0';
      });
      if (!isOpen) {
        item.classList.add('open');
        body.style.maxHeight = body.scrollHeight + 'px';
      }
    });
  });
}

// ─── Tabs ────────────────────────────────────────────────────────
function initTabs(containerSelector) {
  const containers = document.querySelectorAll(containerSelector || '.tabs-container');
  containers.forEach(container => {
    const tabs = container.querySelectorAll('.tab-btn');
    const contents = container.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        const target = tab.dataset.tab;
        const content = container.querySelector('#tab-' + target);
        if (content) content.classList.add('active');
      });
    });
  });
}

// ─── Mobile Nav ──────────────────────────────────────────────────
function initMobileNav() {
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobile-nav');
  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', () => {
      mobileNav.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', mobileNav.classList.contains('open'));
    });
  }
}

// ─── Dropdown Menus ──────────────────────────────────────────────
function initDropdowns() {
  document.querySelectorAll('.dropdown').forEach(dd => {
    dd.addEventListener('mouseenter', () => dd.classList.add('open'));
    dd.addEventListener('mouseleave', () => dd.classList.remove('open'));
  });
}

// ─── Lucide Icons ────────────────────────────────────────────────
function initIcons() {
  if (typeof lucide !== 'undefined') { lucide.createIcons(); }
}

// ─── Easter Egg (Logo 5-click) ────────────────────────────────────
function initEasterEgg() {
  const logo = document.querySelector('.navbar-logo');
  if (!logo) return;
  let clickCount = 0;
  let clickTimer;
  logo.addEventListener('click', () => {
    clickCount++;
    clearTimeout(clickTimer);
    clickTimer = setTimeout(() => { clickCount = 0; }, 2000);
    if (clickCount >= 5) {
      clickCount = 0;
      // Confetti
      if (typeof confetti !== 'undefined') {
        confetti({ particleCount: 180, spread: 100, origin: { y: 0.2 } });
        setTimeout(() => confetti({ particleCount: 80, spread: 120, origin: { y: 0.4 }, colors: ['#649748','#A8D672','#fff'] }), 400);
      }
      // 360° rotation
      document.body.style.transition = 'transform 1s ease-in-out';
      document.body.style.transform = 'rotate(360deg)';
      setTimeout(() => { document.body.style.transform = 'none'; document.body.style.transition = ''; }, 1100);
      showToast('🎉 Easter Egg Found! Made by Group 2!', 'success', 4000);
    }
  });
}

// ─── Copy to Clipboard ───────────────────────────────────────────
function copyToClipboard(text, successMsg = 'Copied to clipboard!') {
  navigator.clipboard.writeText(text).then(() => showToast(successMsg));
}

// ─── Format Number ───────────────────────────────────────────────
function formatNumber(n) {
  if (n >= 1e9) return (n/1e9).toFixed(1) + 'B';
  if (n >= 1e6) return (n/1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n/1e3).toFixed(1) + 'K';
  return n.toLocaleString();
}

// ─── Modal Helpers ───────────────────────────────────────────────
function openModal(id) {
  const overlay = document.getElementById(id);
  if (overlay) { overlay.classList.add('open'); document.body.style.overflow = 'hidden'; }
}
function closeModal(id) {
  const overlay = document.getElementById(id);
  if (overlay) { overlay.classList.remove('open'); document.body.style.overflow = ''; }
}
window.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) { e.target.classList.remove('open'); document.body.style.overflow = ''; }
});

// ─── Init on DOM Ready ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initFadeIn();
  initAccordion();
  initTabs();
  initMobileNav();
  initDropdowns();
  initIcons();
  initEasterEgg();

  // Highlight active nav link
  const current = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href === current || (href !== '/' && current.startsWith(href))) {
      link.classList.add('active');
    }
  });
});
