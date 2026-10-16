// Étape 4 — Simulation des règles géographiques sur les 30 pays.
// 1) vérifie que site/js/geo.js reproduit geolib (donc Tradle) à l'identique ;
// 2) mesure l'étendue des distances et des proximités (échelle Tradle vs échelle européenne) ;
// 3) compte les pays encore possibles après un essai, selon l'information affichée.
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { distanceMeters, compassDirection, proximityTradle, rhumbBearing } from "../site/js/geo.js";

const geolib = createRequire(import.meta.url)("geolib");
const P = JSON.parse(readFileSync(new URL("../data/derived/profils_2024.json", import.meta.url)));
const C = P.map((p) => ({ geo: p.geo, nom: p.nom, lat: p.lat, lon: p.lon }));
const out = [];
const log = (s = "") => { out.push(s); console.log(s); };

// 1. Concordance avec geolib
let mism = 0;
for (const a of C) for (const b of C) {
  const g = { latitude: a.lat, longitude: a.lon }, h = { latitude: b.lat, longitude: b.lon };
  if (geolib.getDistance(g, h) !== distanceMeters(a, b)) mism++;
  if (a !== b && Math.abs(geolib.getRhumbLineBearing(g, h) - rhumbBearing(a, b)) > 1e-9) mism++;
}
log(`1. Concordance geo.js / geolib sur ${C.length * C.length} couples : ${mism} écart(s)`);

// 2. Étendue
const pairs = [];
for (let i = 0; i < C.length; i++) for (let j = i + 1; j < C.length; j++)
  pairs.push({ a: C[i], b: C[j], d: distanceMeters(C[i], C[j]) });
pairs.sort((x, y) => x.d - y.d);
const DMAX = pairs.at(-1).d;
const km = (m) => Math.round(m / 1000).toLocaleString("fr-FR");
const q = (f) => pairs[Math.floor(f * (pairs.length - 1))].d;
log(`\n2. Distances entre centroïdes (${pairs.length} paires)`);
log(`   min ${km(pairs[0].d)} km (${pairs[0].a.nom}–${pairs[0].b.nom}), médiane ${km(q(0.5))} km, max ${km(DMAX)} km (${pairs.at(-1).a.nom}–${pairs.at(-1).b.nom})`);
const pt = pairs.map((p) => proximityTradle(p.d)), pe = pairs.map((p) => proximityTradle(p.d, DMAX));
log(`   Proximité échelle Tradle (20 000 km) : de ${Math.min(...pt)} % à ${Math.max(...pt)} %, médiane ${pt.sort((a, b) => a - b)[pt.length >> 1]} %`);
log(`   Proximité échelle européenne (${km(DMAX)} km) : de ${Math.min(...pe)} % à ${Math.max(...pe)} %, médiane ${pe.sort((a, b) => a - b)[pe.length >> 1]} %`);
log(`   Carrés de partage, échelle Tradle : ${Math.min(...pt) >= 80 ? "toujours 4 carrés verts ou plus" : "variables"}`);

// 3. Candidats restants après UN essai, pour un joueur qui n'utiliserait QUE la géographie
const feedbacks = {
  "km + direction (comme Tradle)": (g, t) => `${Math.round(distanceMeters(g, t) / 1000)}|${compassDirection(g, t)}`,
  "% échelle Tradle + direction": (g, t) => `${proximityTradle(distanceMeters(g, t))}|${compassDirection(g, t)}`,
  "% échelle européenne + direction": (g, t) => `${proximityTradle(distanceMeters(g, t), DMAX)}|${compassDirection(g, t)}`,
  "direction seule": (g, t) => compassDirection(g, t),
  "% échelle européenne seul": (g, t) => `${proximityTradle(distanceMeters(g, t), DMAX)}`,
};
log(`\n3. Pays encore possibles après 1 essai (moyenne sur tous les couples essai × réponse, hors bonne réponse)`);
const res = {};
for (const [name, fb] of Object.entries(feedbacks)) {
  let tot = 0, n = 0, uniq = 0;
  for (const g of C) for (const t of C) {
    if (g === t) continue;
    const k = fb(g, t);
    const cand = C.filter((x) => x !== g && fb(g, x) === k).length;
    tot += cand; n++; if (cand === 1) uniq++;
  }
  res[name] = { moyenne: tot / n, unique: uniq / n };
  log(`   ${name.padEnd(36)} : ${(tot / n).toFixed(2)} candidats en moyenne ; réponse déterminée dans ${(100 * uniq / n).toFixed(0)} % des cas`);
}

// 3bis. Meilleur premier essai « à l'aveugle » (direction seule) : minimise le nombre moyen de candidats
const blind = C.map((g) => {
  let tot = 0;
  for (const t of C) if (t !== g) tot += C.filter((x) => x !== g && compassDirection(g, x) === compassDirection(g, t)).length;
  return { nom: g.nom, m: tot / (C.length - 1) };
}).sort((a, b) => a.m - b.m);
log(`\n   Direction seule — meilleurs premiers essais : ${blind.slice(0, 3).map((b) => `${b.nom} (${b.m.toFixed(1)})`).join(", ")} ; pires : ${blind.slice(-2).map((b) => `${b.nom} (${b.m.toFixed(1)})`).join(", ")}`);

writeFileSync(new URL("../data/derived/simulation_regles.txt", import.meta.url), out.join("\n") + "\n");
writeFileSync(new URL("../data/derived/distance_max_m.json", import.meta.url), JSON.stringify({ distance_max_m: DMAX, paire: [pairs.at(-1).a.geo, pairs.at(-1).b.geo] }));
