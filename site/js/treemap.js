// Treemap « squarifié » (Bruls, Huizing & van Wijk, 2000), sans dépendance.
// Entrée : items [{value, ...}] (valeurs > 0), rectangle {x, y, w, h}.
// Sortie : mêmes items avec {x, y, w, h}, surfaces strictement proportionnelles aux valeurs.

export function squarify(items, rect) {
  const data = items.filter((d) => d.value > 0).sort((a, b) => b.value - a.value);
  const total = data.reduce((s, d) => s + d.value, 0);
  const scale = (rect.w * rect.h) / total;
  const nodes = data.map((d) => ({ ...d, area: d.value * scale }));
  const out = [];
  let { x, y, w, h } = rect;
  let row = [];

  const worst = (r, side) => {
    const s = r.reduce((a, n) => a + n.area, 0);
    let max = -Infinity, min = Infinity;
    for (const n of r) { max = Math.max(max, n.area); min = Math.min(min, n.area); }
    return Math.max((side * side * max) / (s * s), (s * s) / (side * side * min));
  };

  const layoutRow = (r) => {
    const s = r.reduce((a, n) => a + n.area, 0);
    if (w >= h) { // colonne à gauche
      const cw = s / h; let cy = y;
      for (const n of r) { const nh = n.area / cw; out.push({ ...n, x, y: cy, w: cw, h: nh }); cy += nh; }
      x += cw; w -= cw;
    } else { // ligne en haut
      const rh = s / w; let cx = x;
      for (const n of r) { const nw = n.area / rh; out.push({ ...n, x: cx, y, w: nw, h: rh }); cx += nw; }
      y += rh; h -= rh;
    }
  };

  for (const n of nodes) {
    const side = Math.min(w, h);
    if (row.length === 0 || worst([...row, n], side) <= worst(row, side)) row.push(n);
    else { layoutRow(row); row = [n]; }
  }
  if (row.length) layoutRow(row);
  return out;
}
