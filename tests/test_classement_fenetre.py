"""Test de la fenêtre (v0.9.8) : bouton « Publier ce temps » (Mes temps) et
onglet Classement. Le serveur est simulé (fonctions de classement.py
remplacées) : rien ne part sur Internet. Faux catalogue dans un dossier
temporaire : rien ne touche au jeu. Sous Linux : xvfb-run, et un faux winreg."""
import configparser
import csv
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import time
import types
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
tmp = Path(tempfile.mkdtemp())
(tmp / "temps").mkdir()
if sys.platform != "win32":   # (hors Windows : pas de registre, pas de LOCALAPPDATA)
    winreg = types.ModuleType("winreg")
    winreg.HKEY_CURRENT_USER = winreg.HKEY_LOCAL_MACHINE = 0

    def _absent(*args, **kwargs):
        raise OSError("pas de registre (test hors Windows)")
    winreg.OpenKey = winreg.OpenKeyEx = winreg.QueryValueEx = _absent
    sys.modules["winreg"] = winreg
    os.environ.setdefault("LOCALAPPDATA", str(tmp))
    import ctypes
    from unittest import mock
    ctypes.WinDLL = lambda *args, **kwargs: mock.MagicMock()   # (session.py : processus de Windows)
    ctypes.windll = mock.MagicMock()

sys.path.insert(0, str(RACINE / "fenetre"))
chargeur = importlib.machinery.SourceFileLoader("pm", str(RACINE / "fenetre" / "PracticeMode.pyw"))
pm = importlib.util.module_from_spec(importlib.util.spec_from_loader("pm", chargeur))
chargeur.exec_module(pm)
pm.CLASSEMENT_ACTIF = True   # (caché dans la version publique 2.0.0 : testé ici rallumé)
pm.DOSSIER_ECHANGE = tmp
pm.FICHIER_CATALOGUE = tmp / "catalogue.json"
pm.FICHIER_STYLES = tmp / "styles.json"
pm.FICHIER_DIFFICULTES = tmp / "difficultes.json"
pm.FICHIER_COMMANDE = tmp / "commande.txt"
pm.FICHIER_ETAT = tmp / "etat.txt"
pm.FICHIER_PREFERENCES = tmp / "prefs.ini"
pm.FICHIER_TEMPS_CSV = tmp / "temps" / "temps.csv"
pm.FICHIER_PUBLIES = tmp / "temps" / "classement-publies.json"
pm.FICHIER_LANGUE = tmp / "langue.txt"
pm.L.langue_par_defaut = lambda: "fr"
pm.S.session_en_cours = lambda c: None           # pas de vraie session pendant le test
pm.S.jeu_lance = lambda c: False
pm.S.regles_pare_feu_presentes = lambda c: False
C = pm.C

AFFIXE = "/Game/AFX/AFX_Ramjet_Boost.AFX_Ramjet_Boost"
catalogue = {
    "vehicules": [{"nom": "VA_Bike", "chemin": "/Game/V/VA_Bike.VA_Bike", "affiche": "Motojet",
                   "tag": "Vehicle.Standard.Bike"},
                  {"nom": "VA_Car", "chemin": "/Game/V/VA_Car.VA_Car", "affiche": "Voiture",
                   "tag": "Vehicle.Standard.Car"}],
    "planetes": [{"nom": "PLA_Dalmatian", "chemin": "/Game/P/PLA_Dalmatian.PLA_Dalmatian", "affiche": "Dalmatie"}],
    "circuits": [{"nom": "TRAK_DAL_LOOP_A", "chemin": "/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", "affiche": "Dunes",
                  "tag": "Vehicle.Standard", "tours": 3},
                 {"nom": "TRAK_DAL_P2P", "chemin": "/Game/T/TRAK_DAL_P2P.TRAK_DAL_P2P", "affiche": "Canyon",
                  "tag": "Vehicle.Standard", "tours": 1, "p2p": True}],
    "pilotes": [{"nom": "DA_Racer_Star", "chemin": "/Game/R/DA_Racer_Star.DA_Racer_Star", "affiche": "Lyren"}],
    "capacites": [], "interface": {"langue_jeu": "fr-FR"},
    "affixes": [{"nom": "AFX_Ramjet_Boost", "chemin": AFFIXE, "affiche": "Statoréacteur dopé", "rarete": 2,
                 "description": "Plus de poussée."}],
}
pm.FICHIER_CATALOGUE.write_text(json.dumps(catalogue), encoding="utf-8")
(tmp / "catalogue-en.json").write_text(json.dumps({"langue": "en", "objets": {
    "/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A": {"affiche": "Dunes EN"},
    "/Game/R/DA_Racer_Star.DA_Racer_Star": {"affiche": "Lyren EN"}}}), encoding="utf-8")

ENTETE = ["Date", "Planète", "Circuit", "Nb tours", "Véhicule", "Pilote", "Temps", "Secondes", "Meilleur tour",
          "Détail des tours", "Build", "Save state", "Détail du build"]
SANS_BUILD = "niveaux=0,0,0,0,0,0;boost=1;ramjet=1;pannes=1;crashs_illimites=1;adversaires=0"
LIGNES = [
    ["2026-10-11 20:00:00", "Dalmatie", "Dunes [TRAK_DAL_LOOP_A]", "3", "Motojet", "Lyren", "2:05.000", "125.000",
     "0:41.000", "0:42.500 0:41.000 0:41.500", "stats 0/0/0/0/0/0", "non", SANS_BUILD],
    ["2026-10-11 20:05:00", "Dalmatie", "Dunes [TRAK_DAL_LOOP_A]", "3", "Motojet", "Lyren", "1:59.000", "119.000",
     "0:39.000", "", "stats 0/0/0/0/0/0", "oui", SANS_BUILD],
    ["2026-10-10 18:00:00", "Dalmatie", "Dunes [TRAK_DAL_LOOP_A]", "3", "Motojet", "Lyren", "2:10.000", "130.000",
     "0:43.000", "", "stats 0/0/0/0/0/0", "non", ""],
]
with open(pm.FICHIER_TEMPS_CSV, "w", encoding="utf-8", newline="") as fichier:
    ecrivain = csv.writer(fichier, delimiter=";")
    ecrivain.writerow(ENTETE)
    ecrivain.writerows(LIGNES)

# ── Faux serveur : les fonctions réseau de classement.py, remplacées ─────
appels = []
reponses = {}


def faux(nom):
    def fonction(*args, **kwargs):
        appels.append((nom, args, kwargs))
        reponse = reponses.get(nom)
        if isinstance(reponse, Exception):
            raise reponse
        return reponse(*args) if callable(reponse) else reponse
    return fonction


for nom in ("publier", "lire_tableaux", "lire_classement", "verifier"):
    setattr(C, nom, faux(nom))


def appels_de(nom):
    return [a for a in appels if a[0] == nom]


def entree(rang, pseudo, ms, **autres):
    e = {"rang": rang, "pseudo": pseudo, "temps_ms": ms, "meilleur_tour_ms": ms // 3 - 500,
         "tours_ms": [ms // 3, ms // 3, ms - 2 * (ms // 3)], "pilote": "DA_Racer_Star", "adversaires": 0,
         "difficulte": "", "position": None, "version": "0.9.8", "date_course": "2026-10-12 10:00:00",
         "date_envoi": "2026-10-12T10:01:00.000Z",
         "build": {"niveaux": [0] * 6, "capacites": [], "crash": "", "affixes": [], "traits": [], "style": "",
                   "options": {"boost": 1, "ramjet": 1}}}
    e.update(autres)
    return e


DUNES = {"circuit": "TRAK_DAL_LOOP_A", "vehicule": "motojet", "tours": 3}
reponses["publier"] = {"ok": True, "pseudo": "ELODIE", "tableau": {**DUNES, "categorie": "solo-sans"},
                       "categorie": "solo-sans", "ameliore": True, "ancien_ms": None, "record_ms": 125000,
                       "rang": 4, "total": 9}
reponses["lire_tableaux"] = lambda url, categorie: [
    {**DUNES, "categorie": categorie, "nb": 9, "meilleur_ms": 120000, "meilleur_pseudo": "KAIZOKU"},
    {"circuit": "TRAK_DAL_P2P", "vehicule": "voiture", "tours": 1, "categorie": categorie, "nb": 2,
     "meilleur_ms": 61000, "meilleur_pseudo": "R2-D2"}]
reponses["lire_classement"] = lambda url, circuit, vehicule, tours, categorie, *reste: {
    "ok": True, "tableau": {"circuit": circuit, "vehicule": vehicule, "tours": tours, "categorie": categorie},
    "total": 9,
    "temps": [entree(1, "KAIZOKU", 120000),
              entree(2, "R2-D2", 121500, build={"niveaux": [1, 2, 3, 0, 0, 0], "capacites": [], "crash": "",
                                                 "affixes": [AFFIXE], "traits": [], "style": "",
                                                 "options": {"boost": 0}},
                     adversaires=5, difficulte="champion", position=2),
              entree(3, "LE BOSS", 123000)],
    "moi": entree(7, "ELODIE", 125000)}

echecs = []


def ok(nom, cond):
    print(("  [OK]    " if cond else "  [ÉCHEC] ") + nom)
    if not cond:
        echecs.append(nom)


def attendre(f, condition, delai=5.0):
    """Fait tourner la fenêtre jusqu'à ce que `condition()` soit vraie (réponses des tâches de fond)."""
    fin = time.time() + delai
    while time.time() < fin:
        f.update()
        if condition():
            return True
        time.sleep(0.02)
    return False


def fenetre():
    f = pm.Fenetre()
    f.withdraw()
    f.update()
    return f


def ligne_mes_temps(f, date):
    return next(i for i in f.table_temps.get_children() if f.lignes_temps[i]["Date"] == date)


def detail(zone):
    return zone.get("1.0", "end")


print("1. Onglet Classement présent ; rien n'est lu sur Internet tant qu'on ne le regarde pas")
f = fenetre()
onglets = [f.onglets.tab(i, "text") for i in f.onglets.tabs()]
ok("4e onglet « CLASSEMENT »", onglets[-1] == "CLASSEMENT")
ok("4 catégories (solo/IA × sans/avec build)", [f.nom_categorie(c) for c in C.CATEGORIES] ==
   ["Solo sans build", "Solo avec build", "IA sans build", "IA avec build"])
attendre(f, lambda: False, 0.3)
ok("aucun appel au serveur à l'ouverture", appels == [])

print("2. Pseudo « arcade » : majuscules, sans accents, caractères permis, 12 au plus")
f.var_pseudo.set("élodie!")
ok("« élodie! » → « ELODIE »", f.var_pseudo.get() == "ELODIE")
f.var_pseudo.set("abcdefghijklmnop")
ok("12 caractères au plus", f.var_pseudo.get() == "ABCDEFGHIJKL")
f.var_pseudo.set("")

print("3. Mes temps : « Publier ce temps » seulement pour un temps publiable")
f.remplir_temps()
f.table_temps.selection_set(ligne_mes_temps(f, "2026-10-11 20:05:00"))
f.afficher_detail_temps()
ok("temps avec save state : bouton grisé", f.bouton_publier.instate(["disabled"]))
f.table_temps.selection_set(ligne_mes_temps(f, "2026-10-10 18:00:00"))
f.afficher_detail_temps()
ok("ancien temps sans détail : bouton grisé", f.bouton_publier.instate(["disabled"]))
f.table_temps.selection_set(ligne_mes_temps(f, "2026-10-11 20:00:00"))
f.afficher_detail_temps()
ok("temps normal : bouton actif", not f.bouton_publier.instate(["disabled"]))

print("4. Sans pseudo, puis sans adresse : rien n'est envoyé, on est guidé vers l'onglet Classement")
f.var_adresse.set("")
f.publier_temps()
f.update()
ok("sans pseudo : message et onglet Classement", "Choisis d'abord ton pseudo" in f.var_etat.get()
   and f.onglets.select() == str(f.page_classement) and not appels_de("publier"))
ok("onglet ouvert sans adresse : « pas encore configuré », aucun appel",
   "pas encore configuré" in f.var_classement_etat.get() and appels == [])
f.onglets.select(2)
f.var_pseudo.set("Elodie")
f.publier_temps()
ok("sans adresse : message « Pas d'adresse de serveur valable »",
   "Pas d'adresse de serveur valable" in f.var_etat.get() and not appels_de("publier"))
f.onglets.select(2)

print("5. Publication : ce qui part, la réponse, la colonne « En ligne »")
f.var_adresse.set("https://classement.test")
f.publier_temps()
ok("bouton grisé pendant l'envoi", f.bouton_publier.instate(["disabled"]))
ok("réponse reçue", attendre(f, lambda: "Publié" in f.var_etat.get()))
ok("message : « ✔ Publié : 4e sur 9 au classement « Solo sans build ». »",
   f.var_etat.get() == "✔ Publié : 4e sur 9 au classement « Solo sans build ».")
url, envoi, version = appels_de("publier")[0][1]
ok("adresse et version", url == "https://classement.test" and version == pm.VERSION)
ok("circuit, véhicule et pilote en noms internes", envoi["circuit"] == "TRAK_DAL_LOOP_A"
   and envoi["vehicule"] == "motojet" and envoi["pilote"] == "DA_Racer_Star")
ok("pseudo, temps, tours", envoi["pseudo"] == "ELODIE" and envoi["temps_ms"] == 125000 and envoi["tours"] == 3
   and envoi["tours_ms"] == [42500, 41000, 41500] and envoi["save_state"] is False)
prefs = configparser.ConfigParser(interpolation=None)
prefs.read(pm.FICHIER_PREFERENCES, encoding="utf-8")
jeton = prefs["classement"].get("jeton", "")
ok("jeton tiré au hasard et gardé, le même que celui envoyé", len(jeton) == 32 and envoi["jeton"] == jeton)
ok("pseudo et adresse gardés", prefs["classement"].get("pseudo") == "ELODIE"
   and prefs["classement"].get("adresse") == "https://classement.test")
publies = json.loads(pm.FICHIER_PUBLIES.read_text(encoding="utf-8"))
ok("temps noté comme publié", publies.get("2026-10-11 20:00:00|125.000", {}).get("rang") == 4)
iid = ligne_mes_temps(f, "2026-10-11 20:00:00")
ok("colonne « En ligne » : #4 / 9", f.table_temps.item(iid, "values")[-1] == "#4 / 9")
f.table_temps.selection_set(iid)
f.afficher_detail_temps()
ok("détail : « En ligne : publié le … sous le pseudo ELODIE — 4e sur 9 (Solo sans build) »",
   "sous le pseudo ELODIE — 4e sur 9 (Solo sans build)" in detail(f.texte_detail))
ok("l'onglet Classement montre ce classement", f.tableau_affiche == {**DUNES, "categorie": "solo-sans"})
ok("… et le relit en tâche de fond", attendre(f, lambda: appels_de("lire_classement") and appels_de("lire_tableaux")))

print("6. Publication refusée : message traduit")
reponses["publier"] = C.ErreurClassement("pseudo_pris")
f.publier_temps()
ok("« pseudo déjà pris »", attendre(f, lambda: "déjà pris par un autre joueur" in f.var_etat.get()))
ok("bouton de nouveau actif", attendre(f, lambda: not f.bouton_publier.instate(["disabled"])))
reponses["publier"] = {"ok": True, "pseudo": "ELODIE", "tableau": {**DUNES, "categorie": "solo-sans"},
                       "categorie": "solo-sans", "ameliore": False, "ancien_ms": 118000, "record_ms": 118000,
                       "rang": 2, "total": 9}
f.publier_temps()
ok("temps moins bon que son record en ligne : prévenu",
   attendre(f, lambda: "Ton record en ligne (1:58.000) reste meilleur" in f.var_etat.get()))
ok("colonne « En ligne » : ✔ (un meilleur temps est au classement)",
   f.table_temps.item(ligne_mes_temps(f, "2026-10-11 20:00:00"), "values")[-1] == "✔")

print("7. Onglet Classement : liste des classements, le classement, son pseudo")
f.onglets.select(f.page_classement)
f.update()
f.actualiser_classement()
ok("liste et classement lus", attendre(f, lambda: "Chargement" not in f.var_classement_titre.get()
                                       and "Chargement" not in f.var_classement_etat.get()))
dunes = "TRAK_DAL_LOOP_A|motojet|3"
ok("liste : les classements du véhicule choisi (motojet)", f.liste_tableaux.get_children() == (dunes,))
ok("noms du jeu : « Dunes — boucle », 3 tours, 9 temps, record de KAIZOKU",
   f.liste_tableaux.item(dunes, "text") == "Dunes  —  boucle"
   and [str(v) for v in f.liste_tableaux.item(dunes, "values")] == ["3", "9", "2:00.000   KAIZOKU"])
ok("état : nombre de classements, véhicule et heure", f.var_classement_etat.get().startswith(
    "1 classement(s) avec des temps pour ce véhicule (Motojet) dans cette catégorie · mis à jour à "))
ok("classement affiché sélectionné dans la liste", f.liste_tableaux.selection() == (dunes,))
nb_appels = len(appels)
f.var_type.set("voiture")
f.type_change()
ok("véhicule VOITURE : son classement, sans rien redemander", f.liste_tableaux.get_children() ==
   ("TRAK_DAL_P2P|voiture|1",) and len(appels) == nb_appels)
f.var_type.set("motojet")
f.type_change()
ok("5 lignes : 3 premiers, « … », soi-même", len(f.table_classement.get_children()) == 5)
lignes = [f.table_classement.item(i) for i in f.table_classement.get_children()]
ok("titre : circuit, véhicule, tours, catégorie, nombre de pilotes", f.var_classement_titre.get() ==
   "Dunes  —  boucle  ·  Motojet  ·  3 tour(s)  ·  Solo sans build  —  9 pilote(s)")
ok("1er en ambre, écart au 1er", "or" in lignes[0]["tags"] and lignes[1]["values"][3] == "+1.500")
ok("pilote avec son nom du jeu", lignes[0]["values"][5] == "Lyren")
ok("« … » puis ELODIE (7e) en surbrillance", lignes[3]["values"][0] == "…" and lignes[4]["values"][1] == "ELODIE"
   and "moi" in lignes[4]["tags"] and str(lignes[4]["values"][0]) == "7")
ok("solo : colonnes IA cachées", "ia" not in f.table_classement["displaycolumns"])
ok("pseudo envoyé pour avoir sa place", appels_de("lire_classement")[-1][1][5] == "ELODIE")

print("8. Un temps choisi : son build et ses tours ; « Reprendre ce build »")
deuxieme = f.table_classement.get_children()[1]
f.table_classement.selection_set(deuxieme)
f.update()
texte = detail(f.texte_detail_classement)
ok("build lisible (affixe du catalogue, IA, difficulté)", "Statoréacteur dopé" in texte
   and "5 adversaire(s) IA, difficulté Antagoniste" in texte)   # nom du jeu en français (clé « champion »)
ok("tours et version", "Tours : 0:40.500  ·  0:40.500  ·  0:40.500" in texte and "v0.9.8" in texte)
f.reprendre_build_classement()
ok("build repris dans l'onglet Build", [v.get() for v in f.var_niveaux] == [1, 2, 3, 0, 0, 0]
   and f.affixes_choisis == [AFFIXE] and f.onglets.index("current") == 1)
ok("message « Build de R2-D2 repris »", "Build de R2-D2 repris" in f.var_etat.get())

print("9. Autre catégorie : sa liste et le même circuit dans cette catégorie")
f.onglets.select(f.page_classement)
avant = len(appels_de("lire_tableaux"))
f.var_categorie.set("ia-avec")
f.categorie_changee()
ok("liste relue pour « IA avec build »", attendre(f, lambda: len(appels_de("lire_tableaux")) > avant)
   and appels_de("lire_tableaux")[-1][1][1] == "ia-avec")
ok("même circuit, catégorie IA avec build", f.tableau_affiche == {**DUNES, "categorie": "ia-avec"})
ok("IA : colonnes IA, difficulté, place visibles",
   attendre(f, lambda: "difficulte" in f.table_classement["displaycolumns"]))

print("10. Circuit choisi dans l'onglet Course")
f.liste_circuits.selection_clear(0, "end")
f.liste_circuits.selection_set(0)       # (Canyon, trié avant Dunes)
f.var_tours.set(1)
f.var_type.set("motojet")
f.classement_du_circuit_choisi()
ok("classement du circuit choisi demandé", f.tableau_affiche == {"circuit": "TRAK_DAL_P2P", "vehicule": "motojet",
                                                                "tours": 1, "categorie": "ia-avec"}
   and attendre(f, lambda: appels_de("lire_classement")[-1][1][1:5] == ("TRAK_DAL_P2P", "motojet", 1, "ia-avec")))

print("11. Pannes : pas de réponse du serveur, réponse en retard ignorée")
reponses["lire_tableaux"] = C.ErreurClassement("reseau")
f.charger_tableaux()
ok("message « ne répond pas »", attendre(f, lambda: "ne répond pas" in f.var_classement_etat.get()))
ancien = f.numero_demande["classement"]
f.classement_lu(ancien - 1, f.tableau_affiche, {"temps": [entree(1, "VIEUX", 1000)]}, None)
ok("réponse d'une demande dépassée : ignorée", all("VIEUX" not in f.table_classement.item(i, "values")
                                                    for i in f.table_classement.get_children()))

print("12. Passage en anglais : tout est retraduit, sans rien redemander au serveur")
reponses["lire_tableaux"] = lambda url, categorie: [
    {**DUNES, "categorie": categorie, "nb": 9, "meilleur_ms": 120000, "meilleur_pseudo": "KAIZOKU"}]
f.var_categorie.set("solo-sans")
f.tableau_affiche = {**DUNES, "categorie": "solo-sans"}
f.actualiser_classement()
attendre(f, lambda: f.cache_classement and f.cache_classement[0] == f.tableau_affiche
         and f.cache_tableaux and len(f.cache_tableaux[1]) == 1)
nb_appels = len(appels)
f.var_langue.set("en")
f.changer_langue()
f.update()
ok("onglet « LEADERBOARD »", f.onglets.tab(3, "text") == "LEADERBOARD")
ok("titre en anglais, noms anglais du jeu", f.var_classement_titre.get() ==
   "Dunes EN  —  loop  ·  Motojet  ·  3 lap(s)  ·  Solo, no build  —  9 racer(s)")
ok("classement réaffiché", len(f.table_classement.get_children()) == 5)
ok("pilote en anglais", f.table_classement.item(f.table_classement.get_children()[0], "values")[5] == "Lyren EN")
ok("aucun nouvel appel", len(appels) == nb_appels)
f.var_langue.set("fr")
f.changer_langue()
f.destroy()

print("13. Réouverture : pseudo et catégorie repris, temps publiés relus")
f = fenetre()
ok("pseudo ELODIE, catégorie, adresse", f.var_pseudo.get() == "ELODIE" and f.var_categorie.get() == "solo-sans"
   and f.adresse() == "https://classement.test")
f.remplir_temps()
ok("colonne « En ligne » relue du fichier", f.table_temps.item(ligne_mes_temps(f, "2026-10-11 20:00:00"),
                                                              "values")[-1] == "✔")
f.destroy()

if echecs:
    print(f"\n{len(echecs)} ÉCHEC(S)")
    sys.exit(1)
print("\nTOUS LES TESTS SONT PASSÉS")
