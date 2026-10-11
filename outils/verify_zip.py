"""Verification d'une archive avant livraison.

A lancer SYSTEMATIQUEMENT avant de sortir un build exportable.
Ne jamais valider un zip avec l'outil qui l'a cree : le test qui
compte est l'extraction par l'outil natif de Windows (Expand-Archive),
lance separement.

Usage : python verify_zip.py <archive.zip> [dossier_source]
"""
import hashlib
import os
import sys
import zipfile

BACKSLASH = chr(92)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(z, src=None):
    ok = True

    print("1. en-tete : est-ce un VRAI zip ?")
    with open(z, "rb") as f:
        head = f.read(4)
    good = head == b"PK\x03\x04"
    print(f"   octets 0-3 = {head!r} -> {'PK OK' if good else 'PAS UN ZIP'}")
    ok &= good

    with zipfile.ZipFile(z) as f:
        print("2. integrite CRC de chaque entree")
        bad = f.testzip()
        print(f"   testzip() -> {'toutes les entrees OK' if bad is None else 'CORROMPU : ' + bad}")
        ok &= bad is None

        names = f.namelist()
        print("3. hygiene des chemins")
        prob = [n for n in names
                if BACKSLASH in n or n.startswith("/") or ":" in n or ".." in n]
        print(f"   antislash / chemin absolu / .. -> {prob or 'aucun'}")
        ok &= not prob

        print("4. decompression reelle de tout le contenu")
        total = 0
        digests = {}
        for n in names:
            data = f.read(n)
            total += len(data)
            digests[n] = sha(data)
        print(f"   {len(names)} entrees lues, {total / 1024 / 1024:.1f} Mo, aucune erreur")

    if src:
        print("5. comparaison octet par octet avec la source")
        diffs = []
        for n, d in digests.items():
            p = os.path.join(src, n.replace("/", os.sep))
            if not os.path.isfile(p):
                diffs.append(f"{n} : absent de la source")
                continue
            with open(p, "rb") as f:
                if sha(f.read()) != d:
                    diffs.append(f"{n} : contenu different")
        print(f"   {len(digests)} fichiers compares -> {diffs or 'tous identiques'}")
        ok &= not diffs

    print(f"\n   taille sur disque : {os.path.getsize(z) / 1024 / 1024:.1f} Mo")
    print("   VERDICT :", "ARCHIVE SAINE" if ok else "PROBLEME DETECTE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
