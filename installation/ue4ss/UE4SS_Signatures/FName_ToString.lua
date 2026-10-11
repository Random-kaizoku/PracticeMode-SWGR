-- FName_ToString.lua : correctif UE4SS pour Star Wars: Galactic Racer (jeu 1.1.4.1, UE 5.7.4)
-- La fonction qui transforme un nom (FName) en texte : FName::ToString.
-- Trouvée via KismetStringLibrary.Conv_NameToString (5 343 appels).
-- Généré par outils/gen_signatures.py le 10/10/2026. Vérifié : motif unique,
-- résultat = 0x143752AF4 (adresse confirmée dans la mémoire du jeu).

-- Register() donne à UE4SS le motif d'octets à chercher (?? = n'importe quel octet).
function Register()
    return "41 57 41 56 56 57 55 53 48 83 EC 38 48 89 D6 83"
end

-- Le motif commence pile au début de la fonction : on renvoie l'adresse trouvée telle quelle.
function OnMatchFound(MatchAddress)
    return MatchAddress
end
