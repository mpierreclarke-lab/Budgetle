// Affichage partagé par les pages : formats français, couleurs, treemap interactif.
// Script classique (pas de module) : injecté tel quel dans chaque page par scripts/05_build_site.py.
const COLORS = { GF01:"--gf01", GF02:"--gf02", GF03:"--gf03", GF04:"--gf04", GF05:"--gf05", GF06:"--gf06", GF07:"--gf07", GF08:"--gf08", GF09:"--gf09",
  SP_OLD:"--sp1", SP_SURV:"--sp2", SP_SICK:"--sp3", SP_FAM:"--sp4", SP_UNEMP:"--sp5", SP_HOUS:"--sp6", SP_OTHER:"--sp7" };
const fr1 = new Intl.NumberFormat("fr-FR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const fr0 = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });
const pct = (v, approx) => v == null ? "n.d." : `${approx ? "≈ " : ""}${fr1.format(v)} % du PIB`;
function money(mio) {
  if (mio == null) return "n.d.";
  if (mio >= 100000) return `${fr0.format(mio / 1000)} Md€`;
  if (mio >= 1000) return `${fr1.format(mio / 1000)} Md€`;
  return `${fr0.format(mio)} M€`;
}
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
function inkFor(hex) {
  const n = parseInt(hex.slice(1), 16), c = [n >> 16, (n >> 8) & 255, n & 255].map(x => { x /= 255; return x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; });
  const L = .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
  return L > .23 ? "#111317" : "#ffffff";
}
const share = (t) => `${fr1.format(100 * t.part_du_total)} %`;

// Treemap : chaque rectangle affiche sa part dans la dépense totale ; % du PIB et montant au survol, au toucher ou au clavier.
function drawTreemap(box, p, detailEl) {
  box.innerHTML = "";
  const W = box.clientWidth, H = box.clientHeight;
  if (!W || !H) return;
  const top = squarify(p.divisions.map(d => ({ ...d, value: d.mio_eur })), { x: 0, y: 0, w: W, h: H });
  const GAP = 1;
  const tiles = [];
  for (const r of top) {
    if (r.code === "GF10" && r.detail) {
      const kids = r.detail.filter(k => k.mio_eur > 0).map(k => ({ ...k, value: k.mio_eur, pc: k.pc_gdp_somme_publiee, approx: k.cofog.length > 1, sp: true }));
      for (const k of squarify(kids, { x: r.x, y: r.y, w: r.w, h: r.h })) tiles.push(k);
      const ring = document.createElement("div"); ring.className = "group-ring";
      Object.assign(ring.style, { left: r.x + "px", top: r.y + "px", width: r.w + "px", height: r.h + "px" });
      tiles.push({ ring });
    } else tiles.push({ ...r, pc: r.pc_gdp, sp: false, color: r.code === "GF10" ? "--sp3" : COLORS[r.code] });
  }
  const sp = p.divisions[9];
  const show = (t, el) => {
    box.querySelectorAll(".tile.on").forEach(x => x.classList.remove("on"));
    el.classList.add("on");
    const parent = t.sp ? `<span class="small">Protection sociale · ${share(sp)} de la dépense totale</span>` : "";
    const nodet = t.code === "GF10" && !sp.detail ? `<span class="small">Détail par risque non publié pour ce pays.</span>` : "";
    detailEl.innerHTML = `${parent}<span class="k">${t.label}</span><div class="row"><span class="num">${share(t)} de la dépense totale</span><span class="num">${pct(t.pc, t.approx)}</span><span class="num">${money(t.mio_eur)}</span></div>${nodet}`;
  };
  detailEl.innerHTML = `<span class="small">Survolez ou touchez un rectangle pour voir son poids en % du PIB et son montant.</span>`;
  for (const t of tiles) {
    if (t.ring) { box.appendChild(t.ring); continue; }
    const el = document.createElement("div");
    el.className = "tile" + (t.sp ? " sp" : "");
    el.tabIndex = 0;
    el.setAttribute("role", "button");
    el.setAttribute("aria-label", `${t.label} : ${share(t)} de la dépense totale`);
    const bg = css(t.color || COLORS[t.code]);
    Object.assign(el.style, { left: t.x + GAP + "px", top: t.y + GAP + "px", width: Math.max(0, t.w - 2 * GAP) + "px", height: Math.max(0, t.h - 2 * GAP) + "px", background: bg, color: inkFor(bg) });
    const w = t.w, h = t.h;
    if (w > 62 && h > 30) el.innerHTML = `<b>${t.label}</b>` + (h > 46 ? `<span class="v">${share(t)}</span>` : "");
    else if (w > 34 && h > 18) el.innerHTML = `<span class="v">${fr1.format(100 * t.part_du_total)}</span>`;
    el.addEventListener("mouseenter", () => show(t, el));
    el.addEventListener("focus", () => show(t, el));
    el.addEventListener("click", () => show(t, el));
    box.appendChild(el);
  }
}

function profileCard(container, p, opts = {}) {
  const year = opts.hideName ? "" : ` en ${p.annee}`;
  const hasDetail = !!p.divisions[9].detail;
  container.innerHTML = `
    <div class="headline"><span class="big num">${money(p.total.mio_eur).replace(/ /g, "&nbsp;")}</span><span class="unit">de dépenses publiques${year} <span style="white-space:nowrap">(${fr1.format(p.total.pc_gdp)}&nbsp;% du PIB)</span></span></div>
    ${opts.hideName ? `<span class="eyebrow">Pays mystère</span>` : `<span class="eyebrow">${p.nom} · ${p.annee} · ${p.source}${p.provisoire ? " · provisoire" : ""}${p.base_comptable === "caisse" ? " · comptes en caisse" : ""}</span>`}
    <div class="tm" role="group" aria-label="Répartition des dépenses publiques par fonction"></div>
    <div class="detail" aria-live="polite"></div>
    <p class="legend-note">Chiffre affiché = part dans la dépense publique totale, proportionnelle à la surface.${hasDetail ? " Nuances de bleu, encadrées : protection sociale détaillée." : ""}</p>
    ${opts.note ? `<p class="note${opts.noteWarn ? " warn" : ""}">${opts.note}</p>` : ""}`;
  const box = container.querySelector(".tm"), det = container.querySelector(".detail");
  const go = () => drawTreemap(box, p, det);
  go();
  new ResizeObserver(go).observe(box);
}
