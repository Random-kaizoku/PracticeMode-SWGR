-- FName_Constructor.lua : correctif UE4SS pour Star Wars: Galactic Racer (jeu 1.1.4.1, UE 5.7.4)
-- La fonction qui crée un nom à partir d'un texte :
-- FName::FName(const wchar_t* Nom, EFindName Mode).
-- Version qui respecte le paramètre Mode (ajouter / seulement chercher).
-- Généré par outils/gen_signatures.py le 10/10/2026. Vérifié : motif unique,
-- résultat = 0x143C7E216 (adresse confirmée dans la mémoire du jeu).

-- Register() donne à UE4SS le motif d'octets à chercher (?? = n'importe quel octet).
function Register()
    return "41 56 56 57 53 48 81 EC 48 04 00 00 44 89 C3 48"
end

-- Le motif commence pile au début de la fonction : on renvoie l'adresse trouvée telle quelle.
function OnMatchFound(MatchAddress)
    return MatchAddress
end
