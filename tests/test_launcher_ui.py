"""Parcours complet du launcher dans la fenêtre masquée, sur un faux jeu.
Pare-feu et lancement du jeu SIMULÉS : rien n'est modifié dans Windows ni dans le vrai jeu."""
from pathlib import Path as _Chemin
RACINE = _Chemin(__file__).resolve().parent.parent   # dossier du dépôt

import hashlib, importlib.util, json, os, shutil, sys, tempfile, threading, time
from pathlib import Path

sys.path.insert(0, str(RACINE) + r"\fenetre")
import session as S
spec = importlib.util.spec_from_file_location("pm", str(RACINE) + r"\fenetre\PracticeMode.pyw")
pm = importlib.util.module_from_spec(spec); spec.loader.exec_module(pm)
assert pm.S is S
pm.L.langue_par_defaut = lambda: "fr"   # les vérifications ci-dessous lisent les textes français

# ── Faux jeu (même construction que test_session.py) ──
sb = Path(tempfile.mkdtemp())
jeu = sb / "jeu"; w64 = jeu / "Griffin/Binaries/Win64"; w64.mkdir(parents=True)
for n in ("SWGR-Win64-Shipping.exe", "tbb12.dll"): (w64 / n).write_text("faux")
donnees = sb / "donnees"; reel = Path(os.environ["LOCALAPPDATA"]) / "StarWarsGalacticRacer"
for e in ("Saved/SaveGames", "Saved/Config", ".sentry-native"): shutil.copytree(reel / e, donnees / e)
projet = sb / "projet"; (projet / "outils").mkdir(parents=True)
shutil.copytree(str(RACINE) + r"\installation", projet / "installation")
with open(projet / "installation/versions-compatibles.txt", "a", encoding="utf-8") as f:   # faux exe accepté
    f.write(hashlib.sha1((w64 / "SWGR-Win64-Shipping.exe").read_bytes()).hexdigest() + "  faux jeu du test\n")
steam = sb / "steam"; (steam / "config").mkdir(parents=True); (steam / "userdata/1/7/remote").mkdir(parents=True)
(steam / "config/loginusers.vdf").write_text('{\n"WantsOfflineMode"\t"1"\n"Timestamp"\t"9"\n}\n')
(steam / "userdata/1/7/remote/sharedconfig.vdf").write_text('"4078430"\n{\n"cloudenabled"\t"0"\n}\n')
cfg = S.Config(projet=projet, racine_jeu=jeu, donnees_jeu=donnees, steam=steam)
sav = next((donnees / "Saved/SaveGames").glob("*/GriffinSave.6.sav"))   # dossier = identifiant Steam du joueur
h = lambda p: hashlib.sha1(Path(p).read_bytes()).hexdigest()
h_origine = h(sav)

# ── Simulations ──
etat = {"jeu": False, "regles": False, "accepter_uac": True}
S.Config = lambda: cfg
S.jeu_lance = lambda c: etat["jeu"]
S.pare_feu_windows_actif = lambda: True
S.regles_pare_feu_presentes = lambda c: etat["regles"]
def faux_script(c, mode):
    if not etat["accepter_uac"]:
        return False
    def tourne():
        etat["regles"] = True; c.etat_pare_feu.write_text("actif", encoding="utf-8")
        while not c.signal_pare_feu.exists(): time.sleep(0.1)
        c.signal_pare_feu.unlink(); etat["regles"] = False; c.etat_pare_feu.write_text("retire", encoding="utf-8")
    threading.Thread(target=tourne, daemon=True).start()
    return True
S.lancer_script_pare_feu = faux_script
S.lancer_jeu = lambda c: etat.__setitem__("jeu", True)

# Fichiers de la fenêtre dans le bac à sable
cat = json.load(open(str(RACINE) + r"\echange\catalogue.json", encoding="utf-8"))
pm.DOSSIER_ECHANGE = cfg.echange; cfg.echange.mkdir(parents=True, exist_ok=True)
pm.FICHIER_CATALOGUE = cfg.echange / "catalogue.json"; pm.FICHIER_CATALOGUE.write_text(json.dumps(cat), encoding="utf-8")
pm.FICHIER_COMMANDE = cfg.echange / "commande.txt"; pm.FICHIER_ETAT = cfg.echange / "etat.txt"
pm.FICHIER_LANGUE = cfg.echange / "langue.txt"
pm.FICHIER_PREFERENCES = sb / "prefs.ini"; pm.FICHIER_TEMPS_CSV = sb / "temps.csv"

f = pm.Fenetre(); f.withdraw()
def attendre(secondes, condition=lambda: False):
    fin = time.time() + secondes
    while time.time() < fin and not condition():
        f.update(); time.sleep(0.05)
def ok(nom, cond):
    print(("  [OK]    " if cond else "  [ÉCHEC] ") + nom)
    if not cond:
        print("\n".join(f.liste_messages.get(0, "end"))); sys.exit(1)

attendre(3)
ok("état initial : vanilla", "vanilla" in f.var_session.get())
ok("bouton Démarrer actif", "disabled" not in f.bouton_demarrer.state())

print("1. Démarrer l'entraînement")
f.bouton_demarrer.invoke()
attendre(15, lambda: "EN COURS" in f.var_session.get())
ok("UE4SS installé dans le faux jeu", S.ue4ss_installe(cfg))
ok("pare-feu (simulé) actif", S.etat_pare_feu(cfg) == "actif")
ok("jeu lancé, bandeau rouge « EN COURS »", "EN COURS" in f.var_session.get())
ok("bouton Démarrer désactivé pendant la session", "disabled" in f.bouton_demarrer.state())

print("2. On joue (sauvegarde modifiée), puis on ferme le jeu")
sav.write_bytes(sav.read_bytes() + b"MODDE")
etat["jeu"] = False
attendre(25, lambda: "vanilla" in f.var_session.get() and not f.travail_en_cours)
ok("remise d'origine automatique", not S.ue4ss_installe(cfg) and S.session_en_cours(cfg) is None)
ok("sauvegarde d'origine remise", h(sav) == h_origine)
ok("pare-feu (simulé) levé", S.etat_pare_feu(cfg) == "retire" and not etat["regles"])

print("3. Refus de la fenêtre administrateur")
etat["accepter_uac"] = False
f.bouton_demarrer.invoke()
attendre(15, lambda: not f.travail_en_cours and "vanilla" in f.var_session.get() and f.liste_messages.size() > 0
         and "refusé" in " ".join(f.liste_messages.get(0, "end")))
attendre(3)
ok("entraînement annulé et jeu remis d'origine", not S.ue4ss_installe(cfg) and S.session_en_cours(cfg) is None)
ok("le jeu n'a pas été lancé", not etat["jeu"])

VDF = steam / "config/loginusers.vdf"
HORS_LIGNE = VDF.read_text()
print("4. Steam repasse EN LIGNE pendant une session (incident du 11/10)")
etat["accepter_uac"] = True
f.bouton_demarrer.invoke()
attendre(15, lambda: "EN COURS" in f.var_session.get())
VDF.write_text(HORS_LIGNE.replace('"WantsOfflineMode"\t"1"', '"WantsOfflineMode"\t"0"'))
attendre(6, lambda: "EN LIGNE alors" in " ".join(f.liste_messages.get(0, "end")))
ok("alerte « Steam EN LIGNE pendant une session »", "EN LIGNE alors" in " ".join(f.liste_messages.get(0, "end")))
etat["jeu"] = False                          # on quitte le jeu…
f.relancer_jeu()                             # …et on veut le relancer, Steam toujours en ligne
attendre(1)
ok("« Relancer le jeu » refusé tant que Steam est en ligne", not etat["jeu"]
   and "Steam est en ligne" in " ".join(f.liste_messages.get(0, "end")))
VDF.write_text(HORS_LIGNE)
attendre(25, lambda: "vanilla" in f.var_session.get() and not f.travail_en_cours)
ok("remise d'origine automatique quand même", not S.ue4ss_installe(cfg) and S.session_en_cours(cfg) is None)

print("\nMessages affichés dans la fenêtre :")
for m in f.liste_messages.get(0, "end"):
    print("   ", m)

print("5. Fermer la fenêtre pendant une session")
f.bouton_demarrer.invoke()
attendre(15, lambda: "EN COURS" in f.var_session.get())
reponses = {"okcancel": False, "yesnocancel": True}
pm.messagebox.askokcancel = lambda *a: reponses["okcancel"]
pm.messagebox.askyesnocancel = lambda *a: reponses["yesnocancel"]
f.fermer()                                   # le jeu tourne : « Fermer quand même ? » → Annuler
attendre(1)
ok("jeu lancé + Annuler : la fenêtre reste ouverte", f.winfo_exists())
etat["jeu"] = False
attendre(0.5)
detruite = []                                # on note la fermeture de la fenêtre au moment où elle a lieu
_destroy = f.destroy
f.destroy = lambda: (detruite.append(S.session_en_cours(cfg) is None), _destroy())
f.fermer()                                   # jeu fermé : « Remettre d'origine puis fermer ? » → Oui
fin = time.time() + 25
while time.time() < fin and not detruite:
    f.update(); time.sleep(0.05)
fermee = detruite == [True]                  # fermée, et seulement APRÈS la fin de session
print(("  [OK]    " if fermee and not S.ue4ss_installe(cfg) and S.session_en_cours(cfg) is None else "  [ÉCHEC] ")
      + "jeu fermé + Oui : jeu remis d'origine, PUIS fenêtre fermée")
if not (fermee and not S.ue4ss_installe(cfg) and S.session_en_cours(cfg) is None):
    print("   fermetures :", detruite, "| UE4SS :", S.ue4ss_installe(cfg), "| session :", S.session_en_cours(cfg))
    sys.exit(1)
print("\nTOUS LES TESTS SONT PASSÉS")
