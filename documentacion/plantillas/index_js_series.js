/* ---------------- Acto I: producción anual ---------------- */
function buildProdAnualChart() {
  const c = themeColors();
  const labels = DATA.prod_anual.map(d => d.anio);
  const ch = new Chart(document.getElementById('chart-prod-anual'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'No convencional (eje izq.)', data: DATA.prod_anual.map(d => d.noconv), borderColor: c.oil, backgroundColor: c.oil + '40', fill: true, tension: 0.25, pointRadius: 0, borderWidth: 2, yAxisID: 'y' },
        { label: 'Convencional (eje der.; sin dato antes de 2022)', data: DATA.prod_anual.map(d => d.conv), borderColor: c.sea, backgroundColor: c.sea + '30', fill: true, tension: 0.25, pointRadius: 3, borderWidth: 2, yAxisID: 'y1', spanGaps: false }
      ]
    },
    options: baseOptions({
      scales: {
        x: { grid: { color: 'transparent' } },
        y: { position: 'left', ticks: { callback: v => fmtCompact(v) }, title: { display: true, text: 'No convencional (bbl)', color: c.oil, font: { size: 11 } } },
        y1: { position: 'right', grid: { display: false }, ticks: { callback: v => fmtCompact(v), color: c.sea }, title: { display: true, text: 'Convencional (bbl)', color: c.sea, font: { size: 11 } } }
      },
      plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: (ctx) => ctx.raw === null ? ` ${ctx.dataset.label}: sin dato` : ` ${ctx.dataset.label}: ${fmt(ctx.raw,0)} bbl` } } }
    })
  });
  charts.push(ch);
}

/* ---------------- Acto III: índices (media móvil de 12 meses, base 2022) ---------------- */
function buildIndicesChart() {
  const c = themeColors();
  const ch = new Chart(document.getElementById('chart-indices'), {
    type: 'line',
    data: {
      labels: DATA.ma12.map(d => monthLabel(d.m)),
      datasets: [
        { label: 'Producción de Vaca Muerta', data: DATA.ma12.map(d => d.vm), borderColor: c.oil, backgroundColor: c.oil, borderWidth: 2.5, pointRadius: 0, spanGaps: false, tension: 0.15 },
        { label: 'Producción de la cuenca (serie oficial)', data: DATA.ma12.map(d => d.cuenca), borderColor: c.oilDeep, backgroundColor: c.oilDeep, borderWidth: 2.25, pointRadius: 0, spanGaps: false, tension: 0.15 },
        { label: 'Exportación de crudo de la cuenca (comercio exterior)', data: DATA.ma12.map(d => d.exp), borderColor: c.sea, backgroundColor: c.sea, borderWidth: 2, pointRadius: 0, spanGaps: false, tension: 0.15 },
        { label: 'Base 100', data: DATA.ma12.map(() => 100), borderColor: c.border, borderWidth: 1, borderDash: [3,3], pointRadius: 0 }
      ]
    },
    options: baseOptions({
      plugins: { legend: { position: 'bottom' }, tooltip: { callbacks: { label: (ctx) => ctx.raw === null ? ` ${ctx.dataset.label}: sin dato` : ` ${ctx.dataset.label}: ${fmt(ctx.raw,1)}` } } },
      scales: { x: { ticks: { maxTicksLimit: 9, color: c.muted }, grid: {color:'transparent'} }, y: { ticks: { color: c.muted } } }
    })
  });
  charts.push(ch);
}

/* ---------------- Acto II: ductos ---------------- */
function buildUtilChart() {
  const c = themeColors();
  const rows = DATA.ductos_util;
  const refLinePlugin = {
    id: 'capRefLine',
    afterDraw(chart) {
      const xScale = chart.scales.x;
      if (!xScale) return;
      const x = xScale.getPixelForValue(100);
      const { top, bottom } = chart.chartArea;
      const ctx = chart.ctx;
      ctx.save();
      ctx.strokeStyle = c.ink; ctx.globalAlpha = 0.35;
      ctx.setLineDash([3,3]); ctx.lineWidth = 1.25;
      ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, bottom); ctx.stroke();
      ctx.restore();
    }
  };
  const etiqueta = r => (r.d.length > 28 ? r.d.slice(0,26) + '…' : r.d) + (r.p ? ' (parcial)' : '') + (r.r ? ' [a revisar]' : '');
  const ch = new Chart(document.getElementById('chart-util'), {
    type: 'bar',
    data: {
      labels: rows.map(etiqueta),
      datasets: [{ data: rows.map(r => r.u), backgroundColor: rows.map(r => r.u > 100 ? c.alert : c.oil), borderRadius: 2 }]
    },
    options: baseOptions({
      indexAxis: 'y',
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => ` ${fmt(ctx.raw,1)}% de utilización · año ${rows[ctx.dataIndex].a} · ${rows[ctx.dataIndex].m} meses con dato` } } },
      scales: { x: { ticks: { callback: v => v + '%' } }, y: { grid: { color: 'transparent' }, ticks: { font: { size: 10.5 } } } }
    }),
    plugins: [refLinePlugin]
  });
  charts.push(ch);
}
function renderRespaldo() {
  document.getElementById('resp-tbody').innerHTML = DATA.ductos_resp.map(r =>
    `<tr><td>${r.d}</td><td class="num">${fmt(r.v,0)}</td></tr>`
  ).join('');
}
function renderExcluidos() {
  document.getElementById('excl-tbody').innerHTML = DATA.ductos_excl.map(r =>
    `<tr><td>${r.d}</td><td>${r.a}</td><td>${r.m}</td></tr>`
  ).join('');
}

/* ---------------- Acto III: países ---------------- */
function buildPaisesChart() {
  const c = themeColors();
  const rows = DATA.paises_rank;
  const ch = new Chart(document.getElementById('chart-paises'), {
    type: 'bar',
    data: { labels: rows.map(r => titleCase(r.pais)), datasets: [{ data: rows.map(r => r.vol), backgroundColor: c.sea, borderRadius: 2 }] },
    options: baseOptions({
      indexAxis: 'y',
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => ` ${fmt(ctx.raw,0)} m³` } } },
      scales: { x: { ticks: { callback: v => fmtCompact(v) } }, y: { grid: { color: 'transparent' } } }
    })
  });
  charts.push(ch);
}
function buildPaisesTiempoChart() {
  const c = themeColors();
  const palette = [c.oil, c.sea, c.alert, c.muted, c.oilDeep];
  const names = Object.keys(DATA.pais_series);
  const ch = new Chart(document.getElementById('chart-paises-tiempo'), {
    type: 'line',
    data: {
      labels: DATA.pais_years,
      datasets: names.map((name, i) => ({
        label: titleCase(name), data: DATA.pais_series[name],
        borderColor: palette[i % palette.length], backgroundColor: palette[i % palette.length],
        borderWidth: 2, pointRadius: 2, tension: 0.2
      }))
    },
    options: baseOptions({ plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: {size: 10.5} } } }, scales: { y: { ticks: { callback: v => fmtCompact(v) } } } })
  });
  charts.push(ch);
}

/* ---------------- Acto III: concentración ---------------- */
function listaBarras(id, filas) {
  document.getElementById(id).innerHTML = filas.map(e => `
    <div class="empresa-row">
      <div class="top"><span class="name">${e.e}</span><span class="pct">${fmt(e.pct,2)}%</span></div>
      <div class="empresa-bar-track"><div class="empresa-bar-fill" style="width:${e.pct}%"></div></div>
    </div>
  `).join('');
}
function renderEmpresas() { listaBarras('empresa-list', DATA.exportadores); }

/* ---------------- Init ---------------- */
// Cada panel se inicializa por separado: si uno falla, no arrastra a los demás.
function safe(fn, label) {
  try { fn(); } catch (e) { console.error('Panel roto: ' + label, e); }
}
document.addEventListener('DOMContentLoaded', () => {
  safe(buildMapLegend, 'map-legend');
  safe(drawMap, 'map');
  safe(setupMapInteraction, 'map-interaction');
  safe(() => renderYacimientos(10), 'yacimientos');
  safe(buildProdAnualChart, 'prod-anual');
  safe(buildUtilChart, 'util');
  safe(renderRespaldo, 'respaldo');
  safe(renderExcluidos, 'excluidos');
  safe(buildIndicesChart, 'indices');
  safe(buildPaisesChart, 'paises');
  safe(buildPaisesTiempoChart, 'paises-tiempo');
  safe(renderEmpresas, 'empresas');
});
