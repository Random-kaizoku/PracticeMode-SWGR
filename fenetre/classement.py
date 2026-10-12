"""Classement en ligne (v0.9.8) : publier ses temps, lire les classements.

Le serveur (serveur/classement/worker.js) tourne chez Cloudflare. Seule cette
fenêtre lui parle, et seulement quand le joueur clique : le jeu ne sait rien
de ce classement, totalement séparé des classements officiels. On envoie le
pseudo choisi par le joueur (comme sur une borne d'arcade) et le détail de la
course, rien d'autre (rien de Steam, rien sur le PC).

4 classements pour chaque circuit + véhicule + nombre de tours :
    solo-sans  seul (contre-la-montre), sans build
    solo-avec  seul, avec un build
    ia-sans    contre des IA, sans build
    ia-avec    contre des IA, avec un build
« Sans build » : les 6 stats à 0, aucune capacité, pas de capacité de crash,
aucun affixe, aucun buff de pilote (même règle que le serveur, qui décide).

Le pseudo appartient à la première fenêtre qui l'a utilisé : elle tire un
« jeton » au hasard (gardé dans PracticeMode.ini) et l'envoie avec chaque
temps. Personne d'autre ne peut publier sous ce pseudo.

Ce module ne touche pas à l'interface : les appels réseau se font dans une
tâche de fond de la fenêtre. Les erreurs sont des codes (« pseudo_pris »,
« reseau »…) que la fenêtre traduit (langues.py, « err_classement »).
"""
import http.client
import json
import re
import secrets
import string
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

# Adresse du serveur (https://<nom>.<compte>.workers.dev), à remplir une fois
# le serveur en ligne (voir serveur/classement/LISEZ-MOI.md). Chacun peut aussi
# la changer dans l'onglet Classement.
URL_PAR_DEFAUT = ""
DELAI = 8          # secondes au maximum pour chaque appel au serveur
API = 1            # version des adresses du serveur comprise par cette fenêtre

CATEGORIES = ("solo-sans", "solo-avec", "ia-sans", "ia-avec")
VEHICULES = ("motojet", "voiture", "skimmer", "avion")
OPTIONS = ("boost", "ramjet", "pannes", "crashs_illimites")
RE_PSEUDO = re.compile(r"^[A-Z0-9][A-Z0-9 ._-]{1,10}[A-Z0-9]$")   # comme le serveur
RE_NOM = re.compile(r"^[A-Za-z0-9_]{3,80}$")
PSEUDO_MAX = 12
PERMIS = set(string.ascii_uppercase + string.digits + " ._-")


class ErreurClassement(Exception):
    """Un appel au serveur a échoué. `code` : celui du serveur (« pseudo_pris »…)
    ou « adresse » (pas d'adresse valable), « reseau » (pas de réponse),
    « reponse » (réponse illisible), « api » (serveur trop récent)."""

    def __init__(self, code, detail=""):
        super().__init__(f"{code} {detail}".strip())
        self.code = code
        self.detail = detail


# ─────────────────────────────────────────────────────────────────────────
#  PSEUDO ET JETON
# ─────────────────────────────────────────────────────────────────────────
def normaliser_pseudo(texte):
    """« Élodie » → « ELODIE » : majuscules, sans accents, espaces simples."""
    texte = unicodedata.normalize("NFD", str(texte or ""))
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    return " ".join(texte.upper().split())


def nettoyer_saisie(texte):
    """Pendant la frappe du pseudo : majuscules sans accents, caractères permis
    seulement, 12 au plus. (Espaces du début et de la fin : retirés à l'envoi.)"""
    texte = unicodedata.normalize("NFD", str(texte or ""))
    texte = "".join(c for c in texte if not unicodedata.combining(c)).upper()
    return "".join(c for c in texte if c in PERMIS)[:PSEUDO_MAX]


def pseudo_valide(pseudo):
    """3 à 12 caractères : lettres A-Z, chiffres, et « espace . _ - » au milieu.
    (Les mots grossiers sont refusés par le serveur.)"""
    return bool(RE_PSEUDO.match(pseudo or ""))


def nouveau_jeton():
    """Le jeton de cette fenêtre : 32 caractères au hasard."""
    return secrets.token_urlsafe(24)


# ─────────────────────────────────────────────────────────────────────────
#  TEMPS
# ─────────────────────────────────────────────────────────────────────────
def texte_vers_ms(texte):
    """« 1:15.169 » ou « 75.169 » → 75169 (millisecondes), sinon None."""
    texte = (texte or "").strip().replace(",", ".")
    m = re.fullmatch(r"(?:(\d+):)?(\d+(?:\.\d+)?)", texte)
    if not m:
        return None
    ms = round((int(m.group(1) or 0) * 60 + float(m.group(2))) * 1000)
    return ms if ms > 0 else None


def ms_vers_texte(ms):
    """75169 → « 1:15.169 » (comme le mod)."""
    if not isinstance(ms, int) or ms <= 0:
        return "-"
    minutes, reste = divmod(ms, 60000)
    return f"{minutes}:{reste / 1000:06.3f}"


def ecart_texte(ms):
    """Écart avec le premier : 1234 → « +1.234 »."""
    return f"+{ms / 1000:.3f}" if isinstance(ms, int) and ms > 0 else ""


# ─────────────────────────────────────────────────────────────────────────
#  CATÉGORIE ET ENVOI
# ─────────────────────────────────────────────────────────────────────────
def sans_build(build):
    return (all(n == 0 for n in build.get("niveaux", [])) and not build.get("capacites")
            and not build.get("crash") and not build.get("affixes") and not build.get("traits"))


def categorie(adversaires, build):
    """« solo-sans », « ia-avec »… (même règle que le serveur)."""
    return ("ia" if adversaires > 0 else "solo") + "-" + ("sans" if sans_build(build) else "avec")


def build_de_detail(detail):
    """Colonne « Détail du build » de temps.csv (déjà découpée en dictionnaire)
    → build à envoyer, ou None si la course n'a pas son détail (fichier
    d'avant la v0.9.6, course lancée hors du mod)."""
    niveaux = [n.strip() for n in (detail.get("niveaux") or "").split(",")]
    if len(niveaux) != 6 or not all(n.isdigit() for n in niveaux):
        return None
    liste = lambda cle: [x for x in (detail.get(cle) or "").split("|") if x]
    options = {cle: int(detail[cle]) for cle in OPTIONS if detail.get(cle) in ("0", "1")}
    return {"niveaux": [int(n) for n in niveaux], "capacites": liste("capacites"), "crash": detail.get("crash") or "",
            "affixes": liste("affixes"), "traits": liste("traits"), "style": detail.get("style") or "",
            "options": options}


def preparer_envoi(ligne, circuit, vehicule, pilote, pseudo, jeton, version):
    """Une ligne de temps.csv (dictionnaire de la fenêtre, avec « _detail »)
    → (envoi, None) prêt à publier, ou (None, raison) si ce temps ne peut pas
    l'être. `circuit` : nom interne (TRAK_…), `vehicule` : clé (motojet…),
    `pilote` : nom interne (DA_…) ou « » ; retrouvés par la fenêtre dans le catalogue."""
    detail = ligne.get("_detail") or {}
    if (ligne.get("Save state") or "").strip().lower() == "oui":
        return None, "save_state"
    build = build_de_detail(detail)
    if build is None:
        return None, "sans_detail"
    if not circuit or not RE_NOM.match(circuit):
        return None, "circuit_inconnu"
    if vehicule not in VEHICULES:
        return None, "vehicule_inconnu"
    tours = (ligne.get("Nb tours") or "").strip()
    temps = texte_vers_ms(ligne.get("Secondes")) or texte_vers_ms(ligne.get("Temps"))
    if not tours.isdigit() or not 1 <= int(tours) <= 20 or not temps:
        return None, "temps_invalide"
    pseudo = normaliser_pseudo(pseudo)
    if not pseudo_valide(pseudo):
        return None, "pseudo_invalide"
    adversaires = int(detail["adversaires"]) if (detail.get("adversaires") or "").isdigit() else 0
    position = detail.get("position") or ""
    tours_ms = [texte_vers_ms(x) for x in (ligne.get("Détail des tours") or "").split()]
    envoi = {
        "pseudo": pseudo,
        "jeton": jeton,
        "circuit": circuit,
        "vehicule": vehicule,
        "tours": int(tours),
        "temps_ms": temps,
        "meilleur_tour_ms": texte_vers_ms(ligne.get("Meilleur tour")),
        "tours_ms": [x for x in tours_ms if x],
        "pilote": pilote if pilote and RE_NOM.match(pilote) else "",
        "adversaires": adversaires,
        "difficulte": detail.get("difficulte", "") if adversaires else "",
        "position": int(position) if adversaires and position.isdigit() else None,
        "save_state": False,
        "build": build,
        "version": version,
        "date_course": (ligne.get("Date") or "").strip(),
    }
    return envoi, None


def cle_publication(ligne):
    """Ce qui repère une course de temps.csv dans la liste des temps publiés."""
    return f"{(ligne.get('Date') or '').strip()}|{(ligne.get('Secondes') or '').strip()}"


def detail_de_entree(entree):
    """Un temps lu au classement → dictionnaire comme la colonne « Détail du
    build » de temps.csv, pour l'afficher et le reprendre comme un temps à soi."""
    b = entree.get("build") if isinstance(entree.get("build"), dict) else {}
    texte = lambda cle: "|".join(str(x) for x in (b.get(cle) or []) if x)
    detail = {"niveaux": ",".join(str(n) for n in (b.get("niveaux") or [])), "capacites": texte("capacites"),
              "crash": str(b.get("crash") or ""), "affixes": texte("affixes"), "traits": texte("traits"),
              "style": str(b.get("style") or ""), "adversaires": str(entree.get("adversaires") or 0),
              "difficulte": str(entree.get("difficulte") or ""), "position": str(entree.get("position") or "")}
    options = b.get("options") if isinstance(b.get("options"), dict) else {}
    for cle in OPTIONS:
        if options.get(cle) in (0, 1):
            detail[cle] = str(options[cle])
    return detail


# ─────────────────────────────────────────────────────────────────────────
#  APPELS AU SERVEUR (à faire dans une tâche de fond)
# ─────────────────────────────────────────────────────────────────────────
def adresse_valable(url):
    try:
        morceaux = urllib.parse.urlsplit((url or "").strip())
    except ValueError:
        return False
    return morceaux.scheme in ("https", "http") and bool(morceaux.netloc)


def appeler(url, methode, chemin, params=None, corps=None, version="", delai=DELAI):
    """Un appel au serveur → sa réponse (dictionnaire), ou ErreurClassement."""
    if not adresse_valable(url):
        raise ErreurClassement("adresse")
    adresse = url.strip().rstrip("/") + chemin
    if params:
        adresse += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
    donnees = json.dumps(corps).encode("utf-8") if corps is not None else None
    requete = urllib.request.Request(adresse, data=donnees, method=methode, headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": f"PracticeMode/{version or '?'} (fenetre)",
    })
    try:
        with urllib.request.urlopen(requete, timeout=delai) as reponse:
            texte = reponse.read(5_000_000)
    except urllib.error.HTTPError as e:   # (le serveur a répondu, avec un code d'erreur)
        try:
            texte = e.read(100_000)
        except OSError:
            texte = b""
        try:
            code = json.loads(texte).get("erreur") or f"http_{e.code}"
        except (ValueError, AttributeError):
            code = f"http_{e.code}"
        raise ErreurClassement(code, str(e.code)) from None
    except (urllib.error.URLError, http.client.HTTPException, OSError, ValueError) as e:
        # (pas de réponse : pas d'Internet, serveur introuvable, délai dépassé…)
        raise ErreurClassement("reseau", str(getattr(e, "reason", e))) from None
    try:
        reponse = json.loads(texte)
    except ValueError:
        raise ErreurClassement("reponse") from None
    if not isinstance(reponse, dict):
        raise ErreurClassement("reponse")
    if reponse.get("ok") is not True:
        raise ErreurClassement(reponse.get("erreur") or "reponse")
    return reponse


def verifier(url, version=""):
    """Le serveur répond-il ? → sa version d'API (ErreurClassement sinon)."""
    reponse = appeler(url, "GET", "/", version=version)
    if reponse.get("service") != "practice-mode-classement":
        raise ErreurClassement("reponse")
    if not isinstance(reponse.get("api"), int) or reponse["api"] > API:
        raise ErreurClassement("api")
    return reponse["api"]


def publier(url, envoi, version=""):
    """Publie un temps → { categorie, ameliore, ancien_ms, record_ms, rang, total }."""
    return appeler(url, "POST", "/api/temps", corps=envoi, version=version)


def lire_classement(url, circuit, vehicule, tours, categorie, pseudo="", limite=100, version=""):
    """→ { tableau, total, temps: [ { rang, pseudo, temps_ms, … } ], moi }"""
    return appeler(url, "GET", "/api/classement", params={
        "circuit": circuit, "vehicule": vehicule, "tours": tours, "categorie": categorie,
        "pseudo": pseudo, "limite": limite}, version=version)


def lire_tableaux(url, categorie="", circuit="", vehicule="", version=""):
    """→ [ { circuit, vehicule, tours, categorie, nb, meilleur_ms, meilleur_pseudo } ]"""
    return appeler(url, "GET", "/api/tableaux", params={
        "categorie": categorie, "circuit": circuit, "vehicule": vehicule}, version=version)["tableaux"]


def lire_records(url, pseudo, version=""):
    """→ [ { circuit, vehicule, tours, categorie, rang, total, temps_ms, … } ]"""
    return appeler(url, "GET", "/api/pseudo", params={"pseudo": pseudo}, version=version)["records"]
