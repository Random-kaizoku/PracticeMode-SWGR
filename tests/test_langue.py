"""Test de la fenêtre : bouton FR / EN et liste des pilotes en deux groupes.
Fenêtre masquée, fichiers dans un dossier temporaire : rien ne touche au jeu."""
from pathlib import Path as _Chemin
RACINE = _Chemin(__file__).resolve().parent.parent   # dossier du dépôt

import configparser, importlib.util, sys, tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(RACINE) + r"\fenetre")
spec = importlib.util.spec_from_file_location("pm", str(RACINE) + r"\fenetre\PracticeMode.pyw")
pm = importlib.util.module_from_spec(spec); spec.loader.exec_module(pm)
tmp = Path(tempfile.mkdtemp()); (tmp / "temps").mkdir()
pm.DOSSIER_ECHANGE = tmp; pm.FICHIER_CATALOGUE = tmp / "catalogue.json"; pm.FICHIER_COMMANDE = tmp / "commande.txt"
pm.FICHIER_ETAT = tmp / "etat.txt"; pm.FICHIER_PREFERENCES = tmp / "prefs.ini"
pm.FICHIER_TEMPS_CSV = tmp / "temps" / "temps.csv"; pm.FICHIER_LANGUE = tmp / "langue.txt"
import json
catalogue = json.load(open(str(RACINE) + r"\echange\catalogue.json", encoding="utf-8"))
catalogue["capacites"] = [   # deux capacités de test (le vrai catalogue peut ne pas en avoir)
    {"chemin": "/Game/Test/BP_Ability_Shield.BP_Ability_Shield_C", "nom": "BP_Ability_Shield_C",
     "affiche": "Bouclier", "description": "Protège.", "niveau": 1, "crash": False,
     "affiche_src": "Shield", "description_src": "Protects."},
    {"chemin": "/Game/Test/BP_Ability_IonBlast.BP_Ability_IonBlast_C", "nom": "BP_Ability_IonBlast_C",
     "affiche": "Onde ionique", "description": "Boum.", "niveau": 1, "crash": True,
     "affiche_src": "Ion Blast", "description_src": "Boom."},
]
# Jeu en français, textes d'origine en anglais (comme le vrai jeu) : le mod
# exporte les deux versions. Ici, les versions « d'origine » sont marquées EN:
interface = catalogue.setdefault("interface", {})
interface.update({"langue_jeu": "fr-FR", "langue_source": "en"})
interface["stats_src"] = {k: "EN:" + v for k, v in (interface.get("stats") or {"0": "Virage"}).items()}
interface.setdefault("stats", {k: v[3:] for k, v in interface["stats_src"].items()})
for section in ("circuits", "planetes", "vehicules", "affixes"):
    for element in catalogue[section]:
        element["affiche_src"] = "EN:" + (element.get("affiche") or element["nom"])
for p in catalogue["pilotes"]:
    if p["nom"] == "DA_Racer_TestPilot":
        p["affiche"], p["affiche_src"] = "Pilote automatique", "Autopilot"
moto = next(v for v in catalogue["vehicules"] if v["nom"] == "VA_Bike")
pm.FICHIER_CATALOGUE.write_text(json.dumps(catalogue), encoding="utf-8")
pm.L.langue_par_defaut = lambda: "fr"            # comme un Windows en français
pm.S.session_en_cours = lambda c: None           # pas de vraie session pendant le test
pm.S.jeu_lance = lambda c: False
pm.S.regles_pare_feu_presentes = lambda c: False


def ok(nom, cond):
    print(("  [OK]    " if cond else "  [ÉCHEC] ") + nom)
    if not cond:
        sys.exit(1)


def textes(f, groupe):
    a = f.arbre_pilotes
    return [a.item(i, "text") for i in a.get_children("grp:" + groupe)]


f = pm.Fenetre(); f.withdraw(); f.update()

print("1. Démarrage en français (langue de Windows)")
ok("bouton « Démarrer l'entraînement »", f.bouton_demarrer.cget("text") == "▶ Démarrer l'entraînement")
ok("langue.txt = fr pour le mod", (tmp / "langue.txt").read_text(encoding="utf-8") == "fr")

print("2. Pilotes : deux groupes, plus aucun nom en double dans un groupe")
a = f.arbre_pilotes
ok("groupes « Pilotes de module » et « Pilotes de speeder »",
   a.item("grp:module", "text") == "Pilotes de module" and a.item("grp:speeder", "text") == "Pilotes de speeder")
module, speeder = textes(f, "module"), textes(f, "speeder")
ok("les DA_PlaneRacer_* sont dans le groupe module",
   all(pm.groupe_pilote(p) == "module" for p in a.get_children("grp:module")))
ok("aucun doublon dans le groupe module", max(Counter(module).values()) == 1)
ok("aucun doublon dans le groupe speeder", max(Counter(speeder).values()) == 1)
sebulba = [x for x in module + speeder if x.startswith("Sebulba")]
print("      Sebulba :", sebulba)
ok("Sebulba : jeune et âgé (module), mentor et course de boss (speeder)",
   "Sebulba  (version âgée)" in module and "Sebulba" in module
   and "Sebulba" in speeder and "Sebulba  (course de boss)" in speeder)

print("3. On choisit un circuit, un pilote et un build, puis on passe en anglais")
age = "/Game/Griffin/Narrative/CharacterDefs/Racers/DA_PlaneRacer_NesodonAged.DA_PlaneRacer_NesodonAged"
a.selection_set(age); f.update()
ok("pilote choisi : Sebulba âgé", f.pilote == age)
a.selection_set("grp:speeder"); f.update()
ok("clic sur un titre de groupe : le pilote ne change pas", f.pilote == age and a.selection() == (age,))
derniere = f.liste_planetes.size() - 1        # une planète qui n'est PAS la première de la liste
f.liste_planetes.selection_clear(0, "end"); f.liste_planetes.selection_set(derniere); f.remplir_circuits()
planete = f.liste_planetes.get(derniere)
f.liste_circuits.selection_clear(0, "end"); f.liste_circuits.selection_set(0)
circuit = f.circuits_affiches[0]["chemin"]
f.var_niveaux[0].set(7)
capacite = f.catalogue.capacites[0]
f.var_capacites[2].set(capacite["texte"])
f.liste_messages.insert("end", "message d'avant")
f.onglets.select(1)
f.var_langue.set("en"); f.changer_langue(); f.update()
ok("bouton « Start practice »", f.bouton_demarrer.cget("text") == "▶ Start practice")
ok("onglet Build toujours affiché", f.onglets.index("current") == 1)
ok("onglets traduits", f.onglets.tab(2, "text") == "  My times  ")
ok("groupes traduits", f.arbre_pilotes.item("grp:module", "text") == "Podracer pilots")
ok("pilote gardé, variante traduite",
   f.pilote == age and f.arbre_pilotes.item(age, "text") == "Sebulba  (older version)")
sel = f.liste_circuits.curselection()
ok("circuit gardé, sur la même planète (dont le nom a changé de langue)",
   sel and f.circuits_affiches[sel[0]]["chemin"] == circuit
   and f.liste_planetes.get(f.liste_planetes.curselection()[0]) == "EN:" + planete)
ok("niveau de stat gardé", f.var_niveaux[0].get() == 7)
ok("capacité gardée dans l'emplacement 3", f.chemin_par_texte.get(f.var_capacites[2].get()) == capacite["chemin"])
ok("capacités vides en anglais : « (none) »", f.var_capacites[0].get() == "(none)")
ok("messages gardés", "message d'avant" in f.liste_messages.get(0, "end"))
ok("langue.txt = en pour le mod", (tmp / "langue.txt").read_text(encoding="utf-8") == "en")
prefs = configparser.ConfigParser(interpolation=None); prefs.read(tmp / "prefs.ini", encoding="utf-8")
ok("langue gardée dans les préférences", prefs["fenetre"]["langue"] == "en")
ok("bandeau traduit", f.var_session.get() == "● Original game (vanilla) — ready for multiplayer"
   or f.var_session.get() == "")

print("3b. Noms venus du jeu : version d'origine (anglais) quand la fenêtre est en anglais")
ok("circuits en anglais", all(f.liste_circuits.get(i).startswith("EN:") for i in range(f.liste_circuits.size())))
ok("planètes en anglais", all(f.liste_planetes.get(i).startswith("EN:") for i in range(f.liste_planetes.size())))
ok("véhicules en anglais", all(r.cget("text").startswith("EN:") for r in f.cadre_types.winfo_children()))
ok("pilote : « Autopilot »", f.arbre_pilotes.item(
    next(p["chemin"] for p in catalogue["pilotes"] if p["nom"] == "DA_Racer_TestPilot"), "text") == "Autopilot")
ok("capacités en anglais", "Shield   (Shield)" in f.combos_capacites[0]["values"])
ok("noms des stats en anglais", f.etiquettes_stats[0].cget("text").startswith("EN:"))
noms_affixes = [f.arbre.item(i, "text") for c in f.arbre.get_children() for i in f.arbre.get_children(c)]
ok("affixes en anglais", noms_affixes and all("EN:" in n for n in noms_affixes))

print("4. Lancer en anglais : la commande garde les vrais chemins")
f.lancer()
commande = dict(l.split("=", 1) for l in (tmp / "commande.txt").read_text(encoding="utf-8").splitlines() if "=" in l)
ok("pilote = chemin de Sebulba âgé", commande["pilote"] == age)
ok("nom du pilote lisible", commande["nom_pilote"] == "Sebulba  (older version)")
ok("capacité envoyée par son chemin", capacite["chemin"] in commande["capacites"].split("|"))
ok("état en anglais", f.var_etat.get() == "Command sent to the game…")

print("5. Retour au français, puis réouverture de la fenêtre")
f.var_langue.set("fr"); f.changer_langue(); f.update()
ok("bouton « Démarrer l'entraînement »", f.bouton_demarrer.cget("text") == "▶ Démarrer l'entraînement")
ok("capacité toujours là", f.chemin_par_texte.get(f.var_capacites[2].get()) == capacite["chemin"])
ok("noms venus du jeu de nouveau en français",
   not f.liste_circuits.get(0).startswith("EN:") and "Bouclier   (Shield)" in f.combos_capacites[0]["values"])

print("6. Records : un même circuit noté en français puis en anglais compte ensemble")
c0 = next(c for c in catalogue["circuits"] if c.get("interne"))
fr_nom = f"{c0['affiche']} [{c0['interne']}]"
en_nom = f"{c0['affiche_src']} [{c0['interne']}]"
en_tete = "Date;Planète;Circuit;Nb tours;Véhicule;Pilote;Temps;Secondes;Meilleur tour;Détail des tours;Build;Save state\n"
(tmp / "temps" / "temps.csv").write_text(
    en_tete + f'"1";"P";"{fr_nom}";"3";"{moto["affiche"]}";"S";"1:10.000";"70.000";"";"";"";"non"\n'
    + f'"2";"P";"{en_nom}";"3";"{moto["affiche_src"]}";"S";"1:05.000";"65.000";"";"";"";"non"\n', encoding="utf-8")
f._date_temps = None; f.rafraichir_etat(); f.update()
etoiles = [f.table_temps.item(i, "values")[6] for i in f.table_temps.get_children()]
print("      ", etoiles)
ok("une seule ★, sur le temps le plus rapide (noté en anglais)", etoiles == ["★ 1:05.000", "1:10.000"])
f.var_langue.set("en"); f.changer_langue(); f.update()
f.fermer()
g = pm.Fenetre(); g.withdraw(); g.update()
ok("la fenêtre rouverte est en anglais", g.bouton_demarrer.cget("text") == "▶ Start practice")
ok("et le pilote est toujours Sebulba âgé", g.pilote == age)
g.destroy()
print("\nTOUS LES TESTS SONT PASSÉS")
