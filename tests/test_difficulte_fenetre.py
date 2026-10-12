"""Test de la fenêtre (v0.9.7) : choix de la difficulté des IA dans l'onglet Course.
Faux catalogue minimal dans un dossier temporaire : rien ne touche au jeu.
Marche sous Windows comme ailleurs (sous Linux : xvfb-run, et un faux winreg)."""
import configparser
import csv
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
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
pm.DOSSIER_ECHANGE = tmp
pm.FICHIER_CATALOGUE = tmp / "catalogue.json"
pm.FICHIER_STYLES = tmp / "styles.json"
pm.FICHIER_DIFFICULTES = tmp / "difficultes.json"
pm.FICHIER_COMMANDE = tmp / "commande.txt"
pm.FICHIER_ETAT = tmp / "etat.txt"
pm.FICHIER_PREFERENCES = tmp / "prefs.ini"
pm.FICHIER_TEMPS_CSV = tmp / "temps" / "temps.csv"
pm.FICHIER_LANGUE = tmp / "langue.txt"
pm.L.langue_par_defaut = lambda: "fr"
pm.S.session_en_cours = lambda c: None           # pas de vraie session pendant le test
pm.S.jeu_lance = lambda c: False
pm.S.regles_pare_feu_presentes = lambda c: False

PISTE = "/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A"
catalogue = {
    "vehicules": [{"nom": "VA_Bike", "chemin": "/Game/V/VA_Bike.VA_Bike", "affiche": "Motojet",
                   "tag": "Vehicle.Standard.Bike"}],
    "planetes": [{"nom": "PLA_Dalmatian", "chemin": "/Game/P/PLA_Dalmatian.PLA_Dalmatian", "affiche": "Dalmatie"}],
    "circuits": [{"nom": "TRAK_DAL_LOOP_A", "chemin": PISTE, "affiche": "Dunes", "tag": "Vehicle.Standard",
                  "tours": 3}],
    "pilotes": [{"nom": "DA_Racer_Star", "chemin": "/Game/R/DA_Racer_Star.DA_Racer_Star", "affiche": "Lyren"}],
    "capacites": [], "affixes": [], "interface": {"langue_jeu": "fr-FR"},
}
pm.FICHIER_CATALOGUE.write_text(json.dumps(catalogue), encoding="utf-8")
# Ce que le mod écrit au menu (jeu en français), et la traduction anglaise
NOMS = {"cadet": "Cadet", "pilote": "Pilote", "as": "As", "champion": "Champion"}
difficultes = {
    "difficultes": [{"niveau": n, "chemin": f"/Game/Diff/CDD_{n}.CDD_{n}", "nom": f"CDD_{n}", "affiche": a,
                     "description": f"Description de {a}."} for n, a in NOMS.items()],
    "bases": [],
    # (valeurs du mod v0.9.9, calées sur le jeu)
    "reglages_mod": {"cadet": {"AiMaxTimeAheadMultiplier": 0.65, "AiMinTimeAheadModifier": -3.0,
                               "AiAggressionVPlayerChanceMultiplier": 0.5,
                               "AiAggressionVPlayerCooldownMultiplier": 1.5, "AiAbilityChanceMultiplier": 0.5},
                     "pilote": {},
                     "as": {"AiMaxTimeAheadModifier": 1.0, "AiMinTimeAheadModifier": 1.0, "AiAbilityChanceMultiplier": 1.25},
                     "champion": {"AiMaxTimeAheadModifier": 2.0, "AiMinTimeAheadModifier": 2.0,
                                  "AiAggressionVPlayerChanceMultiplier": 2.0,
                                  "AiAggressionVPlayerCooldownMultiplier": 0.5, "AiAbilityChanceMultiplier": 1.5}},
}
pm.FICHIER_DIFFICULTES.write_text(json.dumps(difficultes), encoding="utf-8")
(tmp / "catalogue-en.json").write_text(json.dumps({"langue": "en", "objets": {
    "/Game/Diff/CDD_pilote.CDD_pilote": {"affiche": "Racer", "description": "Racer's description."},
    "/Game/Diff/CDD_as.CDD_as": {"affiche": "Ace", "description": "Ace's description."}}}), encoding="utf-8")

echecs = []


def ok(nom, cond):
    print(("  [OK]    " if cond else "  [ÉCHEC] ") + nom)
    if not cond:
        echecs.append(nom)


def fenetre():
    f = pm.Fenetre()
    f.withdraw()
    f.update()
    return f


def choisir(f, niveau):
    f.combo_difficulte.current(pm.NIVEAUX_DIFFICULTE.index(niveau) + 1 if niveau else 0)
    f.difficulte_choisie()


def commande():
    lignes = pm.FICHIER_COMMANDE.read_text(encoding="utf-8").splitlines()
    return dict(l.split("=", 1) for l in lignes if "=" in l)


print("1. Liste des difficultés : noms du jeu, « celle du jeu » en premier")
f = fenetre()
ok("5 choix dans l'ordre", list(f.combo_difficulte["values"]) ==
   ["Celle du jeu (sans changement)", "Cadet", "Pilote", "As", "Champion"])
ok("par défaut : celle du jeu", f.difficulte == "" and f.var_difficulte.get() == "Celle du jeu (sans changement)")

print("2. Champion : description du jeu et réglages du mod ; note sans adversaires")
f.var_adversaires.set(0)
choisir(f, "champion")
texte = f.var_difficulte_texte.get()
ok("niveau retenu", f.difficulte == "champion")
ok("description du jeu", "Description de Champion." in texte)
ok("réglages du mod lisibles", "Le mod règle : avance des IA +2 s, agressivité ×2, "
   "délai entre leurs attaques ×0.5, capacités ×1.5." in texte)
ok("note : seulement avec des adversaires", "(seulement avec des adversaires IA)" in texte)
f.var_adversaires.set(5)
f.update()
ok("avec 5 adversaires : plus de note", "(seulement" not in f.var_difficulte_texte.get())
choisir(f, "pilote")
ok("Pilote : rien changé par le mod", "Le mod règle : rien (réglages du jeu)." in f.var_difficulte_texte.get())

print("3. Lancement : difficulté envoyée seulement avec des adversaires")
choisir(f, "champion")
f.liste_circuits.selection_set(0)
f.lancer()
c = commande()
ok("course à 5 : difficulte=champion et son nom", c.get("difficulte") == "champion"
   and c.get("nom_difficulte") == "Champion" and c.get("adversaires") == "5")
f.var_adversaires.set(0)
f.lancer()
c = commande()
ok("contre-la-montre : pas de difficulté", "difficulte" not in c and "nom_difficulte" not in c)
prefs = configparser.ConfigParser(interpolation=None)
prefs.read(pm.FICHIER_PREFERENCES, encoding="utf-8")
ok("préférences : difficulté gardée", prefs["choix"].get("difficulte") == "champion")
f.destroy()

print("4. Réouverture : le choix revient ; passage en anglais : noms traduits")
f = fenetre()
ok("Champion repris", f.difficulte == "champion" and f.var_difficulte.get() == "Champion")
f.var_langue.set("en")
f.changer_langue()
f.update()
ok("noms en anglais (traduits par chemin, sinon ceux du jeu)", list(f.combo_difficulte["values"]) ==
   ["Game default (unchanged)", "Cadet", "Racer", "Ace", "Champion"])
ok("choix gardé", f.difficulte == "champion" and f.var_difficulte.get() == "Champion")
choisir(f, "as")
ok("description traduite", "Ace's description." in f.var_difficulte_texte.get()
   and "The mod sets: AI lead +1 s, abilities ×1.25." in f.var_difficulte_texte.get())
f.var_langue.set("fr")
f.changer_langue()
f.destroy()

print("5. Sans difficultes.json (le mod ne l'a pas encore écrit) : noms de secours")
pm.FICHIER_DIFFICULTES.unlink()
f = fenetre()
ok("noms de secours en français (ceux du jeu)",
   list(f.combo_difficulte["values"])[1:] == ["Recrue", "Pilote", "As", "Antagoniste"])
f.var_langue.set("en")
f.changer_langue()
f.update()
ok("noms de secours en anglais", list(f.combo_difficulte["values"])[1:] == ["Cadet", "Pilot", "Ace", "Champion"])
f.var_langue.set("fr")
f.changer_langue()
f.destroy()

print("6. Mes temps : un record par difficulté, difficulté dans le détail")
entete = ["Date", "Planète", "Circuit", "Nb tours", "Véhicule", "Pilote", "Temps", "Secondes", "Meilleur tour",
          "Détail des tours", "Build", "Save state", "Détail du build"]
lignes = [
    ["2026-10-11 20:00:00", "Dalmatie", "Dunes [TRAK_DAL_LOOP_A]", "3", "Motojet", "Lyren", "2:05.000", "125.000",
     "0:41.000", "", "", "non", "niveaux=0,0,0,0,0,0;adversaires=5;difficulte=champion;position=2"],
    ["2026-10-11 20:10:00", "Dalmatie", "Dunes [TRAK_DAL_LOOP_A]", "3", "Motojet", "Lyren", "2:01.000", "121.000",
     "0:40.000", "", "", "non", "niveaux=0,0,0,0,0,0;adversaires=5;difficulte=cadet;position=1"],
]
with open(pm.FICHIER_TEMPS_CSV, "w", encoding="utf-8", newline="") as fichier:
    ecrivain = csv.writer(fichier, delimiter=";")
    ecrivain.writerow(entete)
    ecrivain.writerows(lignes)
f = fenetre()
f.remplir_temps()
lignes_tableau = [f.table_temps.item(i, "values") for i in f.table_temps.get_children()]
ok("deux records (un par difficulté)", sum(1 for v in lignes_tableau if v[6].startswith("★")) == 2)
champion = next(i for i in f.table_temps.get_children() if f.lignes_temps[i]["Temps"] == "2:05.000")
f.table_temps.selection_set(champion)
f.afficher_detail_temps()
detail = f.texte_detail.get("1.0", "end")
ok("détail : « 5 adversaire(s) IA, difficulté Antagoniste » (nom de secours)",
   "Course : 5 adversaire(s) IA, difficulté Antagoniste — place 2 / 6" in detail)
f.destroy()

print("7. difficultes.json de la v0.9.7 (fichier réel du 11/10) : Recrue et Antagoniste sans niveau")
reel = {"difficultes": [
    {"niveau": None, "nom": "CAM_DIFF_Easy", "chemin": "/Game/D/CAM_DIFF_Easy.CAM_DIFF_Easy", "affiche": "Recrue",
     "description": "Pour les pilotes qui découvrent les jeux de course."},
    {"niveau": "pilote", "nom": "CAM_DIFF_Normal", "chemin": "/Game/D/CAM_DIFF_Normal.CAM_DIFF_Normal",
     "affiche": "Pilote (recommandé)", "description": ""},
    {"niveau": "as", "nom": "CAM_DIFF_Hard", "chemin": "/Game/D/CAM_DIFF_Hard.CAM_DIFF_Hard", "affiche": "As",
     "description": ""},
    {"niveau": None, "nom": "CAM_DIFF_Nightmare", "chemin": "/Game/D/CAM_DIFF_Nightmare.CAM_DIFF_Nightmare",
     "affiche": "Antagoniste", "description": "Pour les pilotes en quête du défi ultime."}],
    "bases": [], "reglages_mod": difficultes["reglages_mod"]}
pm.FICHIER_DIFFICULTES.write_text(json.dumps(reel), encoding="utf-8")
f = fenetre()
ok("les 4 noms du jeu, reconnus à leur nom interne", list(f.combo_difficulte["values"])[1:] ==
   ["Recrue", "Pilote (recommandé)", "As", "Antagoniste"])
f.var_adversaires.set(5)
choisir(f, "cadet")
texte = f.var_difficulte_texte.get()
ok("Recrue : description du jeu et valeurs du jeu (×0.65, −3 s)",
   "découvrent les jeux de course" in texte and "Le mod règle : avance max. des IA ×0.65, avance min. des IA -3 s, "
   "agressivité ×0.5, délai entre leurs attaques ×1.5, capacités ×0.5." in texte)
f.destroy()

if echecs:
    print(f"\n{len(echecs)} ÉCHEC(S)")
    sys.exit(1)
print("\nTOUS LES TESTS SONT PASSÉS")
