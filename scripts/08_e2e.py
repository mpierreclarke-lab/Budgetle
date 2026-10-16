"""Test de bout en bout dans un vrai navigateur (Chromium sans interface, via Playwright).

Sert site/dist en local, joue une partie gagnée et une partie perdue, vérifie la sauvegarde
après rechargement, les messages d'erreur, et l'absence d'erreur et de défilement horizontal.
Usage : python3 scripts/08_e2e.py [dossier_captures]
"""
import functools
import http.server
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHOTS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "site/dist"))
handler.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_port}/"
fails = 0


def check(ok, msg):
    global fails
    print(("OK    " if ok else "ÉCHEC ") + msg)
    fails += not ok


with sync_playwright() as p:
    b = p.chromium.launch()
    for width, scheme in [(390, "dark"), (1200, "light")]:
        ctx = b.new_context(viewport={"width": width, "height": 844 if width < 600 else 900}, color_scheme=scheme)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "fonts" not in m.text else None)

        # Partie n° 1 : erreurs de saisie, puis victoire au 2e essai (réponse lue dans le calendrier de la page)
        pg.goto(BASE + "index.html#partie1")
        answer = pg.evaluate("BY[CAL.pays[0]].nom")
        assert answer != "France", "le test suppose que la partie n° 1 n'est pas la France"
        pg.fill("#guess", "Fra")
        check(pg.locator("#sugg li").first.inner_text() == "France", f"[{width}px] suggestion « Fra » → France")
        top = pg.evaluate("document.getElementById('guess').getBoundingClientRect().bottom")
        check(top <= (844 if width < 600 else 900), f"[{width}px] champ de saisie visible sans défiler (bas à {top:.0f} px)")
        pg.keyboard.press("ArrowDown"); pg.keyboard.press("Enter")
        pg.wait_for_timeout(300)
        check(pg.locator(".reveal-row .sq span").count() == 5, f"[{width}px] révélation : 5 carrés affichés un par un")
        pg.wait_for_timeout(1500)
        check(pg.locator(".reveal-row").count() == 0 and "km" in pg.locator("#slots .g").first.inner_text(), f"[{width}px] après la révélation : distance, direction, proximité")
        check(pg.locator("#slots .g").count() == 1, f"[{width}px] 1er essai enregistré par le clavier")
        pg.fill("#guess", "Atlantide"); pg.keyboard.press("Enter")
        check("Pays inconnu" in pg.inner_text("#msg"), f"[{width}px] pays inconnu signalé")
        pg.fill("#guess", "france"); pg.click("#go")
        check("déjà été proposé" in pg.inner_text("#msg"), f"[{width}px] doublon signalé")
        pg.fill("#guess", answer[:4])
        pg.locator("#sugg li", has_text=answer).first.dispatch_event("pointerdown")
        pg.wait_for_timeout(1800)
        check(pg.is_visible("#end") and pg.inner_text("#end h2") == answer, f"[{width}px] victoire : écran de fin « {answer} »")
        check(pg.locator(".tile").first.inner_text().strip().endswith("%"), f"[{width}px] les rectangles affichent une part en %")
        pg.locator(".tile").first.hover()
        check("% du PIB" in pg.inner_text("#mystery .detail") and "€" in pg.inner_text("#mystery .detail"), f"[{width}px] survol : % du PIB et montant affichés")
        check(pg.locator(".recap div").count() == 2, f"[{width}px] fin de partie : les carrés reviennent (2 lignes)")
        share = pg.input_value("#sharetxt")
        check(share.startswith("#Budgetle #1 2/6") and share.endswith("https://mpierreclarke-lab.github.io/Budgetle/"), f"[{width}px] texte de partage correct")
        check(pg.locator("#end li").count() >= 1, f"[{width}px] faits pédagogiques affichés")
        pg.reload()
        check(pg.locator("#slots .g").count() == 2 and pg.is_visible("#end"), f"[{width}px] partie restaurée après rechargement")
        check(pg.evaluate("document.documentElement.scrollWidth") <= width, f"[{width}px] pas de défilement horizontal (jeu)")
        if SHOTS and width == 390:
            pg.screenshot(path=str(SHOTS / "jeu_fin_mobile.png"), full_page=True)

        # Partie n° 2 : défaite après six essais
        pg.goto("about:blank"); pg.goto(BASE + "index.html#partie2")
        target = pg.evaluate("CAL.pays[1]")
        wrong = [g for g in pg.evaluate("PROFILES.map(p => p.nom + '|' + p.geo)") if not g.endswith("|" + target)][:6]
        for w in wrong:
            pg.fill("#guess", w.split("|")[0]); pg.keyboard.press("Enter"); pg.wait_for_timeout(1700)
        check(pg.inner_text("#end .eyebrow") == "PERDU" or pg.inner_text("#end .eyebrow").lower() == "perdu", f"[{width}px] défaite après 6 essais")
        check(pg.input_value("#sharetxt").startswith("#Budgetle #2 X/6"), f"[{width}px] partage d'une défaite (X/6)")
        check(pg.is_hidden("#form"), f"[{width}px] saisie fermée en fin de partie")

        # Parties infinies : tirage, victoire, pays suivant, reprise après rechargement
        pg.goto("about:blank"); pg.goto(BASE + "index.html#infini")
        check(pg.get_attribute("#mode-infini", "aria-current") == "page", f"[{width}px] infini : mode actif")
        seen = set()
        for k in range(3):
            geo = pg.evaluate("target.geo"); seen.add(geo)
            nom = pg.evaluate("target.nom")
            pg.fill("#guess", nom); pg.keyboard.press("Enter"); pg.wait_for_timeout(1700)
            check(pg.inner_text("#end h2") == nom and pg.is_visible("#next"), f"[{width}px] infini : partie {k + 1} gagnée ({nom}), bouton « Pays suivant »")
            pg.click("#next"); pg.wait_for_timeout(200)
        check(len(seen) == 3 and pg.evaluate("target.geo") not in seen, f"[{width}px] infini : nouveaux pays à chaque partie ({', '.join(sorted(seen))})")
        check(pg.locator("#slots .g").count() == 0 and pg.is_visible("#form"), f"[{width}px] infini : essais remis à zéro")
        cur = pg.evaluate("target.geo"); pg.reload(); pg.wait_for_timeout(300)
        check(pg.evaluate("target.geo") == cur and "Partie infinie n° 4" in pg.inner_text("#num"), f"[{width}px] infini : même pays et compteur après rechargement")
        check("3 pays trouvés sur 3" in (pg.evaluate("(()=>{const i=JSON.parse(localStorage.getItem('budgetle-v2-infini'));return i.won+' pays trouvés sur '+i.played})()")), f"[{width}px] infini : score cumulé")

        # Petit écran : pendant la révélation, la ligne de l'essai reste visible juste au-dessus de la saisie
        if width < 600:
            pg.set_viewport_size({"width": 375, "height": 560})
            pg.goto("about:blank"); pg.goto(BASE + "index.html#infini"); pg.wait_for_timeout(300)
            pg.fill("#guess", "Islande" if pg.evaluate("target.geo") != "IS" else "Japon"); pg.keyboard.press("Enter"); pg.wait_for_timeout(400)
            box = pg.evaluate("(()=>{const a=document.querySelector('.reveal-row').getBoundingClientRect(),b=document.getElementById('guess').getBoundingClientRect();return [a.top,a.bottom,b.top,b.bottom,innerHeight]})()")
            check(0 <= box[0] and box[1] <= box[2] and box[3] <= box[4], f"[375×560] révélation visible au-dessus de la saisie collée en bas {[round(x) for x in box]}")
            pg.wait_for_timeout(1500)
            check(pg.inner_text(".g.pending").startswith("Essai 2 sur 6"), "[375×560] ligne du prochain essai affichée au-dessus de la saisie")
            pg.locator(".tile").first.hover()
            check(len(pg.inner_text("#mystery .detail .desc")) > 10, "[375×560] survol : courte explication de la catégorie")
            pg.set_viewport_size({"width": width, "height": 844})

        # Partie du jour et page de règles
        pg.goto(BASE + "index.html")
        n = pg.inner_text("#num")
        check(n.startswith("Partie n° "), f"[{width}px] partie du jour affichée ({n})")
        if SHOTS and width == 390:
            pg.screenshot(path=str(SHOTS / "jeu_debut_mobile.png"), full_page=True)
        pg.goto(BASE + "regles.html")
        check(pg.locator(".tile").count() > 20, f"[{width}px] page de règles : treemaps dessinés")
        check(pg.evaluate("document.documentElement.scrollWidth") <= width, f"[{width}px] pas de défilement horizontal (règles)")
        check(not errors, f"[{width}px] aucune erreur JavaScript {errors[:2]}")
        ctx.close()
    b.close()
srv.shutdown()
print(f"\n{fails} échec(s)")
sys.exit(1 if fails else 0)
