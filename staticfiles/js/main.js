function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// Activar tab según hash
document.addEventListener('DOMContentLoaded', function() {
  if (window.location.hash) {
    const tab = document.querySelector(`[href="${window.location.hash}"]`);
    if (tab) {
      new bootstrap.Tab(tab).show();
    }
  }

  // Guardar tab activo
  document.querySelectorAll('[data-bs-toggle="tab"]').forEach(t => {
    t.addEventListener('shown.bs.tab', e => {
      history.replaceState(null, null, e.target.getAttribute('href'));
    });
  });
});

// ── Búsqueda global ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const input = document.getElementById('searchGlobal');
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
