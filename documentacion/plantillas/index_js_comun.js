/* ---------------- Theme toggle ---------------- */
(function() {
  const btn = document.getElementById('theme-btn');
  let saved = null;
  try { saved = localStorage.getItem('vm-theme'); } catch(e) {}
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  btn.addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme') ||
      (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('vm-theme', next); } catch(e) {}
    refreshChartColors();
  });
})();

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
function fmt(n, dec=0) {
  return Number(n).toLocaleString('es-AR', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
function fmtCompact(n) {
  if (n >= 1e6) return fmt(n/1e6, 2) + ' M';
  if (n >= 1e3) return fmt(n/1e3, 0) + ' mil';
  return fmt(n, 0);
}
function monthLabel(ym) {
  const meses = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
  const [y,m] = ym.split('-');
  return meses[parseInt(m,10)-1] + ' ' + y;
}

/* ---------------- Chart.js theme ---------------- */
let charts = [];
function themeColors() {
  return {
    ink: cssVar('--ink'), muted: cssVar('--muted'), border: cssVar('--panel-border'),
    oil: cssVar('--oil'), sea: cssVar('--sea'), alert: cssVar('--alert'), panel: cssVar('--panel'),
    oilDeep: cssVar('--oil-deep')
  };
}
function baseOptions(extra) {
  const c = themeColors();
  Chart.defaults.font.family = "'IBM Plex Sans', system-ui, sans-serif";
  Chart.defaults.color = c.muted;
  return Object.assign({
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: { legend: { labels: { color: c.ink, boxWidth: 12, font: {size: 12} } } },
    scales: {
      x: { grid: { color: 'transparent' }, ticks: { color: c.muted } },
      y: { grid: { color: c.border }, ticks: { color: c.muted } }
    }
  }, extra || {});
}
function refreshChartColors() {
  // Simplest robust approach for a portfolio piece: re-render map (canvas, not Chart.js) and leave
  // Chart.js instances as-is between light/dark (palette differences are subtle enough not to require
  // full chart teardown/rebuild).
  drawMap();
}

/* ---------------- Acto I: mapa ---------------- */
let mapState = { hoverIdx: -1 };

// Recuadro FIJO (no min/max de los datos): un puñado de pozos de la formación se extiende muy al norte,
// hacia el norte (hasta -34,7°), y usar el rango efectivo de los datos estiraba la proyección y encogía el
// clúster principal de Neuquén a una mancha diminuta — la causa del "no se entiende dónde estoy parado".
// Estos límites encierran el núcleo de la cuenca y las localidades de referencia; los pozos que caen
// afuera se dibujan igual, pero sujetos (clamped) al borde del recuadro, y se contabilizan en la nota.
const MAP_BOUNDS = { latMin: -39.4, latMax: -37.15, lonMin: -69.95, lonMax: -67.95 };
const LANDMARKS = [
  { name: 'Neuquén (capital)', lat: -38.9516, lon: -68.0591 },
  { name: 'Plaza Huincul', lat: -38.9338, lon: -69.1987 },
  { name: 'Añelo', lat: -38.3543, lon: -68.7876 },
  { name: 'Rincón de los Sauces', lat: -37.39, lon: -68.92 }
];
// Contorno oficial simplificado de la provincia de Neuquén (fuente: IGN/OSM, vía
// github.com/alvarezgarcia/provincias-argentinas-geojson), redondeado a 3 decimales.
const NEUQUEN_POLY = [[-68.258,-37.571],[-68.269,-38.668],[-68.104,-38.814],[-67.994,-38.934],[-68.192,-39.002],[-68.39,-39.036],[-68.5,-39.07],[-68.599,-39.232],[-68.73,-39.275],[-68.917,-39.462],[-69.203,-39.589],[-69.258,-39.682],[-69.434,-39.792],[-69.796,-39.91],[-69.972,-39.977],[-69.95,-40.145],[-70.082,-40.246],[-70.082,-40.363],[-70.159,-40.455],[-70.137,-40.522],[-70.214,-40.522],[-70.291,-40.505],[-70.378,-40.539],[-70.554,-40.505],[-70.642,-40.606],[-70.763,-40.589],[-70.906,-40.606],[-71.016,-40.664],[-71.005,-40.731],[-71.104,-40.764],[-71.093,-40.805],[-71.06,-40.864],[-71.049,-40.922],[-71.049,-40.963],[-71.082,-41.005],[-71.18,-41.063],[-71.334,-41.112],[-71.411,-41.055],[-71.499,-41.021],[-71.598,-41.021],[-71.73,-41.013],[-71.862,-41.005],[-71.884,-40.963],[-71.84,-40.897],[-71.917,-40.83],[-71.949,-40.747],[-71.917,-40.672],[-71.829,-40.639],[-71.796,-40.589],[-71.884,-40.572],[-71.862,-40.505],[-71.829,-40.422],[-71.73,-40.422],[-71.686,-40.397],[-71.642,-40.338],[-71.686,-40.271],[-71.752,-40.229],[-71.763,-40.28],[-71.807,-40.229],[-71.829,-40.154],[-71.818,-40.07],[-71.686,-40.103],[-71.609,-40.095],[-71.675,-40.044],[-71.686,-40.002],[-71.631,-39.943],[-71.598,-39.884],[-71.598,-39.825],[-71.675,-39.809],[-71.697,-39.749],[-71.62,-39.69],[-71.697,-39.64],[-71.752,-39.538],[-71.609,-39.597],[-71.521,-39.673],[-71.422,-39.614],[-71.444,-39.546],[-71.532,-39.529],[-71.499,-39.462],[-71.433,-39.385],[-71.4,-39.334],[-71.334,-39.283],[-71.389,-39.249],[-71.422,-39.19],[-71.444,-39.087],[-71.444,-39.002],[-71.477,-38.925],[-71.378,-38.891],[-71.29,-38.848],[-71.301,-38.763],[-71.202,-38.814],[-71.125,-38.754],[-71.005,-38.746],[-70.917,-38.72],[-70.862,-38.694],[-70.862,-38.634],[-70.829,-38.557],[-70.873,-38.479],[-70.972,-38.454],[-71.005,-38.359],[-70.972,-38.264],[-71.016,-38.186],[-71.049,-38.117],[-70.939,-38.109],[-71.005,-38.057],[-71.049,-38.005],[-71.115,-37.953],[-71.125,-37.892],[-71.147,-37.849],[-71.202,-37.858],[-71.104,-37.762],[-71.158,-37.719],[-71.202,-37.658],[-71.158,-37.614],[-71.125,-37.536],[-71.125,-37.466],[-71.169,-37.396],[-71.235,-37.344],[-71.202,-37.3],[-71.147,-37.239],[-71.093,-37.195],[-71.071,-37.143],[-71.115,-37.073],[-71.169,-36.967],[-71.104,-36.959],[-71.136,-36.906],[-71.158,-36.844],[-71.104,-36.73],[-71.005,-36.704],[-71.016,-36.624],[-71.093,-36.571],[-71.038,-36.536],[-70.983,-36.465],[-70.862,-36.395],[-70.73,-36.439],[-70.675,-36.404],[-70.719,-36.342],[-70.719,-36.271],[-70.609,-36.2],[-70.532,-36.147],[-70.455,-36.2],[-70.411,-36.138],[-70.378,-36.182],[-70.378,-36.271],[-70.378,-36.368],[-70.291,-36.342],[-70.236,-36.342],[-70.214,-36.404],[-70.192,-36.51],[-70.082,-36.616],[-69.983,-36.721],[-69.895,-36.8],[-69.818,-36.88],[-69.741,-36.941],[-69.763,-37.003],[-69.763,-37.073],[-69.609,-37.125],[-69.543,-37.204],[-69.291,-37.143],[-69.17,-37.169],[-69.038,-37.239],[-69.049,-37.318],[-69.049,-37.388],[-68.95,-37.405],[-68.829,-37.37],[-68.719,-37.396],[-68.665,-37.44],[-68.577,-37.449],[-68.478,-37.501],[-68.39,-37.562],[-68.258,-37.571]];

function drawMap() {
  const canvas = document.getElementById('map-canvas');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const W = rect.width, H = rect.height;
  const c = themeColors();

  const pts = DATA.mapa; // [lat, lon, subtipo, yacimiento, produccion]
  const { latMin, latMax, lonMin, lonMax } = MAP_BOUNDS;
  const pad = 34;
  function project(lat, lon) {
    const latC = Math.min(Math.max(lat, latMin), latMax);
    const lonC = Math.min(Math.max(lon, lonMin), lonMax);
    const x = pad + (lonC - lonMin) / (lonMax - lonMin) * (W - pad*2);
    const y = pad + (1 - (latC - latMin) / (latMax - latMin)) * (H - pad*2);
    return [x, y];
  }
  // Igual que project(), pero SIN sujetar al recuadro — para el contorno provincial, que se
  // dibuja recortado (clip) en vez de aplastado contra el borde, así no distorsiona su forma.
  function projectRaw(lat, lon) {
    const x = pad + (lon - lonMin) / (lonMax - lonMin) * (W - pad*2);
    const y = pad + (1 - (lat - latMin) / (latMax - latMin)) * (H - pad*2);
    return [x, y];
  }

  ctx.clearRect(0,0,W,H);

  // graticule
  ctx.strokeStyle = c.border; ctx.lineWidth = 1;
  ctx.font = '10px IBM Plex Sans, sans-serif'; ctx.fillStyle = c.muted;
  for (let lon = Math.ceil(lonMin); lon <= lonMax; lon += 1) {
    const [x] = project(latMin, lon);
    ctx.beginPath(); ctx.moveTo(x, pad); ctx.lineTo(x, H-pad); ctx.stroke();
    ctx.fillText(lon.toFixed(0) + '°O', x+3, H-pad+14);
  }
  for (let lat = Math.ceil(latMin); lat <= latMax; lat += 1) {
    const [, y] = project(lat, lonMin);
    ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(W-pad, y); ctx.stroke();
    ctx.fillText(lat.toFixed(0) + '°S', 4, y-3);
  }

  // contorno de la provincia de Neuquén, recortado al área del gráfico (no sujetado al borde,
  // para no deformar su forma verdadera)
  ctx.save();
  ctx.beginPath(); ctx.rect(pad, pad, W - pad*2, H - pad*2); ctx.clip();
  ctx.beginPath();
  NEUQUEN_POLY.forEach(([lon, lat], i) => {
    const [x, y] = projectRaw(lat, lon);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.strokeStyle = c.ink; ctx.lineWidth = 1.5; ctx.globalAlpha = 0.5;
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.restore();

  const colorMap = { 'SHALE': c.oil, 'TIGHT': c.sea, 'N/D': c.muted };
  const prodMax = Math.max(...pts.map(p => p[4]));
  let outside = 0;
  pts.forEach((p, i) => {
    if (p[0] < latMin || p[0] > latMax || p[1] < lonMin || p[1] > lonMax) outside++;
    const [x, y] = project(p[0], p[1]);
    const r = 1.3 + Math.sqrt(p[4] / prodMax) * 7;
    ctx.beginPath();
    ctx.fillStyle = colorMap[p[2]] || c.muted;
    ctx.globalAlpha = i === mapState.hoverIdx ? 1 : 0.55;
    ctx.arc(x, y, i === mapState.hoverIdx ? r+2 : r, 0, Math.PI*2);
    ctx.fill();
  });
  ctx.globalAlpha = 1;

  // localidades de referencia
  LANDMARKS.forEach(lm => {
    const [x, y] = project(lm.lat, lm.lon);
    ctx.save();
    ctx.translate(x, y); ctx.rotate(Math.PI/4);
    ctx.fillStyle = c.ink;
    ctx.fillRect(-3.5, -3.5, 7, 7);
    ctx.restore();
    ctx.fillStyle = c.ink;
    ctx.font = '600 10.5px IBM Plex Sans, sans-serif';
    ctx.fillText(lm.name, x + 8, y + 3);
  });

  // N (orientación)
  ctx.fillStyle = c.muted; ctx.font = '600 11px IBM Plex Sans, sans-serif';
  ctx.fillText('N ↑', W - pad - 4, pad - 12);

  // mini-mapa de ubicación: la provincia entera, con un recuadro marcando qué parte estamos viendo
  drawLocatorInset(ctx, c, W, H);

  const note = document.getElementById('map-outliers-note');
  if (note) {
    note.textContent = outside > 0
      ? `${outside} pozos de la formación quedan fuera de este recuadro (al norte o al este) y se dibujan sujetos al borde, no en su posición.`
      : '';
  }

  canvas._project = project;
}

function drawLocatorInset(ctx, c, W, H) {
  const iw = 84, ih = 84, ix = W - iw - 10, iy = H - ih - 10;
  const lons = NEUQUEN_POLY.map(p => p[0]), lats = NEUQUEN_POLY.map(p => p[1]);
  const lonMin = Math.min(...lons), lonMax = Math.max(...lons);
  const latMin = Math.min(...lats), latMax = Math.max(...lats);
  const span = Math.max(lonMax - lonMin, latMax - latMin);
  const pip = 6; // padding interno del inset
  function proj(lat, lon) {
    const x = ix + pip + (lon - lonMin) / span * (iw - pip*2);
    const y = iy + pip + (1 - (lat - latMin) / span) * (ih - pip*2);
    return [x, y];
  }
  ctx.save();
  ctx.fillStyle = c.panel; ctx.globalAlpha = 0.92;
  ctx.fillRect(ix, iy, iw, ih);
  ctx.globalAlpha = 1;
  ctx.strokeStyle = c.border; ctx.lineWidth = 1;
  ctx.strokeRect(ix, iy, iw, ih);

  ctx.beginPath();
  NEUQUEN_POLY.forEach(([lon, lat], i) => {
    const [x, y] = proj(lat, lon);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = c.muted; ctx.globalAlpha = 0.18; ctx.fill();
  ctx.globalAlpha = 1;
  ctx.strokeStyle = c.muted; ctx.lineWidth = 1; ctx.stroke();

  const b = MAP_BOUNDS;
  const [x1, y1] = proj(b.latMax, b.lonMin);
  const [x2, y2] = proj(b.latMin, b.lonMax);
  ctx.strokeStyle = c.alert; ctx.lineWidth = 1.5;
  ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

  ctx.fillStyle = c.muted; ctx.font = '600 9px IBM Plex Sans, sans-serif';
  ctx.fillText('Neuquén', ix + 5, iy - 4);
  ctx.restore();
}

function setupMapInteraction() {
  const canvas = document.getElementById('map-canvas');
  const tip = document.getElementById('map-tooltip');
  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left, my = e.clientY - rect.top;
    const pts = DATA.mapa;
    let best = -1, bestD = 8; // px threshold
    for (let i = 0; i < pts.length; i++) {
      const [x, y] = canvas._project(pts[i][0], pts[i][1]);
      const d = Math.hypot(x-mx, y-my);
      if (d < bestD) { bestD = d; best = i; }
    }
    if (best !== mapState.hoverIdx) {
      mapState.hoverIdx = best;
      drawMap();
    }
    if (best >= 0) {
      const p = pts[best];
      tip.style.opacity = 1;
      tip.style.left = mx + 'px';
      tip.style.top = my + 'px';
      tip.textContent = p[3] + ' · ' + p[2] + ' · ' + fmtCompact(p[4]) + ' bbl acum.';
    } else {
      tip.style.opacity = 0;
    }
  });
  canvas.addEventListener('mouseleave', () => { tip.style.opacity = 0; mapState.hoverIdx = -1; drawMap(); });
  window.addEventListener('resize', () => drawMap());
}

function buildMapLegend() {
  const c = themeColors();
  const items = [
    ['SHALE', c.oil], ['TIGHT', c.sea]
  ];
  const el = document.getElementById('map-legend');
  el.innerHTML = items.map(([label, color]) =>
    `<span class="legend-item"><span class="legend-dot" style="background:${color}"></span>${label}</span>`
  ).join('');
}

/* ---------------- Acto I: top yacimientos ---------------- */
function renderYacimientos(n) {
  const tbody = document.getElementById('yac-tbody');
  const rows = DATA.top_yac.slice(0, n);
  tbody.innerHTML = rows.map(r =>
    `<tr><td class="rank">${r.r}</td><td>${titleCase(r.n)}</td><td class="num">${fmt(r.v,0)}</td></tr>`
  ).join('');
}
function titleCase(s) {
  return s.toLowerCase().replace(/(^|\s|-)\S/g, c => c.toUpperCase());
}
document.getElementById('yac-toggle').addEventListener('click', (e) => {
  if (e.target.tagName !== 'BUTTON') return;
  document.querySelectorAll('#yac-toggle button').forEach(b => b.classList.remove('active'));
  e.target.classList.add('active');
  renderYacimientos(parseInt(e.target.dataset.n, 10));
});

