-- GMalloc.lua : correctif UE4SS pour Star Wars: Galactic Racer (build Steam 25880680 du 12/10/2026, UE 5.7.4-382801)
-- Le gestionnaire de mémoire du jeu (variable globale GMalloc).
-- Motif : début de FMemory::Free (145 293 appels), qui lit GMalloc.
-- Généré par outils/gen_signatures.py le 12/10/2026. Vérifié : motif unique,
-- résultat = 0x14AB757C8 (adresse confirmée dans la mémoire du jeu).

-- Register() donne à UE4SS le motif d'octets à chercher (?? = n'importe quel octet).
function Register()
    return "41 57 41 56 41 55 41 54 56 57 55 53 48 83 EC 58 48 85 C9 0F 84 ?? ?? ?? ?? 48 89 CF 48 8B 35 ?? ?? ?? ?? 48 85 F6 0F 84 ?? ?? ?? ?? 48 8B 06 48 8B 40 48 48 8D 0D ?? ?? ?? ?? 48 39 C8 0F 85 ?? ?? ?? ?? 66 85 FF 0F 84 ?? ?? ?? ?? 48 89 FB 48 81 E3 00 00 FF FF 0F B6 43 03 3D ?? ?? ?? ?? 0F"
end

-- Le motif contient une instruction qui désigne la variable par un décalage
-- relatif de 4 octets, situé à +0x1F dans le motif.
-- Adresse de la variable = fin de ce décalage + valeur du décalage.
function OnMatchFound(MatchAddress)
    local PositionDuDecalage = MatchAddress + 0x1F
    return PositionDuDecalage + 4 + DerefToInt32(PositionDuDecalage)
end
