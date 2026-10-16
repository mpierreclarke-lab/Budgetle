// Étape 5 — Vérification de la page construite (site/dist/regles.html).
// a) les données embarquées sont identiques à data/derived/profils_2024.json ;
// b) le treemap donne à chaque rectangle une surface proportionnelle à sa part (30 pays) ;
// c) chaque affirmation chiffrée des notes est vraie dans les données ;
// d) le script de la page se compile.
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { squarify } from "../site/js/treemap.js";
import { distanceMeters, compassDirection, proximityTradle } from "../site/js/geo.js";

const html = readFileSync(new URL("../site/dist/regles.html", import.meta.url), "utf8");
const ref = JSON.parse(readFileSync(new URL("../data/derived/profils_2024.json", import.meta.url)));
let fails = 0;
const check = (ok, msg) => { console.log(`${ok ? "OK   " : "ÉCHEC"} ${msg}`); if (!ok) fails++; };

// a) données embarquées
const embedded = JSON.parse(html.match(/const PROFILES = (\[.*?\]);\n/s)[1]);
check(JSON.stringify(embedded) === JSON.stringify(ref), "données embarquées identiques à profils_2024.json");

// b) surfaces du treemap
let worst = 0;
for (const p of ref) {
  for (const [W, H] of [[1000, 625], [380, 399]]) {
    const top = squarify(p.divisions.map((d) => ({ ...d, value: d.mio_eur })), { x: 0, y: 0, w: W, h: H });
    const all = [];
    for (const r of top) {
      if (r.code === "GF10") all.push(...squarify(r.detail.filter((k) => k.mio_eur > 0).map((k) => ({ ...k, value: k.mio_eur })), r));
      else all.push(r);
    }
    for (const t of all) worst = Math.max(worst, Math.abs((t.w * t.h) / (W * H) - t.part_du_total));
    const covered = all.reduce((s, t) => s + t.w * t.h, 0) / (W * H);
    if (Math.abs(covered - 1) > 1e-6) check(false, `${p.geo} : le treemap ne couvre pas tout le cadre (${covered})`);
  }
}
// Tolérance 0,01 point de part : les sous-catégories publiées somment à GF10 à ±0,004 % près (arrondis Eurostat)
check(worst < 1e-4, `surfaces proportionnelles aux parts (écart max ${(100 * worst).toFixed(4)} point) sur 30 pays × 2 formats`);

// c) affirmations des notes
const by = Object.fromEntries(ref.map((p) => [p.geo, p]));
const div = (g, c) => by[g].divisions.find((d) => d.code === c);
const sortBy = (f) => [...ref].sort((a, b) => f(b) - f(a)).map((p) => p.geo);
const tot = sortBy((p) => p.total.pc_gdp);
check(tot[1] === "FR" && tot[0] === "FI", `France 2ᵉ ratio de dépense, derrière la Finlande (${tot.slice(0, 3)})`);
check(Math.round(100 * div("FR", "GF10").part_du_total) === 41, "France : protection sociale = 41 % de la dépense");
check(Math.round(100 * div("FR", "GF10").detail[0].part_du_total) === 23, "France : vieillesse = 23 % de la dépense");
check(tot.at(-1) === "IE", "Irlande : ratio au PIB le plus bas");
check(div("CH", "GF07").pc_gdp === 2.2, "Suisse : santé 2,2 % du PIB");
const g01 = sortBy((p) => div(p.geo, "GF01").pc_gdp);
check(g01[0] === "HU" && div("HU", "GF01").pc_gdp === 10.0, "Hongrie : services généraux 10,0 %, plus haut niveau");
const g08 = sortBy((p) => div(p.geo, "GF08").pc_gdp);
check(div("HU", "GF08").pc_gdp === 2.5 && g08.indexOf("HU") <= 2, `Hongrie : culture 2,5 %, parmi les plus hauts (rang ${g08.indexOf("HU") + 1})`);
const g02 = sortBy((p) => div(p.geo, "GF02").pc_gdp);
check(g02[0] === "EE" && g02[1] === "PL" && g02[2] === "LV" && div("PL", "GF02").pc_gdp === 2.9 && div("LV", "GF02").pc_gdp === 2.7,
  `Défense : Estonie 3,7 %, puis Pologne 2,9 % et Lettonie 2,7 % (${g02.slice(0, 3)})`);
const allP = []; for (const a of ref) for (const b of ref) if (a.geo < b.geo) allP.push(proximityTradle(distanceMeters(a, b)));
check(Math.min(...allP) === 76 && Math.max(...allP) === 99, "échelle Tradle : proximités entre 76 % et 99 %");

// Exemple de partie (cible PT)
for (const g of ["DE", "IT", "ES"]) console.log(`      essai ${by[g].nom} → ${Math.round(distanceMeters(by[g], by.PT) / 1000)} km ${compassDirection(by[g], by.PT)}`);

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
