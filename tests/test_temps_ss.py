"""Test : les temps faits avec save state sont affichés mais exclus des records."""
from pathlib import Path as _Chemin
RACINE = _Chemin(__file__).resolve().parent.parent   # dossier du dépôt

import importlib.util, json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(RACINE) + r"\fenetre")
spec = importlib.util.spec_from_file_location("pm", str(RACINE) + r"\fenetre\PracticeMode.pyw")
pm = importlib.util.module_from_spec(spec); spec.loader.exec_module(pm)
tmp = Path(tempfile.mkdtemp()); (tmp / "temps").mkdir()
pm.DOSSIER_ECHANGE = tmp; pm.FICHIER_CATALOGUE = tmp / "catalogue.json"; pm.FICHIER_COMMANDE = tmp / "c.txt"
pm.FICHIER_ETAT = tmp / "e.txt"; pm.FICHIER_LANGUE = tmp / "langue.txt"; pm.FICHIER_PREFERENCES = tmp / "p.ini"; pm.FICHIER_TEMPS_CSV = tmp / "temps" / "temps.csv"
pm.FICHIER_CATALOGUE.write_text(open(str(RACINE) + r"\echange\catalogue.json", encoding="utf-8").read(), encoding="utf-8")
en_tete = "Date;Planète;Circuit;Nb tours;Véhicule;Pilote;Temps;Secondes;Meilleur tour;Détail des tours;Build;Save state\n"
ligne = lambda d, t, s, ss: f'"{d}";"P";"X";"3";"Motojet";"Star";"{t}";"{s}";"";"";"";"{ss}"\n'
pm.FICHIER_TEMPS_CSV.write_text(en_tete + ligne("10:00", "1:16.000", "76.000", "non")
                                + ligne("10:05", "1:02.000", "62.000", "oui")
                                + ligne("10:09", "1:15.500", "75.500", "non"), encoding="utf-8")
f = pm.Fenetre(); f.withdraw(); f.update(); f.rafraichir_etat(); f.update()
lignes = [(f.table_temps.item(i, "values")[0], f.table_temps.item(i, "values")[6], f.table_temps.item(i, "tags"))
          for i in f.table_temps.get_children()]
for l in lignes: print("  ", l)
assert lignes[1][1] == "1:02.000  (save state)" and lignes[1][2] == ""
assert lignes[0][1] == "★ 1:15.500" and lignes[0][2] == ("record",)
print("OK : le temps avec save state est affiché mais n'est pas le record")
f.destroy()
