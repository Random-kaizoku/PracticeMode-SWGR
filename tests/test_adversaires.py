"""Test v0.9.6 : adversaires IA (LaunchCustomRace), buffs du pilote, styles.json,
place à l'arrivée et build complet dans temps.csv. Vrai main.lua dans Lua 5.4,
faux jeu (stubs UE4SS)."""
import csv
import json
import re
import sys
import tempfile
from pathlib import Path

from lupa import lua54

RACINE = Path(__file__).resolve().parent.parent
src = (RACINE / "installation" / "ue4ss" / "Mods" / "PracticeMode" / "Scripts" / "main.lua").read_text(encoding="utf-8")
tmp = Path(tempfile.mkdtemp())
(tmp / "echange").mkdir()
(tmp / "temps").mkdir()
src = src.replace('local DOSSIER_PRACTICEMODE = "ECRIT-PAR-LE-LAUNCHER/"', f'local DOSSIER_PRACTICEMODE = "{tmp.as_posix()}/"')
VDF = tmp / "loginusers.vdf"
VDF.write_text('"users"\n{\n"1"\n{\n"WantsOfflineMode"\t\t"1"\n"Timestamp"\t\t"200"\n}\n}\n', encoding="utf-8")
src = src.replace('local FICHIER_STEAM = "ECRIT-PAR-LE-LAUNCHER"', f'local FICHIER_STEAM = "{VDF.as_posix()}"')
assert "ECRIT-PAR-LE-LAUNCHER" not in src
(tmp / "echange" / "pare-feu.txt").write_text("actif", encoding="utf-8-sig")

# Table des styles de test à la place de celle relevée dans le jeu
STYLE = "/Game/Styles/STYLE_Star_IA.STYLE_Star_IA"
TRAIT = "/Game/Traits/TRT_Drift.TRT_Drift"
BUILD_STYLE = "/Game/Builds/VBD_PvP_IA_Star.VBD_PvP_IA_Star"
CAPACITE = "/Game/Ab/BP_Ability_Shield.BP_Ability_Shield_C"
table_test = (f'local STYLES_PILOTES = {{ ["{STYLE}"] = {{ build = "{BUILD_STYLE}", '
              f'capacites = {{ "{CAPACITE}" }}, traits = {{ "{TRAIT}" }} }} }}')
src, n = re.subn(r"local STYLES_PILOTES = \{.*?\n\}\n-- FIN STYLES_PILOTES", table_test + "\n-- FIN STYLES_PILOTES",
                 src, flags=re.S)
assert n == 1

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
-- Horloge qui avance de 10 s à chaque lecture (les nouveaux essais du catalogue ne se font pas attendre)
do local h = 0; os.clock = function() h = h + 10; return h end end
boucles = {}
LoopInGameThreadWithDelay = function(ms, f) boucles[ms] = f end
LoopAsync = function(ms, f) anciens_appels = anciens_appels + 1; boucles[ms] = f end
FName = function(s) return {nom = s} end

function texte(s) return {ToString = function() return s end} end
local adresses = 0
function objet(nom, chemin, classe, champs)
    local o = champs or {}
    adresses = adresses + 1
    local adresse = adresses
    function o:IsValid() return true end
    function o:GetAddress() return adresse end
    function o:GetFName() return {ToString = function() return nom end} end
    function o:GetFullName() return classe .. " " .. chemin end
    function o:GetClass() return {GetFName = function() return {ToString = function() return classe end} end} end
    return o
end
-- TArray d'UE4SS : t[i], #t, t[#t + 1] = x, ForEach, Empty
function tableau(liste)
    local t = {elements = liste or {}}
    local mt = {}
    mt.__index = function(self, k)
        if type(k) == "number" then return rawget(self, "elements")[k] end
        return mt[k]
    end
    mt.__newindex = function(self, k, v)
        if type(k) == "number" then rawget(self, "elements")[k] = v else rawset(self, k, v) end
    end
    mt.__len = function(self) return #rawget(self, "elements") end
    function mt.ForEach(self, f)
        for i, e in ipairs(rawget(self, "elements")) do
            f(i, {get = function() return e end, set = function(_, v) rawget(self, "elements")[i] = v end})
        end
    end
    function mt.Empty(self) rawset(self, "elements", {}) end
    return setmetatable(t, mt)
end
-- TMap : Add, ForEach
function carte(paires)
    local t = {p = paires or {}}
    function t:Add(k, v) for _, e in ipairs(self.p) do if e[1] == k then e[2] = v return end end table.insert(self.p, {k, v}) end
    function t:ForEach(f) for _, e in ipairs(self.p) do f({get = function() return e[1] end}, {get = function() return e[2] end}) end end
    return t
end

-- Le monde et le joueur
carte_actuelle = "L_FrontEnd"
monde = {GameState = {}}
function monde.GameState:GetServerWorldTimeSeconds() return 1000.0 end
function monde:GetFName() return {ToString = function() return carte_actuelle end} end
function monde:IsValid() return true end
pion = objet("Pion", "/Temp/Pion", "VehiclePawn", {})
comp = {bHasFinishedEvent = false, PreviousLapTime = -1, EventFinishTime = -1, BestLapTime = -1, EventPosition = 0,
        CurrentSectorNumber = 255, SectorStartServerTime = 0}
function comp:IsValid() return true end
function nouvel_etat()
    return objet("GfnPlayerState", "/Temp/PS", "GfnPlayerState", {RaceEventComponent = comp,
        PassiveManagerComponent = objet("PMC", "/Temp/PMC", "PassiveManagerComponent",
                                        {PassivesToAdd = tableau({}), PassiveList = tableau({"passif du jeu"})})})
end
ctrl = {PlayerState = nil}; function ctrl:IsValid() return true end
function ctrl:IsInputKeyDown() return false end
function ctrl:GetWorld() return monde end
package.preload["UEHelpers"] = function() return {
    GetPlayerController = function() return ctrl end,
    GetPlayer = function() return ctrl.PlayerState and pion or nil end,
    GetWorld = function() return monde end,
    GetGameplayStatics = function() return {IsGamePaused = function() return false end} end } end

-- Les objets du jeu
local tag = function(s) return {TagName = texte(s)} end
archetype = objet("VA_Bike", "/Game/Griffin/Vehicles/Bikes/VA_Bike.VA_Bike", "VehicleArchetype", {})
modele = objet("EVT_TT", "/Game/Griffin/Gameplay/Arcade/Events/TimeTrial/EVT_ARC_TT_BIKE_DAL_P2P_SHORT_05.EVT_ARC_TT_BIKE_DAL_P2P_SHORT_05",
               "ArcadeEventDef", {VehicleTypeTag = tag("Vehicle.Standard.Bike"), LapCount = 3,
                                  EventMode = objet("TimeTrialConfig", "/Temp/TTC", "TimeTrialConfig", {bUsePlayerHealth = true})})
build_tt = objet("VBD_TT", "/Game/Griffin/Gameplay/Campaign/Builds/Arcade/VBD_ARC_TT_BIKE_DAL_P2P_SHORT_05.VBD_ARC_TT_BIKE_DAL_P2P_SHORT_05",
                 "VehicleBuildDef", {SlotToUpgradeLevelMap = carte({}), AbilitySlots = tableau({}), Affixes = tableau({}),
                                     PlaneOnlyAffixes = tableau({}), UseHealth = true})
build_base = objet("VBD_Bike_Base", "/Game/Griffin/Gameplay/Campaign/Builds/VBD_Bike_Base.VBD_Bike_Base", "VehicleBuildDef", {})
piste = objet("TRAK_DAL_LOOP_A", "/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", "TrackDef",
              {VehicleTypeTag = tag("Vehicle.Standard"), DefaultLapCount = 3})
gmv_race = objet("GMV_Race", "/Game/Griffin/Gameplay/Campaign/GameModes/GMV_Race.GMV_Race", "GameModeVariantDef",
                 {GridMakeup = {Entries = tableau({{EntryType = 4, NumEntrants = 5}})}})
liste_pilotes = objet("DA_CharacterList", "/Game/Griffin/Narrative/CharacterDefs/DA_CharacterList.DA_CharacterList", "CharacterList", {})
capacite = objet("BP_Ability_Shield_C", "/Game/Ab/BP_Ability_Shield.BP_Ability_Shield_C", "BlueprintGeneratedClass", {})
trait = objet("TRT_Drift", "/Game/Traits/TRT_Drift.TRT_Drift", "CharacterTrait",
              {PlayerFacingName = texte("Dérapage maîtrisé"), PlayerFacingDescription = texte("Dérive {perc} plus longue."),
               DescriptionPercentParameters = carte({{"perc", 15}}), DescriptionIntParameters = carte({})})
build_style = objet("VBD_PvP_IA_Star", "/Game/Builds/VBD_PvP_IA_Star.VBD_PvP_IA_Star", "VehicleBuildDef",
                    {SlotToUpgradeLevelMap = carte({{0, 4}, {1, 6}}), AbilitySlots = tableau({capacite}), Affixes = tableau({}),
                     CrashAbility = nil, RamjetInstalled = true, BasicBoostType = 1, CriticalMalfunctions = false})
style = objet("STYLE_Star_IA", "/Game/Styles/STYLE_Star_IA.STYLE_Star_IA", "RacerStyle",
              {PlayerFacingName = texte("Virtuose"), PlayerFacingDescription = texte("Pilote technique"), Rank = 1})
star = objet("DA_Racer_Star", "/Game/Racers/DA_Racer_Star.DA_Racer_Star", "RacerDef",
             {CharacterName = texte("Lyren Shok"), CampaignRacerStyle = style, PvpRacerStyles = carte({{5, style}})})

local par_chemin = {}
for _, o in ipairs({archetype, modele, build_tt, build_base, piste, gmv_race, liste_pilotes, capacite, trait,
                    build_style, style, star}) do
    par_chemin[o:GetFullName():match("^%S+%s+(.+)$")] = o
end
StaticFindObject = function(chemin) return par_chemin[chemin] end

-- Menu principal : ses fonctions de lancement
appels_ia, appels_rapides = {}, {}
mode_menu = objet("FrontEndGameMode", "/Temp/FEGM", "FrontEndGameMode", {})
function mode_menu:LaunchCustomRace(...) table.insert(appels_ia, table.pack(...)) end
function mode_menu:LaunchQuickRace(...) table.insert(appels_rapides, table.pack(...)) end
arcade = objet("ArcadeSubsystem", "/Temp/Arcade", "ArcadeSubsystem", {})
voyages = {}
function arcade:TravelToEvent(e) table.insert(voyages, e) end
FindFirstOf = function(c)
    if c == "FrontEndGameMode" and carte_actuelle == "L_FrontEnd" then return mode_menu end
    if c == "ArcadeSubsystem" then return arcade end
    return nil
end
FindAllOf = function(c)
    if c == "TrackDef" then return {piste} end
    if c == "RacerDef" then return {star} end
    if c == "RacerStyle" then return {style} end
    return nil
end
""")
lua.execute(src)
L = lua.globals()
echecs = []


def ok(nom, cond):
    print(("  [OK]    " if cond else "  [ÉCHEC] ") + nom)
    if not cond:
        echecs.append(nom)


def boucle():
    L.boucles[500]()


def etat_txt():
    try:
        return (tmp / "echange" / "etat.txt").read_text(encoding="utf-8")
    except OSError:
        return ""


def touche(nom):
    for l in L.liaisons.values():
        if l.touche == nom and len(list(l.mods.values())) == 0:
            l.fn()
    L.boucles[20]()      # la boucle des touches (fil du jeu) fait l'action


def commande(**cles):
    (tmp / "echange" / "commande.txt").write_text("\n".join(f"{k}={v}" for k, v in cles.items()) + "\n",
                                                  encoding="utf-8")


print("1. Au menu : catalogue, exploration, puis styles des pilotes (styles.json)")
for _ in range(8):
    boucle()
fichier = tmp / "echange" / "styles.json"
if not fichier.exists():
    print("\n".join(str(x) for x in L.journal.values()))
ok("styles.json écrit", fichier.exists())
styles = json.loads(fichier.read_text(encoding="utf-8"))
ok("pilote → ses styles (mode 5 et campagne)",
   styles["pilotes"] == [{"chemin": "/Game/Racers/DA_Racer_Star.DA_Racer_Star", "styles": {"5": STYLE, "campagne": STYLE}}])
s = styles["styles"][0]
ok("style : nom, description, capacités, traits",
   s["affiche"] == "Virtuose" and s["description"] == "Pilote technique" and s["capacites"] == [CAPACITE]
   and s["traits"] == [TRAIT])
ok("style : son build (niveaux, capacités, boost, ramjet)",
   s["build"]["niveaux"] == {"0": 4, "1": 6} and s["build"]["capacites"] == [CAPACITE]
   and s["build"]["boost"] == 1 and s["build"]["ramjet"] is True and s["build"]["pannes"] is False)
ok("trait : nom, description, valeurs", styles["traits"] == [{"chemin": TRAIT, "nom": "TRT_Drift",
   "affiche": "Dérapage maîtrisé", "description": "Dérive {perc} plus longue.", "perc": {"perc": 15}, "int": {}}])
ok("miette effacée", not (tmp / "echange" / "exploration-etape.txt").exists())

print("2. Course avec 7 adversaires, 5 tours, depuis le menu")
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=5, adversaires=7,
         pilote="/Game/Racers/DA_Racer_Star.DA_Racer_Star", niveaux="4,6,0,0,0,0", capacites=CAPACITE,
         crashs_illimites=1, style=STYLE, traits=TRAIT, nom_circuit="Dunes [TRAK_DAL_LOOP_A]", nom_vehicule="Motojet")
boucle()
appels = list(L.appels_ia.values())
ok("LaunchCustomRace appelée une fois, LaunchQuickRace jamais", len(appels) == 1 and len(list(L.appels_rapides.values())) == 0)
ok("paramètres : archétype, mode GMV_Race, circuit, conditions vides, build rempli, build debug vide",
   lua.eval("""(function() local a = appels_ia[1]
       return a ~= nil and a.n == 6 and a[1] == archetype and a[2] == gmv_race and a[3] == piste
          and a[4].TagName.nom == "None" and a[5] == build_tt and a[6] == nil end)()"""))
ok("grille : joueur + 7 = 8", L.gmv_race.GridMakeup.Entries[1].NumEntrants == 8)
ok("tours du circuit : 5", L.piste.DefaultLapCount == 5)
ok("build rempli (niveaux, crashs illimités)", L.build_tt.UseHealth is False)
ok("pilote choisi", lua.eval("liste_pilotes.Player == star"))
ok("message de lancement avec le nombre d'adversaires", "7 adversaire(s)" in etat_txt())

print("3. En course : relance avec IA refusée (menu seulement), F6 explique")
L.carte_actuelle = "L_Dalmatian_LOOP_A"
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=5, adversaires=3)
boucle()
ok("message « depuis le menu principal »", "menu principal" in etat_txt() and len(list(L.appels_ia.values())) == 1)
touche("F6")
ok("F6 : utiliser le menu pause du jeu", "menu pause" in etat_txt())

print("4. Buffs du pilote : ajoutés une fois par course chargée")
lua.execute("ctrl.PlayerState = nouvel_etat()")
boucle()
pmc = L.ctrl.PlayerState.PassiveManagerComponent
ok("trait mis dans la file PassivesToAdd",
   lua.eval("#ctrl.PlayerState.PassiveManagerComponent.PassivesToAdd == 1 "
            "and ctrl.PlayerState.PassiveManagerComponent.PassivesToAdd[1] == trait"))
ok("message « buffs du pilote : 1 trait »", "1 trait(s)" in etat_txt() and "Dérapage maîtrisé" in etat_txt())
ok("miette « buffs » posée", (tmp / "echange" / "exploration-etape.txt").read_text(encoding="utf-8") == "buffs")
L.avancer(2500)
ok("2 s plus tard : miette retirée, contrôle noté",
   not (tmp / "echange" / "exploration-etape.txt").exists()
   and any("buffs du pilote actifs" in str(x) for x in L.journal.values()))
boucle(); boucle()
NB_BUFFS = "#ctrl.PlayerState.PassiveManagerComponent.PassivesToAdd"
ok("pas ajoutés deux fois", lua.eval(NB_BUFFS) == 1)
lua.execute("ctrl.PlayerState = nouvel_etat()")   # restart : nouveau PlayerState
boucle()
ok("course rechargée : ajoutés à nouveau", lua.eval(NB_BUFFS) == 1)

print("5. Arrivée : place et build complet notés")
L.comp.EventPosition = 2
L.comp.PreviousLapTime = 61.0
L.comp.EventFinishTime = 305.5
L.comp.BestLapTime = 60.1
L.comp.bHasFinishedEvent = True
boucle()
lignes = list(csv.DictReader((tmp / "temps" / "temps.csv").read_text(encoding="utf-8").splitlines(), delimiter=";"))
detail = dict(p.split("=", 1) for p in lignes[0]["Détail du build"].split(";"))
ok("détail : adversaires, place, niveaux, style, traits",
   detail.get("adversaires") == "7" and detail.get("position") == "2" and detail.get("niveaux") == "4,6,0,0,0,0"
   and detail.get("style") == STYLE and detail.get("traits") == TRAIT)
ok("temps.txt : « place 2/8 »", "place 2/8" in (tmp / "temps" / "temps.txt").read_text(encoding="utf-8"))

print("6. Retour au menu, contre-la-montre : tours du circuit remis à l'origine")
L.carte_actuelle = "L_FrontEnd"
lua.execute("ctrl.PlayerState = nil")
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=2, adversaires=0)
boucle()
ok("LaunchQuickRace (contre-la-montre) appelée", len(list(L.appels_rapides.values())) == 1)
ok("tours d'origine du circuit remis (3)", L.piste.DefaultLapCount == 3)
ok("épreuve modèle : 2 tours", L.modele.LapCount == 2)

print("7. Plantage pendant les buffs : la session suivante ne les ajoute plus")
(tmp / "echange" / "exploration-etape.txt").write_text("buffs", encoding="utf-8")
L.comp.bHasFinishedEvent = False   # (course pas encore finie : pas de temps noté pendant ce test)
lua.execute(src.replace('Journal(Traduire("charge"', 'local _ = (Traduire("charge"'))
L = lua.globals()
boucle(); boucle(); boucle()          # au menu : la miette est lue
L.carte_actuelle = "L_Dalmatian_LOOP_A"
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=2, traits=TRAIT)
boucle()                              # (lancement refusé hors menu ? non : contre-la-montre en course = voyage Arcade)
lua.execute("ctrl.PlayerState = nouvel_etat()")
boucle()
ok("buffs non ajoutés, et c'est expliqué", lua.eval(NB_BUFFS) == 0 and "désactivés" in etat_txt())

print("8. Build et trait du style PAS en mémoire (cas réel du 11/10) : chargés peu à peu, une miette par objet")
# Le 11/10 à 21:10 (LoadAsset coupé) : 0 build sur 21 et 0 trait sur 50 en
# mémoire au menu, styles et buffs ne marchaient pas. v0.9.9 : LoadAsset
# rallumé, chaque objet avec sa propre miette « charger <chemin> ».
# Le faux LoadAsset note, à chaque appel, la miette posée à ce moment-là.
(tmp / "echange" / "exploration-interdites.txt").write_text("pilotes_ia\n", encoding="utf-8")
(tmp / "echange" / "styles.json").unlink(missing_ok=True)
L.DOSSIER_ECHANGE_TEST = (tmp / "echange").as_posix() + "/"
lua.execute(f"""
absents = {{["{TRAIT}"] = true, ["{BUILD_STYLE}"] = true}}
charges = {{}}
local trouver = StaticFindObject
StaticFindObject = function(c) if absents[c] then return nil end return trouver(c) end
LoadAsset = function(chemin)
    local f = io.open(DOSSIER_ECHANGE_TEST .. "exploration-etape.txt", "r")
    table.insert(charges, {{chemin = chemin, miette = f and f:read("a") or ""}})
    if f then f:close() end
    absents[chemin] = nil   -- « chargé »
end
""")
NB_CHARGES = "#charges"
SANS_MESSAGE = src.replace('Journal(Traduire("charge"', 'local _ = (Traduire("charge"')
fichier = tmp / "echange" / "styles.json"


def nouvelle_session_au_menu(source, passages=10):
    global L
    L.carte_actuelle = "L_FrontEnd"
    lua.execute("ctrl.PlayerState = nil")
    lua.execute(source)
    L = lua.globals()
    for _ in range(passages):
        boucle()
    return json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else {"styles": [{}], "traits": None}


def course_avec_buffs():
    """Le jeu a déchargé le trait en changeant de carte ; course avec ce buff."""
    lua.execute(f'absents["{TRAIT}"] = true')
    L.carte_actuelle = "L_Dalmatian_LOOP_A"
    commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=2, traits=TRAIT)
    boucle()
    lua.execute("ctrl.PlayerState = nouvel_etat()")
    boucle()


styles = nouvelle_session_au_menu(SANS_MESSAGE)
s = styles["styles"][0]
ok("styles.json écrit", fichier.exists())
ok("style : build lu (chargé), son chemin, traits et capacités",
   s.get("build") is not None and s.get("build_chemin") == BUILD_STYLE and s.get("traits") == [TRAIT]
   and s.get("capacites") == [CAPACITE])
ok("nom du trait lu (chargé)", len(styles["traits"] or []) == 1 and styles["traits"][0].get("chemin") == TRAIT)
charges = sorted((c.chemin, c.miette) for c in L.charges.values())
ok("chaque objet chargé une fois, avec SA miette posée avant",
   charges == sorted([(BUILD_STYLE, "charger " + BUILD_STYLE), (TRAIT, "charger " + TRAIT)]))
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : chargés depuis le disque, en un passage",
   "2 objet(s) chargé(s) depuis le disque (sur 2) en 1 passage(s), 0 introuvable(s), 0 sauté(s)" in journal)
ok("journal : tout est en mémoire ensuite",
   "en mémoire au menu, 1 build(s) sur 1 et 1 trait(s) sur 1 (LoadAsset : oui)" in journal)
ok("aucune miette restée (pas de plantage)", not (tmp / "echange" / "exploration-etape.txt").exists())

course_avec_buffs()
charges = [(c.chemin, c.miette) for c in L.charges.values()]
ok("en course : trait rechargé, avec sa miette", charges[-1] == (TRAIT, "charger " + TRAIT) and len(charges) == 3)
ok("en course : puis ajouté aux buffs", lua.eval(NB_BUFFS) == 1)
ok("en course : la miette « buffs » est remise après le chargement",
   (tmp / "echange" / "exploration-etape.txt").read_text(encoding="utf-8") == "buffs")
L.avancer(2500)
ok("en course : miette retirée après le contrôle des buffs", not (tmp / "echange" / "exploration-etape.txt").exists())

print("8b. Option coupée (CONFIG.ChargementAssets = false) : rien n'est chargé, styles.json quand même")
assert SANS_MESSAGE.count("ChargementAssets    = true,") == 1
lua.execute(f'absents["{TRAIT}"] = true; absents["{BUILD_STYLE}"] = true; charges = {{}}')
fichier.unlink()
styles = nouvelle_session_au_menu(SANS_MESSAGE.replace("ChargementAssets    = true,", "ChargementAssets    = false,"))
s = styles["styles"][0]
ok("styles.json écrit, build absent mais son chemin donné",
   fichier.exists() and s.get("build") is None and s.get("build_chemin") == BUILD_STYLE)
ok("aucun nom de trait (pas en mémoire)", styles["traits"] == [])
ok("LoadAsset jamais appelé au menu", lua.eval(NB_CHARGES) == 0)
course_avec_buffs()
ok("en course : buffs non ajoutés, et c'est expliqué",
   lua.eval(NB_BUFFS) == 0 and "aucun de ses 1 trait(s)" in etat_txt())
ok("en course : LoadAsset jamais appelé", lua.eval(NB_CHARGES) == 0)
ok("en course : miette effacée (ce n'est pas un plantage)", not (tmp / "echange" / "exploration-etape.txt").exists())

print("8c. Le chargement du build a fait planter la session précédente : seul ce build est sauté")
lua.execute(f'absents["{TRAIT}"] = true; absents["{BUILD_STYLE}"] = true; charges = {{}}')
fichier.unlink()
(tmp / "echange" / "exploration-etape.txt").write_text("charger " + BUILD_STYLE, encoding="utf-8")
styles = nouvelle_session_au_menu(SANS_MESSAGE)
s = styles["styles"][0]
charges = [(c.chemin, c.miette) for c in L.charges.values()]
ok("le build n'est plus chargé, le trait si", charges == [(TRAIT, "charger " + TRAIT)])
ok("styles.json : build absent (chemin donné), trait lu",
   s.get("build") is None and s.get("build_chemin") == BUILD_STYLE and len(styles["traits"]) == 1)
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : l'objet sauté et pourquoi",
   "l'étape « charger " + BUILD_STYLE + " » a fait planter le jeu" in journal
   and "1 objet(s) chargé(s) depuis le disque (sur 2) en 1 passage(s), 0 introuvable(s), 1 sauté(s)" in journal)
ok("interdit noté pour les sessions suivantes", "charger " + BUILD_STYLE in
   (tmp / "echange" / "exploration-interdites.txt").read_text(encoding="utf-8"))
course_avec_buffs()
ok("en course : le trait (autorisé) est chargé et ajouté", lua.eval(NB_BUFFS) == 1)
L.avancer(2500)

print("8d. Le jeu décharge les objets juste après leur chargement (ramasse-miettes) : styles.json complet quand même")
# Cas réel du 12/10 à 16:50 : 69 objets chargés, mais seulement 14 builds sur
# 21 et 29 traits sur 50 encore là au moment d'écrire styles.json.
lua.execute(f"""
absents["{TRAIT}"] = true; absents["{BUILD_STYLE}"] = true; charges = {{}}
ramasse, vus_une_fois = true, {{}}
local trouver_8d = StaticFindObject
StaticFindObject = function(c)
    if ramasse and (c == "{TRAIT}" or c == "{BUILD_STYLE}") and not absents[c] then
        if vus_une_fois[c] then return nil end   -- déjà déchargé par le jeu
        vus_une_fois[c] = true
    end
    return trouver_8d(c)
end
""")
fichier.unlink()
(tmp / "echange" / "exploration-interdites.txt").write_text("pilotes_ia\n", encoding="utf-8")   # (8c : build interdit)
debut_journal = len(list(L.journal.values()))
styles = nouvelle_session_au_menu(SANS_MESSAGE)
s = styles["styles"][0]
ok("build lu au chargement, gardé malgré le déchargement",
   s.get("build") is not None and s.get("build_chemin") == BUILD_STYLE)
ok("trait lu au chargement, gardé malgré le déchargement", len(styles["traits"] or []) == 1)
journal = " ".join(str(x) for x in list(L.journal.values())[debut_journal:])
ok("journal : tout compté", "en mémoire au menu, 1 build(s) sur 1 et 1 trait(s) sur 1 (LoadAsset : oui)" in journal)
ok("et c'est bien le déchargement qui est simulé", lua.eval(f'StaticFindObject("{BUILD_STYLE}") == nil'))
lua.execute("ramasse = false")
course_avec_buffs()
L.avancer(2500)

print("9. Performance : plus aucun parcours de tous les objets en course ni au menu")
# Freezes du 11/10/2026 : UEHelpers.GetPlayerController / GetPlayer / GetWorld font
# chacun un FindAllOf (tous les objets du jeu), jusqu'à 6 fois toutes les 0,5 s.
# Ici, une vraie GameInstance : le mod doit passer par elle, sans aucune recherche.
lua.execute("""
recherches, appels_lents = {}, {}
local findAll, findFirst, trouver2 = FindAllOf, FindFirstOf, StaticFindObject
FindAllOf = function(c) table.insert(recherches, "FindAllOf " .. c) return findAll(c) end
instance_jeu = objet("GfnGameInstance", "/Temp/GI", "GameInstance",
                     {LocalPlayers = tableau({ {PlayerController = ctrl} })})
FindFirstOf = function(c)
    table.insert(recherches, "FindFirstOf " .. c)
    if c == "GameInstance" then return instance_jeu end
    return findFirst(c)
end
langues_jeu = objet("Default__KismetInternationalizationLibrary",
                    "/Script/Engine.Default__KismetInternationalizationLibrary", "Class", {})
function langues_jeu:GetCurrentLanguage() return "fr-FR" end
StaticFindObject = function(c)
    if c == "/Script/Engine.Default__KismetInternationalizationLibrary" then return langues_jeu end
    return trouver2(c)
end
function ctrl:GetClass() return {GetFName = function() return {ToString = function() return "GfnPlayerController" end} end} end
-- Les fonctions lentes d'UEHelpers : comptées
local uh = package.loaded["UEHelpers"]
for _, nom in ipairs({"GetPlayerController", "GetPlayer", "GetWorld"}) do
    local f = uh[nom]
    uh[nom] = function(...) table.insert(appels_lents, nom) return f(...) end
end
""")
recherches = lambda: [str(x) for x in L.recherches.values()]
L.avancer(2500)                      # fin du contrôle des buffs de 8b : miette retirée (pas un plantage)
(tmp / "echange" / "exploration-interdites.txt").unlink(missing_ok=True)
L.carte_actuelle = "L_FrontEnd"
lua.execute("ctrl.PlayerState = nil; ctrl.Pawn = nil")
lua.execute(SANS_MESSAGE)            # nouvelle session
L = lua.globals()
for _ in range(8):
    boucle()                         # au menu : catalogue, exploration, styles, langue (une seule fois)
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : accès direct par la GameInstance", "accès direct par la GameInstance" in journal)
ok("GameInstance cherchée une seule fois", recherches().count("FindFirstOf GameInstance") == 1)
lua.execute("recherches = {}")
for _ in range(10):
    boucle()
ok("au menu, ensuite : aucun parcours des objets", recherches() == [])

L.carte_actuelle = "L_Dalmatian_LOOP_A"
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=2, traits=TRAIT)
boucle()                             # lancement (contre-la-montre en course)
lua.execute("ctrl.PlayerState = nouvel_etat(); ctrl.Pawn = pion")
boucle(); boucle()                   # buffs ajoutés, style du joueur noté
ok("le joueur est bien trouvé par l'accès direct (buffs ajoutés)", lua.eval(NB_BUFFS) == 1)
lua.execute("recherches = {}")
for _ in range(20):
    boucle()                         # 10 s de course
for _ in range(60):
    L.boucles[33]()                  # 2 s de manette (30 lectures par seconde)
ok("en course : aucun parcours des objets (FindAllOf / FindFirstOf)", recherches() == [])
ok("aucun appel lent à UEHelpers depuis le début de la session",
   [str(x) for x in L.appels_lents.values()] == [])
L.comp.EventPosition = 1
L.comp.PreviousLapTime = 62.0
L.comp.EventFinishTime = 125.0
L.comp.BestLapTime = 62.0
L.comp.bHasFinishedEvent = True
boucle()
ok("le chrono marche par l'accès direct (temps noté à l'arrivée)",
   "2:05.000" in (tmp / "temps" / "temps.txt").read_text(encoding="utf-8"))

print("10. Difficulté des IA : export des 4 difficultés au menu, réglages appliqués puis remis")
lua.execute("""
function fname(s) return {ToString = function() return s end} end
function config_ia(max)
    return {AiMaxTimeAheadModifier = max, AiMinTimeAheadModifier = -1.0, AiMaxTimeAheadMultiplier = 1.0,
            AiMinTimeAheadMultiplier = 1.0, AiTimeAheadSlowdownModifier = 0.0,
            AiAggressionVPlayerCooldownMultiplier = 1.0, AiAggressionVPlayerChanceMultiplier = 1.0,
            AiCountdownToSlamPlayerModifier = 0.0, AiAbilityChanceMultiplier = 1.0, TotalCrashAllowance = 3}
end
-- Deux bases de réglages de course : celle du joueur (secours), une autre (IA)
rtd = objet("RTD_Default", "/Game/Tune/RTD_Default.RTD_Default", "RaceTuneData", {Config = config_ia(0.0)})
rtd_ia = objet("RTD_AI", "/Game/Tune/RTD_AI.RTD_AI", "RaceTuneData", {Config = config_ia(0.5)})
instance_jeu.FallbackGameTuneComponent = objet("GTC", "/Temp/GTC", "GameTuneComponent", {RaceTuneData = rtd})
local fa = FindAllOf
FindAllOf = function(c) if c == "RaceTuneData" then return {rtd, rtd_ia} end return fa(c) end
-- Une faveur de difficulté et son TuneSet
ts_cadet = objet("TNS_Diff_AiEasy", "/Game/Tune/TNS_Diff_AiEasy.TNS_Diff_AiEasy", "TuneSet", {
    Operations = tableau({
        {Category = fname("RaceTuneConfig"), Property = fname("AiMaxTimeAheadMultiplier"), Operation = 7, FloatParam = 0.65, IntParam = 1, Priority = 3},
        {Category = fname("RaceConfig"), Property = fname("TotalCrashAllowance"), Operation = 1, FloatParam = 0.0, IntParam = 2, Priority = 0}}),
    PlaneOperations = tableau({}), CoreVehicleOperations = tableau({})})
effet = objet("Effet", "/Temp/Effet", "AddPassiveRuleEffectConfig", {})
fav_cadet = objet("Favour_Diff_Easy", "/Game/Fav/Favour_Diff_Easy.Favour_Diff_Easy", "RacerFavour", {
    PlayerFacingName = texte("Coup de pouce"), PlayerFacingDescription = texte("Les rivaux vous attendent."),
    DescriptionPercentParameters = carte({}), DescriptionIntParameters = carte({}), bIsNegative = false,
    PassiveRule = tableau({ {TuneSetsToApply = tableau({ts_cadet}), Requirements = tableau({}),
                             OneTimeEffects = tableau({effet}), TrackedEffects = tableau({})} })})
-- Liste « souple » : seul son compteur peut être lu
souple_lu = false
souple = setmetatable({}, {__len = function() return 3 end,
                           __index = function() souple_lu = true; error("liste souple lue") end})
function difficulte(nom, affiche, faveurs, passifs)
    return objet(nom, "/Game/Diff/" .. nom .. "." .. nom, "CampaignDifficultyDef", {
        PlayerFacingName = texte(affiche), PreciseName = texte(affiche .. " (précis)"), Description = texte("Pour " .. affiche),
        Bars = tableau({ {Title = texte("Rivaux"), Description = texte("Vitesse des rivaux"), BarAmount = 0.25} }),
        bIsGauntlet = false, bDoesCrashAllowanceResetAtRaceStart = true,
        OpponentPassives = passifs or tableau({}), FavoursToApply = tableau(faveurs or {})})
end
instance_jeu.CampaignDifficulties = tableau({difficulte("CAM_DIFF_Easy", "Recrue", {fav_cadet}),
    difficulte("CAM_DIFF_Normal", "Pilote (recommandé)"), difficulte("CAM_DIFF_Hard", "As"),
    difficulte("CAM_DIFF_Nightmare", "Antagoniste", {}, souple)})
""")
L.avancer(2500)
(tmp / "echange" / "exploration-interdites.txt").unlink(missing_ok=True)
L.carte_actuelle = "L_FrontEnd"
lua.execute("ctrl.PlayerState = nil; ctrl.Pawn = nil")
lua.execute(SANS_MESSAGE)            # nouvelle session
L = lua.globals()
for _ in range(8):
    boucle()
fichier = tmp / "echange" / "difficultes.json"
ok("difficultes.json écrit", fichier.exists())
dj = json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else {"difficultes": [], "bases": []}
ok("4 difficultés, niveaux reconnus aux noms du jeu (Easy, Normal, Hard, Nightmare)",
   [d["niveau"] for d in dj["difficultes"]] == ["cadet", "pilote", "as", "champion"]
   and [d["affiche"] for d in dj["difficultes"]] == ["Recrue", "Pilote (recommandé)", "As", "Antagoniste"])
cadet = dj["difficultes"][0] if dj["difficultes"] else {}
ops = cadet.get("faveurs", [{}])[0].get("regles", [{}])[0].get("tunesets", [{}])[0].get("operations", []) if cadet else []
ok("Recrue : faveur, TuneSet et opérations lus",
   cadet.get("faveurs", [{}])[0].get("affiche") == "Coup de pouce"
   and {"categorie": "RaceTuneConfig", "propriete": "AiMaxTimeAheadMultiplier", "operation": 7, "flottant": 0.65,
        "entier": 1, "priorite": 3} in ops)
ok("Recrue : autres effets de la règle (classe seulement)",
   "OneTimeEffects : AddPassiveRuleEffectConfig" in cadet.get("faveurs", [{}])[0].get("regles", [{}])[0].get("autres", []))
ok("Recrue : barres et description", cadet.get("barres") == [{"titre": "Rivaux", "description": "Vitesse des rivaux", "valeur": 0.25}]
   and cadet.get("description") == "Pour Recrue")
ok("Antagoniste : passifs des adversaires comptés, jamais lus",
   dj["difficultes"][3]["passifs_adversaires"] == 3 and not L.souple_lu if len(dj["difficultes"]) == 4 else False)
ok("bases de réglages et leurs valeurs",
   [(b["nom"], b["valeurs"]["AiMaxTimeAheadModifier"]) for b in dj["bases"]] == [("RTD_Default", 0.0), ("RTD_AI", 0.5)])
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : ce que change chaque difficulté",
   "difficulté « Recrue » (CAM_DIFF_Easy, niveau cadet) : 1 faveur(s), 0 passif(s) des adversaires, "
   "réglages IA : AiMaxTimeAheadMultiplier op7 0.65/1" in journal)
ok("miette effacée", not (tmp / "echange" / "exploration-etape.txt").exists())

def reglage(base, champ="AiMaxTimeAheadModifier"):
    return lua.eval(f"{base}.Config.{champ}")

print("10b. Course à 5 adversaires en Champion : réglages Ai… de chaque base changés")
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=3, adversaires=5,
         difficulte="champion", nom_difficulte="Champion", nom_circuit="Dunes", nom_vehicule="Motojet")
boucle()
ok("avance permise : +2 s (base du joueur et base des IA)", reglage("rtd") == 2.0 and reglage("rtd_ia") == 2.5
   and reglage("rtd", "AiMinTimeAheadModifier") == 1.0)
ok("agressivité et capacités multipliées",
   reglage("rtd", "AiAggressionVPlayerChanceMultiplier") == 2.0
   and abs(reglage("rtd", "AiAggressionVPlayerCooldownMultiplier") - 0.5) < 1e-9
   and reglage("rtd", "AiAbilityChanceMultiplier") == 1.5)
ok("le reste n'est pas touché", reglage("rtd", "AiMaxTimeAheadMultiplier") == 1.0 and reglage("rtd", "TotalCrashAllowance") == 3)
ok("message de lancement avec la difficulté", "difficulté Champion" in etat_txt())

print("10c. En course : base de chaque contrôleur notée ; arrivée : résultats des IA")
L.comp.bHasFinishedEvent = False     # (la course de la section 9 était finie)
L.comp.EventPosition = 0
lua.execute("""
L_carte = nil
ctrl.PlayerState = nouvel_etat(); ctrl.Pawn = pion
ctrl.GameTuneComponent = objet("GTC_J", "/Temp/GTC_J", "GameTuneComponent", {RaceTuneData = rtd})
function controleur_ia(base)
    return objet("IA", "/Temp/IA", "DrivingAIController",
                 {GameTuneComponent = objet("GTC_IA", "/Temp/GTC_IA", "GameTuneComponent", {RaceTuneData = base})})
end
function etat_ia(nom, place, temps, base)
    local e = objet("PS_IA", "/Temp/PS_IA", "GfnPlayerState", {RaceEventComponent = {EventPosition = place, EventFinishTime = temps}})
    local c = controleur_ia(base)
    function e:GetOwner() return c end
    function e:GetPlayerName() return nom end
    return e
end
monde.GameState.Racers = tableau({ctrl.PlayerState, etat_ia("Lyren Shok", 1, 120.5, rtd),
                                  etat_ia("Biddy Blas", 0, -1, rtd_ia)})
""")
L.carte_actuelle = "L_Dalmatian_LOOP_A"
boucle(); boucle()
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : base du joueur et des IA",
   "difficulté des IA, en course : base du joueur RTD_Default ; bases des IA RTD_AI ×1, RTD_Default ×1" in journal)
L.comp.EventPosition = 2
L.comp.PreviousLapTime = 41.0
L.comp.EventFinishTime = 125.0
L.comp.BestLapTime = 41.0
L.comp.bHasFinishedEvent = True
boucle()
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : arrivée des IA", "arrivée : 1. Lyren Shok 2:00.500 — 2. vous 2:05.000 — pas encore arrivés : 1" in journal)
lignes = list(csv.DictReader((tmp / "temps" / "temps.csv").read_text(encoding="utf-8").splitlines(), delimiter=";"))
detail = dict(p.split("=", 1) for p in lignes[-1]["Détail du build"].split(";"))
ok("temps.csv : difficulté notée", detail.get("difficulte") == "champion" and detail.get("adversaires") == "5")
ok("temps.txt : « place 2/6, Champion »", "place 2/6, Champion" in (tmp / "temps" / "temps.txt").read_text(encoding="utf-8"))

print("10d. Retour au menu : réglages du jeu remis")
L.comp.bHasFinishedEvent = False
lua.execute("ctrl.PlayerState = nil; ctrl.Pawn = nil")
L.carte_actuelle = "L_FrontEnd"
boucle()
ok("bases remises comme avant", reglage("rtd") == 0.0 and reglage("rtd_ia") == 0.5
   and reglage("rtd", "AiAggressionVPlayerChanceMultiplier") == 1.0)
ok("journal : remise notée", "difficulté des IA : réglages du jeu remis" in " ".join(str(x) for x in L.journal.values()))

print("10e. Pas de cumul, contre-la-montre, « jeu », échec du lancement")
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=3, adversaires=3, difficulte="as")
boucle()
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=3, adversaires=3, difficulte="cadet")
boucle()
ok("as puis recrue : valeurs du jeu (×0,65 et −3 s) depuis la base d'origine, pas de cumul",
   reglage("rtd") == 0.0 and abs(reglage("rtd", "AiMaxTimeAheadMultiplier") - 0.65) < 1e-9
   and reglage("rtd", "AiMinTimeAheadModifier") == -4.0 and reglage("rtd", "AiAbilityChanceMultiplier") == 0.5)
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=2, adversaires=0, difficulte="champion")
boucle()
ok("contre-la-montre : difficulté ignorée, réglages du jeu", reglage("rtd") == 0.0 and lua.eval("dernierChoix == nil or true"))
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=3, adversaires=3, difficulte="")
boucle()
ok("« jeu » : rien changé, pas de difficulté dans le message", reglage("rtd") == 0.0 and "difficulté" not in etat_txt())
lua.execute("""function mode_menu:LaunchCustomRace(...) error("refusé (simulé)") end""")
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=3, adversaires=3, difficulte="champion")
boucle()
ok("lancement refusé : réglages remis aussitôt", reglage("rtd") == 0.0 and reglage("rtd_ia") == 0.5)
lua.execute("""function mode_menu:LaunchCustomRace(...) table.insert(appels_ia, table.pack(...)) end
-- (erreur voulue : retirée du journal avant le contrôle final)
for i = #journal, 1, -1 do if journal[i]:find("refusé (simulé)", 1, true) then table.remove(journal, i) end end""")

print("11. Apparence du véhicule du pilote (commentaire Nexus : tous les podracers identiques)")
# L'épreuve modèle impose sa « recette » (apparence) ; le pilote a la sienne
# par type de véhicule (PreferredCustomisationForVehicleArchetype).
lua.execute("""
rec_epreuve = objet("CST_Pod_Epreuve_C", "/Game/Cst/CST_Pod_Epreuve.CST_Pod_Epreuve_C", "BlueprintGeneratedClass", {})
rec_star = objet("CST_Bike_Star_C", "/Game/Cst/CST_Bike_Star.CST_Bike_Star_C", "BlueprintGeneratedClass", {})
rec_ia = objet("CST_Bike_IA_C", "/Game/Cst/CST_Bike_IA.CST_Bike_IA_C", "BlueprintGeneratedClass", {})
autre_pilote = objet("DA_Racer_Biddy", "/Game/Racers/DA_Racer_Biddy.DA_Racer_Biddy", "RacerDef", {})
star.PreferredCustomisationForVehicleArchetype = carte({{2, rec_star}})   -- 2 = Bike (motojet) seulement
modele.EventMode.bUseCustomVehicle = true                                 -- l'épreuve modèle impose son véhicule
demandes_apparence = {}
function etat_avec_apparence()
    local e = nouvel_etat()
    local composant = objet("PVCC", "/Temp/PVCC", "PlayerVehicleCustomisationComponent", {})
    function composant:Client_SetOverrideVehicleRecipe(r)
        table.insert(demandes_apparence, r)
        for _, x in ipairs(rawget(monde.GameState.EventRecipeState_Replication.Racers, "elements")) do
            if x.Player == e then x.VehicleCustomisation = r end
        end
    end
    e.VehicleCustomisationComponent = composant
    e.RacerBuildState = {VehicleBuilds = tableau({ {VehicleBuildDef = build_tt, BuildArchetype = 2,
                                                     AbilitySlots = tableau({capacite})} })}
    monde.GameState.EventRecipeState_Replication = {Racers = tableau({
        {Player = e, Pilot = star, vehicleType = 2, VehicleCustomisation = rec_epreuve},
        {Player = objet("PS_IA", "/Temp/PS_IA_A", "GfnPlayerState", {}), Pilot = autre_pilote, vehicleType = 2,
         VehicleCustomisation = rec_ia}})}
    return e
end
""")
miette = tmp / "echange" / "exploration-etape.txt"


def course_avec_pilote(type_vehicule="motojet", **cles):
    L.comp.bHasFinishedEvent = False
    lua.execute("ctrl.PlayerState = nil; ctrl.Pawn = nil")
    L.carte_actuelle = "L_FrontEnd"
    boucle()                                   # retour au menu : nouvelle course ensuite
    L.carte_actuelle = "L_Dalmatian_LOOP_A"
    commande(type=type_vehicule, piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=2,
             pilote="/Game/Racers/DA_Racer_Star.DA_Racer_Star", **cles)
    boucle()
    lua.execute("ctrl.PlayerState = etat_avec_apparence(); ctrl.Pawn = pion")
    boucle()


course_avec_pilote()
journal = " ".join(str(x) for x in L.journal.values())
ok("contre-la-montre : véhicule de l'épreuve toujours imposé (coupure essayée le 12/10 : landspeeder)",
   lua.eval("modele.EventMode.bUseCustomVehicle") is True and "n'est plus imposé" not in journal)
ok("aucune demande au jeu (essayée le 12/10 : sans effet)", len(list(L.demandes_apparence.values())) == 0)
ok("journal : la recette de chaque pilote de la course",
   "apparence des véhicules de la course : vous, DA_Racer_Star (type 2) : CST_Pod_Epreuve_C — "
   "DA_Racer_Biddy (type 2) : CST_Bike_IA_C" in journal)
ok("journal : celle du pilote, notée seulement", "celle du pilote serait CST_Bike_Star_C (demande coupée)" in journal)
ok("journal : build donné par le jeu au joueur", "build du joueur selon le jeu : VBD_TT (type 2, 1 capacité(s))" in journal)
ok("pas de miette restée", not miette.exists())

print("11b. Avec des buffs : l'apparence attend qu'ils aient fini (une seule miette à la fois)")
n_avant = len(list(L.journal.values()))
course_avec_pilote(traits=TRAIT)
nouveaux = " ".join(str(x) for x in list(L.journal.values())[n_avant:])
ok("buffs d'abord : pas encore d'apparence", "apparence des véhicules" not in nouveaux
   and miette.read_text(encoding="utf-8") == "buffs")
L.avancer(2500)                                # contrôle des buffs : miette retirée
boucle()
nouveaux = " ".join(str(x) for x in list(L.journal.values())[n_avant:])
ok("puis l'apparence", "apparence des véhicules" in nouveaux and not miette.exists())

print("11c. Déjà la bonne recette, ou pilote sans recette pour ce véhicule")
lua.execute("rec_epreuve_garde = rec_epreuve; rec_epreuve = rec_star")
course_avec_pilote()
ok("déjà celle du pilote : noté", not miette.exists()
   and "le véhicule a déjà celle du pilote (CST_Bike_Star_C)" in " ".join(str(x) for x in L.journal.values()))
lua.execute("rec_epreuve = rec_epreuve_garde; star.PreferredCustomisationForVehicleArchetype = carte({{1, rec_star}})")
course_avec_pilote()                           # (recette pour les modules seulement)
lua.execute("star.PreferredCustomisationForVehicleArchetype = carte({{2, rec_star}})")
ok("pas de recette propre pour ce véhicule → celle de l'épreuve gardée, et c'est dit",
   lua.eval("modele.EventMode.bUseCustomVehicle") is True and not miette.exists()
   and "DA_Racer_Star n'a pas d'apparence propre pour ce véhicule" in etat_txt())

print("11d. L'apparence a fait planter la session précédente : plus rien, et c'est dit")
lua.execute("ctrl.PlayerState = nil")
L.carte_actuelle = "L_FrontEnd"
miette.write_text("apparence", encoding="utf-8")
lua.execute("demandes_apparence = {}")
lua.execute(SANS_MESSAGE)                     # nouvelle session
L = lua.globals()
for _ in range(10):
    boucle()
course_avec_pilote()
ok("aucune demande, message clair", len(list(L.demandes_apparence.values())) == 0
   and "apparence du véhicule du pilote désactivée" in etat_txt())

print("12. Course de modules avec IA : des pilotes de module, pas les speeders du jeu (vu le 12/10/2026)")
# LaunchCustomRace prend ses IA dans DA_CharacterList.Opponents (11 pilotes de
# speeder) : le 12/10, motos et skimmers dans une course de pods.
lua.execute("""
local tag = function(s) return {TagName = texte(s)} end
local function racer(nom) return objet(nom, "/Game/Racers/" .. nom .. "." .. nom, "RacerDef", {}) end
thrall, onion, onion_age, cabbage, garlic = racer("DA_Racer_Thrall"), racer("DA_PlaneRacer_Onion"),
    racer("DA_PlaneRacer_OnionAged"), racer("DA_PlaneRacer_Cabbage"), racer("DA_PlaneRacer_Garlic")
liste_pilotes.Opponents = tableau({star, thrall})
liste_pilotes.PvpPlaneInstantActionPlayable = tableau({cabbage, garlic, onion})
liste_pilotes.PvpPlanePlayable = tableau({onion_age, garlic})          -- (garlic en double)
local objets12 = {}
for _, o in ipairs({
    objet("VA_Plane", "/Game/Griffin/Vehicles/Planes/VA_Plane.VA_Plane", "VehicleArchetype", {}),
    objet("EVT_TT_PLANE", "/Game/Griffin/Gameplay/Arcade/Events/TimeTrial/EVT_ARC_TT_PLANE_BGL_PLANE_FWD.EVT_ARC_TT_PLANE_BGL_PLANE_FWD",
          "ArcadeEventDef", {VehicleTypeTag = tag("Vehicle.Special.Plane"), LapCount = 3, EventMode = {bUsePlayerHealth = true}}),
    objet("VBD_TT_PLANE", "/Game/Griffin/Gameplay/Campaign/Builds/Arcade/VBD_ARC_TT_PLANE_BGL_PLANE_FWD.VBD_ARC_TT_PLANE_BGL_PLANE_FWD",
          "VehicleBuildDef", {SlotToUpgradeLevelMap = carte({}), AbilitySlots = tableau({}), Affixes = tableau({}),
                              PlaneOnlyAffixes = tableau({}), UseHealth = true}),
    objet("VBD_Plane_Base", "/Game/Griffin/Gameplay/Campaign/Builds/VBD_Plane_Base.VBD_Plane_Base", "VehicleBuildDef", {}),
    objet("TRAK_WHP_PLANE_FWD", "/Game/T/TRAK_WHP_PLANE_FWD.TRAK_WHP_PLANE_FWD", "TrackDef",
          {VehicleTypeTag = tag("Vehicle.Special.Plane"), DefaultLapCount = 2}),
    objet("GMV_PlaneRaces", "/Game/Griffin/Gameplay/Campaign/GameModes/GMV_PlaneRaces.GMV_PlaneRaces", "GameModeVariantDef",
          {GridMakeup = {Entries = tableau({{EntryType = 1, NumEntrants = 6}})}}),
    onion}) do
    objets12[o:GetFullName():match("^%S+%s+(.+)$")] = o
end
gmv_planes = objets12["/Game/Griffin/Gameplay/Campaign/GameModes/GMV_PlaneRaces.GMV_PlaneRaces"]
local avant12 = StaticFindObject
StaticFindObject = function(c) return objets12[c] or avant12(c) end
function noms_adversaires()
    local t = {}
    liste_pilotes.Opponents:ForEach(function(_, e) table.insert(t, e:get():GetFName():ToString()) end)
    return table.concat(t, ",")
end
""")
L.comp.bHasFinishedEvent = False
lua.execute("ctrl.PlayerState = nil; ctrl.Pawn = nil")
L.carte_actuelle = "L_FrontEnd"
boucle()
nb_appels = len(list(L.appels_ia.values()))
commande(type="avion", piste="/Game/T/TRAK_WHP_PLANE_FWD.TRAK_WHP_PLANE_FWD", tours=2, adversaires=5,
         pilote="/Game/Racers/DA_PlaneRacer_Onion.DA_PlaneRacer_Onion")
boucle()
ok("course lancée", len(list(L.appels_ia.values())) == nb_appels + 1)
ok("adversaires = pilotes de module, sans le joueur (Onion) ni doublon",
   L.noms_adversaires() == "DA_PlaneRacer_Cabbage,DA_PlaneRacer_Garlic,DA_PlaneRacer_OnionAged")
ok("5 demandés, 3 pilotes de module : grille de 1 + 3", lua.eval("gmv_planes.GridMakeup.Entries[1].NumEntrants") == 4)
journal = " ".join(str(x) for x in L.journal.values())
ok("journal : ce qui a été fait",
   "3 pilote(s) de module à la place des 2 pilotes de speeder du jeu (DA_PlaneRacer_Cabbage, DA_PlaneRacer_Garlic, "
   "DA_PlaneRacer_OnionAged)" in journal and "5 demandés, mais seulement 3 pilotes de module" in journal)
L.carte_actuelle = "L_Whippet_PLANE"
boucle()
ok("en course : toujours les pilotes de module", L.noms_adversaires().startswith("DA_PlaneRacer_Cabbage"))
L.carte_actuelle = "L_FrontEnd"
boucle()
ok("retour au menu : liste du jeu remise", L.noms_adversaires() == "DA_Racer_Star,DA_Racer_Thrall"
   and "liste du jeu remise (2 pilotes)" in " ".join(str(x) for x in L.journal.values()))

print("12b. Course de speeders avec IA : la liste du jeu n'est pas touchée ; lancement refusé : liste remise")
commande(type="motojet", piste="/Game/T/TRAK_DAL_LOOP_A.TRAK_DAL_LOOP_A", tours=2, adversaires=3)
boucle()
ok("speeders : liste du jeu", L.noms_adversaires() == "DA_Racer_Star,DA_Racer_Thrall")
lua.execute("""mode_menu.LaunchCustomRace_garde = mode_menu.LaunchCustomRace
function mode_menu:LaunchCustomRace(...) error("refusé (simulé)") end""")
commande(type="avion", piste="/Game/T/TRAK_WHP_PLANE_FWD.TRAK_WHP_PLANE_FWD", tours=2, adversaires=2,
         pilote="/Game/Racers/DA_PlaneRacer_Onion.DA_PlaneRacer_Onion")
boucle()
ok("modules, lancement refusé : liste du jeu remise aussitôt", L.noms_adversaires() == "DA_Racer_Star,DA_Racer_Thrall")
lua.execute("""mode_menu.LaunchCustomRace = mode_menu.LaunchCustomRace_garde
for i = #journal, 1, -1 do if journal[i]:find("refusé (simulé)", 1, true) then table.remove(journal, i) end end""")

print("12c. Module seul avec un pilote qui a son pod : course perso sans adversaire (pod du pilote)")
# Commentaire Nexus : tous les podracers ont le même pod en contre-la-montre
# (l'épreuve impose le sien). Contre des IA, le jeu donne bien le pod du pilote.
lua.execute("""
rec_onion = objet("PRE_Plane_Dearc_C", "/Game/Cst/PRE_Plane_Dearc.PRE_Plane_Dearc_C", "BlueprintGeneratedClass", {})
onion.PreferredCustomisationForVehicleArchetype = carte({{1, rec_onion}})   -- 1 = Plane
""")
L.carte_actuelle = "L_FrontEnd"
lua.execute("ctrl.PlayerState = nil; ctrl.Pawn = nil")
boucle()
n_ia, n_rapides, n_voyages = (len(list(L.appels_ia.values())), len(list(L.appels_rapides.values())),
                              len(list(L.voyages.values())))
commande(type="avion", piste="/Game/T/TRAK_WHP_PLANE_FWD.TRAK_WHP_PLANE_FWD", tours=2,
         pilote="/Game/Racers/DA_PlaneRacer_Onion.DA_PlaneRacer_Onion")
boucle()
ok("depuis le menu : course perso (LaunchCustomRace), pas le contre-la-montre de l'épreuve",
   len(list(L.appels_ia.values())) == n_ia + 1 and len(list(L.appels_rapides.values())) == n_rapides)
ok("grille : le joueur seul", lua.eval("gmv_planes.GridMakeup.Entries[1].NumEntrants") == 1)
ok("liste des adversaires du jeu pas touchée", L.noms_adversaires() == "DA_Racer_Star,DA_Racer_Thrall")
ok("fenêtre : « seul, avec le pod du pilote »", "seul, avec le pod du pilote" in etat_txt())
L.carte_actuelle = "L_Whippet_PLANE"
touche("F6")
ok("F6 : explique « Recommencer » du menu pause", "course personnalisée (pod du pilote)" in etat_txt())
commande(type="avion", piste="/Game/T/TRAK_WHP_PLANE_FWD.TRAK_WHP_PLANE_FWD", tours=2,
         pilote="/Game/Racers/DA_PlaneRacer_Onion.DA_PlaneRacer_Onion")
boucle()
journal = " ".join(str(x) for x in L.journal.values())
ok("depuis une course : l'épreuve (et son pod), et c'est dit",
   len(list(L.voyages.values())) == n_voyages + 1 and "seulement en lançant depuis le menu principal" in journal)
L.carte_actuelle = "L_FrontEnd"
boucle()
n_rapides = len(list(L.appels_rapides.values()))
commande(type="avion", piste="/Game/T/TRAK_WHP_PLANE_FWD.TRAK_WHP_PLANE_FWD", tours=2,
         pilote="/Game/Racers/DA_PlaneRacer_Garlic.DA_PlaneRacer_Garlic")
lua.execute("""local avant = StaticFindObject
StaticFindObject = function(c) if c == "/Game/Racers/DA_PlaneRacer_Garlic.DA_PlaneRacer_Garlic" then return garlic end return avant(c) end""")
boucle()
ok("pilote sans pod propre : contre-la-montre de l'épreuve, comme avant",
   len(list(L.appels_rapides.values())) == n_rapides + 1)

ok("aucun LoopAsync ni ExecuteWithDelay (fil « async » d'UE4SS, v0.9.9)", L.anciens_appels == 0)
erreurs = [str(x) for x in L.journal.values() if "ERREUR" in str(x) or "ERROR" in str(x)]
ok("aucune erreur dans le journal", not erreurs)
if erreurs:
    print("\n".join(erreurs[:5]))
if echecs:
    print(f"\n{len(echecs)} ÉCHEC(S)")
    sys.exit(1)
print("\nTOUS LES TESTS SONT PASSÉS")
