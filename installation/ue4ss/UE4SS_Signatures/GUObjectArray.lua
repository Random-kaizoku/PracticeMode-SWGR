-- GUObjectArray.lua : correctif UE4SS pour Star Wars: Galactic Racer (jeu 1.1.4.1, UE 5.7.4)
-- La liste de tous les objets du jeu (variable globale GUObjectArray).
-- Motif : « lea rcx,[GUObjectArray] » juste avant l'appel qui réserve la
-- liste au démarrage (fonction qui lit gc.MaxObjectsInGame).
-- Généré par outils/gen_signatures.py le 10/10/2026. Vérifié : motif unique,
-- résultat = 0x14AC5E910 (adresse confirmée dans la mémoire du jeu).

-- Register() donne à UE4SS le motif d'octets à chercher (?? = n'importe quel octet).
function Register()
    return "48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? E8 ?? ?? ?? ?? E8 ?? ?? ?? ?? C6 05"
end

-- Le motif contient une instruction qui désigne la variable par un décalage
-- relatif de 4 octets, situé à +0x3 dans le motif.
-- Adresse de la variable = fin de ce décalage + valeur du décalage.
function OnMatchFound(MatchAddress)
    local PositionDuDecalage = MatchAddress + 0x3
    return PositionDuDecalage + 4 + DerefToInt32(PositionDuDecalage)
end
