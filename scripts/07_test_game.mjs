// Tests de la logique de partie (site/js/game.js) et du calendrier.
import { readFileSync } from "node:fs";
import * as G from "../site/js/game.js";

const P = JSON.parse(readFileSync(new URL("../data/derived/profils_monde.json", import.meta.url)));
const CAL = JSON.parse(readFileSync(new URL("../data/derived/calendrier.json", import.meta.url)));
const DMAX = 20_000_000; // échelle mondiale de Tradle
const BY = Object.fromEntries(P.map((p) => [p.geo, p]));
let fails = 0;
const eq = (a, b, msg) => { const ok = JSON.stringify(a) === JSON.stringify(b); console.log(`${ok ? "OK   " : "ÉCHEC"} ${msg}${ok ? "" : ` → obtenu ${JSON.stringify(a)}, attendu ${JSON.stringify(b)}`}`); if (!ok) fails++; };

// Saisie
const idx = G.buildIndex(P);
eq(G.findCountry("  république TCHÈQUE ", idx), "CZ", "alias avec accents et majuscules");
eq(G.findCountry("Grece", idx), "EL", "« Grece » sans accent → Grèce (code Eurostat EL)");
eq(G.findCountry("Hollande", idx), "NL", "alias Hollande");
eq(G.findCountry("Atlantide", idx), null, "pays inconnu refusé");
eq(P.every((p) => G.findCountry(p.nom, idx) === p.geo), true, `les ${P.length} noms français sont reconnus`);
eq([G.findCountry("Etats-Unis", idx), G.findCountry("usa", idx), G.findCountry("United Kingdom", idx), G.findCountry("Coree du Sud", idx)], ["US", "US", "GB", "KR"], "noms sans accents, sigles et noms anglais");
eq(new Set([...idx.values()]).size, P.length, "chaque pays a au moins une entrée dans l'index");
eq(G.suggest("slo", P).map((p) => p.geo), ["SK", "SI"], "suggestions « slo » : Slovaquie, Slovénie");
eq(G.suggest("a", P).length, 6, "suggestions limitées à 6");
eq(G.suggest("thai", P).map((p) => p.geo), ["TH"], "suggestion « thai » → Thaïlande");
eq(G.suggest("fran", P, ["FR"]).length, 0, "un pays déjà proposé n'est plus suggéré");

// Calendrier
eq(G.dayNumber("2026-10-16", CAL), 1, "16/10/2026 = partie n° 1");
eq(G.dayNumber("2026-10-15", CAL), null, "pas de partie avant le début");
eq(G.dayNumber("2027-03-28", CAL), 164, "passage à l'heure d'été sans décalage (n° 164)");
eq(G.dayNumber("2027-12-09", CAL), 420, "dernière partie du calendrier (420 jours)");
eq(G.dayNumber("2027-12-10", CAL), null, "au-delà du calendrier : null");
eq(G.localDay(new Date(2026, 0, 5, 23, 59)), "2026-01-05", "date locale au format AAAA-MM-JJ");

// Déroulement
const T = BY.PT;
const BYG = BY;
const g1 = G.evaluate(BY.DE, T, DMAX), g4 = G.evaluate(BY.PT, T, DMAX);
eq([Math.round(g1.distance / 1000), g1.direction, g1.proximity], [1953, "SW", 90], "Allemagne → Portugal : 1 953 km, SW, 90 % (échelle 20 000 km)");
eq([g4.distance, g4.direction, g4.proximity], [0, null, 100], "bonne réponse : 0 km, 100 %");
eq(G.status([g1]), "playing", "partie en cours après une erreur");
eq(G.status([g1, g4]), "won", "partie gagnée");
eq(G.status(Array(6).fill(g1)), "lost", "partie perdue après 6 erreurs");
eq(G.shareText(1, [g1, g4], "https://x.test"), "#Budgetle #1 2/6\n🟩🟩🟩🟩🟨↙️\n🟩🟩🟩🟩🟩🎉\nhttps://x.test", "texte de partage (victoire)");
eq(G.shareText(3, Array(6).fill(g1), "").split("\n")[0], "#Budgetle #3 X/6", "texte de partage (défaite)");

// Faits de fin de partie : contrôle indépendant sur tous les pays (recalcul des rangs depuis les parts)
let factFail = 0, noFact = [];
for (const p of P) {
  const f = G.facts(p.geo, P);
  if (!f.length) noFact.push(p.geo);
  for (const line of f) {
    const d = p.divisions.find((x) => line.startsWith(x.label + " :"));
    const share = Math.round(1000 * d.part_du_total) / 10;
    const vals = P.map((q) => Math.round(1000 * q.divisions.find((x) => x.code === d.code).part_du_total) / 10);
    if (line.includes("médiane")) {
      const med = [...vals].sort((a, b) => a - b)[Math.floor(vals.length / 2)];
      if (!line.includes(med.toLocaleString("fr-FR", { minimumFractionDigits: 1 })) || !line.includes(share.toLocaleString("fr-FR", { minimumFractionDigits: 1 }))) factFail++;
      continue;
    }
    const rank = line.includes("plus forte") ? 1 + vals.filter((v) => v > share).length : 1 + vals.filter((v) => v < share).length;
    const said = +(line.match(/la (\d+)ᵉ part/)?.[1] ?? 1);
    if (rank !== said || rank > 10 || !line.includes(share.toLocaleString("fr-FR", { minimumFractionDigits: 1 }))) factFail++;
  }
}
eq(factFail, 0, `faits de fin de partie : rangs et valeurs recalculés indépendamment (${P.length} pays)`);
console.log(`      pays sans fait affiché : ${noFact.length ? noFact.join(", ") : "aucun"}`);
eq(G.dataNotes(BY.US).some((n) => n.includes("environnement")) && G.dataNotes(BY.US).some((n) => n.includes("pas publié")), true, "notes automatiques : États-Unis (fonction nulle, détail absent)");
eq(G.dataNotes(BY.UA).some((n) => n.startsWith("Comptes tenus en caisse")), true, "notes automatiques : Ukraine en caisse");
eq(G.dataNotes(BY.FR).length, 1, "notes automatiques : France, source seule");
for (const g of ["EE", "FR", "US", "UA"]) console.log(`      ${g} :`, G.facts(g, P).join(" "));
console.log(`\n${fails} échec(s)`);
process.exit(fails ? 1 : 0);
