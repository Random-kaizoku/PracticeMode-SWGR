"""Recompile le « bootloader » de PyInstaller (le petit programme de démarrage
de PracticeMode.exe) avec le Visual Studio de ce PC.

Pourquoi : le bootloader livré avec PyInstaller est le même pour tous les .exe
fabriqués avec PyInstaller… y compris des virus. Certains antivirus repèrent
donc ce bootloader lui-même et accusent à tort tout .exe qui le contient
(« faux positif »). Un bootloader compilé ici est différent : ces signatures
ne le reconnaissent plus.

    1. télécharge le code source de la version de PyInstaller installée (PyPI),
       et vérifie son empreinte SHA-256 publiée par PyPI ;
    2. le compile (waf + Visual Studio C++) ;
    3. remplace run.exe / runw.exe de PyInstaller, en gardant les originaux
       (*.officiel) ; outils/empaqueter.py refuse de construire sans cela.

À relancer après chaque mise à jour de PyInstaller.
Usage : python outils\\bootloader.py
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

import PyInstaller

RACINE = Path(__file__).resolve().parent.parent
TRAVAIL = RACINE / "construction" / "bootloader"
INSTALLE = Path(PyInstaller.__file__).resolve().parent / "bootloader" / "Windows-64bit-intel"
FICHIERS = ("run.exe", "runw.exe", "run_d.exe", "runw_d.exe")


def main():
    version = PyInstaller.__version__
    print(f"PyInstaller {version} : {INSTALLE}")
    if TRAVAIL.exists():
        shutil.rmtree(TRAVAIL)
    TRAVAIL.mkdir(parents=True)

    # 1. Code source depuis PyPI, empreinte vérifiée
    info = json.load(urllib.request.urlopen(f"https://pypi.org/pypi/pyinstaller/{version}/json", timeout=60))
    sdist = next(u for u in info["urls"] if u["packagetype"] == "sdist")
    donnees = urllib.request.urlopen(sdist["url"], timeout=300).read()
    if hashlib.sha256(donnees).hexdigest() != sdist["digests"]["sha256"]:
        sys.exit("ERREUR : empreinte du code source différente de celle de PyPI, abandon")
    print(f"source : {sdist['filename']} ({len(donnees) / 1024 / 1024:.1f} Mo), SHA-256 conforme à PyPI")
    archive = TRAVAIL / sdist["filename"]
    archive.write_bytes(donnees)
    with tarfile.open(archive) as t:
        t.extractall(TRAVAIL, filter="data")
    source = TRAVAIL / f"pyinstaller-{version}"

    # 2. Compilation (waf trouve Visual Studio tout seul)
    r = subprocess.run([sys.executable, "./waf", "distclean", "all", "--target-arch=64bit"],
                       cwd=source / "bootloader", capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print(r.stdout[-4000:], r.stderr[-4000:])
        sys.exit("ERREUR : la compilation du bootloader a échoué (Visual Studio C++ installé ?)")
    compiles = source / "PyInstaller" / "bootloader" / "Windows-64bit-intel"

    # 3. Remplacement, en gardant les originaux une seule fois
    for nom in FICHIERS:
        officiel = INSTALLE / (nom + ".officiel")
        if not officiel.exists():
            shutil.copy2(INSTALLE / nom, officiel)
        shutil.copy2(compiles / nom, INSTALLE / nom)
        print(f"   {nom} remplacé (original gardé : {officiel.name})")
    print("Bootloader maison installé.")


if __name__ == "__main__":
    main()
