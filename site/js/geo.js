// Règles géographiques du jeu — reprise fidèle de Tradle (licence MIT, src/domain/geography.ts)
// Distance : loi sphérique des cosinus, rayon 6 378 137 m, comme geolib.getDistance (v3).
// Direction : cap loxodromique (geolib.getRhumbLineBearing), arrondi aux 8 points cardinaux.
// Ces fonctions sont vérifiées contre geolib par scripts/04_simulate.mjs.

const EARTH_RADIUS_M = 6378137;
const rad = (d) => (d * Math.PI) / 180;
const deg = (r) => (r * 180) / Math.PI;

export function distanceMeters(a, b) {
  const x = Math.sin(rad(b.lat)) * Math.sin(rad(a.lat)) +
    Math.cos(rad(b.lat)) * Math.cos(rad(a.lat)) * Math.cos(rad(a.lon) - rad(b.lon));
  return Math.round(Math.acos(Math.min(1, Math.max(-1, x))) * EARTH_RADIUS_M);
}

export function rhumbBearing(from, to) {
  let dLon = rad(to.lon) - rad(from.lon);
  const dPhi = Math.log(Math.tan(rad(to.lat) / 2 + Math.PI / 4) / Math.tan(rad(from.lat) / 2 + Math.PI / 4));
  if (Math.abs(dLon) > Math.PI) dLon = dLon > 0 ? -(2 * Math.PI - dLon) : 2 * Math.PI + dLon;
  return (deg(Math.atan2(dLon, dPhi)) + 360) % 360;
}

const DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"];
/** Direction à suivre depuis le pays proposé vers le pays mystère. */
export function compassDirection(guess, target) {
  return DIRS[Math.round(rhumbBearing(guess, target) / 45)];
}

/** Proximité Tradle : 100 % − distance / 20 000 km, plafonnée à 99 % si ce n'est pas la bonne réponse. */
export function proximityTradle(distanceM, maxM = 20_000_000) {
  const p = Math.round((Math.max(maxM - distanceM, 0) / maxM) * 100);
  return distanceM > 0 && p >= 100 ? 99 : p;
}

/** Variante « échelle européenne » : même formule, rapportée à la plus grande distance du jeu. */
export function proximityScaled(distanceM, maxM) {
  return proximityTradle(distanceM, maxM);
}

/** Carrés de partage Tradle : un vert par tranche de 20 %, un jaune si le reste ≥ 10. */
export function squares(p) {
  const g = Math.floor(p / 20), y = p - g * 20 >= 10 ? 1 : 0;
  return "🟩".repeat(g) + "🟨".repeat(y) + "⬜".repeat(5 - g - y);
}
