"""Test du module session.py sur un faux jeu. Le pare-feu est SIMULÉ."""
from pathlib import Path as _Chemin
RACINE = _Chemin(__file__).resolve().parent.parent   # dossier du dépôt

import hashlib, importlib.util, os, shutil, sys, tempfile, threading, time
from pathlib import Path

spec = importlib.util.spec_from_file_location("session", str(RACINE) + r"\fenetre\session.py")
S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)

def h(p): return hashlib.sha1(Path(p).read_bytes()).hexdigest()
journal = lambda m: print("      journal :", m)

# ── Bac à sable ──
sb = Path(tempfile.mkdtemp())
jeu = sb / "jeu"; w64 = jeu / "Griffin/Binaries/Win64"; w64.mkdir(parents=True)
for n in ("SWGR-Win64-Shipping.exe", "tbb12.dll", "PartyWin.dll"): (w64 / n).write_text("faux")
(w64 / "D3D12").mkdir(); (w64 / "D3D12/D3D12Core.dll").write_text("faux")
for n in ("SWGR.exe", "Launcher.exe"): (jeu / n).write_text("faux")
donnees = sb / "donnees"; reel = Path(os.environ["LOCALAPPDATA"]) / "StarWarsGalacticRacer"
shutil.copytree(reel / "Saved/SaveGames", donnees / "Saved/SaveGames")
shutil.copytree(reel / "Saved/Config", donnees / "Saved/Config")
shutil.copytree(reel / ".sentry-native", donnees / ".sentry-native")
projet = sb / "projet"; (projet / "outils").mkdir(parents=True)
shutil.copytree(str(RACINE) + r"\installation", projet / "installation")
steam = sb / "steam"; (steam / "config").mkdir(parents=True); (steam / "userdata/123/7/remote").mkdir(parents=True)
(steam / "config/loginusers.vdf").write_text('"users"\n{\n"1"\n{\n"WantsOfflineMode"\t\t"1"\n"Timestamp"\t\t"200"\n}\n"2"\n{\n"WantsOfflineMode"\t\t"0"\n"Timestamp"\t\t"100"\n}\n}\n')
(steam / "userdata/123/7/remote/sharedconfig.vdf").write_text('"4078430"\n{\n"cloudenabled"\t\t"0"\n}\n')
cfg = S.Config(projet=projet, racine_jeu=jeu, donnees_jeu=donnees, steam=steam)
sav = next((donnees / "Saved/SaveGames").glob("*/GriffinSave.6.sav"))   # dossier = identifiant Steam du joueur
h_avant = h(sav)

def test(nom, cond):
    print(("  [OK]   " if cond else "  [ÉCHEC] ") + nom)
    if not cond: sys.exit(1)

print("1. Vérifications Steam (faux Steam)")
test("Steam hors ligne détecté", S.steam_hors_ligne(cfg))
test("Steam Cloud désactivé détecté", S.cloud_desactive(cfg))
print("2. Version du jeu inconnue (faux exe) → refus")
try:
    S.debut(cfg, journal); test("refus", False)
except S.ErreurSession as e:
    test(f"refusé : « {str(e)[:70]}… »", "Version du jeu inconnue" in str(e) and not S.ue4ss_installe(cfg))
# On ajoute l'empreinte du faux exe aux versions compatibles (dans le bac à sable)
with open(projet / "installation/versions-compatibles.txt", "a", encoding="utf-8") as f:
    f.write(h(w64 / "SWGR-Win64-Shipping.exe") + "  faux jeu du test\n")
print("2b. Début de session")
session = S.debut(cfg, journal)
test("UE4SS installé", S.ue4ss_installe(cfg))
test("session enregistrée", S.session_en_cours(cfg) == session)
installe = (w64 / "ue4ss/Mods/PracticeMode/Scripts/main.lua").read_text(encoding="utf-8")
test("dossier de PracticeMode écrit dans le mod installé",
     f'local DOSSIER_PRACTICEMODE = "{projet.as_posix()}/"' in installe)
test("le main.lua du dossier « installation » n'est pas modifié",
     'local DOSSIER_PRACTICEMODE = "ECRIT-PAR-LE-LAUNCHER/"'
     in (projet / "installation/ue4ss/Mods/PracticeMode/Scripts/main.lua").read_text(encoding="utf-8"))
test("dossiers echange et temps créés", (projet / "echange").is_dir() and (projet / "temps").is_dir())
print("3. Deuxième début refusé")
try:
    S.debut(cfg, journal); test("refus", False)
except S.ErreurSession as e:
    test(f"refusé : « {e} »", True)
print("4. Simulation d'une session moddée")
sav.write_bytes(sav.read_bytes() + b"TEMPS MODDE")
(w64 / "ue4ss/UE4SS.log").write_text("journal"); (w64 / "ue4ss/CXXHeaderDump").mkdir(); (w64 / "ue4ss/CXXHeaderDump/x.hpp").write_text("x")
(donnees / "Saved/Crashes/UECC").mkdir(parents=True); (donnees / "Saved/Crashes/UECC/dump.dmp").write_text("crash")
(donnees / ".sentry-native/cache/modde.envelope").write_text("rapport")
print("5. Fin de session")
S.fin(cfg, journal)
test("UE4SS retiré", not S.ue4ss_installe(cfg))
test("Win64 identique à l'origine", sorted(p.name for p in w64.iterdir()) == ["D3D12", "PartyWin.dll", "SWGR-Win64-Shipping.exe", "tbb12.dll"])
test("sauvegarde remise à l'identique", h(sav) == h_avant)
test("crash moddé sorti du jeu", not (donnees / "Saved/Crashes").exists())
test("rapport Sentry moddé sorti du jeu", not (donnees / ".sentry-native/cache/modde.envelope").exists())
test("dumps gardés dans la session", (session / "retire-du-jeu/ue4ss/CXXHeaderDump/x.hpp").exists())
test("session fermée", S.session_en_cours(cfg) is None and (session / "session-terminee.txt").exists())
print("6. Compatibilité avec session-dev.ps1 (même marqueur, même fichier d'origine)")
test("win64-origine.txt lisible", (session / "win64-origine.txt").read_text(encoding="utf-8").split()[0] == "D3D12")

print("7. Pare-feu SIMULÉ")
cfg.echange.mkdir(parents=True, exist_ok=True)
# a) le script tourne et attend le signal → il lève le blocage
cfg.etat_pare_feu.write_text("actif", encoding="utf-8")
def faux_script():
    while not cfg.signal_pare_feu.exists(): time.sleep(0.2)
    cfg.signal_pare_feu.unlink(); cfg.etat_pare_feu.write_text("retire", encoding="utf-8")
threading.Thread(target=faux_script, daemon=True).start()
test("a) blocage levé par le script qui attendait", S.liberer_pare_feu(cfg, journal, lanceur=lambda c, m: False))
# b) script disparu, règles absentes
cfg.etat_pare_feu.write_text("", encoding="utf-8")
S_regles = S.regles_pare_feu_presentes
S.regles_pare_feu_presentes = lambda c: False
test("b) rien à lever", S.liberer_pare_feu(cfg, journal, lanceur=lambda c, m: False))
# c) script disparu, règles présentes, confirmation refusée
S.regles_pare_feu_presentes = lambda c: True
test("c) refus de confirmation → signalé, pas d'erreur", S.liberer_pare_feu(cfg, journal, lanceur=lambda c, m: False) is False)
S.regles_pare_feu_presentes = S_regles

print("8. Chemin pour le mod, détection du jeu")
test("chemin simple : barres « / » et « / » final", S.chemin_pour_lua(Path(r"C:\PracticeMode")) == "C:/PracticeMode/")
accents = sb / "Dossier é"; accents.mkdir()
try:
    r = S.chemin_pour_lua(accents)
    test(f"chemin accentué → nom court sans accent ({r})", r.isascii())
except S.ErreurSession as e:
    test("chemin accentué sans nom court → refus clair", "accents" in str(e))
(steam / "steamapps").mkdir(); biblio = sb / "biblio"
(steam / "steamapps/libraryfolders.vdf").write_text('"libraryfolders"\n{\n"0"\n{\n"path"\t\t"'
                                                    + str(biblio).replace("\\", "\\\\") + '"\n}\n}\n')
(biblio / "steamapps/common/SWGR/Griffin/Binaries/Win64").mkdir(parents=True)
(biblio / "steamapps/common/SWGR/Griffin/Binaries/Win64/SWGR-Win64-Shipping.exe").write_text("faux")
(biblio / "steamapps/appmanifest_4078430.acf").write_text('"AppState"\n{\n"installdir"\t\t"SWGR"\n}\n')
test("jeu trouvé dans une 2e bibliothèque Steam", S.trouver_jeu(steam) == biblio / "steamapps/common/SWGR")
test("Config sans jeu : racine_jeu = None, pas de plantage",
     S.Config(projet=projet, steam=sb / "vide").racine_jeu is None
     and not S.jeu_trouve(S.Config(projet=projet, steam=sb / "vide")))

print("9. Fonctions réelles en LECTURE seule")
reel_cfg = S.Config()
print("      jeu trouvé :", reel_cfg.racine_jeu)
print("      processus lancés :", len(S.processus()))
print("      vrai jeu lancé (tu joues) :", S.jeu_lance(reel_cfg))
print("      Steam hors ligne (réel) :", S.steam_hors_ligne(reel_cfg), "| Cloud désactivé (réel) :", S.cloud_desactive(reel_cfg))
print("      règles PracticeMode dans le pare-feu (lecture) :", S.regles_pare_feu_presentes(reel_cfg))
print("      pare-feu Windows activé :", S.pare_feu_windows_actif())
print("\nTOUS LES TESTS SONT PASSÉS")
