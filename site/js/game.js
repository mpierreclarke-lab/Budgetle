// Logique de partie de Budgetle — fonctions pures, sans accès à la page (testées par scripts/07_test_game.mjs).
import { distanceMeters, compassDirection, proximityScaled, squares } from "./geo.js";

export const MAX_TRIES = 6;

// Autres noms acceptés à la saisie (anglais et variantes usuelles)
export const ALIASES = {
  AT: ["Austria"], BE: ["Belgium"], BG: ["Bulgaria"], CH: ["Switzerland", "Confédération suisse"],
  CY: ["Cyprus"], CZ: ["République tchèque", "Czechia", "Czech Republic"], DE: ["Germany"],
  DK: ["Denmark"], EE: ["Estonia"], EL: ["Greece", "Hellade"], ES: ["Spain"], FI: ["Finland"],
  FR: [], HR: ["Croatia"], HU: ["Hungary"], IE: ["Ireland", "Eire"], IS: ["Iceland"], IT: ["Italy"],
  LT: ["Lithuania"], LU: [], LV: ["Latvia"], MT: ["Malta"], NL: ["Netherlands", "Hollande"],
  NO: ["Norway"], PL: ["Poland"], PT: [], RO: ["Romania"], SE: ["Sweden"], SI: ["Slovenia"], SK: ["Slovakia"],
  US: ["USA", "Amérique"], GB: ["Angleterre", "Grande-Bretagne", "UK"], KR: ["Corée"], AE: ["Émirats"],
  BY: ["Bélarus"], CN: ["République populaire de Chine"], DO: ["Dominicaine"], ZA: ["South Africa"],
};

export function normalize(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z]/g, "");
}

export function buildIndex(profiles) {
  const idx = new Map();
  for (const p of profiles) for (const n of [p.nom, p.geo, ...(ALIASES[p.geo] || []), ...(p.alias || [])]) idx.set(normalize(n), p.geo);
  return idx;
}

export function findCountry(input, idx) {
  return idx.get(normalize(input)) ?? null;
}

/** Suggestions : noms français commençant par la saisie, puis ceux qui la contiennent ; hors pays déjà proposés. */
export function suggest(input, profiles, exclude = []) {
  const q = normalize(input);
  if (!q) return [];
  const pool = profiles.filter((p) => !exclude.includes(p.geo));
  const names = (p) => [p.nom, ...(ALIASES[p.geo] || []), ...(p.alias || [])].filter((n) => n.length > 3).map(normalize);
  const starts = pool.filter((p) => names(p).some((n) => n.startsWith(q)));
  const contains = pool.filter((p) => !starts.includes(p) && names(p).some((n) => n.includes(q)));
  return [...starts, ...contains].sort((a, b) => starts.includes(b) - starts.includes(a) || a.nom.localeCompare(b.nom, "fr")).slice(0, 6);
}

/** Date locale du joueur au format AAAA-MM-JJ (comme Tradle : le jour change à minuit chez le joueur). */
export function localDay(d = new Date()) {
  const z = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${z(d.getMonth() + 1)}-${z(d.getDate())}`;
}

/** Numéro de partie (1 = date de début) ; null avant le début ou après la fin du calendrier. */
export function dayNumber(day, calendar) {
  const ms = Date.UTC(...day.split("-").map((x, i) => +x - (i === 1 ? 1 : 0))) -
    Date.UTC(...calendar.debut.split("-").map((x, i) => +x - (i === 1 ? 1 : 0)));
  const n = Math.round(ms / 86400000) + 1;
  return n >= 1 && n <= calendar.pays.length ? n : null;
}

export function evaluate(guess, target, dmax) {
  const distance = distanceMeters(guess, target);
  return {
    geo: guess.geo,
    distance,
    direction: distance === 0 ? null : compassDirection(guess, target),
    proximity: distance === 0 ? 100 : proximityScaled(distance, dmax),
  };
}

export function status(guesses) {
  if (guesses.some((g) => g.distance === 0)) return "won";
  return guesses.length >= MAX_TRIES ? "lost" : "playing";
}

const ARROWS = { N: "⬆️", NE: "↗️", E: "➡️", SE: "↘️", S: "⬇️", SW: "↙️", W: "⬅️", NW: "↖️" };
export function shareText(n, guesses, url) {
  const st = status(guesses);
  const lines = guesses.map((g) => squares(g.proximity) + (g.distance === 0 ? "🎉" : ARROWS[g.direction]));
  return [`#Budgetle #${n} ${st === "won" ? guesses.length : "X"}/${MAX_TRIES}`, ...lines, url].filter(Boolean).join("\n");
}

/** Rangs d'une fonction parmi tous les pays, selon sa part dans la dépense publique totale
 *  (comparable même quand le PIB est atypique, comme en Irlande) : high = 1 pour la part la plus forte,
 *  low = 1 pour la plus faible, avec le nombre d'ex aequo (parts arrondies au dixième de point). */
export function rankOf(code, geo, profiles) {
  const val = (p) => Math.round(1000 * p.divisions.find((d) => d.code === code).part_du_total) / 10;
  const me = val(profiles.find((p) => p.geo === geo));
  return {
    value: me,
    high: 1 + profiles.filter((p) => val(p) > me).length,
    low: 1 + profiles.filter((p) => val(p) < me).length,
    ties: profiles.filter((p) => p.geo !== geo && val(p) === me).length,
  };
}

const fmt1 = (v) => v.toLocaleString("fr-FR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const ord = (r) => (r === 1 ? "" : `${r}ᵉ `);
const tie = (r) => (r.ties ? `, à égalité avec ${r.ties} autre${r.ties > 1 ? "s" : ""} pays` : "");
const TOP = 10;

/** Faits vérifiables pour l'écran de fin : la fonction où la part du pays est la plus forte
 *  (relativement aux autres pays) et celle où elle est la plus faible, si elles sont dans le top 5. */
export function facts(geo, profiles) {
  const n = profiles.length;
  const p = profiles.find((x) => x.geo === geo);
  // Les fonctions publiées à 0 (non isolées dans les comptes du pays) ne donnent pas lieu à un fait
  const r = p.divisions.filter((d) => d.mio_eur > 0).map((d) => ({ d, ...rankOf(d.code, geo, profiles) }));
  const hi = [...r].sort((a, b) => a.high - b.high || b.value - a.value)[0];
  const lo = r.filter((x) => x !== hi).sort((a, b) => a.low - b.low || a.value - b.value)[0];
  const out = [];
  if (hi.high <= TOP) out.push(`${hi.d.label} : ${fmt1(hi.value)} % de la dépense publique, la ${ord(hi.high)}part la plus forte des ${n} pays${tie(hi)}.`);
  if (lo.low <= TOP) out.push(`${lo.d.label} : ${fmt1(lo.value)} % de la dépense publique, la ${ord(lo.low)}part la plus faible des ${n} pays${tie(lo)}.`);
  if (!out.length) {
    // Profil proche de la moyenne : on signale la fonction qui s'écarte le plus de la médiane des pays du jeu
    const med = (code) => {
      const v = profiles.map((q) => rankOf(code, q.geo, profiles).value).sort((a, b) => a - b);
      return v[Math.floor(v.length / 2)];
    };
    const far = r.map((x) => ({ ...x, med: med(x.d.code) })).sort((a, b) => Math.abs(b.value / b.med - 1) - Math.abs(a.value / a.med - 1))[0];
    out.push(`${far.d.label} : ${fmt1(far.value)} % de la dépense publique, contre une médiane de ${fmt1(far.med)} % pour les ${n} pays.`);
  }
  return out;
}

/** Notes de lecture automatiques pour l'écran de fin : source, année, base comptable, lacunes du détail. */
export function dataNotes(p) {
  const out = [`Source : ${p.source}, données ${p.annee}${p.provisoire ? " (provisoires)" : ""}.`];
  if (p.base_comptable === "caisse") out.push("Comptes tenus en caisse : une dépense est enregistrée quand elle est payée, et non quand elle est engagée comme dans la plupart des autres pays du jeu.");
  if (!p.divisions[9].detail) out.push("Le détail de la protection sociale (retraites, famille, chômage…) n'est pas publié pour ce pays.");
  const zeros = p.divisions.filter((d) => d.mio_eur === 0).map((d) => d.label.toLowerCase());
  if (zeros.length) out.push(`Dépense nulle dans les données publiées pour : ${zeros.join(", ")}. La fonction n'est pas isolée dans les comptes du pays : ces dépenses figurent dans d'autres rubriques.`);
  if (p.devise && p.devise !== "EUR" && p.taux_eur) out.push(`Montants convertis en euros au taux moyen de ${p.annee} : 1 € = ${p.taux_eur.toLocaleString("fr-FR", { maximumSignificantDigits: 5 })} ${p.devise} (FMI).`);
  return out;
}
