/* ══════════════════════════════════════════════════
   AdmiDent — main.js
   ══════════════════════════════════════════════════ */

/* ── Sidebar toggle ──────────────────────────────── */
function toggleSidebar() {
  const isMobile = window.innerWidth <= 768;
  if (isMobile) {
    _mobileToggle();
  } else {
    _desktopToggle();
  }
}

function _desktopToggle() {
  const collapsed = document.body.classList.toggle('sb-collapsed');
  localStorage.setItem('sb-collapsed', collapsed ? '1' : '0');
}

function _mobileToggle() {
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sbOverlay');
  const isOpen   = sidebar.classList.contains('open');
  if (isOpen) {
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  } else {
    sidebar.classList.add('open');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeMobileSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sbOverlay').classList.remove('active');
  document.body.style.overflow = '';
}

document.addEventListener('DOMContentLoaded', function () {

  /* ── Restaurar estado colapsado en desktop ─────── */
  if (window.innerWidth > 768) {
    if (localStorage.getItem('sb-collapsed') === '1') {
      document.body.classList.add('sb-collapsed');
    }
  }

  /* ── Cerrar sidebar móvil al hacer clic en overlay */
  const overlay = document.getElementById('sbOverlay');
  if (overlay) overlay.addEventListener('click', closeMobileSidebar);

  /* ── Cerrar sidebar móvil al navegar ──────────── */
  document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
    link.addEventListener('click', function () {
      if (window.innerWidth <= 768) closeMobileSidebar();
    });
  });

  /* ── Cerrar sidebar móvil con Escape ──────────── */
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && window.innerWidth <= 768) closeMobileSidebar();
  });

  /* ── Adaptar al cambiar orientación ──────────── */
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      // En desktop: cerrar overlay móvil si queda abierto
      document.getElementById('sbOverlay').classList.remove('active');
      document.getElementById('sidebar').classList.remove('open');
      document.body.style.overflow = '';
    }
  });

  /* ── Swipe táctil para abrir/cerrar sidebar ──── */
  let touchStartX = 0;
  let touchStartY = 0;
  const SWIPE_THRESHOLD   = 60;   // px mínimos para contar como swipe
  const EDGE_ZONE         = 30;   // px desde el borde izquierdo para abrir

  document.addEventListener('touchstart', e => {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  }, { passive: true });

  document.addEventListener('touchend', e => {
    if (window.innerWidth > 768) return;
    const dx = e.changedTouches[0].clientX - touchStartX;
    const dy = e.changedTouches[0].clientY - touchStartY;

    // Solo procesar swipes mayormente horizontales
    if (Math.abs(dy) > Math.abs(dx)) return;

    const sidebar = document.getElementById('sidebar');
    const isOpen  = sidebar.classList.contains('open');

    // Swipe derecha desde el borde: abrir
    if (!isOpen && dx > SWIPE_THRESHOLD && touchStartX <= EDGE_ZONE) {
      _mobileToggle();
    }
    // Swipe izquierda estando abierto: cerrar
    if (isOpen && dx < -SWIPE_THRESHOLD) {
      closeMobileSidebar();
    }
  }, { passive: true });

  /* ── Activar tab según hash en URL ────────────── */
  if (window.location.hash) {
    const tab = document.querySelector(`[href="${window.location.hash}"]`);
    if (tab) new bootstrap.Tab(tab).show();
  }
  document.querySelectorAll('[data-bs-toggle="tab"]').forEach(t => {
    t.addEventListener('shown.bs.tab', e => {
      history.replaceState(null, null, e.target.getAttribute('href'));
    });
  });

  /* ── Búsqueda global ──────────────────────────── */
  const input   = document.getElementById('searchGlobal');
  const results = document.getElementById('searchResults');
  if (!input) return;

  let timer;
  input.addEventListener('input', function () {
    clearTimeout(timer);
    const q = this.value.trim();
    if (q.length < 2) { results.style.display = 'none'; return; }
    timer = setTimeout(async () => {
      const resp = await fetch(`/buscar/?q=${encodeURIComponent(q)}`);
      const data = await resp.json();
      if (!data.resultados.length) {
        results.innerHTML = '<div style="padding:.75rem 1rem;font-size:.82rem;color:var(--text-2)">Sin resultados</div>';
      } else {
        results.innerHTML = data.resultados.map(r => `
          <a href="${r.url}" style="display:block;padding:.65rem 1rem;text-decoration:none;
             border-bottom:1px solid var(--border);transition:background .15s"
             onmouseover="this.style.background='var(--bg-hover)'"
             onmouseout="this.style.background=''">
            <div style="font-weight:500;font-size:.875rem;color:var(--text-1)">${r.texto}</div>
            <div style="font-size:.75rem;color:var(--text-2)">${r.subtexto}</div>
          </a>`).join('');
      }
      results.style.display = 'block';
    }, 280);
  });

  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !results.contains(e.target)) {
      results.style.display = 'none';
    }
  });
});
