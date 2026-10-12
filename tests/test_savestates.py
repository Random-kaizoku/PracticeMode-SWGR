"""Test des save states : vrai main.lua dans Lua 5.4, faux véhicule, horloge simulée."""
from pathlib import Path as _Chemin
RACINE = _Chemin(__file__).resolve().parent.parent   # dossier du dépôt

import math, sys, tempfile
from pathlib import Path
from lupa import lua54

src = Path(str(RACINE) + r"\installation\ue4ss\Mods\PracticeMode\Scripts\main.lua").read_text(encoding="utf-8")
tmp = Path(tempfile.mkdtemp()); (tmp / "echange").mkdir(); (tmp / "temps").mkdir()
ligne = 'local DOSSIER_PRACTICEMODE = "ECRIT-PAR-LE-LAUNCHER/"'
assert src.count(ligne) == 1
src = src.replace(ligne, f'local DOSSIER_PRACTICEMODE = "{tmp.as_posix()}/"')   # comme le fait le launcher
# L'exploration doit être allumée pour ces tests (si elle est coupée dans le mod, on la
# rallume ICI seulement, pour continuer à tester son code)
src = src.replace("Exploration                  = false,", "Exploration                  = true,")
assert src.count("Exploration                  = true,") == 1
# CONFIG rendue globale ICI seulement, pour que les tests puissent changer une option
assert src.count("local CONFIG = {") == 1
src = src.replace("local CONFIG = {", "CONFIG = {")
VDF = tmp / "loginusers.vdf"                 # faux fichier de Steam (2 comptes, le plus récent compte)
STEAM_HORS_LIGNE = ('"users"\n{\n"1"\n{\n"WantsOfflineMode"\t\t"1"\n"Timestamp"\t\t"200"\n}\n'
                    '"2"\n{\n"WantsOfflineMode"\t\t"0"\n"Timestamp"\t\t"100"\n}\n}\n')
STEAM_EN_LIGNE = STEAM_HORS_LIGNE.replace('"1"\n"Timestamp"\t\t"200"', '"0"\n"Timestamp"\t\t"200"')
VDF.write_text(STEAM_HORS_LIGNE, encoding="utf-8")
ligne = 'local FICHIER_STEAM = "ECRIT-PAR-LE-LAUNCHER"'
assert src.count(ligne) == 1
src = src.replace(ligne, f'local FICHIER_STEAM = "{VDF.as_posix()}"')
assert "ECRIT-PAR-LE-LAUNCHER" not in src
(tmp / "echange" / "pare-feu.txt").write_text("actif", encoding="utf-8-sig")   # session protégée (avec BOM, comme PowerShell)

lua = lua54.LuaRuntime()
lua.execute(r"""
Key = setmetatable({}, {__index = function(t, k) return k end})
ModifierKey = {SHIFT = "SHIFT", CONTROL = "CONTROL", ALT = "ALT"}
journal = {}; print = function(s) table.insert(journal, s) end
liaisons = {}
RegisterKeyBind = function(touche, a, b)
    if b then table.insert(liaisons, {touche = touche, mods = a, fn = b})
    else table.insert(liaisons, {touche = touche, mods = {}, fn = a}) end
end
-- Horloge simulée pour ExecuteWithDelay
maintenant, attente = 0, {}
ExecuteInGameThreadWithDelay = function(ms, fn) table.insert(attente, {t = maintenant + ms, fn = fn}) end
-- (fonctions du fil « async » d'UE4SS : le mod ne doit plus s'en servir, v0.9.9)
anciens_appels = 0
ExecuteWithDelay = function(ms, fn) anciens_appels = anciens_appels + 1; ExecuteInGameThreadWithDelay(ms, fn) end
function avancer(ms)
    maintenant = maintenant + ms
    local reste = {}
    for _, a in ipairs(attente) do if a.t <= maintenant then a.fn() else table.insert(reste, a) end end
    attente = reste
end
ExecuteInGameThread = function(f) f() end
FindFirstOf = function() return nil end
FindAllOf = function() return nil end
boucles = {}
LoopInGameThreadWithDelay = function(ms, f) boucles[ms] = f end
LoopAsync = function(ms, f) anciens_appels = anciens_appels + 1; boucles[ms] = f end
-- Sons
sons = {}
bib = {}
function bib:IsValid() return true end
setmetatable(bib, {__index = function(t, k) return function(self, pion) table.insert(sons, k) end end})
StaticFindObject = function(chemin) if chemin:find("UIAudioLibrary") then return bib end return nil end
-- Faux véhicule
appels_reset = {}
reset = {}
function reset:Server_RequestResetAtLocationAtSpeed(tr, mph, prot, sol, tele, ia)
    table.insert(appels_reset, {tr = tr, mph = mph, prot = prot, sol = sol, tele = tele, ia = ia})
    pion.vit = {X = 0, Y = 0, Z = 0}   -- comme en jeu : la remise en place repart à l'arrêt
end
pion = {ResetComponent = reset, pos = {X = 100, Y = 200, Z = 300}, rot = {Pitch = 0, Yaw = 90, Roll = 0}, vit = {X = 4470.4, Y = 0, Z = 0}}
function pion:IsValid() return true end
function pion:K2_GetActorLocation() return {X = self.pos.X, Y = self.pos.Y, Z = self.pos.Z} end
function pion:K2_GetActorRotation() return {Pitch = self.rot.Pitch, Yaw = self.rot.Yaw, Roll = self.rot.Roll} end
function pion:GetVelocity() return self.vit end
-- Corps physique du véhicule (composant racine) et téléportation
FName = function(s) return {nom = s} end
teleportations, vitesses_rendues, rotations_rendues = {}, {}, {}
teleport_refusee = false
racine = {w = {X = 0, Y = 0, Z = 15}}
function racine:IsValid() return true end
function racine:IsSimulatingPhysics(os) return true end
function racine:GetPhysicsAngularVelocityInDegrees(os) return self.w end
function racine:SetPhysicsLinearVelocity(v, ajout, os)
    table.insert(vitesses_rendues, v); pion.vit = {X = v.X, Y = v.Y, Z = v.Z}
end
function racine:SetPhysicsAngularVelocityInDegrees(w, ajout, os) table.insert(rotations_rendues, w) end
function pion:K2_GetRootComponent() return racine end
function pion:K2_SetActorLocationAndRotation(pos, rot, balayage, impact, teleport)
    if teleport_refusee then error("téléportation refusée (simulée)") end
    table.insert(teleportations, {pos = pos, rot = rot, teleport = teleport})
    self.pos = {X = pos.X, Y = pos.Y, Z = pos.Z}
end
-- Monde, horloge serveur, chrono
carte = "L_Dalmatian_P2P"; heure_serveur = 1000.0
monde = {GameState = {}}
function monde.GameState:GetServerWorldTimeSeconds() return heure_serveur end
function monde:GetFName() return {ToString = function() return carte end} end
comp = {bHasFinishedEvent = false, PreviousLapTime = -1, EventFinishTime = -1, BestLapTime = -1,
        CurrentSectorNumber = 4, SectorStartServerTime = 990.0}
function comp:IsValid() return true end
etat = {RaceEventComponent = comp}; function etat:IsValid() return true end
-- Contrôleur : état des boutons de la manette
boutons = {}
ctrl = {PlayerState = etat}; function ctrl:IsValid() return true end
function ctrl:IsInputKeyDown(cle) return boutons[cle.KeyName.nom] == true end
function ctrl:GetClass() return {GetFName = function() return {ToString = function() return "GfnPlayerController" end} end} end
function ctrl:GetWorld() return monde end
en_pause = false
statiques = {}
function statiques:IsGamePaused(monde) return en_pause end
package.preload["UEHelpers"] = function() return {
    GetPlayerController = function() return ctrl end,
    GetPlayer = function() return pion end,
    GetWorld = function() return monde end,
    GetGameplayStatics = function() return statiques end } end
""")
lua.execute(src)
L = lua.globals()

def boucle():
    L.boucles[500]()   # la boucle principale du mod (commandes + chrono)

def touche(nom, mods=()):
    """Simule un appui : le rappel d'UE4SS (fil des touches) lève le drapeau,
    puis la boucle des touches (fil du jeu, 20 ms) fait l'action. UE4SS compare
    les modificateurs exactement : Maj+F7 ne déclenche que la liaison Maj+F7."""
    for l in L.liaisons.values():
        if l.touche == nom and sorted(l.mods.values()) == sorted(mods):
            l.fn()
    L.boucles[20]()
    L.avancer(300)

def derniers(n=1):
    return [str(x) for x in list(L.journal.values())[-n:]]

def ok(nom, cond):
    print(("  [OK]    " if cond else "  [ÉCHEC] ") + nom)
    if not cond:
        print("\n".join(str(x) for x in L.journal.values())); sys.exit(1)

print("Liaisons enregistrées :", sorted((l.touche, tuple(l.mods.values())) for l in L.liaisons.values()))
etat_txt = lambda: (tmp / "echange" / "etat.txt").read_text(encoding="utf-8")

print("0. Fils d'exécution (v0.9.9) : tout dans le fil du jeu, touches par drapeau")
ok("boucles du fil du jeu : principale (500 ms), touches (20 ms), manette (33 ms)",
   L.boucles[500] is not None and L.boucles[20] is not None and L.boucles[33] is not None)
ok("aucun LoopAsync ni ExecuteWithDelay (fil « async » d'UE4SS)", L.anciens_appels == 0)
lua.execute("""
collectgarbage("stop")
local avant = collectgarbage("count")
liaisons[1].fn()                        -- le rappel d'UE4SS, sur son propre fil
rappel_memoire = collectgarbage("count") - avant
collectgarbage("restart")
""")
ok("le rappel d'une touche ne crée aucun objet Lua (rien pour le ramasse-miettes)", L.rappel_memoire == 0)
ok("et ne fait rien d'autre que lever le drapeau (l'action attend la boucle)", "sauvegard" not in etat_txt())
L.boucles[20]()                          # (on vide ce drapeau : appui de F5 sans dernier choix)

print("1. F7 seul → emplacement 1")
touche("F7")
ok("emplacement 1 sauvegardé, 100 mph ≈ 161 km/h", "emplacement 1 sauvegardé (161 km/h)" in etat_txt())
ok("son de checkpoint joué", list(L.sons.values())[-1] == "PlayPrecisionCheckpointSfx")

print("2. Maj+F7 → seulement l'emplacement 2")
L.pion.pos.X = 5000
touche("F7", ["SHIFT"])
ok("emplacement 2 sauvegardé", "emplacement 2 sauvegardé" in etat_txt())
journal = " ".join(str(x) for x in L.journal.values())
ok("l'emplacement 1 n'a PAS été écrasé", journal.count("emplacement 1 sauvegardé") == 1)

print("3. Ctrl+F8 sur un emplacement vide → erreur et son d'erreur")
touche("F8", ["CONTROL"])
ok("message emplacement vide", "emplacement 3 vide" in etat_txt())
ok("son d'erreur", list(L.sons.values())[-1] == "PlayHitmarkerSfx")

print("4. Maj+F8 → retour DIRECT à l'emplacement 2 (téléportation + vitesse rendue)")
lua.execute("pion.vit = {X = 0, Y = 0, Z = 0}")       # on roule au ralenti avant le retour
touche("F8", ["SHIFT"])
tps = list(L.teleportations.values())
ok("une seule téléportation (pas aussi l'emplacement 1)", len(tps) == 1)
ok("position de l'emplacement 2, en mode téléportation", tps[0].pos.X == 5000 and tps[0].teleport is True)
ok("orientation rendue (cap 90°)", tps[0].rot.Yaw == 90)
vr = list(L.vitesses_rendues.values())
ok("vitesse rendue : le vecteur sauvegardé (100 mph vers +X)", len(vr) >= 1 and abs(vr[0].X - 4470.4) < 1e-6)
ok("rotation du véhicule rendue", len(list(L.rotations_rendues.values())) >= 1)
ok("pas de remise en place du jeu", len(list(L.appels_reset.values())) == 0)

print("4b. Si la téléportation est refusée → remise en place du jeu, puis vitesse réinjectée")
L.teleport_refusee = True
touche("F8", ["SHIFT"])
L.avancer(700)
appels = list(L.appels_reset.values())
ok("une remise en place du jeu", len(appels) == 1)
a = appels[0]
q = a.tr.Rotation
ok("orientation : cap 90° → quaternion (0, 0, 0.7071, 0.7071)",
   abs(q.X) < 1e-9 and abs(q.Y) < 1e-9 and abs(q.Z - math.sqrt(0.5)) < 1e-9 and abs(q.W - math.sqrt(0.5)) < 1e-9)
ok("vitesse 100 mph passée, télémétrie coupée, protection et IA désactivées",
   abs(a.mph - 100) < 0.01 and a.tele is False and a.prot is False and a.ia is False)
journal = " ".join(str(x) for x in L.journal.values())
ok("le jeu avait remis à l'arrêt → vitesse réinjectée par le mod", "remise à 161" in journal)
L.teleport_refusee = False

print("5. Chrono de section : départ secteur 4 → passage au secteur 5")
boucle()                                   # 1er passage : note le secteur de départ (4)
L.comp.CurrentSectorNumber = 5; L.comp.SectorStartServerTime = 1012.345
boucle()
ok("section enregistrée : 0:12.345", "section depuis l'emplacement 2 : 0:12.345" in etat_txt())
ok("son de réussite", list(L.sons.values())[-1] == "PlayShakedownSuccessSfx")
ok("fichier sections.txt écrit", "secteur 4 → 5 | 0:12.345" in (tmp / "temps" / "sections.txt").read_text(encoding="utf-8"))

print("6. Arrivée : le temps est marqué « save state » (hors records)")
L.comp.PreviousLapTime = 70.0; L.comp.bHasFinishedEvent = True; L.comp.EventFinishTime = 70.0; L.comp.BestLapTime = 70.0
boucle()
txt = (tmp / "temps" / "temps.txt").read_text(encoding="utf-8")
csv = (tmp / "temps" / "temps.csv").read_text(encoding="utf-8")
ok("temps.txt : « (save state) »", "1:10.000 (save state)" in txt)
import csv as _csv
_lignes = list(_csv.DictReader(csv.splitlines(), delimiter=";"))
ok("temps.csv : colonne Save state = oui", _lignes and _lignes[0].get("Save state") == "oui")
ok("temps.csv : colonne Détail du build (v0.9.6)", "Détail du build" in _lignes[0])

print("7. Course suivante (sans retour F8) : plus marquée save state")
L.comp.bHasFinishedEvent = False; L.comp.PreviousLapTime = -1
boucle()
L.comp.PreviousLapTime = 71.0; L.comp.bHasFinishedEvent = True; L.comp.EventFinishTime = 71.0
boucle()
_lignes = list(_csv.DictReader((tmp / "temps" / "temps.csv").read_text(encoding="utf-8").splitlines(), delimiter=";"))
ok("2e temps sans mention save state", len(_lignes) == 2 and _lignes[1].get("Save state") == "non")

print("8. Autre circuit : retour refusé")
L.carte = "L_Corgi_LOOP_A"
touche("F8")
ok("refus « autre circuit »", "autre circuit" in etat_txt())

print("9. Manette : croix bas = sauvegarder, croix droite = revenir (emplacement 1)")
manette = L.boucles[33]
def bouton(nom, enfonce):
    L.boutons[nom] = enfonce
    manette()
    L.avancer(50)
nb_tp = len(list(L.teleportations.values()))
lua.execute("pion.pos = {X = 777, Y = 0, Z = 0}")
bouton("Gamepad_DPad_Down", True); bouton("Gamepad_DPad_Down", False)
ok("écran de résultats (course terminée) : la croix est ignorée", "emplacement 1 sauvegardé" not in etat_txt())
L.comp.bHasFinishedEvent = False             # nouvelle course
bouton("Gamepad_DPad_Down", True)
ok("croix bas : emplacement 1 sauvegardé", "emplacement 1 sauvegardé" in etat_txt())
bouton("Gamepad_DPad_Down", True)            # bouton maintenu : pas de 2e sauvegarde
bouton("Gamepad_DPad_Down", False)
journal = " ".join(str(x) for x in L.journal.values())
ok("bouton maintenu = une seule sauvegarde", journal.count("emplacement 1 sauvegardé") == 2)  # 1 au test 1 + 1 ici
bouton("Gamepad_DPad_Right", True); bouton("Gamepad_DPad_Right", False)
tps = list(L.teleportations.values())
ok("croix droite : retour à l'emplacement 1", len(tps) == nb_tp + 1 and tps[-1].pos.X == 777)
L.en_pause = True
bouton("Gamepad_DPad_Right", True); bouton("Gamepad_DPad_Right", False)
ok("en pause (menu) : la croix est ignorée", len(list(L.teleportations.values())) == nb_tp + 1)
L.en_pause = False

print("10. Situation du crash du 10/10 : Ctrl+R en course, objet du menu resté en mémoire")
lua.execute("""
menu_fantome = {}; function menu_fantome:IsValid() return true end
FindFirstOf = function(c) if c == "FrontEndGameMode" then return menu_fantome end return nil end
FindAllOf = function() return nil end
ForEachUObject = function() error("ForEachUObject ne doit JAMAIS être appelé") end
""")
catalogue = tmp / "echange" / "catalogue.json"
L.carte = "L_Dalmatian_P2P"                  # en course
boucle()
ok("en course : pas d'export du catalogue malgré l'objet du menu", not catalogue.exists())
L.carte = "L_FrontEnd"                       # retour au menu principal
boucle()
ok("au menu principal : export fait, sans ForEachUObject ni erreur",
   catalogue.exists() and not any("ERREUR" in str(x) for x in L.journal.values()))

print("11. Boost : énergie de postcombustion, chaleur et état du ramjet rendus au retour")
L.carte = "L_Dalmatian_P2P"
lua.execute("""
etat_vehicule = {BoostState = 4, AfterburnerState = 0, AfterburnerEnergy = 0.8,
                 RamjetState = 3, RamjetHeat = 0.4, RamjetBypassHeat = 0.1}
function etat_vehicule:IsValid() return true end
appels_boost = {}
ramjet = {RamjetState = 3}; function ramjet:IsValid() return true end
function ramjet:Server_ChangeHeat(h)
    table.insert(appels_boost, "chaleur " .. h.EngineHeat .. " " .. h.BypassHeat); etat_vehicule.RamjetHeat = h.EngineHeat
end
function ramjet:Server_ChangeState(s) table.insert(appels_boost, "ramjet " .. s); self.RamjetState = s end
-- Fausse postcombustion qui fait comme on soupçonne le jeu : un appel qui ne
-- change pas d'état est ignoré (l'énergie n'est alors PAS rendue)
post = {State = 0}; function post:IsValid() return true end
function post:Server_UpdateState(s, e)
    table.insert(appels_boost, "post " .. s .. " " .. e)
    if s ~= self.State then self.State = s; etat_vehicule.AfterburnerEnergy = e end
end
boost = {BoostState = 4, Ramjet = ramjet, Afterburner = post}; function boost:IsValid() return true end
function boost:Server_ChangeState(m) table.insert(appels_boost, "mode " .. m); self.BoostState = m end
pion.VehicleState = etat_vehicule; pion.BoostComponent = boost
""")
appels_boost = lambda: [str(x) for x in L.appels_boost.values()]
touche("F7")
journal = " ".join(str(x) for x in L.journal.values())
ok("boost lu à la sauvegarde", "emplacement 1 : mode 4, postcombustion état 0 énergie 0.800, ramjet état 3 chaleur 0.400 / 0.100" in journal)
lua.execute("etat_vehicule.AfterburnerEnergy = 0.1; etat_vehicule.RamjetHeat = 0.9; boost.BoostState = 2; ramjet.RamjetState = 6")
touche("F8")
ok("mode ramjet, chaleur, état ramjet et énergie rendus par les fonctions du jeu",
   appels_boost() == ["mode 4", "chaleur 0.4 0.1", "ramjet 3", "post 2 0.8", "post 0 0.8"])
ok("postcombustion revenue à son état sauvegardé (0)", L.post.State == 0)
ok("énergie et chaleur de nouveau à 0.8 / 0.4", L.etat_vehicule.AfterburnerEnergy == 0.8 and L.etat_vehicule.RamjetHeat == 0.4)
L.avancer(700)   # les relectures partent de l'appui réel (après le garde-fou de 80 ms)
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : chaque étape notée", "boost rendu : mode 4 ok, chaleur ramjet ok, état ramjet 3 ok, postcombustion via état 2 ok, postcombustion ok, écriture directe ok" in journal)
ok("journal : relecture à +100 ms", "retour 1, +100 ms : mode 4, postcombustion état 0 énergie 0.800" in journal)

print("11b. Sauvegarde pendant un passage de mode et ramjet explosé : mode d'arrivée, explosion jamais rendue")
lua.execute("appels_boost = {}; etat_vehicule.BoostState = 3; etat_vehicule.RamjetState = 7")
touche("F7", ["CONTROL"])
lua.execute("boost.BoostState = 2; ramjet.RamjetState = 0")
touche("F8", ["CONTROL"])
ok("mode d'arrivée (ramjet = 4) demandé", "mode 4" in appels_boost())
ok("l'état « explosé » n'est pas rendu", not any(a.startswith("ramjet ") for a in appels_boost()))

print("11c. Véhicule sans ramjet : seule la postcombustion est rendue, sans erreur")
lua.execute("""appels_boost = {}; etat_vehicule.BoostState = 2; etat_vehicule.RamjetState = 0
sans_ramjet = {}; function sans_ramjet:IsValid() return false end
boost.Ramjet = sans_ramjet""")
touche("F7", ["SHIFT"])
touche("F8", ["SHIFT"])
ok("postcombustion rendue, rien sur le ramjet",
   any(a.startswith("post ") for a in appels_boost()) and not any(a.startswith(("chaleur", "ramjet")) for a in appels_boost()))
lua.execute("boost.Ramjet = ramjet")

print("11d. Retour par la remise en place du jeu : boost rendu une 2e fois après elle")
lua.execute("appels_boost = {}")
L.teleport_refusee = True
touche("F8", ["SHIFT"])
L.avancer(700)
L.teleport_refusee = False
ok("postcombustion rendue 2 fois (juste après, puis +50 ms)", appels_boost().count("post 0 0.8") == 2)

print("11f. Postcombustion : énergie rendue malgré un état identique, et état 2 voulu → passage par 1")
lua.execute("""appels_boost = {}; pion.VehicleState = etat_vehicule; post.State = 0
etat_vehicule.AfterburnerState = 0; etat_vehicule.AfterburnerEnergy = 0.681""")
touche("F7")
lua.execute("etat_vehicule.AfterburnerEnergy = 1.0; post.State = 0; appels_boost = {}")
# Sans écriture directe, pour vérifier que c'est bien la fonction du jeu qui rend l'énergie
lua.execute("CONFIG.Boost_EcritureDirecte = false")
touche("F8")
ok("énergie 0.681 rendue alors que l'état était déjà 0", L.etat_vehicule.AfterburnerEnergy == 0.681)
lua.execute("""etat_vehicule.AfterburnerState = 2; appels_boost = {}""")
touche("F7", ["CONTROL"])
lua.execute("post.State = 2; appels_boost = {}")
touche("F8", ["CONTROL"])
ok("état voulu 2 : passage par 1, puis 2", [a for a in appels_boost() if a.startswith("post ")][:2] == ["post 1 0.681", "post 2 0.681"])
lua.execute("CONFIG.Boost_EtatIntermediaire = false; appels_boost = {}; post.State = 2")
touche("F8", ["CONTROL"])
ok("option coupée : un seul appel, comme avant", [a for a in appels_boost() if a.startswith("post ")][:1] == ["post 2 0.681"]
   and sum(a.startswith("post ") for a in appels_boost()) == 1)
lua.execute("CONFIG.Boost_EtatIntermediaire = true; CONFIG.Boost_EcritureDirecte = true; etat_vehicule.AfterburnerState = 0")

print("11e. Boost illisible (pas de VehicleState) : le save state marche quand même")
lua.execute("pion.VehicleState = nil; appels_boost = {}")
nb_tp = len(list(L.teleportations.values()))
touche("F7"); touche("F8")
ok("retour fait, aucune fonction de boost appelée",
   len(list(L.teleportations.values())) == nb_tp + 1 and appels_boost() == [])

print("12. Anglais : la fenêtre écrit « en » dans langue.txt, les messages suivent")
lua.execute("pion.VehicleState = etat_vehicule")
(tmp / "echange" / "langue.txt").write_text("en", encoding="utf-8")
boucle()                                     # le mod relit langue.txt
touche("F7", ["SHIFT"])
ok("« slot 2 saved (161 km/h) »", "slot 2 saved (161 km/h)" in etat_txt())
touche("F8", ["SHIFT"])
ok("« back to slot 2 … section timer started »", "back to slot 2 (161 km/h) — section timer started" in etat_txt())
(tmp / "echange" / "langue.txt").write_text("xx", encoding="utf-8")
boucle()
touche("F7", ["SHIFT"])
ok("code inconnu : on garde l'anglais", "slot 2 saved" in etat_txt())
(tmp / "echange" / "langue.txt").write_text("fr", encoding="utf-8")
boucle()
touche("F7", ["SHIFT"])
ok("retour au français", "emplacement 2 sauvegardé" in etat_txt())

print("13. Capacités lues dans les listes du jeu (sans parcourir tous les objets)")
lua.execute("""
CLASSE_CAPACITE = {IsValid = function() return true end}
CLASSE_CRASH = {IsValid = function() return true end}
local ancien = StaticFindObject
-- Bibliothèques du moteur : version d'origine des textes, langues
BIB_TEXTES = {IsValid = function() return true end}
function BIB_TEXTES:GetTextSourceString(texte) return {ToString = function() return texte.source end} end
BIB_LANGUES = {IsValid = function() return true end}
function BIB_LANGUES:GetCurrentLanguage() return "fr-FR" end
function BIB_LANGUES:GetNativeCulture(categorie) return "en" end
StaticFindObject = function(chemin)
    if chemin == "/Script/Griffin.GfnAbility" then return CLASSE_CAPACITE end
    if chemin == "/Script/Griffin.GfnCrashAbility" then return CLASSE_CRASH end
    if chemin == "/Script/Engine.Default__KismetTextLibrary" then return BIB_TEXTES end
    if chemin == "/Script/Engine.Default__KismetInternationalizationLibrary" then return BIB_LANGUES end
    return ancien(chemin)
end
function tableau(elements)
    local t = {}
    function t:ForEach(f) for i, e in ipairs(elements) do f(i, {get = function() return e end}) end end
    return setmetatable(t, {__len = function() return #elements end})
end
function classe(nom, ameliorations, estCapacite, estCrash)
    local cdo = {PlayerFacingName = {ToString = function() return "Nom " .. nom end, source = "Name " .. nom},
                 AbilityLevel = 1, CanUpgradeTo = tableau(ameliorations or {})}
    function cdo:IsA(c) return (c == CLASSE_CAPACITE and estCapacite) or (c == CLASSE_CRASH and estCrash) end
    function cdo:IsValid() return true end
    local c = {}
    function c:IsValid() return true end
    function c:GetFName() return {ToString = function() return nom end} end
    function c:GetFullName() return "BlueprintGeneratedClass /Game/Abilities/" .. nom .. "." .. nom end
    function c:GetCDO() return cdo end
    return c
end
bouclier2 = classe("BP_Ability_Shield_Lv2_C", nil, true)
bouclier = classe("BP_Ability_Shield_C", {bouclier2}, true)
turbo = classe("BP_Ability_Boost_C", nil, true)
ion = classe("BP_Ability_IonBlast_C", nil, true, true)
pas_capacite = classe("BP_Decor_C", nil, false)
liste_jeu = {IsValid = function() return true end, All = tableau({bouclier, turbo})}
build1 = {IsValid = function() return true end, AbilitySlots = tableau({turbo, pas_capacite}), CrashAbility = ion}
build2 = {IsValid = function() return true end, AbilitySlots = tableau({})}
FindAllOf = function(c)
    if c == "GfnAbilityList" then return {liste_jeu} end
    if c == "VehicleBuildDef" then return {build1, build2} end
    return nil
end
""")
L.carte = "L_FrontEnd"                       # au menu principal
(tmp / "echange" / "commande.txt").write_text("action=catalogue\n", encoding="utf-8")
boucle()
import json as _json
cat_exporte = _json.loads((tmp / "echange" / "catalogue.json").read_text(encoding="utf-8"))
capacites = cat_exporte["capacites"]
ok("plus de texte « d'origine » (affiche_src) : ne marche pas à travers UE4SS, remplacé par la traduction",
   all("affiche_src" not in c for c in capacites))
ok("langues exportées : jeu fr-FR, textes d'origine en",
   cat_exporte["interface"].get("langue_jeu") == "fr-FR" and cat_exporte["interface"].get("langue_source") == "en")
noms = sorted(c["nom"] for c in capacites)
print("      capacités exportées :", noms)
ok("liste du jeu + builds + version améliorée, sans doublon ni intrus",
   noms == ["BP_Ability_Boost_C", "BP_Ability_IonBlast_C", "BP_Ability_Shield_C", "BP_Ability_Shield_Lv2_C"])
ok("la capacité de crash est marquée crash",
   [c["nom"] for c in capacites if c.get("crash")] == ["BP_Ability_IonBlast_C"])
ok("nom affiché lu sur l'objet par défaut", any(c.get("affiche") == "Nom BP_Ability_Shield_Lv2_C" for c in capacites))
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : détail des sources (le turbo, déjà vu, n'est compté qu'une fois)",
   "(liste du jeu 2, builds 2, blueprints 0, améliorations 1), 4 retenues" in journal)

print("14. Verrou : sans pare-feu actif (installation à la main, sans launcher), le mod ne fait rien")
L.carte = "L_Dalmatian_P2P"
nb_tp = len(list(L.teleportations.values()))
(tmp / "echange" / "pare-feu.txt").write_text("retire", encoding="utf-8")
L.avancer(3000); lua.execute("os.clock = (function(h) return function() return h() + 1000 end end)(os.clock)")
touche("F8", ["SHIFT"])
ok("F8 refusé : message du verrou", "PracticeMode est inactif" in etat_txt())
ok("aucune téléportation", len(list(L.teleportations.values())) == nb_tp)
(tmp / "echange" / "commande.txt").write_text("type=motojet\npiste=/Game/X\n", encoding="utf-8")
boucle()
ok("commande de course jetée, pas exécutée", not (tmp / "echange" / "commande.txt").exists()
   and "lancement" not in etat_txt())
(tmp / "echange" / "pare-feu.txt").unlink()
lua.execute("os.clock = (function(h) return function() return h() + 1000 end end)(os.clock)")
touche("F7")
ok("fichier absent : toujours verrouillé", "PracticeMode est inactif" in etat_txt())
(tmp / "echange" / "pare-feu.txt").write_text("actif", encoding="utf-8-sig")
lua.execute("os.clock = (function(h) return function() return h() + 1000 end end)(os.clock)")
touche("F7")
ok("pare-feu de nouveau actif : la sauvegarde marche", "emplacement 1 sauvegardé" in etat_txt())

print("15. Verrou : Steam repasse EN LIGNE pendant la session (incident du 11/10), le mod se bloque")
VDF.write_text(STEAM_EN_LIGNE, encoding="utf-8")
lua.execute("os.clock = (function(h) return function() return h() + 1000 end end)(os.clock)")
nb_tp = len(list(L.teleportations.values()))
touche("F8")
ok("F8 refusé, message « Steam est EN LIGNE »", "Steam est EN LIGNE" in etat_txt())
ok("aucune téléportation", len(list(L.teleportations.values())) == nb_tp)
VDF.unlink()
lua.execute("os.clock = (function(h) return function() return h() + 1000 end end)(os.clock)")
touche("F7")
ok("fichier de Steam illisible : bloqué aussi (on ne sait pas)", "Steam est EN LIGNE" in etat_txt()
   and "sauvegardé" not in etat_txt())
VDF.write_text(STEAM_HORS_LIGNE, encoding="utf-8")
lua.execute("os.clock = (function(h) return function() return h() + 1000 end end)(os.clock)")
touche("F7")
ok("Steam de nouveau hors ligne : la sauvegarde marche", "emplacement 1 sauvegardé" in etat_txt())

print("16. Exploration (lecture seule) des modes et épreuves : préparation des adversaires IA")
lua.execute("""
local function objet(nom, chemin, classe, champs)
    local o = champs or {}
    function o:IsValid() return true end
    function o:GetFName() return {ToString = function() return nom end} end
    function o:GetFullName() return classe .. " " .. chemin end
    function o:GetClass() return {GetFName = function() return {ToString = function() return classe end} end} end
    return o
end
local function texte(s) return {ToString = function() return s end} end
function carte(cles)
    local t = {}
    function t:ForEach(f) for _, k in ipairs(cles) do f({get = function() return k end}, {get = function() return 0 end}) end end
    return t
end
local grille = {PlayerFacingName = texte("1 joueur + 11 motojets"),
                Entries = tableau({{EntryType = 4, NumEntrants = 1}, {EntryType = 2, NumEntrants = 11}})}
mode_course = objet("GMV_TeamRace_Bikes", "/Game/Modes/GMV_TeamRace_Bikes.GMV_TeamRace_Bikes", "GameModeVariantDef",
                    {PlayerFacingName = texte("Course par équipes"), GameMode = 1, GridMakeup = grille})
local classement = objet("LDB_ARC_TMR_BIKE_X", "/Game/LDB/LDB_ARC_TMR_BIKE_X.LDB_ARC_TMR_BIKE_X", "LeaderboardDef")
local config = objet("TeamRaceConfig_0", "/Game/E/EVT.EVT:TeamRaceConfig_0", "TeamRaceConfig",
                     {RaceEventModeType = 1, bUseCustomVehicle = false, bUsePlayerHealth = true, Leaderboard = classement})
local adversaire = {Driver = texte("/Game/Racers/DA_Racer_Star.DA_Racer_Star"), vehicleType = 2,
                    vehicleBuild = texte("/Game/Builds/VBD_Bike_AI.VBD_Bike_AI"),
                    AIState = {RacerAggressionLevel = {RowName = texte("Agressif")}, GameModePacingConfigs = carte({1, 2})}}
epreuve_ia = objet("EVT_ARC_TMR_BIKE_X", "/Game/Arcade/EVT_ARC_TMR_BIKE_X.EVT_ARC_TMR_BIKE_X", "ArcadeEventDef",
                   {PlayerFacingName = texte("Course des Dunes"), LapCount = 3, Category = 1,
                    TrackDef = objet("TRAK_DAL_LOOP_A", "/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", "TrackDef"),
                    VehicleTypeTag = {TagName = texte("Vehicle.Standard.Bike")}, EventMode = config,
                    GridMakeup = grille, CustomOpponents = tableau({adversaire})})
local liste = objet("DA_EventList", "/Game/Lists/DA_EventList.DA_EventList", "GfnEventList",
                    {QuickRaceGameModes = tableau({mode_course}), QuickRacePlanets = tableau({texte("/Game/P/PLA_Corgi.PLA_Corgi")}),
                     AllEventSets = tableau({{PlayerFacingName = texte("Arcade"), Events = tableau({epreuve_ia})}}),
                     QuickPlayEvents = tableau({epreuve_ia})})
local circuit = objet("TRAK_COR", "/Game/T/TRAK_COR.TRAK_COR", "TrackDef", {})
local ancienFindAllOf = FindAllOf
FindAllOf = function(c)
    if c == "GameModeVariantDef" then return {mode_course} end
    if c == "GfnEventList" then return {liste} end
    if c == "ArcadeEventDef" then return {epreuve_ia} end
    if c == "TrackDef" then return {circuit} end            -- 1 circuit : le catalogue compte comme fait
    return ancienFindAllOf(c)
end
local ancienStatic = StaticFindObject
StaticFindObject = function(chemin)
    if chemin == "/Script/Griffin.FrontEndGameMode:LaunchCustomRace" then return objet("LaunchCustomRace", chemin, "Function") end
    return ancienStatic(chemin)
end
-- Noms des stats du jeu (VehicleUIConfig) chargés : le catalogue est complet
local config_ui = objet("VehicleUIConfig_0", "/Game/UI/VehicleUIConfig.VehicleUIConfig", "VehicleUIConfig")
local ancienFindFirstOf = FindFirstOf
FindFirstOf = function(c)
    if c == "VehicleUIConfig" then return config_ui end
    return ancienFindFirstOf(c)
end
""")
L.carte = "L_FrontEnd"
(tmp / "echange" / "commande.txt").write_text("action=catalogue\n", encoding="utf-8")
boucle()                                     # catalogue (1 circuit, des capacités) → fait
boucle()                                     # exploration, une fois le catalogue fait
fichier = tmp / "echange" / "epreuves.json"
ok("epreuves.json écrit", fichier.exists())
explo = _json.loads(fichier.read_text(encoding="utf-8"))   # doit être du JSON valide
ok("mode relevé : course par équipes (1), grille 1 joueur + 11 motojets",
   explo["modes"][0]["mode"] == 1 and explo["modes"][0]["grille"] == [{"type": 4, "nombre": 1}, {"type": 2, "nombre": 11}])
ep = explo["epreuves"][0]
ok("épreuve : circuit, tours, mode, classement en ligne lié",
   ep["circuit"] == "TRAK_DAL_LOOP_A" and ep["tours"] == 3 and ep["mode"] == 1 and ep["classement"] == "LDB_ARC_TMR_BIKE_X")
ok("« false » gardé tel quel (véhicule non imposé)", ep["vehicule_impose"] is False and ep["sante"] is True)
ok("adversaire relevé SANS lire ses références souples (pilote, build) ni ses réglages de rythme",
   ep["adversaires"] == [{"pilote": None, "type": 2, "build": None, "agressivite": "Agressif",
                          "rythme_par_mode": []}])
ok("liste du jeu : modes et planètes de la course rapide, ensembles",
   explo["listes"][0]["modes_course_rapide"] == ["GMV_TeamRace_Bikes"]
   and explo["listes"][0]["ensembles"] == [{"nom": "Arcade", "epreuves": 1}]
   and explo["listes"][0]["planetes_course_rapide"] == [] and explo["listes"][0]["nb_planetes_course_rapide"] == 1)
ok("miette effacée : exploration finie sans plantage", not (tmp / "echange" / "exploration-etape.txt").exists())
ok("fonctions : LaunchCustomRace trouvée", explo["fonctions"]["LaunchCustomRace"] is True)
ok("pilotes, pilotes IA, parcours : sections présentes (vides ici)",
   explo["pilotes"] == [] and explo["pilotes_ia"] == [] and explo["parcours_multi"] == [])
avant = fichier.stat().st_mtime_ns
boucle()
ok("une seule exploration par session", fichier.stat().st_mtime_ns == avant)

print("16b. Exploration des pilotes : styles (capacités, traits, build), builds d'IA, modes multi")
lua.execute("""
local function objet(nom, chemin, classe, champs)
    local o = champs or {}
    function o:IsValid() return true end
    function o:GetFName() return {ToString = function() return nom end} end
    function o:GetFullName() return classe .. " " .. chemin end
    function o:GetClass() return {GetFName = function() return {ToString = function() return classe end} end} end
    return o
end
local function texte(s) return {ToString = function() return s end} end
local function paires(liste)   -- TMap : ForEach(clé, valeur)
    local t = {}
    function t:ForEach(f) for _, p in ipairs(liste) do f({get = function() return p[1] end}, {get = function() return p[2] end}) end end
    return t
end
local trait = objet("TRAIT_Star_Drift", "/Game/Traits/TRAIT_Star_Drift.TRAIT_Star_Drift", "CharacterTrait",
                    {PlayerFacingName = texte("Dérapage maîtrisé"), PlayerFacingDescription = texte("Dérive {perc} plus longue."),
                     DescriptionPercentParameters = paires({{"perc", 15}}), DescriptionIntParameters = paires({})})
style_star = objet("STYLE_Star_InstantAction", "/Game/Styles/STYLE_Star_IA.STYLE_Star_IA", "RacerStyle",
                   {PlayerFacingName = texte("Virtuose"), PlayerFacingDescription = texte("Pilote technique"), Rank = 1,
                    StandardAbilities = tableau({texte("/Game/Ab/BP_Ability_Shield.BP_Ability_Shield_C")}),
                    Traits = tableau({{get = function() return trait end}}),
                    BuildUpgradePriority = tableau({{UpgradeSlotDistribution = tableau({{Slot = 0, StatDistribution = 0.5},
                                                                                        {Slot = 3, StatDistribution = 0.5}})}}),
                    VehicleBuildOverride = texte("/Game/Builds/VBD_Star.VBD_Star")})
local star = objet("DA_Racer_Star", "/Game/Racers/DA_Racer_Star.DA_Racer_Star", "RacerDef",
                   {CharacterName = texte("Lyren Shok"), PreferredVehicleType = 2, CampaignRacerStyle = style_star,
                    PvpRacerStyles = paires({{5, style_star}})})
local capacite = objet("BP_Ability_Shield_C", "/Game/Ab/BP_Ability_Shield.BP_Ability_Shield_C", "BlueprintGeneratedClass")
local affixe = objet("AFX_Shield_I", "/Game/Afx/AFX_Shield_I.AFX_Shield_I", "AffixPassiveConfig")
local build_voiture = objet("VBD_AI_Star_Car", "/Game/Builds/VBD_AI_Star_Car.VBD_AI_Star_Car", "VehicleBuildDef",
                            {SlotToUpgradeLevelMap = paires({{0, 5}, {3, 9}}), AbilitySlots = tableau({capacite}),
                             Affixes = tableau({affixe}), CrashAbility = capacite, RamjetInstalled = true, BasicBoostType = 1})
local setup = objet("PRS_Star", "/Game/Pvp/PRS_Star.PRS_Star", "PvpRacerSetup",
                    {Character = star, Build = {CarBuild = build_voiture}})
local parcours = objet("PRD_InstantAction", "/Game/Pvp/PRD_IA.PRD_IA", "PvpRunDef",
                       {PlayerFacingName = texte("Action immédiate"), ForceVehicleTypeOnAllPlayers = 0,
                        AvailableRacerStyles = tableau({style_star})})
local precedent = FindAllOf
FindAllOf = function(c)
    if c == "RacerDef" then return {star} end
    if c == "PvpRacerSetup" then return {setup} end
    if c == "PvpRunDef" then return {parcours} end
    return precedent(c)
end
""")
(tmp / "echange" / "commande.txt").write_text("action=catalogue\n", encoding="utf-8")
lua.execute("epreuves_a_refaire = true")
# nouvelle session simulée : on recharge le mod pour refaire l'exploration
assert src.count("Exploration_Souples          = false,") == 1
lua.execute(src.replace("Journal(Traduire(\"charge\"", "local _ = (Traduire(\"charge\"")
               .replace("Exploration_Souples          = false,", "Exploration_Souples          = true,"))
boucle(); boucle()
explo = _json.loads(fichier.read_text(encoding="utf-8"))
p = explo["pilotes"][0]
st = p["style_campagne"]
ok("pilote : nom affiché, véhicule préféré", p["affiche"] == "Lyren Shok" and p["vehicule_prefere"] == 2)
ok("style : capacités, build imposé, priorités des stats",
   st["capacites"] == ["/Game/Ab/BP_Ability_Shield.BP_Ability_Shield_C"] and st["build_impose"] == "/Game/Builds/VBD_Star.VBD_Star"
   and st["priorites_stats"] == [[{"emplacement": 0, "part": 0.5}, {"emplacement": 3, "part": 0.5}]])
ok("trait : nom, description et valeurs", st["traits"] == [{"chemin": "/Game/Traits/TRAIT_Star_Drift.TRAIT_Star_Drift",
   "affiche": "Dérapage maîtrisé", "description": "Dérive {perc} plus longue.", "affiche_src": None,
   "description_src": None, "perc": {"perc": 15}, "int": {}}])
ok("style par mode multi (5 = Action immédiate)", p["styles_multi"][0]["mode"] == 5
   and p["styles_multi"][0]["style"]["nom"] == "STYLE_Star_InstantAction")
b = explo["pilotes_ia"][0]["builds"]
ok("build d'IA par véhicule : niveaux, capacités, affixes, crash (chemins)",
   b["voiture"]["niveaux"] == {"0": 5, "3": 9} and b["voiture"]["affixes"] == ["/Game/Afx/AFX_Shield_I.AFX_Shield_I"]
   and b["voiture"]["crash"] == "/Game/Ab/BP_Ability_Shield.BP_Ability_Shield_C" and b["motojet"] is None)
ok("mode multi : styles disponibles", explo["parcours_multi"][0]["styles"] == ["STYLE_Star_InstantAction"])

print("16d. Plantage pendant une étape : la session suivante la saute (miettes)")
miette = tmp / "echange" / "exploration-etape.txt"
miette.write_text("listes", encoding="utf-8")        # comme si le jeu avait planté pendant « listes »
lua.execute(src.replace("Journal(Traduire(\"charge\"", "local _ = (Traduire(\"charge\""))
boucle(); boucle()
explo = _json.loads(fichier.read_text(encoding="utf-8"))
ok("étape « listes » sautée, les autres faites", explo["etapes_sautees"] == ["listes"] and explo["listes"] == []
   and len(explo["modes"]) == 1 and len(explo["pilotes"]) == 1)
ok("notée dans exploration-interdites.txt", (tmp / "echange" / "exploration-interdites.txt").read_text(encoding="utf-8").split() == ["listes"])
journal = " ".join(str(x) for x in L.journal.values())
ok("expliqué dans le journal", "l'étape « listes » a fait planter le jeu la dernière fois" in journal)
ok("miette effacée à la fin", not miette.exists())
lua.execute(src.replace("Journal(Traduire(\"charge\"", "local _ = (Traduire(\"charge\""))
boucle(); boucle()
ok("session suivante : toujours sautée", _json.loads(fichier.read_text(encoding="utf-8"))["etapes_sautees"] == ["listes"])

print("16c. En course : style mis par le jeu sur le PlayerState du joueur (noté une fois par circuit)")
L.carte = "L_Husky_LOOP_A"
boucle(); boucle()
lua.execute("etat.RacerStyle = style_star")
L.carte = "L_Mastiff_LOOP_A"
boucle()
journal = " ".join(str(x) for x in L.journal.values())
ok("sans style : « aucun »", "style du joueur sur L_Husky_LOOP_A = aucun" in journal)
ok("avec style : son nom", "style du joueur sur L_Mastiff_LOOP_A = STYLE_Star_InstantAction" in journal)
ok("noté une seule fois par circuit", journal.count("style du joueur sur L_Husky_LOOP_A") == 1)
journal = " ".join(str(x) for x in L.journal.values())
ok("résumé dans le journal", "exploration : 1 modes, 1 listes, 1 épreuves (mode 1 : 1), dont 1 avec adversaires" in journal)

print("17. Noms du jeu dans la langue de la fenêtre : jeu passé en anglais le temps de lire, puis remis")
lua.execute("""
langue_du_jeu = "fr-FR"
function BIB_LANGUES:GetCurrentLanguage() return {ToString = function() return langue_du_jeu end} end
appels_langue = {}
function BIB_LANGUES:SetCurrentLanguage(code, enregistrer)
    table.insert(appels_langue, code .. (enregistrer and " (enregistré !)" or ""))
    langue_du_jeu = code
end
local function texte_selon_langue(fr, en)
    return {ToString = function() return langue_du_jeu:sub(1, 2) == "en" and en or fr end}
end
circuit_trad = {PlayerFacingName = texte_selon_langue("Champs de guerre", "Battlefield")}
function circuit_trad:IsValid() return true end
function circuit_trad:GetFName() return {ToString = function() return "TRAK_MAS_LOOP_A" end} end
function circuit_trad:GetFullName() return "TrackDef /Game/T/TRAK_MAS_LOOP_A.TRAK_MAS_LOOP_A" end
local avant = FindAllOf
FindAllOf = function(c)
    if c == "TrackDef" then return {circuit_trad} end
    return avant(c)
end
""")
L.carte = "L_FrontEnd"
(tmp / "echange" / "langue.txt").write_text("fr", encoding="utf-8")
boucle(); L.avancer(5000)
ok("fenêtre dans la langue du jeu : rien n'est changé", list(L.appels_langue.values()) == []
   and not (tmp / "echange" / "catalogue-en.json").exists())
(tmp / "echange" / "langue.txt").write_text("en", encoding="utf-8")
boucle()
ok("fenêtre en anglais : le jeu passe en anglais, SANS enregistrer", list(L.appels_langue.values()) == ["en"])
L.avancer(1000)
trad = _json.loads((tmp / "echange" / "catalogue-en.json").read_text(encoding="utf-8"))
ok("catalogue-en.json : le circuit en anglais", trad["langue"] == "en"
   and trad["objets"]["/Game/T/TRAK_MAS_LOOP_A.TRAK_MAS_LOOP_A"]["affiche"] == "Battlefield")
ok("langue du jeu remise à « fr-FR »", list(L.appels_langue.values()) == ["en", "fr-FR"] and L.langue_du_jeu == "fr-FR")
ok("miette effacée", not (tmp / "echange" / "exploration-etape.txt").exists())
boucle(); L.avancer(5000)
ok("une seule fois par langue et par session", list(L.appels_langue.values()) == ["en", "fr-FR"])
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : témoins changés, objets écrits, langue remise",
   "traduction « en » : 1 noms témoins changés après 1 essai(s)" in journal and "remise à « fr-FR »" in journal)
(tmp / "echange" / "langue.txt").write_text("fr", encoding="utf-8")
boucle()

erreurs = [str(x) for x in L.journal.values() if "ERREUR" in str(x) or "ERROR" in str(x)]
ok("aucune erreur dans le journal", not erreurs)
print("\nTOUS LES TESTS SONT PASSÉS")
