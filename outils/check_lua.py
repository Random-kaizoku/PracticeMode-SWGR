"""Vérifie la syntaxe de fichiers Lua avec Lua 5.4 (la version d'UE4SS).

Usage : python check_lua.py <fichier_ou_dossier> [...]
On utilise lupa.lua54 et pas la version par défaut de lupa (Lua 5.5),
plus stricte qu'UE4SS : elle signalerait des erreurs sur du code valide.
"""
import os
import sys

from lupa import lua54

lua = lua54.LuaRuntime()
charger = lua.eval("function(src, nom) local f, err = load(src, nom) return err end")

fichiers = []
for arg in sys.argv[1:]:
    if os.path.isdir(arg):
        for racine, _, noms in os.walk(arg):
            fichiers += [os.path.join(racine, n) for n in noms if n.endswith(".lua")]
    else:
        fichiers.append(arg)

erreurs = 0
for f in fichiers:
    with open(f, encoding="utf-8") as fh:
        err = charger(fh.read(), "@" + os.path.basename(f))
    if err:
        erreurs += 1
        print(f"[ERREUR] {err}")
    else:
        print(f"[OK] {f}")
print(f"{len(fichiers)} fichier(s), {erreurs} erreur(s)")
sys.exit(1 if erreurs else 0)
