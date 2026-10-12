"""Test du classement en ligne côté fenêtre (fenetre/classement.py, v0.9.8).

1. Sans réseau : pseudo, temps, catégorie, préparation d'un envoi depuis une
   ligne de temps.csv (ce qui part vraiment sur Internet).
2. Contre le VRAI serveur (serveur/classement/worker.js) lancé sur ce PC par
   Node.js (tests/d1_local.mjs, base en mémoire) : rien ne sort du PC.
   Sans Node.js 22 ou plus récent, cette partie est sautée.
3. Pannes : pas d'adresse, serveur éteint, réponse illisible, serveur trop récent.
"""
import http.server
import json
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "fenetre"))
import classement as C   # noqa: E402

echecs = []


def ok(nom, cond):
    print(("  [OK]    " if cond else "  [ÉCHEC] ") + nom)
    if not cond:
        echecs.append(nom)


def erreur_de(fonction, *args, **kwargs):
    """Le code d'ErreurClassement levé par l'appel (None s'il a réussi)."""
    try:
        fonction(*args, **kwargs)
    except C.ErreurClassement as e:
        return e.code
    return None


SANS_BUILD = {"niveaux": "0,0,0,0,0,0", "boost": "1", "ramjet": "1", "pannes": "1", "crashs_illimites": "1",
              "adversaires": "0"}


def ligne(**changements):
    """Une ligne de temps.csv telle que la fenêtre la lit (avec « _detail »)."""
    detail = dict(SANS_BUILD)
    detail.update(changements.pop("detail", {}))
    l = {"Date": "2026-10-11 20:00:00", "Planète": "Dalmatie", "Circuit": "Dunes  [TRAK_DAL_LOOP_A]",
         "Nb tours": "3", "Véhicule": "Motojet", "Pilote": "Lyren", "Temps": "2:05.000", "Secondes": "125.000",
         "Meilleur tour": "0:41.000", "Détail des tours": "0:42.500 0:41.000 0:41.500", "Build": "stats 0/0/0/0/0/0",
         "Save state": "non"}
    l.update(changements)
    l["_detail"] = detail
    return l


def envoi(l=None, pseudo="Kaizoku", jeton="jeton-de-test-0123456789", circuit="TRAK_DAL_LOOP_A"):
    return C.preparer_envoi(l or ligne(), circuit, "motojet", "DA_Racer_Star", pseudo, jeton, "0.9.8")


print("1. Pseudo arcade et jeton")
ok("« Élodie » → ELODIE", C.normaliser_pseudo("  Élodie ") == "ELODIE")
ok("espaces simplifiés", C.normaliser_pseudo("le   boss") == "LE BOSS")
ok("valides : R2-D2, LE BOSS, ABC", all(C.pseudo_valide(p) for p in ("R2-D2", "LE BOSS", "ABC", "X" * 12)))
ok("invalides : AB, 13 lettres, BAD!, -ABC, vide",
   not any(C.pseudo_valide(p) for p in ("AB", "X" * 13, "BAD!", "-ABC", "", None)))
j1, j2 = C.nouveau_jeton(), C.nouveau_jeton()
ok("jeton : 32 caractères au hasard", len(j1) == 32 and j1 != j2 and C.re.fullmatch(r"[A-Za-z0-9_-]+", j1))

print("2. Temps")
ok("« 1:15.169 » → 75169 ms", C.texte_vers_ms("1:15.169") == 75169)
ok("« 125.000 » et « 125,000 » → 125000 ms", C.texte_vers_ms("125.000") == C.texte_vers_ms("125,000") == 125000)
ok("« - », vide, texte → None", C.texte_vers_ms("-") is None and C.texte_vers_ms("") is None
   and C.texte_vers_ms("abc") is None)
ok("75169 → « 1:15.169 », 5169 → « 0:05.169 »", C.ms_vers_texte(75169) == "1:15.169"
   and C.ms_vers_texte(5169) == "0:05.169")
ok("écart : +1.234", C.ecart_texte(1234) == "+1.234" and C.ecart_texte(0) == "")

print("3. Catégorie : solo / IA, sans / avec build")
b0 = C.build_de_detail(SANS_BUILD)
ok("6 stats à 0, rien d'autre : sans build", C.categorie(0, b0) == "solo-sans")
ok("options lues (1/0)", b0["options"] == {"boost": 1, "ramjet": 1, "pannes": 1, "crashs_illimites": 1})
for nom, changement in (("une stat", {"niveaux": "0,0,3,0,0,0"}), ("une capacité", {"capacites": "/Game/A.A_C"}),
                        ("capacité de crash", {"crash": "/Game/C.C_C"}), ("un affixe", {"affixes": "/Game/X.X|/Game/Y.Y"}),
                        ("un buff", {"traits": "/Game/T.T"})):
    ok(f"{nom} : avec build", C.categorie(0, C.build_de_detail({**SANS_BUILD, **changement})) == "solo-avec")
ok("5 IA sans build : ia-sans", C.categorie(5, b0) == "ia-sans")
ok("détail incomplet (5 stats, vide) : pas de build", C.build_de_detail({"niveaux": "0,0,0,0,0"}) is None
   and C.build_de_detail({}) is None)

print("4. Préparation d'un envoi depuis temps.csv")
e, raison = envoi()
ok("prêt", raison is None and e is not None)
ok("pseudo normalisé, circuit et véhicule internes", e["pseudo"] == "KAIZOKU" and e["circuit"] == "TRAK_DAL_LOOP_A"
   and e["vehicule"] == "motojet" and e["pilote"] == "DA_Racer_Star")
ok("temps, meilleur tour et tours en millisecondes", e["temps_ms"] == 125000 and e["meilleur_tour_ms"] == 41000
   and e["tours_ms"] == [42500, 41000, 41500] and e["tours"] == 3)
ok("seul : pas de difficulté ni de place", e["adversaires"] == 0 and e["difficulte"] == "" and e["position"] is None)
ok("save_state=False, version et date", e["save_state"] is False and e["version"] == "0.9.8"
   and e["date_course"] == "2026-10-11 20:00:00")
ok("rien d'autre n'est envoyé", sorted(e) == sorted(
    ["pseudo", "jeton", "circuit", "vehicule", "tours", "temps_ms", "meilleur_tour_ms", "tours_ms", "pilote",
     "adversaires", "difficulte", "position", "save_state", "build", "version", "date_course"]))
e, _ = envoi(ligne(detail={"adversaires": "5", "difficulte": "champion", "position": "2"}))
ok("course IA : 5 adversaires, Champion, 2e", e["adversaires"] == 5 and e["difficulte"] == "champion"
   and e["position"] == 2)
ok("refus : save state", envoi(ligne(**{"Save state": "oui"}))[1] == "save_state")
ok("refus : ligne sans détail (ancienne version)", envoi(ligne(detail={"niveaux": ""}))[1] == "sans_detail")
ok("refus : circuit inconnu", envoi(circuit="")[1] == "circuit_inconnu"
   and envoi(circuit="Dunes [x]")[1] == "circuit_inconnu")
ok("refus : véhicule inconnu", C.preparer_envoi(ligne(), "TRAK_A", "", "", "ABC", "j" * 20, "1")[1] == "vehicule_inconnu")
ok("refus : temps illisible", envoi(ligne(Secondes="", Temps="-"))[1] == "temps_invalide")
ok("refus : pseudo invalide", envoi(pseudo="A!")[1] == "pseudo_invalide")
ok("« Secondes » vide : repris de « Temps »", envoi(ligne(Secondes=""))[0]["temps_ms"] == 125000)
ok("clé d'une course publiée", C.cle_publication(ligne()) == "2026-10-11 20:00:00|125.000")


# ── Faux serveurs pour les pannes ─────────────────────────────────────────
class FauxServeur(http.server.BaseHTTPRequestHandler):
    reponse = (200, "text/plain", b"bonjour")

    def do_GET(self):
        statut, type_, corps = self.reponse
        self.send_response(statut)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, *args):
        pass


def faux_serveur(statut, type_, corps):
    gestion = type("Gestion", (FauxServeur,), {"reponse": (statut, type_, corps)})
    serveur = http.server.HTTPServer(("127.0.0.1", 0), gestion)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    return serveur, f"http://127.0.0.1:{serveur.server_address[1]}"


print("5. Pannes : pas d'adresse, serveur éteint, réponse illisible, serveur trop récent")
ok("pas d'adresse : « adresse »", erreur_de(C.verifier, "") == "adresse"
   and erreur_de(C.verifier, "pas une adresse") == "adresse")
s = socket.socket()
s.bind(("127.0.0.1", 0))
port_libre = s.getsockname()[1]
s.close()
ok("serveur éteint : « reseau »", erreur_de(C.verifier, f"http://127.0.0.1:{port_libre}") == "reseau")
serveur, url = faux_serveur(200, "text/plain", b"bonjour")
ok("réponse qui n'est pas du JSON : « reponse »", erreur_de(C.verifier, url) == "reponse")
serveur.shutdown()
serveur, url = faux_serveur(404, "text/html", b"<html>404</html>")
ok("page d'erreur HTML : « http_404 »", erreur_de(C.verifier, url) == "http_404")
serveur.shutdown()
serveur, url = faux_serveur(200, "application/json", b'{"ok": true, "service": "autre chose", "api": 1}')
ok("un autre service : « reponse »", erreur_de(C.verifier, url) == "reponse")
serveur.shutdown()
serveur, url = faux_serveur(200, "application/json", b'{"ok": true, "service": "practice-mode-classement", "api": 9}')
ok("serveur plus récent que la fenêtre : « api »", erreur_de(C.verifier, url) == "api")
serveur.shutdown()

print("6. Contre le vrai serveur (worker.js) lancé sur ce PC")
node = shutil.which("node")
processus = None
url = ""
serveur_present = (RACINE / "tests" / "d1_local.mjs").exists() and (RACINE / "serveur" / "classement" / "worker.js").exists()
if node and serveur_present:
    processus = subprocess.Popen([node, "--no-warnings", str(RACINE / "tests" / "d1_local.mjs"), "0"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    premiere = processus.stdout.readline().split()
    url = premiere[1] if len(premiere) == 2 and premiere[0] == "PRET" else ""
if not url:
    print("  (sauté : " + ("le serveur n'est pas dans ce dossier" if not serveur_present
                          else "Node.js 22 ou plus récent introuvable") + ")")
    if processus:
        processus.kill()
else:
    try:
        ok("le serveur répond (api 1)", C.verifier(url, "0.9.8") == 1)
        e, _ = envoi()
        r = C.publier(url, e, "0.9.8")
        ok("publié : solo-sans, 1er sur 1", r["categorie"] == "solo-sans" and r["rang"] == 1 and r["total"] == 1
           and r["ameliore"] is True)
        e2, _ = envoi(ligne(Secondes="121.500", **{"Meilleur tour": "0:40.000",
                                                    "Détail des tours": "0:41.000 0:40.000 0:40.500"}))
        r = C.publier(url, e2, "0.9.8")
        ok("record battu : ancien 125000, nouveau 121500", r["ameliore"] and r["ancien_ms"] == 125000
           and r["record_ms"] == 121500)
        e3, _ = envoi(pseudo="Elodie", jeton="autre-jeton-0123456789")
        ok("autre joueur : 2e sur 2", C.publier(url, e3)["rang"] == 2)
        e4, _ = envoi(ligne(detail={"adversaires": "11", "difficulte": "as", "position": "1",
                                    "affixes": "/Game/AFX/AFX_Ramjet_A.AFX_Ramjet_A"}))
        ok("course IA avec un affixe : ia-avec", C.publier(url, e4)["categorie"] == "ia-avec")
        e5, _ = envoi(jeton="un-autre-jeton-0123456789")
        ok("KAIZOKU depuis une autre fenêtre : « pseudo_pris »", erreur_de(C.publier, url, e5) == "pseudo_pris")
        e6, _ = envoi(pseudo="FUCKER")
        ok("mot grossier : « pseudo_interdit »", erreur_de(C.publier, url, e6) == "pseudo_interdit")
        c = C.lire_classement(url, "TRAK_DAL_LOOP_A", "motojet", 3, "solo-sans", pseudo="elodie", limite=1)
        ok("classement : KAIZOKU 1er, total 2", [t["pseudo"] for t in c["temps"]] == ["KAIZOKU"] and c["total"] == 2)
        ok("« moi » : ELODIE 2e, temps et tours", c["moi"]["rang"] == 2 and c["moi"]["temps_ms"] == 125000
           and c["moi"]["tours_ms"] == [42500, 41000, 41500])
        tableaux = C.lire_tableaux(url)
        ok("2 classements (solo-sans, ia-avec)", sorted(t["categorie"] for t in tableaux) == ["ia-avec", "solo-sans"])
        ok("filtre par catégorie", [t["nb"] for t in C.lire_tableaux(url, categorie="solo-sans")] == [2])
        records = C.lire_records(url, "KAIZOKU")
        ok("records de KAIZOKU : 2, avec place et total", len(records) == 2
           and all(x["rang"] == 1 and x["total"] >= 1 for x in records))
        ok("classement inexistant : liste vide", C.lire_classement(url, "TRAK_X", "avion", 1, "ia-sans")["temps"] == [])
        ok("catégorie inconnue : « tableau_invalide »",
           erreur_de(C.lire_classement, url, "TRAK_X", "avion", 1, "nimporte") == "tableau_invalide")
    finally:
        processus.kill()
        processus.communicate()

if echecs:
    print(f"\n{len(echecs)} ÉCHEC(S)")
    sys.exit(1)
print("\nTOUS LES TESTS SONT PASSÉS")
