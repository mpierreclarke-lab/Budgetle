// Étape 5 — Vérification de la page construite (site/dist/regles.html).
// a) les données embarquées sont identiques à data/derived/profils_monde.json ;
// b) le treemap donne à chaque rectangle une surface proportionnelle à sa part (tous les pays) ;
// c) chaque affirmation chiffrée des notes est vraie dans les données ;
// d) le script de la page se compile.
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { squarify } from "../site/js/treemap.js";
import { distanceMeters, compassDirection, proximityTradle } from "../site/js/geo.js";

const html = readFileSync(new URL("../site/dist/regles.html", import.meta.url), "utf8");
const ref = JSON.parse(readFileSync(new URL("../data/derived/profils_monde.json", import.meta.url)));
let fails = 0;
const check = (ok, msg) => { console.log(`${ok ? "OK   " : "ÉCHEC"} ${msg}`); if (!ok) fails++; };

// a) données embarquées
const embedded = JSON.parse(html.match(/const PROFILES = (\[.*?\]);\n/s)[1]);
check(JSON.stringify(embedded) === JSON.stringify(ref), "données embarquées identiques à profils_monde.json");

// b) surfaces du treemap
let worst = 0;
for (const p of ref) {
  for (const [W, H] of [[1000, 625], [380, 399]]) {
    const top = squarify(p.divisions.map((d) => ({ ...d, value: d.mio_eur })), { x: 0, y: 0, w: W, h: H });
    const all = [];
    for (const r of top) {
      if (r.code === "GF10" && r.detail) all.push(...squarify(r.detail.filter((k) => k.mio_eur > 0).map((k) => ({ ...k, value: k.mio_eur })), r));
      else all.push(r);
    }
    for (const t of all) worst = Math.max(worst, Math.abs((t.w * t.h) / (W * H) - t.part_du_total));
    const covered = all.reduce((s, t) => s + t.w * t.h, 0) / (W * H);
    if (Math.abs(covered - 1) > 1e-6) check(false, `${p.geo} : le treemap ne couvre pas tout le cadre (${covered})`);
  }
}
// Tolérance 0,01 point de part : les sous-catégories publiées somment à GF10 à ±0,004 % près (arrondis Eurostat)
check(worst < 1e-4, `surfaces proportionnelles aux parts (écart max ${(100 * worst).toFixed(4)} point) sur ${ref.length} pays × 2 formats`);

// c) affirmations des notes
const by = Object.fromEntries(ref.map((p) => [p.geo, p]));
const div = (g, c) => by[g].divisions.find((d) => d.code === c);
const sortBy = (f) => [...ref].sort((a, b) => f(b) - f(a)).map((p) => p.geo);
const tot = sortBy((p) => p.total.pc_gdp);
const sh = (g, c) => Math.round(1000 * div(g, c).part_du_total) / 10;
check(tot.indexOf("FR") === 3 && tot.slice(0, 3).join() === "KI,UA,FI", `France 4ᵉ ratio de dépense au PIB, après Kiribati, l'Ukraine, la Finlande (${tot.slice(0, 4)})`);
check(sh("FR", "GF10") === 41.5 && Math.round(1000 * div("FR", "GF10").detail[0].part_du_total) / 10 === 23.4, "France : protection sociale 41,5 %, vieillesse 23,4 % de la dépense");
const health = sortBy((p) => div(p.geo, "GF07").part_du_total);
check(health[0] === "US" && sh("US", "GF07") === 26.0, "États-Unis : santé 26,0 % de la dépense, part la plus forte");
check(div("US", "GF05").mio_eur === 0 && div("US", "GF10").detail === null, "États-Unis : environnement à 0, détail social non publié");
check(sh("JP", "GF10") === 40.7 && sh("JP", "GF02") === 3.2, "Japon : protection sociale 40,7 %, défense 3,2 % de la dépense");
const def = sortBy((p) => div(p.geo, "GF02").part_du_total);
check(def[0] === "UA" && sh("UA", "GF02") === 43.1 && div("UA", "GF02").pc_gdp === 31.6 && by.UA.annee === 2023 && by.UA.base_comptable === "caisse",
  "Ukraine 2023 : défense 43,1 % de la dépense (31,6 % du PIB), la plus forte ; comptes en caisse");
check(div("CH", "GF07").pc_gdp === 2.2, "Suisse : santé 2,2 % du PIB");
check(new Set(ref.map((p) => p.geo)).size === ref.length && ref.every((p) => p.nom && p.lat != null), "codes uniques, noms et centres géographiques présents");

// Exemple de partie (cible JP)
for (const g of ["FR", "CN", "KR"]) console.log(`      essai ${by[g].nom} → ${Math.round(distanceMeters(by[g], by.JP) / 1000)} km ${compassDirection(by[g], by.JP)} ${proximityTradle(distanceMeters(by[g], by.JP))} %`);

// d) page de jeu : mêmes données, même calendrier ; les scripts des deux pages se compilent
const game = readFileSync(new URL("../site/dist/index.html", import.meta.url), "utf8");
const cal = JSON.parse(readFileSync(new URL("../data/derived/calendrier.json", import.meta.url)));
check(JSON.stringify(JSON.parse(game.match(/const PROFILES = (\[.*?\]);\n/s)[1])) === JSON.stringify(ref), "page de jeu : données identiques");
check(JSON.stringify(JSON.parse(game.match(/const CAL = (\{.*?\});\n/s)[1]).pays) === JSON.stringify(cal.pays), "page de jeu : calendrier identique");
for (const [name, h] of [["règles", html], ["jeu", game]]) {
  const script = h.match(/<script>([\s\S]*)<\/script>/)[1];
  try { new vm.Script(script); check(true, `script de la page ${name} syntaxiquement valide`); } catch (e) { check(false, `script ${name} : ` + e.message); }
}

console.log(`\n${fails} échec(s)`);
process.exit(fails ? 1 : 0);
