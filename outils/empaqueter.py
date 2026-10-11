"""Fabrique l'archive à publier (Nexus) : construction/PracticeMode-SWGR-v<version>.zip

    1. tests automatiques (tests/test_*.py)            → tout doit passer
    2. PracticeMode.exe (PyInstaller, Python inclus)   → construction/pyinstaller/
    3. dossier PracticeMode/ prêt à distribuer          → construction/PracticeMode-v<version>/
         PracticeMode.exe + _internal/                  la fenêtre
         installation/                                  UE4SS + correctifs + le mod (réglages publics)
         outils/pare-feu-session.ps1                    le blocage pare-feu
         LISEZMOI.txt, README.txt, licences/
    4. auto-test du .exe (sur une COPIE du dossier)     → il démarre, trouve tout, se ferme
    5. archive zip (chemins en « / », sans dossier vide)
    6. vérifications : verify_zip.py, puis Expand-Archive de Windows (l'expérience
       réelle de l'utilisateur), comparaison octet par octet, et recherche de
       données personnelles (identifiant Steam, nom d'utilisateur Windows…)

Usage : python outils\\empaqueter.py [--sans-tests]
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CONSTRUCTION = RACINE / "construction"
MOD = RACINE / "installation" / "ue4ss" / "Mods" / "PracticeMode" / "Scripts" / "main.lua"
AUTEUR = "RNGKZK"   # pseudo Nexus de l'auteur

# Réglages d'UE4SS pour la version publique : pas de console ni de raccourcis
# de développement (le journal UE4SS.log reste écrit, pour les dépannages).
REGLAGES_PUBLICS = {
    "ConsoleEnabled": "0", "GuiConsoleEnabled": "0", "GuiConsoleVisible": "0",
    "EnableHotReloadSystem": "0", "EnableDumping": "0",
}
MODS_TXT = "; Mods UE4SS actifs (1) ou inactifs (0)\nPracticeMode : 1\n"
MODS_JSON = json.dumps([{"mod_name": "PracticeMode", "mod_enabled": True}], indent=4) + "\n"


def mots_interdits():
    """Ce qui ne doit JAMAIS se trouver dans l'archive : les données personnelles
    de CE PC, relevées sur place (rien n'est écrit en dur dans ce script) :
    identifiant(s) Steam des sauvegardes du jeu, nom de compte et pseudo Steam,
    nom d'utilisateur Windows, début de l'e-mail de git."""
    mots = {os.environ.get("USERNAME", "")}
    saves = Path(os.environ.get("LOCALAPPDATA", "")) / "StarWarsGalacticRacer" / "Saved" / "SaveGames"
    if saves.exists():
        mots |= {p.name for p in saves.iterdir() if p.is_dir() and p.name.isdigit()}
    sys.path.insert(0, str(RACINE / "fenetre"))
    import session
    try:
        vdf = (session.trouver_steam() / "config" / "loginusers.vdf").read_text(encoding="utf-8", errors="replace")
        mots |= set(re.findall(r'"(?:AccountName|PersonaName)"\s+"([^"]+)"', vdf))
        mots |= set(re.findall(r'^\s*"(\d{17})"', vdf, re.M))
    except OSError:
        pass
    email = subprocess.run(["git", "config", "user.email"], cwd=RACINE, capture_output=True, text=True).stdout
    if "@" in email:
        mots.add(email.strip().split("@")[0])
    # Le pseudo d'auteur est public par choix (crédits) : on ne le compte pas
    return sorted({m.encode("utf-8") for m in mots if len(m) >= 4 and m.lower() != AUTEUR.lower()})


def etape(titre):
    print(f"\n=== {titre}", flush=True)


def sha256(chemin):
    return hashlib.sha256(Path(chemin).read_bytes()).hexdigest()


def lire_version():
    fenetre = (RACINE / "fenetre" / "PracticeMode.pyw").read_text(encoding="utf-8")
    version = re.search(r'^VERSION = "([\d.]+)"', fenetre, re.M).group(1)
    if f'Traduire("charge", "{version}")' not in MOD.read_text(encoding="utf-8"):
        sys.exit(f"ERREUR : la fenêtre est en v{version} mais pas le mod (main.lua)")
    return version


def lancer_tests():
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for test in sorted((RACINE / "tests").glob("test_*.py")):
        r = subprocess.run([sys.executable, str(test)], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env, timeout=900)
        print(f"   {'OK    ' if r.returncode == 0 else 'ÉCHEC '} {test.name}")
        if r.returncode != 0:
            print(r.stdout[-3000:], r.stderr[-3000:])
            sys.exit("ERREUR : un test a échoué, pas d'archive")


def verifier_bootloader():
    """Le .exe doit utiliser le bootloader compilé ici (outils/bootloader.py) :
    celui livré avec PyInstaller fait réagir certains antivirus (faux positifs)."""
    import PyInstaller
    dossier = Path(PyInstaller.__file__).resolve().parent / "bootloader" / "Windows-64bit-intel"
    officiel = dossier / "runw.exe.officiel"
    if not officiel.exists() or sha256(officiel) == sha256(dossier / "runw.exe"):
        sys.exit("ERREUR : bootloader officiel de PyInstaller → lance d'abord : python outils\\bootloader.py")
    print(f"   bootloader maison : runw.exe {sha256(dossier / 'runw.exe')[:16]}… (officiel {sha256(officiel)[:16]}…)")


def construire_exe(version):
    verifier_bootloader()
    travail = CONSTRUCTION / "pyinstaller"
    if travail.exists():
        shutil.rmtree(travail)
    travail.mkdir(parents=True)
    a, b, c = (version.split(".") + ["0", "0"])[:3]
    (travail / "version.txt").write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers=({a}, {b}, {c}, 0), prodvers=({a}, {b}, {c}, 0), mask=0x3f, flags=0x0,
                    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', '{AUTEUR}'),
      StringStruct('FileDescription', 'PracticeMode for STAR WARS Galactic Racer'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', 'PracticeMode'),
      StringStruct('OriginalFilename', 'PracticeMode.exe'),
      StringStruct('ProductName', 'PracticeMode'),
      StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""", encoding="utf-8")
    # --onedir et --noupx : un .exe en un seul bloc ou compressé par UPX
    # fait davantage réagir les antivirus.
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed",
                    "--noupx",
                    "--log-level", "WARN", "--name", "PracticeMode",
                    "--version-file", str(travail / "version.txt"),
                    "--distpath", str(travail / "dist"), "--workpath", str(travail / "work"),
                    "--specpath", str(travail), "--paths", str(RACINE / "fenetre"),
                    str(RACINE / "fenetre" / "PracticeMode.pyw")], check=True)
    dist = travail / "dist" / "PracticeMode"
    if not (dist / "PracticeMode.exe").exists():
        sys.exit("ERREUR : PracticeMode.exe n'a pas été créé")
    return dist


def regler_ini(texte, reglages):
    for cle, valeur in reglages.items():
        texte, n = re.subn(rf"^{cle}\s*=.*$", f"{cle} = {valeur}", texte, flags=re.M)
        if n != 1:
            sys.exit(f"ERREUR : réglage {cle} introuvable dans UE4SS-settings.ini")
    return texte


def assembler(version, dist):
    dossier = CONSTRUCTION / f"PracticeMode-v{version}"
    if dossier.exists():
        shutil.rmtree(dossier)
    pm = dossier / "PracticeMode"
    shutil.copytree(dist, pm)

    # UE4SS, ses correctifs et le mod : seulement ce qui sert
    source = RACINE / "installation"
    inst = pm / "installation"
    ue = inst / "ue4ss"
    (ue / "Mods").mkdir(parents=True)
    shutil.copy2(source / "dwmapi.dll", inst / "dwmapi.dll")
    shutil.copy2(source / "versions-compatibles.txt", inst / "versions-compatibles.txt")
    shutil.copy2(source / "ue4ss" / "UE4SS.dll", ue / "UE4SS.dll")
    shutil.copy2(source / "ue4ss" / "LICENSE", ue / "LICENSE")
    shutil.copytree(source / "ue4ss" / "UE4SS_Signatures", ue / "UE4SS_Signatures")
    shutil.copytree(source / "ue4ss" / "Mods" / "shared", ue / "Mods" / "shared")
    (ue / "Mods" / "PracticeMode" / "Scripts").mkdir(parents=True)
    (ue / "Mods" / "PracticeMode" / "enabled.txt").write_bytes(b"")
    lua = MOD.read_bytes().decode("utf-8")   # octets tels quels (fins de ligne gardées)
    # Le dossier de l'utilisateur est écrit à l'installation par le launcher
    lua, n = re.subn(r'^local DOSSIER_PRACTICEMODE = "[^"\r\n]*"',
                     'local DOSSIER_PRACTICEMODE = "ECRIT-PAR-LE-LAUNCHER/"', lua, flags=re.M)
    if n != 1:
        sys.exit("ERREUR : ligne DOSSIER_PRACTICEMODE introuvable dans main.lua")
    (ue / "Mods" / "PracticeMode" / "Scripts" / "main.lua").write_bytes(lua.encode("utf-8"))
    # (écrits en octets, fins de ligne « LF » : identiques à ceux du dépôt public)
    (ue / "Mods" / "mods.txt").write_bytes(MODS_TXT.encode("utf-8"))
    (ue / "Mods" / "mods.json").write_bytes(MODS_JSON.encode("utf-8"))
    ini = (source / "ue4ss" / "UE4SS-settings.ini").read_text(encoding="utf-8")
    (ue / "UE4SS-settings.ini").write_bytes(regler_ini(ini, REGLAGES_PUBLICS).encode("utf-8"))

    # Script du pare-feu (lancé en administrateur par la fenêtre ; UTF-8 avec BOM pour PowerShell 5.1)
    (pm / "outils").mkdir()
    shutil.copy2(RACINE / "outils" / "pare-feu-session.ps1", pm / "outils" / "pare-feu-session.ps1")

    # Modes d'emploi et licences
    for nom in ("LISEZMOI.txt", "README.txt"):
        texte = (RACINE / "publication" / nom).read_text(encoding="utf-8").replace("{VERSION}", version)
        (pm / nom).write_text(texte, encoding="utf-8-sig")   # BOM : bons accents dans le Bloc-notes
    (pm / "licences").mkdir()
    shutil.copy2(source / "ue4ss" / "LICENSE", pm / "licences" / "UE4SS-LICENSE.txt")
    return dossier


def auto_test(dossier):
    essai = CONSTRUCTION / "auto-test"
    if essai.exists():
        shutil.rmtree(essai)
    shutil.copytree(dossier, essai)
    resultat = essai / "resultat.json"
    subprocess.run([str(essai / "PracticeMode" / "PracticeMode.exe"), "--auto-test", str(resultat)], timeout=180)
    if not resultat.exists():
        sys.exit("ERREUR : le .exe n'a écrit aucun résultat (il ne démarre pas ?)")
    r = json.loads(resultat.read_text(encoding="utf-8"))
    print("   ", r)
    attendu = {"ok": True, "exe": True, "pare_feu_script": True, "ue4ss": True}
    rates = [k for k, v in attendu.items() if r.get(k) != v] + ([] if r.get("versions_compatibles") else ["versions"])
    if rates:
        sys.exit(f"ERREUR : auto-test du .exe raté : {rates}")
    if Path(r["dossier"]).resolve() != (essai / "PracticeMode").resolve():
        sys.exit("ERREUR : le .exe ne travaille pas dans son propre dossier")
    shutil.rmtree(essai)


def zipper(dossier, version):
    archive = CONSTRUCTION / f"PracticeMode-SWGR-v{version}.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(dossier.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(dossier).as_posix())
    return archive


def donnees_personnelles(dossier):
    """Cherche les données personnelles dans chaque fichier, y compris dans les
    modules Python compressés à l'intérieur du .exe (archive PYZ de PyInstaller)."""
    from PyInstaller.archive.readers import CArchiveReader, ZlibArchiveReader
    trouves = []
    interdits = mots_interdits()
    print(f"   {len(interdits)} mots personnels recherchés (relevés sur ce PC, non affichés)")

    def examiner(nom, data):
        for mot in interdits:
            if mot.lower() in data.lower():
                trouves.append(f"{nom} : mot n° {interdits.index(mot) + 1}")

    for f in dossier.rglob("*"):
        if f.is_file():
            examiner(str(f.relative_to(dossier)), f.read_bytes())
    exe = dossier / "PracticeMode" / "PracticeMode.exe"
    lecteur = CArchiveReader(str(exe))
    for nom in lecteur.toc:
        examiner(f"PracticeMode.exe!{nom}", lecteur.extract(nom) or b"")
    for pyz in (dossier / "PracticeMode").rglob("*.pyz"):
        za = ZlibArchiveReader(str(pyz))
        for nom in za.toc:
            examiner(f"{pyz.name}!{nom}", za.extract(nom, raw=True) or b"")
    pyz_exe = [n for n in lecteur.toc if n.endswith(".pyz") or "PYZ" in n.upper()]
    for nom in pyz_exe:
        tmp = Path(tempfile.mkdtemp()) / "x.pyz"
        tmp.write_bytes(lecteur.extract(nom))
        za = ZlibArchiveReader(str(tmp))
        for module in za.toc:
            examiner(f"PracticeMode.exe!{nom}!{module}", za.extract(module, raw=True) or b"")
    return trouves


def verifier(archive, dossier):
    import importlib.util
    spec = importlib.util.spec_from_file_location("verify_zip", RACINE / "outils" / "verify_zip.py")
    vz = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vz)
    if vz.main(str(archive), str(dossier)) != 0:
        sys.exit("ERREUR : verify_zip a trouvé un problème")

    print("\n   Expand-Archive (l'outil de Windows, comme l'utilisateur) :")
    cible = Path(tempfile.mkdtemp()) / "extrait"
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"Expand-Archive -LiteralPath '{archive}' -DestinationPath '{cible}' -Force"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ERREUR : Expand-Archive a échoué : {r.stderr}")
    source = {f.relative_to(dossier).as_posix(): sha256(f) for f in dossier.rglob("*") if f.is_file()}
    extrait = {f.relative_to(cible).as_posix(): sha256(f) for f in cible.rglob("*") if f.is_file()}
    if source != extrait:
        manque = sorted(set(source) ^ set(extrait))[:10]
        differe = [k for k in source if k in extrait and source[k] != extrait[k]][:10]
        sys.exit(f"ERREUR : l'extraction diffère de la source : manque {manque}, diffère {differe}")
    print(f"   {len(extrait)} fichiers extraits, tous identiques à la source (SHA-256)")
    shutil.rmtree(cible.parent)

    print("\n   Données personnelles :")
    trouves = donnees_personnelles(dossier)
    if trouves:
        sys.exit("ERREUR : données personnelles dans l'archive :\n   " + "\n   ".join(trouves[:20]))
    print("   aucune (identifiant Steam, nom d'utilisateur, e-mail)")


def analyse_defender(chemins):
    """Analyse Microsoft Defender, en lecture seule (-DisableRemediation : rien
    n'est mis en quarantaine). Code 0 = aucune menace, 2 = menace trouvée."""
    mpcmdrun = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Windows Defender" / "MpCmdRun.exe"
    if not mpcmdrun.exists():
        print("   (Microsoft Defender absent : analyse sautée)")
        return
    subprocess.run([str(mpcmdrun), "-SignatureUpdate"], capture_output=True)   # dernières définitions
    for chemin in chemins:
        r = subprocess.run([str(mpcmdrun), "-Scan", "-ScanType", "3", "-File", str(chemin), "-DisableRemediation"],
                           capture_output=True, text=True, errors="replace")
        if r.returncode != 0:
            sys.exit(f"ERREUR : Defender signale un problème sur {chemin} :\n{r.stdout[-2000:]}")
        print(f"   {Path(chemin).name} : aucune menace")


def main():
    version = lire_version()
    print(f"PracticeMode v{version}")
    if "--sans-tests" not in sys.argv:
        etape("1. Tests automatiques")
        lancer_tests()
    etape("2. PracticeMode.exe (PyInstaller)")
    dist = construire_exe(version)
    etape("3. Dossier à distribuer")
    dossier = assembler(version, dist)
    print(f"   {dossier}")
    etape("4. Auto-test du .exe (sur une copie)")
    auto_test(dossier)
    etape("5. Archive")
    archive = zipper(dossier, version)
    etape("6. Vérifications de l'archive")
    verifier(archive, dossier)
    etape("7. Antivirus (Microsoft Defender, signatures à jour)")
    analyse_defender([dossier, archive])
    print(f"\nARCHIVE PRÊTE : {archive}  ({archive.stat().st_size / 1024 / 1024:.1f} Mo)")
    print(f"SHA-256 : {sha256(archive)}")


if __name__ == "__main__":
    main()
