// Tests de la logique de partie (site/js/game.js) et du calendrier.
import { readFileSync } from "node:fs";
import * as G from "../site/js/game.js";

const P = JSON.parse(readFileSync(new URL("../data/derived/profils_2024.json", import.meta.url)));
const CAL = JSON.parse(readFileSync(new URL("../data/derived/calendrier.json", import.meta.url)));
const { distance_max_m: DMAX } = JSON.parse(readFileSync(new URL("../data/derived/distance_max_m.json", import.meta.url)));
const BY = Object.fromEntries(P.map((p) => [p.geo, p]));
let fails = 0;
const eq = (a, b, msg) => { const ok = JSON.stringify(a) === JSON.stringify(b); console.log(`${ok ? "OK   " : "ÉCHEC"} ${msg}${ok ? "" : ` → obtenu ${JSON.stringify(a)}, attendu ${JSON.stringify(b)}`}`); if (!ok) fails++; };

// Saisie
const idx = G.buildIndex(P);
eq(G.findCountry("  république TCHÈQUE ", idx), "CZ", "alias avec accents et majuscules");
eq(G.findCountry("Grece", idx), "EL", "« Grece » sans accent → Grèce (code Eurostat EL)");
eq(G.findCountry("Hollande", idx), "NL", "alias Hollande");
eq(G.findCountry("Atlantide", idx), null, "pays inconnu refusé");
eq(P.every((p) => G.findCountry(p.nom, idx) === p.geo), true, "les 30 noms français sont reconnus");
eq(G.suggest("slo", P).map((p) => p.geo), ["SK", "SI"], "suggestions « slo » : Slovaquie, Slovénie");
eq(G.suggest("land", P).map((p) => p.geo).sort(), ["CH", "FI", "IE", "IS", "NL", "PL"].sort(), "suggestions par contenu (alias anglais, dont Switzerland)");
eq(G.suggest("fr", P, ["FR"]).length, 0, "un pays déjà proposé n'est plus suggéré");

// Calendrier
eq(G.dayNumber("2026-10-16", CAL), 1, "16/10/2026 = partie n° 1");
eq(G.dayNumber("2026-10-15", CAL), null, "pas de partie avant le début");
eq(G.dayNumber("2027-03-28", CAL), 164, "passage à l'heure d'été sans décalage (n° 164)");
eq(G.dayNumber("2027-10-10", CAL), 360, "dernière partie du calendrier");
eq(G.dayNumber("2027-10-11", CAL), null, "au-delà du calendrier : null");
eq(G.localDay(new Date(2026, 0, 5, 23, 59)), "2026-01-05", "date locale au format AAAA-MM-JJ");

// Déroulement
const T = BY.PT;
const g1 = G.evaluate(BY.DE, T, DMAX), g4 = G.evaluate(BY.PT, T, DMAX);
eq([Math.round(g1.distance / 1000), g1.direction, g1.proximity], [1953, "SW", 59], "Allemagne → Portugal : 1 953 km, SW, 59 %");
eq([g4.distance, g4.direction, g4.proximity], [0, null, 100], "bonne réponse : 0 km, 100 %");
eq(G.status([g1]), "playing", "partie en cours après une erreur");
eq(G.status([g1, g4]), "won", "partie gagnée");
eq(G.status(Array(6).fill(g1)), "lost", "partie perdue après 6 erreurs");
eq(G.shareText(1, [g1, g4], "https://x.test"), "#Budgetle #1 2/6\n🟩🟩🟨⬜⬜↙️\n🟩🟩🟩🟩🟩🎉\nhttps://x.test", "texte de partage (victoire)");
eq(G.shareText(3, Array(6).fill(g1), "").split("\n")[0], "#Budgetle #3 X/6", "texte de partage (défaite)");

// Faits de fin de partie : contrôle indépendant sur les 30 pays (recalcul des rangs depuis les parts)
let factFail = 0, noFact = [];
for (const p of P) {
  const f = G.facts(p.geo, P);
  if (!f.length) noFact.push(p.geo);
  for (const line of f) {
    const d = p.divisions.find((x) => line.startsWith(x.label + " :"));
    const share = Math.round(1000 * d.part_du_total) / 10;
    const vals = P.map((q) => Math.round(1000 * q.divisions.find((x) => x.code === d.code).part_du_total) / 10);
    const rank = line.includes("plus forte") ? 1 + vals.filter((v) => v > share).length : 1 + vals.filter((v) => v < share).length;
    const said = +(line.match(/la (\d+)ᵉ part/)?.[1] ?? 1);
    if (rank !== said || rank > 5 || !line.includes(share.toLocaleString("fr-FR", { minimumFractionDigits: 1 }))) factFail++;
  }
}
eq(factFail, 0, "faits de fin de partie : rangs et valeurs recalculés indépendamment (30 pays)");
console.log(`      pays sans fait affiché : ${noFact.length ? noFact.join(", ") : "aucun"}`);
for (const g of ["EE", "FR", "IE", "CH"]) console.log(`      ${g} :`, G.facts(g, P).join(" "));
console.log(`\n${fails} échec(s)`);
process.exit(fails ? 1 : 0);
