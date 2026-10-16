"""Contrôles de sécurité automatiques (exécutés en intégration continue avant chaque publication).

Pages publiques (site/dist/*.html) :
  1. une politique de sécurité de contenu (CSP) est présente, sans 'unsafe-inline' ni 'unsafe-eval' pour les scripts ;
  2. chaque script en ligne correspond à une empreinte autorisée par la CSP, et aucun script n'est chargé de l'extérieur ;
  3. aucune ressource (script, style, police, image, cadre) n'est chargée depuis un autre site ;
  4. aucune redirection ni ouverture de fenêtre : pas de meta refresh, location.href/assign/replace, window.open,
     document.write, eval, new Function, iframe, object, embed ;
  5. tout lien qui ouvre un nouvel onglet porte rel="noopener" ;
  6. Referrer-Policy « no-referrer » présente.
Dépôt :
  7. aucun secret apparent (jetons GitHub, clés AWS, clés privées) dans les fichiers versionnés ;
  8. les actions GitHub sont épinglées par empreinte de commit complète (40 caractères).
"""
import base64
import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
fails = []


def check(ok, msg):
    print(("OK    " if ok else "ÉCHEC ") + msg)
    if not ok:
        fails.append(msg)


for page in sorted((ROOT / "site/dist").glob("*.html")):
    h = page.read_text(encoding="utf-8")
    n = page.name
    m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)"', h)
    check(bool(m), f"{n} : CSP présente")
    csp = m.group(1) if m else ""
    script_src = re.search(r"script-src ([^;]+)", csp)
    check(bool(script_src) and "unsafe" not in script_src.group(1), f"{n} : scripts sans 'unsafe-inline' ni 'unsafe-eval'")
    for d in ("default-src 'none'", "base-uri 'none'", "object-src 'none'", "form-action 'none'", "connect-src 'none'"):
        check(d in csp, f"{n} : CSP contient {d}")
    scripts = re.findall(r"<script([^>]*)>(.*?)</script>", h, re.S)
    allowed = set(re.findall(r"'sha256-([^']+)'", csp))
    for attrs, body in scripts:
        check("src=" not in attrs, f"{n} : aucun script externe")
        digest = base64.b64encode(hashlib.sha256(body.encode()).digest()).decode()
        check(digest in allowed, f"{n} : script en ligne autorisé par son empreinte")
    res = re.findall(r'<(?:script|link|img|iframe|source|video|audio|embed|object)\b[^>]*(?:src|href)="(https?:)?//', h)
    check(not res, f"{n} : aucune ressource chargée depuis un autre site")
    check(not re.search(r"https?://", re.sub(r'<a [^>]*href="https://[^"]+"', "", "\n".join(b for _, b in scripts)
                                             ).replace("https://mpierreclarke-lab.github.io/Budgetle/", "")),
          f"{n} : aucune adresse externe dans les scripts (hors adresse de partage du jeu)")
    bad = re.findall(r'http-equiv="refresh"|location\.(?:href\s*=|assign|replace)|window\.open|document\.write|\beval\(|new Function|<iframe|<object|<embed', h)
    check(not bad, f"{n} : aucune redirection ni code dynamique dangereux {sorted(set(bad))}")
    blank = re.findall(r"<a [^>]*target=\"_blank\"[^>]*>", h)
    check(all('rel="noopener' in a for a in blank), f"{n} : liens vers nouvel onglet avec rel=noopener ({len(blank)})")
    check('<meta name="referrer" content="no-referrer">' in h, f"{n} : Referrer-Policy no-referrer")

files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
SECRET = re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----")
leaks = [f for f in files if (ROOT / f).is_file() and (ROOT / f).stat().st_size < 5_000_000
         and SECRET.search((ROOT / f).read_text(encoding="utf-8", errors="ignore"))]
check(not leaks, f"aucun secret apparent dans les {len(files)} fichiers versionnés {leaks}")
for wf in (ROOT / ".github/workflows").glob("*.yml"):
    uses = re.findall(r"uses:\s*([^\s#]+)", wf.read_text())
    check(all(re.search(r"@[0-9a-f]{40}$", u) for u in uses), f"{wf.name} : {len(uses)} actions épinglées par empreinte de commit")

print(f"\n{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
