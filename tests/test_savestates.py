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
ExecuteWithDelay = function(ms, fn) table.insert(attente, {t = maintenant + ms, fn = fn}) end
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
LoopAsync = function(ms, f) boucles[ms] = f end
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

def touche(nom, mods=(), aussi_sans_modificateur=False):
    """Simule un appui. Si `aussi_sans_modificateur`, UE4SS déclenche AUSSI la liaison sans modificateur."""
    for l in L.liaisons.values():
        lm = sorted(l.mods.values())
        if l.touche == nom and (lm == sorted(mods) or (aussi_sans_modificateur and lm == [])):
            l.fn()
    L.avancer(300)

def derniers(n=1):
    return [str(x) for x in list(L.journal.values())[-n:]]

def ok(nom, cond):
    print(("  [OK]    " if cond else "  [ÉCHEC] ") + nom)
    if not cond:
        print("\n".join(str(x) for x in L.journal.values())); sys.exit(1)

print("Liaisons enregistrées :", sorted((l.touche, tuple(l.mods.values())) for l in L.liaisons.values()))
etat_txt = lambda: (tmp / "echange" / "etat.txt").read_text(encoding="utf-8")

print("1. F7 seul → emplacement 1")
touche("F7")
ok("emplacement 1 sauvegardé, 100 mph ≈ 161 km/h", "emplacement 1 sauvegardé (161 km/h)" in etat_txt())
ok("son de checkpoint joué", list(L.sons.values())[-1] == "PlayPrecisionCheckpointSfx")

print("2. Maj+F7 alors que UE4SS envoie aussi F7 seul → seulement l'emplacement 2")
L.pion.pos.X = 5000
touche("F7", ["SHIFT"], aussi_sans_modificateur=True)
ok("emplacement 2 sauvegardé", "emplacement 2 sauvegardé" in etat_txt())
journal = " ".join(str(x) for x in L.journal.values())
ok("l'emplacement 1 n'a PAS été écrasé", journal.count("emplacement 1 sauvegardé") == 1)

print("3. Ctrl+F8 sur un emplacement vide → erreur et son d'erreur")
touche("F8", ["CONTROL"])
ok("message emplacement vide", "emplacement 3 vide" in etat_txt())
ok("son d'erreur", list(L.sons.values())[-1] == "PlayHitmarkerSfx")

print("4. Maj+F8 → retour DIRECT à l'emplacement 2 (téléportation + vitesse rendue)")
lua.execute("pion.vit = {X = 0, Y = 0, Z = 0}")       # on roule au ralenti avant le retour
touche("F8", ["SHIFT"], aussi_sans_modificateur=True)
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
ok("temps.csv : colonne Save state = oui", csv.splitlines()[0].endswith(";Save state") and csv.splitlines()[1].endswith('"oui"'))

print("7. Course suivante (sans retour F8) : plus marquée save state")
L.comp.bHasFinishedEvent = False; L.comp.PreviousLapTime = -1
boucle()
L.comp.PreviousLapTime = 71.0; L.comp.bHasFinishedEvent = True; L.comp.EventFinishTime = 71.0
boucle()
ok("2e temps sans mention save state", csv != (tmp / "temps" / "temps.csv").read_text(encoding="utf-8")
   and (tmp / "temps" / "temps.csv").read_text(encoding="utf-8").splitlines()[2].endswith('"non"'))

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
post = {}; function post:IsValid() return true end
function post:Server_UpdateState(s, e)
    table.insert(appels_boost, "post " .. s .. " " .. e); etat_vehicule.AfterburnerEnergy = e
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
   appels_boost() == ["mode 4", "chaleur 0.4 0.1", "ramjet 3", "post 0 0.8"])
ok("énergie et chaleur de nouveau à 0.8 / 0.4", L.etat_vehicule.AfterburnerEnergy == 0.8 and L.etat_vehicule.RamjetHeat == 0.4)
L.avancer(700)   # les relectures partent de l'appui réel (après le garde-fou de 80 ms)
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : chaque étape notée", "boost rendu : mode 4 ok, chaleur ramjet ok, état ramjet 3 ok, postcombustion ok, écriture directe ok" in journal)
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
ok("postcombustion rendue 2 fois (juste après, puis +50 ms)", sum(a.startswith("post ") for a in appels_boost()) == 2)

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
    return t
end
function classe(nom, ameliorations, estCapacite, estCrash)
    local cdo = {PlayerFacingName = {ToString = function() return "Nom " .. nom end, source = "Name " .. nom},
                 AbilityLevel = 1, CanUpgradeTo = tableau(ameliorations or {})}
    function cdo:IsA(c) return (c == CLASSE_CAPACITE and estCapacite) or (c == CLASSE_CRASH and estCrash) end
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
ok("texte d'origine exporté à côté du texte du jeu (affiche / affiche_src)",
   any(c.get("affiche") == "Nom BP_Ability_Boost_C" and c.get("affiche_src") == "Name BP_Ability_Boost_C"
       for c in capacites))
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

erreurs = [str(x) for x in L.journal.values() if "ERREUR" in str(x) or "ERROR" in str(x)]
ok("aucune erreur dans le journal", not erreurs)
print("\nTOUS LES TESTS SONT PASSÉS")
