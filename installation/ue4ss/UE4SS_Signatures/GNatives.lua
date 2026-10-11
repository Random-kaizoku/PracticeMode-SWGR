-- GNatives.lua : correctif UE4SS pour Star Wars: Galactic Racer (jeu 1.1.4.1, UE 5.7.4)
-- La table des fonctions natives de Blueprint (variable globale GNatives).
-- Motif : dans KismetStringLibrary.execConv_NameToString.
-- Généré par outils/gen_signatures.py le 10/10/2026. Vérifié : motif unique,
-- résultat = 0x14AA40040 (adresse confirmée dans la mémoire du jeu).

-- Register() donne à UE4SS le motif d'octets à chercher (?? = n'importe quel octet).
function Register()
    return "0F B6 00 48 8D 15 ?? ?? ?? ?? 48 8B 04 C2 48 8D 15 ?? ?? ?? ?? 4C 8D 44 24 40 48 39 D0 74 79 48"
end

-- Le motif contient une instruction qui désigne la variable par un décalage
-- relatif de 4 octets, situé à +0x6 dans le motif.
-- Adresse de la variable = fin de ce décalage + valeur du décalage.
function OnMatchFound(MatchAddress)
    local PositionDuDecalage = MatchAddress + 0x6
    return PositionDuDecalage + 4 + DerefToInt32(PositionDuDecalage)
end
