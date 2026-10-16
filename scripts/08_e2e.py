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
        ctx = b.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "fonts" not in m.text else None)

        # Partie n° 1 (Irlande) : erreurs de saisie, puis victoire au 2e essai
        pg.goto(BASE + "index.html#partie1")
        pg.fill("#guess", "Fra")
        check(pg.locator("#sugg li").first.inner_text() == "France", f"[{width}px] suggestion « Fra » → France")
        pg.keyboard.press("ArrowDown"); pg.keyboard.press("Enter")
        check(pg.locator(".g:not(.empty):not(.head)").count() == 1, f"[{width}px] 1er essai enregistré par le clavier")
        pg.fill("#guess", "Atlantide"); pg.keyboard.press("Enter")
        check("Pays inconnu" in pg.inner_text("#msg"), f"[{width}px] pays inconnu signalé")
        pg.fill("#guess", "france"); pg.click("#go")
        check("déjà été proposé" in pg.inner_text("#msg"), f"[{width}px] doublon signalé")
        pg.fill("#guess", "Irl")
        pg.locator("#sugg li", has_text="Irlande").dispatch_event("pointerdown")
        check(pg.is_visible("#end") and pg.inner_text("#end h2") == "Irlande", f"[{width}px] victoire : écran de fin « Irlande »")
        share = pg.input_value("#sharetxt")
        check(share.startswith("#Budgetle #1 2/6") and share.endswith("https://mpierreclarke-lab.github.io/Budgetle/"), f"[{width}px] texte de partage correct")
        check(pg.locator("#end li").count() >= 1, f"[{width}px] faits pédagogiques affichés")
        pg.reload()
        check(pg.locator(".g:not(.empty):not(.head)").count() == 2 and pg.is_visible("#end"), f"[{width}px] partie restaurée après rechargement")
        check(pg.evaluate("document.documentElement.scrollWidth") <= width, f"[{width}px] pas de défilement horizontal (jeu)")
        if SHOTS and width == 390:
            pg.screenshot(path=str(SHOTS / "jeu_fin_mobile.png"), full_page=True)

        # Partie n° 2 : défaite après six essais
        pg.goto("about:blank"); pg.goto(BASE + "index.html#partie2")
        target = pg.evaluate("CAL.pays[1]")
        wrong = [g for g in pg.evaluate("PROFILES.map(p => p.nom + '|' + p.geo)") if not g.endswith("|" + target)][:6]
        for w in wrong:
            pg.fill("#guess", w.split("|")[0]); pg.keyboard.press("Enter")
        check(pg.inner_text("#end .eyebrow") == "PERDU" or pg.inner_text("#end .eyebrow").lower() == "perdu", f"[{width}px] défaite après 6 essais")
        check(pg.input_value("#sharetxt").startswith("#Budgetle #2 X/6"), f"[{width}px] partage d'une défaite (X/6)")
        check(pg.is_hidden("#form"), f"[{width}px] saisie fermée en fin de partie")

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
