--[[
    PracticeMode : mode entraînement pour Star Wars: Galactic Racer
    =================================================================
    Version 0.9.4 (10/10/2026) : messages en français ou en anglais, selon
    le bouton FR / EN de la fenêtre (echange/langue.txt). Voir « LANGUE ».

    Version 0.9.3 (10/10/2026) : le save state garde aussi le boost
    (énergie de postcombustion, chaleur et état du ramjet) et le rend au
    retour. Voir « Boost » plus bas.

    Version 0.9 (11/10/2026) : save states, 3 emplacements.
        F7 / Maj+F7 / Ctrl+F7 : sauvegarder la position, l'orientation et la
                                vitesse du véhicule dans l'emplacement 1 / 2 / 3
        F8 / Maj+F8 / Ctrl+F8 : y revenir instantanément
    Le retour passe par la fonction de remise en place du jeu lui-même (celle
    utilisée après un crash) : ResetComponent:Server_RequestResetAtLocationAtSpeed,
    télémétrie coupée. Une course où l'on est revenu à un emplacement est
    marquée « save state » dans les temps (exclue des records). Après chaque
    retour, un chrono de section mesure le temps jusqu'au secteur suivant
    (temps/sections.txt).

    Version 0.8 (10/10/2026) : enregistrement des temps.
    Pendant la course, le mod surveille PlayerState.RaceEventComponent du
    joueur (toutes les 0,5 s) : il relève chaque tour (PreviousLapTime) et,
    quand bHasFinishedEvent passe à vrai, écrit le temps final
    (EventFinishTime) dans temps/temps.txt et temps/temps.csv.

    Version 0.7 (10/10/2026) : capacités enfin exportées (repérées par leur
    nom + IsA), valeurs des affixes ({perc}, {int}…) et noms des stats du
    jeu (VehicleUIConfig) exportés pour la fenêtre.

    Version 0.6 (10/10/2026) : + éditeur de build et crashs illimités.

    Le build : chaque épreuve contre-la-montre Arcade impose son propre build
    (EventMode.CustomVehicle.VehicleBuildDef = VBD_ARC_TT_<épreuve>). On
    remplit ce build-là avec les choix de la fenêtre, pièce par pièce :
    niveaux des 6 améliorations de stat, capacités, capacité de crash,
    affixes, boost, ramjet, pannes critiques. Comme c'est le build de
    l'épreuve, il s'applique aussi au restart (F6). En mémoire seulement.

    Crashs illimités : on coupe la « santé » du build (UseHealth) et celle
    du mode contre-la-montre (bUsePlayerHealth).

    Version 0.5 (10/10/2026) : pilotage par la fenêtre « PracticeMode ».

    Fonctionnement général :

        Fenêtre (Python)                       Mod (ce fichier)
        ────────────────                       ────────────────
        lit catalogue.json      ◄────────────  écrit catalogue.json
                                               (circuits, véhicules, pilotes,
                                                avec leurs noms affichés)
        écrit commande.txt      ────────────►  lit commande.txt toutes les
        (véhicule, circuit,                    0,5 s, puis lance la course
         tours, pilote)
        affiche etat.txt        ◄────────────  écrit etat.txt (ce qui se passe)

    Les trois fichiers sont dans le dossier d'échange (CONFIG.DossierEchange).

    Comment on lance la course de son choix (méthode testée le 10/10/2026) :
      une épreuve contre-la-montre Arcade n'est qu'un « circuit + nombre de
      tours + mode TimeTrial ». On prend une épreuve MODÈLE du bon type de
      véhicule et on remplace, en mémoire seulement, son circuit et son
      nombre de tours. On remplace aussi le pilote du joueur
      (DA_CharacterList.Player). Rien n'est écrit sur le disque : au
      prochain lancement du jeu, tout est revenu d'origine.

    Touches en jeu :
        F5     : relancer le dernier choix (depuis le menu principal)
        F6     : recommencer la course en cours
        Ctrl+R : recharger le mod après une modification

    Règles de sécurité (voir PROJET.md) :
      - aucun appel aux fonctions multijoueur ;
      - à utiliser uniquement avec Steam hors ligne, dans une session ouverte
        par Debut-Session.bat (qui remet la sauvegarde d'origine à la fin).
]]

-- ─────────────────────────────────────────────────────────────────────────
--  CONFIGURATION : tous les noms qui viennent du jeu sont ici.
--  Après une mise à jour du jeu, c'est la seule partie à corriger.
-- ─────────────────────────────────────────────────────────────────────────
-- Dossier de PracticeMode (celui de la fenêtre / PracticeMode.exe), barres « / »
-- et « / » final. Le launcher remplace cette ligne, dans la copie installée
-- dans le jeu, par le vrai dossier de l'utilisateur.
local DOSSIER_PRACTICEMODE = "ECRIT-PAR-LE-LAUNCHER/"

local CONFIG = {
    -- Dossier partagé avec la fenêtre
    DossierEchange = DOSSIER_PRACTICEMODE .. "echange/",

    -- Fichiers des temps (hors du dossier du jeu : ils survivent à la fin de session)
    FichierTemps    = DOSSIER_PRACTICEMODE .. "temps/temps.txt",
    FichierTempsCsv = DOSSIER_PRACTICEMODE .. "temps/temps.csv",

    FichierSections = DOSSIER_PRACTICEMODE .. "temps/sections.txt",

    -- Verrou de sécurité : le mod ne fait RIEN tant que la session n'est pas
    -- protégée par le pare-feu du launcher (echange/pare-feu.txt = « actif »).
    -- Le jeu garde les temps faits hors ligne pour les envoyer plus tard aux
    -- classements : sans pare-feu ni sauvegarde remise à la fin de session,
    -- un temps fait avec le mod pourrait partir en ligne. Ne pas désactiver.
    Verrou          = true,
    Verrou_Relecture = 2,   -- secondes entre deux lectures de pare-feu.txt

    -- Save states
    -- Méthode de retour :
    --   "direct" : téléportation + vitesse physique rendue telle quelle (le plus fidèle)
    --   "reset"  : remise en place du jeu (comme après un crash) puis vitesse réinjectée
    -- (essai 10/10 : la remise en place du jeu seule repart À L'ARRÊT, malgré la vitesse passée)
    SaveState_Methode    = "direct",
    SaveState_Relances   = { 50, 150, 300, 600 },   -- ms : on revérifie la vitesse et on la remet si le jeu l'a cassée
    SaveState_Composant  = "ResetComponent",                        -- sur le véhicule
    SaveState_Fonction   = "Server_RequestResetAtLocationAtSpeed",  -- (transform, mph, protection, au sol, télémétrie, IA)
    SaveState_Protection = false,   -- protection brève après le retour (à essayer si on recrashe)
    SaveState_AuSol      = false,   -- la position sauvegardée est celle du véhicule, pas du sol
    SaveState_Touches    = { { touche = Key.F7, charger = Key.F8, modificateurs = {} },
                             { touche = Key.F7, charger = Key.F8, modificateurs = { ModifierKey.SHIFT } },
                             { touche = Key.F7, charger = Key.F8, modificateurs = { ModifierKey.CONTROL } } },
    DelaiTouches         = 80,      -- ms : voir LierTouche (F7 seul ≠ Maj+F7)

    -- Manette (UE4SS ne gère que le clavier : le mod interroge le jeu avec
    -- PlayerController:IsInputKeyDown, 30 fois par seconde)
    Manette_Sauver      = "Gamepad_DPad_Down",    -- croix bas    = sauvegarder
    Manette_Charger     = "Gamepad_DPad_Right",   -- croix droite = revenir
    Manette_Emplacement = 1,                      -- emplacement utilisé par la manette
    Manette_Delai       = 33,                     -- ms entre deux lectures

    -- Boost rendu au retour (v0.9.3)
    --   pion.VehicleState   : l'état complet du véhicule (énergie de
    --                         postcombustion, chaleur du ramjet…), lisible
    --   pion.BoostComponent : ses parties .Afterburner et .Ramjet, avec les
    --                         fonctions du jeu qui règlent énergie, chaleur, état
    Boost_Actif           = true,
    Boost_Etat            = "VehicleState",
    Boost_Composant       = "BoostComponent",
    Boost_EcritureDirecte = true,   -- écrire AUSSI énergie et chaleur dans VehicleState
    Boost_Verification    = 100,    -- ms : relecture après le retour (notée dans le journal)
    BibliothequeSons     = "/Script/Griffin.Default__UIAudioLibrary",
    Son_Sauvegarde       = "PlayPrecisionCheckpointSfx",
    Son_Erreur           = "PlayHitmarkerSfx",
    Son_Section          = "PlayShakedownSuccessSfx",
    Chrono_Secteur       = "CurrentSectorNumber",     -- 255 = aucun secteur
    Chrono_DebutSecteur  = "SectorStartServerTime",

    -- Chrono du joueur : PlayerState.RaceEventComponent
    Chrono_Composant = "RaceEventComponent",
    Chrono_Fini      = "bHasFinishedEvent",
    Chrono_Final     = "EventFinishTime",
    Chrono_Meilleur  = "BestLapTime",
    Chrono_Precedent = "PreviousLapTime",

    -- Pour chaque type de véhicule : son archétype, son épreuve modèle
    -- (contre-la-montre Arcade du même type), le build imposé par cette
    -- épreuve (celui qu'on remplit avec les choix de la fenêtre) et un
    -- build de base de secours.
    Types = {
        motojet = {
            Archetype   = "/Game/Griffin/Vehicles/Bikes/VA_Bike.VA_Bike",
            Modele      = "/Game/Griffin/Gameplay/Arcade/Events/TimeTrial/EVT_ARC_TT_BIKE_DAL_P2P_SHORT_05.EVT_ARC_TT_BIKE_DAL_P2P_SHORT_05",
            BuildModele = "/Game/Griffin/Gameplay/Campaign/Builds/Arcade/VBD_ARC_TT_BIKE_DAL_P2P_SHORT_05.VBD_ARC_TT_BIKE_DAL_P2P_SHORT_05",
            Build       = "/Game/Griffin/Gameplay/Campaign/Builds/VBD_Bike_Base.VBD_Bike_Base",
        },
        voiture = {
            Archetype   = "/Game/Griffin/Vehicles/Cars/VA_Car.VA_Car",
            Modele      = "/Game/Griffin/Gameplay/Arcade/Events/TimeTrial/EVT_ARC_TT_CAR_COR_A_FWD.EVT_ARC_TT_CAR_COR_A_FWD",
            BuildModele = "/Game/Griffin/Gameplay/Campaign/Builds/Arcade/VBD_ARC_TT_CAR_COR_A_FWD.VBD_ARC_TT_CAR_COR_A_FWD",
            Build       = "/Game/Griffin/Gameplay/Campaign/Builds/VBD_Car_Base.VBD_Car_Base",
        },
        skimmer = {
            Archetype   = "/Game/Griffin/Vehicles/Skimmers/VA_Skimmer.VA_Skimmer",
            Modele      = "/Game/Griffin/Gameplay/Arcade/Events/TimeTrial/EVT_ARC_TT_SKIMMER_COR_B_FWD.EVT_ARC_TT_SKIMMER_COR_B_FWD",
            BuildModele = "/Game/Griffin/Gameplay/Campaign/Builds/Arcade/VBD_ARC_TT_SKIMMER_COR_B_FWD.VBD_ARC_TT_SKIMMER_COR_B_FWD",
            Build       = "/Game/Griffin/Gameplay/Campaign/Builds/VBD_Skimmer_Base.VBD_Skimmer_Base",
        },
        avion = {
            Archetype   = "/Game/Griffin/Vehicles/Planes/VA_Plane.VA_Plane",
            Modele      = "/Game/Griffin/Gameplay/Arcade/Events/TimeTrial/EVT_ARC_TT_PLANE_BGL_PLANE_FWD.EVT_ARC_TT_PLANE_BGL_PLANE_FWD",
            BuildModele = "/Game/Griffin/Gameplay/Campaign/Builds/Arcade/VBD_ARC_TT_PLANE_BGL_PLANE_FWD.VBD_ARC_TT_PLANE_BGL_PLANE_FWD",
            Build       = "/Game/Griffin/Gameplay/Campaign/Builds/VBD_Plane_Base.VBD_Plane_Base",
        },
    },

    -- Propriétés d'un build (VehicleBuildDef) modifiées par l'éditeur
    Build_Niveaux     = "SlotToUpgradeLevelMap", -- emplacement (0 à 5) → niveau (0 à 10)
    Build_Capacites   = "AbilitySlots",          -- liste de classes de capacités
    Build_Crash       = "CrashAbility",          -- classe de capacité de crash
    Build_Affixes     = "Affixes",               -- liste d'affixes
    Build_AffixesAvion = "PlaneOnlyAffixes",
    Build_SlotsOuverts = "UnlockedAffixSlots",
    Build_SlotsMax    = "MaximumAffixSlots",
    Build_Boost       = "BasicBoostType",        -- 0 = aucun, 1 = Afterburner
    Build_Ramjet      = "RamjetInstalled",
    Build_Pannes      = "CriticalMalfunctions",
    Build_Sante       = "UseHealth",
    Mode_Sante        = "bUsePlayerHealth",      -- dans EventMode de l'épreuve
    ProprieteMode     = "EventMode",
    NbEmplacements    = 6,                       -- Virage, Accélération, Résistance, Boost, Capacités, Avancé

    -- Pour reconnaître les capacités dans le catalogue
    PrefixeCapacite      = "BP_Ability_",                      -- nom des classes de capacités
    CheminClasseCapacite = "/Script/Griffin.GfnAbility",       -- classe de base des capacités
    CheminClasseCrash    = "/Script/Griffin.GfnCrashAbility",  -- classe de base des capacités de crash
    MotCleCrash          = "IonBlast",                         -- secours si IsA n'est pas disponible
    Capacites_Liste         = "GfnAbilityList",                -- liste du jeu…
    Capacites_ListeToutes   = "All",                           -- …de toutes les capacités
    Capacites_Builds        = "VehicleBuildDef",               -- builds du jeu (AbilitySlots, CrashAbility)
    Capacites_Ameliorations = "CanUpgradeTo",                  -- versions améliorées d'une capacité
    Capacites_Essais        = 5,                               -- 0 capacité au menu : nouveaux essais…
    Capacites_Intervalle    = 3,                               -- …toutes les 3 s
    -- Textes dans leur langue d'origine (voir SourceDuTexte) ; false = seulement la langue du jeu
    TextesSource         = true,
    BibliothequeTextes   = "/Script/Engine.Default__KismetTextLibrary",
    BibliothequeLangues  = "/Script/Engine.Default__KismetInternationalizationLibrary",
    ClasseAffixe         = "AffixPassiveConfig",
    ClasseConfigUI       = "VehicleUIConfig",                  -- noms des stats affichés en jeu

    -- Pilote du joueur
    ListePilotes    = "/Game/Griffin/Narrative/CharacterDefs/DA_CharacterList.DA_CharacterList",
    ProprietePilote = "Player",

    -- Classes, fonctions et propriétés du jeu utilisées
    ClasseModeMenu      = "FrontEndGameMode",      -- existe au menu principal (et peut traîner en mémoire après)
    CarteMenu           = "L_FrontEnd",            -- carte du menu principal : seul endroit où l'on exporte le catalogue
    FonctionLancer      = "LaunchQuickRace",       -- (archétype, épreuve, build)
    ClasseArcade        = "ArcadeSubsystem",
    FonctionRecommencer = "RequestRestartEvent",   -- relance LastPlayedArcadeEvent
    FonctionVoyager     = "TravelToEvent",         -- (épreuve Arcade), utilisable en course
    ProprieteDerniere   = "LastPlayedArcadeEvent",
    ProprietePiste      = "TrackDef",
    ProprieteTours      = "LapCount",
    ClassesCatalogue    = { Circuits = "TrackDef", Planetes = "PlanetDef",
                            Vehicules = "VehicleArchetype", Pilotes = "RacerDef" },

    -- Touches
    ToucheRelancer    = Key.F5,
    ToucheRecommencer = Key.F6,

    -- Délai entre deux lectures de commande.txt (millisecondes)
    DelaiScrutation = 500,
}

local FICHIER_CATALOGUE = CONFIG.DossierEchange .. "catalogue.json"
local FICHIER_COMMANDE  = CONFIG.DossierEchange .. "commande.txt"
local FICHIER_ETAT      = CONFIG.DossierEchange .. "etat.txt"

-- Mémoire du mod
local dernierChoix = nil        -- dernière commande reçue (pour F5 et pour les temps)
local catalogueExporte = false  -- le catalogue a-t-il déjà été écrit ?
local essaisCatalogue = 0       -- exports automatiques déjà faits (voir ExporterCatalogue)
local prochainEssaiCatalogue = 0

-- ─────────────────────────────────────────────────────────────────────────
--  LANGUE DES MESSAGES (v0.9.4)
--  La fenêtre écrit « fr » ou « en » dans echange/langue.txt (bouton FR/EN) ;
--  le mod le relit toutes les 0,5 s. Chaque message affiché à l'utilisateur
--  a ses deux versions ; %s et %.0f sont remplis par Traduire(). Les lignes de
--  diagnostic de la console (Detail) restent en français.
-- ─────────────────────────────────────────────────────────────────────────
local FICHIER_LANGUE = CONFIG.DossierEchange .. "langue.txt"
local langue = "fr"
local MESSAGES = {
    introuvable      = { fr = "introuvable : %s (%s)", en = "not found: %s (%s)" },
    erreur_pendant   = { fr = "ERREUR pendant %s : %s", en = "ERROR during %s: %s" },
    ecriture         = { fr = "impossible d'écrire %s (le dossier d'échange existe-t-il ?)",
                         en = "cannot write %s (does the exchange folder exist?)" },
    catalogue        = { fr = "catalogue exporté : %s circuits, %s planètes, %s véhicules, %s pilotes, %s capacités, %s affixes",
                         en = "catalogue exported: %s tracks, %s planets, %s vehicles, %s racers, %s abilities, %s affixes" },
    build_charge     = { fr = "build : impossible de charger %s", en = "build: cannot load %s" },
    build_bilan      = { fr = "build appliqué (%s)", en = "build applied (%s)" },
    build_echec      = { fr = " ; ÉCHEC : %s (détails dans UE4SS.log)", en = "; FAILED: %s (details in UE4SS.log)" },
    etape_niveaux    = { fr = "niveaux", en = "stat levels" },
    etape_capacites  = { fr = "capacités", en = "abilities" },
    etape_crash      = { fr = "crash", en = "crash" },
    etape_affixes    = { fr = "affixes", en = "affixes" },
    etape_boost      = { fr = "boost", en = "boost" },
    etape_ramjet     = { fr = "ramjet", en = "ramjet" },
    etape_pannes     = { fr = "pannes", en = "malfunctions" },
    etape_illimites  = { fr = "crashs illimités", en = "unlimited crashes" },
    type_inconnu     = { fr = "type de véhicule inconnu : %s", en = "unknown vehicle type: %s" },
    incompatible     = { fr = "ce circuit (%s) n'accepte pas ce véhicule (%s)",
                         en = "this track (%s) does not accept this vehicle (%s)" },
    resume           = { fr = "%s, %s tour(s), %s", en = "%s, %s lap(s), %s" },
    lancement        = { fr = "lancement : %s", en = "launching: %s" },
    changement       = { fr = "changement de course : %s", en = "switching race: %s" },
    lancement_ko     = { fr = "impossible de lancer : ni menu principal, ni sous-système Arcade trouvé",
                         en = "cannot launch: neither the main menu nor the Arcade subsystem was found" },
    temps_ok         = { fr = "temps enregistré : %s  (meilleur tour %s)%s", en = "time saved: %s  (best lap %s)%s" },
    temps_ss         = { fr = "  [save state : hors records]", en = "  [save state: not counted for records]" },
    temps_ko         = { fr = "temps %s NON enregistré : impossible d'écrire %s", en = "time %s NOT saved: cannot write %s" },
    section          = { fr = "section depuis l'emplacement %s : %s  (secteur %s → %s)",
                         en = "section from slot %s: %s  (sector %s → %s)" },
    sans_vehicule    = { fr = "emplacement %s : aucun véhicule (il faut être en course)",
                         en = "slot %s: no vehicle (you must be in a race)" },
    sauvegarde       = { fr = "emplacement %s sauvegardé (%.0f km/h)", en = "slot %s saved (%.0f km/h)" },
    vide             = { fr = "emplacement %s vide : sauvegarde d'abord avec %s", en = "slot %s empty: save first with %s" },
    autre_circuit    = { fr = "emplacement %s : il a été pris sur un autre circuit",
                         en = "slot %s: it was saved on another track" },
    retour_ko        = { fr = "emplacement %s : retour impossible (%s)", en = "slot %s: cannot go back (%s)" },
    retour           = { fr = "retour à l'emplacement %s (%.0f km/h) — chrono de section lancé",
                         en = "back to slot %s (%.0f km/h) — section timer started" },
    f6_introuvable   = { fr = "F6 : %s introuvable", en = "F6: %s not found" },
    f6_rien          = { fr = "F6 : aucune course à recommencer (lance d'abord une course depuis la fenêtre)",
                         en = "F6: no race to restart (start a race from the window first)" },
    f6_ok            = { fr = "F6 : restart demandé", en = "F6: restart requested" },
    catalogue_menu   = { fr = "catalogue : va au menu principal du jeu pour le recharger",
                         en = "catalogue: go to the game's main menu to reload it" },
    f5_rien          = { fr = "F5 : aucun choix précédent (utilise la fenêtre)",
                         en = "F5: no previous choice (use the window)" },
    verrou           = { fr = "PracticeMode est inactif : lance l'entraînement depuis la fenêtre PracticeMode "
                               .. "(pare-feu actif). Sans cette protection, le mod ne fait rien.",
                         en = "PracticeMode is inactive: start practice from the PracticeMode window "
                               .. "(firewall on). Without this protection, the mod does nothing." },
    charge           = { fr = "version %s chargée : F6 = recommencer, F7/F8 (+Maj, +Ctrl) ou croix bas/droite = save states (avec le boost)",
                         en = "version %s loaded: F6 = restart, F7/F8 (+Shift, +Ctrl) or D-pad down/right = save states (with boost)" },
    touches          = { fr = { "F7/F8", "Maj+F7/Maj+F8", "Ctrl+F7/Ctrl+F8" },
                         en = { "F7/F8", "Shift+F7/Shift+F8", "Ctrl+F7/Ctrl+F8" } },
    -- Fichiers texte des temps (le .csv, lu par la fenêtre, garde un format fixe)
    txt_entete       = { fr = "Date | Planète | Circuit | Tours | Véhicule | Pilote | Temps | Meilleur tour | Détail des tours | Build",
                         en = "Date | Planet | Track | Laps | Vehicle | Racer | Time | Best lap | Lap times | Build" },
    txt_hors_mod     = { fr = "(course lancée hors PracticeMode)", en = "(race not started from PracticeMode)" },
    txt_tours        = { fr = "%s tour(s)", en = "%s lap(s)" },
    txt_meilleur     = { fr = "meilleur tour %s", en = "best lap %s" },
    txt_detail       = { fr = "tours : %s", en = "laps: %s" },
    txt_build        = { fr = "build : %s", en = "build: %s" },
    sections_entete  = { fr = "Date | Planète | Circuit | Véhicule | Départ | Secteurs | Temps de section",
                         en = "Date | Planet | Track | Vehicle | Start | Sectors | Section time" },
    sections_depart  = { fr = "emplacement %s", en = "slot %s" },
    sections_secteur = { fr = "secteur %s → %s", en = "sector %s → %s" },
}

-- Relit echange/langue.txt (« fr » ou « en » ; sinon on garde la langue actuelle)
local function LireLangue()
    local f = io.open(FICHIER_LANGUE, "r")
    if not f then
        return
    end
    local code = (f:read("*l") or ""):match("^%s*(%a+)")
    f:close()
    if code and MESSAGES.charge[code] then
        langue = code
    end
end

-- Le message `cle` dans la langue choisie, avec ses valeurs
local function Traduire(cle, ...)
    local m = MESSAGES[cle]
    if not m then
        return cle
    end
    local modele = m[langue] or m.fr
    if select("#", ...) == 0 then
        return modele
    end
    return string.format(modele, ...)
end

-- ─────────────────────────────────────────────────────────────────────────
--  VERROU DE SÉCURITÉ (voir CONFIG.Verrou)
--
--   fenêtre PracticeMode ──► script pare-feu (administrateur) ──► pare-feu.txt = « actif »
--                                                                        │
--   mod : chaque action (F5, F6, F7/F8, manette, lancement) ◄── lit ─────┘
--         « actif » ? oui → l'action se fait ; non → message, rien d'autre
-- ─────────────────────────────────────────────────────────────────────────
local FICHIER_PARE_FEU = CONFIG.DossierEchange .. "pare-feu.txt"
local verrou = { protege = false, luA = nil, messageA = nil }

local function SessionProtegee()
    if not CONFIG.Verrou then
        return true
    end
    local maintenant = os.clock()
    if verrou.luA == nil or maintenant - verrou.luA >= CONFIG.Verrou_Relecture then
        verrou.luA = maintenant
        local etat = ""
        local f = io.open(FICHIER_PARE_FEU, "r")
        if f then
            etat = f:read("*a") or ""
            f:close()
        end
        -- (le script PowerShell écrit en UTF-8 avec BOM : on l'enlève)
        etat = etat:gsub("^\239\187\191", ""):match("^%s*(.-)%s*$")
        verrou.protege = (etat == "actif")
    end
    return verrou.protege
end

-- ─────────────────────────────────────────────────────────────────────────
--  OUTILS
-- ─────────────────────────────────────────────────────────────────────────

-- Écrit un message dans le journal d'UE4SS ET dans etat.txt (pour la fenêtre).
local function Journal(message)
    print("[PracticeMode] " .. message .. "\n")
    local f = io.open(FICHIER_ETAT, "w")
    if f then
        f:write(os.date("%H:%M:%S") .. "  " .. message)
        f:close()
    end
end

-- Vrai si l'objet existe et est encore valide. Appeler une fonction sur un
-- objet détruit ferait planter le jeu, et pcall ne protège PAS de ce genre
-- de plantage : il faut toujours vérifier AVANT d'appeler.
local function EstValide(objet)
    return objet ~= nil and objet:IsValid()
end

-- Exécute une tâche en attrapant toute erreur Lua, notée une seule fois par
-- message dans le journal. Une erreur Lua qui remonte jusqu'à UE4SS peut
-- déstabiliser le jeu (crash du 10/10) : TOUTES les tâches (boucles, touches,
-- manette, délais) passent donc par ici.
local erreursVues = {}
local function Proteger(nom, tache, ...)
    local ok, err = pcall(tache, ...)
    if not ok then
        local message = nom .. " : " .. tostring(err)
        if not erreursVues[message] then
            erreursVues[message] = true
            print("[PracticeMode]    ERREUR " .. message .. "\n")
        end
    end
    return ok
end

-- Vrai si l'action peut se faire (session protégée) ; sinon explique
-- pourquoi dans le journal et la fenêtre (au plus une fois toutes les 5 s).
local function Autorise()
    if SessionProtegee() then
        return true
    end
    local maintenant = os.clock()
    if verrou.messageA == nil or maintenant - verrou.messageA > 5 then
        verrou.messageA = maintenant
        Journal(Traduire("verrou"))
    end
    return false
end

-- Cherche un objet du jeu par son chemin complet. Renvoie nil s'il n'existe pas.
local function Trouver(chemin, description)
    local objet = StaticFindObject(chemin)
    if EstValide(objet) then
        return objet
    end
    Journal(Traduire("introuvable", description, tostring(chemin)))
    return nil
end

-- Appelle une fonction du jeu en attrapant les erreurs Lua.
local function Appeler(objet, nomFonction, ...)
    local args = { ... }
    local ok, erreur = pcall(function()
        objet[nomFonction](objet, table.unpack(args))
    end)
    if not ok then
        Journal(Traduire("erreur_pendant", nomFonction, tostring(erreur)))
    end
    return ok
end

-- Chemin d'un objet, sans le nom de classe que GetFullName met devant.
local function Chemin(objet)
    local complet = objet:GetFullName()
    return complet:match("^%S+%s+(.+)$") or complet
end

-- Lit une propriété texte (FText ou FString) sans jamais faire échouer l'export.
local function Texte(objet, propriete)
    local ok, valeur = pcall(function() return objet[propriete]:ToString() end)
    return ok and valeur or ""
end

-- Textes dans les deux langues (v0.9.4) : un texte du jeu (FText) s'affiche
-- dans la langue du jeu, mais garde aussi sa version d'ORIGINE, celle dans
-- laquelle les développeurs l'ont écrit (en général l'anglais). Le moteur la
-- donne avec KismetTextLibrary.GetTextSourceString : tout se passe en mémoire,
-- sans rien lire dans les fichiers .pak. La fenêtre choisit ensuite la
-- version qui correspond à son bouton FR / EN.
local bibliothequesTextes = {}
local function Bibliotheque(chemin)
    local b = bibliothequesTextes[chemin]
    if not EstValide(b) then
        b = StaticFindObject(chemin)
        bibliothequesTextes[chemin] = b
    end
    return EstValide(b) and b or nil
end

local function ChaineLua(r)
    if r ~= nil and type(r) ~= "string" then
        r = r:ToString()
    end
    return r
end

-- Version d'origine d'un texte du jeu (nil si indisponible)
local function SourceDuTexte(texte)
    if not CONFIG.TextesSource then
        return nil
    end
    local bib = Bibliotheque(CONFIG.BibliothequeTextes)
    if not bib or texte == nil then
        return nil
    end
    local ok, r = pcall(function() return ChaineLua(bib:GetTextSourceString(texte)) end)
    return ok and r or nil
end

local function TexteSource(objet, propriete)
    local ok, texte = pcall(function() return objet[propriete] end)
    return ok and SourceDuTexte(texte) or nil
end

-- Langue actuelle du jeu et langue d'origine de ses textes (« fr », « en »…)
local function LanguesDuJeu()
    local bib = Bibliotheque(CONFIG.BibliothequeLangues)
    local jeu, source = "", ""
    if bib then
        pcall(function() jeu = ChaineLua(bib:GetCurrentLanguage()) or "" end)
        pcall(function() source = ChaineLua(bib:GetNativeCulture(0)) or "" end)   -- 0 = textes du jeu
    end
    return jeu, source
end

-- Lit le nom d'un « tag » de jeu (FGameplayTag), ex. « Vehicle.Standard ».
local function Tag(objet, propriete)
    local ok, valeur = pcall(function() return objet[propriete].TagName:ToString() end)
    return ok and valeur or ""
end

-- Vrai si un véhicule portant le tag `tagVehicule` peut rouler sur un
-- circuit portant le tag `tagCircuit`. Ex. : « Vehicle.Standard.Bike »
-- roule sur « Vehicle.Standard », pas sur « Vehicle.Special.Plane ».
local function Compatible(tagVehicule, tagCircuit)
    return tagVehicule == tagCircuit or tagVehicule:sub(1, #tagCircuit + 1) == tagCircuit .. "."
end

-- Met un texte entre guillemets au format JSON (avec les échappements).
local function JsonTexte(s)
    s = tostring(s or "")
    s = s:gsub("\\", "\\\\"):gsub('"', '\\"'):gsub("\n", "\\n"):gsub("\r", "\\r"):gsub("\t", "\\t")
    return '"' .. s .. '"'
end

-- Liste les classes de capacités.
-- v0.6 remontait la « parenté » des classes avec GetSuperStruct : 0 résultat
-- sur ce jeu. v0.7 : classes repérées par leur nom (BP_Ability_…_C), trouvées
-- en fait grâce au secours ForEachUObject, retiré en v0.9.2 (crash du 10/10)
-- → 0 capacité. v0.9.4 : on lit les listes que le jeu tient lui-même :
--
--   GfnAbilityList.All             toutes les capacités (liste du jeu)
--   VehicleBuildDef.AbilitySlots   les capacités de chaque build du jeu
--   VehicleBuildDef.CrashAbility   leur capacité de crash
--   classes BP_Ability_…_C         celles que FindAllOf trouve (souvent aucune)
--   <capacité>.CanUpgradeTo        puis les versions améliorées de chacune
--
-- Chaque classe est confirmée avec IsA sur son objet par défaut (CDO).
-- Renvoie la liste, et un tableau nom → vrai pour les capacités de crash.
local function ListeCapacites()
    local classeCapacite = StaticFindObject(CONFIG.CheminClasseCapacite)
    local classeCrash = StaticFindObject(CONFIG.CheminClasseCrash)
    local vues, candidates = {}, {}
    local parSource = { liste = 0, builds = 0, blueprints = 0, ameliorations = 0 }

    -- Ajoute une classe une seule fois (repérée par son chemin)
    local function Ajouter(classe, source)
        if not EstValide(classe) then
            return
        end
        local ok, chemin = pcall(Chemin, classe)
        if ok and not vues[chemin] then
            vues[chemin] = true
            table.insert(candidates, classe)
            parSource[source] = parSource[source] + 1
        end
    end
    -- Ajoute chaque classe d'une liste du jeu (TArray de classes)
    local function AjouterListe(liste, source)
        pcall(function()
            liste:ForEach(function(_, element)
                Ajouter(element:get(), source)
            end)
        end)
    end

    for _, l in ipairs(FindAllOf(CONFIG.Capacites_Liste) or {}) do
        if EstValide(l) then
            AjouterListe(l[CONFIG.Capacites_ListeToutes], "liste")
        end
    end
    for _, b in ipairs(FindAllOf(CONFIG.Capacites_Builds) or {}) do
        if EstValide(b) then
            AjouterListe(b[CONFIG.Build_Capacites], "builds")
            pcall(function() Ajouter(b[CONFIG.Build_Crash], "builds") end)
        end
    end
    for _, c in ipairs(FindAllOf("BlueprintGeneratedClass") or {}) do
        if EstValide(c) then
            local ok, nom = pcall(function() return c:GetFName():ToString() end)
            if ok and nom:sub(1, #CONFIG.PrefixeCapacite) == CONFIG.PrefixeCapacite and nom:sub(-2) == "_C" then
                Ajouter(c, "blueprints")
            end
        end
    end
    -- Versions améliorées : la liste grandit pendant qu'on la parcourt (voulu)
    local i = 1
    while i <= #candidates do
        local classe = candidates[i]
        pcall(function()
            AjouterListe(classe:GetCDO()[CONFIG.Capacites_Ameliorations], "ameliorations")
        end)
        i = i + 1
    end
    -- (Il n'y a VOLONTAIREMENT pas de parcours de tous les objets avec
    -- ForEachUObject : le 10/10, il a fait planter le jeu après un Ctrl+R.)

    local liste, crashParNom = {}, {}
    for _, classe in ipairs(candidates) do
        local nom = classe:GetFName():ToString()
        local estCapacite, estCrash = true, nom:find(CONFIG.MotCleCrash) ~= nil
        pcall(function()
            local cdo = classe:GetCDO()
            if EstValide(classeCapacite) then estCapacite = cdo:IsA(classeCapacite) end
            if EstValide(classeCrash) then estCrash = cdo:IsA(classeCrash) end
        end)
        if estCapacite then
            table.insert(liste, classe)
            if estCrash then
                crashParNom[nom] = true
            end
        end
    end
    print(string.format("[PracticeMode]    capacités : %d classes candidates (liste du jeu %d, builds %d, "
                        .. "blueprints %d, améliorations %d), %d retenues\n", #candidates, parSource.liste,
                        parSource.builds, parSource.blueprints, parSource.ameliorations, #liste))
    return liste, crashParNom
end

-- Lit une table « texte → entier » du jeu (TMap<FString, int32>) et la
-- renvoie au format JSON, ex. {"perc": 10}. Sert aux valeurs des affixes.
local function CarteEnJson(objet, propriete)
    local morceaux = {}
    pcall(function()
        objet[propriete]:ForEach(function(cle, valeur)
            local k = cle:get()
            if type(k) ~= "string" then k = k:ToString() end
            table.insert(morceaux, JsonTexte(k) .. ": " .. tostring(valeur:get()))
        end)
    end)
    return { json = "{" .. table.concat(morceaux, ", ") .. "}" }
end

-- Lit une table « numéro → texte » du jeu (TMap<enum, FText>) au format JSON,
-- ex. {"0": "Maniabilité"}. Sert aux noms des stats dans VehicleUIConfig.
-- `source` = vrai : la version d'origine des textes (voir SourceDuTexte)
local function CarteTextesEnJson(objet, propriete, source)
    local morceaux = {}
    pcall(function()
        objet[propriete]:ForEach(function(cle, valeur)
            local k = cle:get()
            local v = valeur:get()
            if source then
                v = SourceDuTexte(v)
            elseif type(v) ~= "string" then
                v = v:ToString()
            end
            if v ~= nil then
                table.insert(morceaux, JsonTexte(tostring(k)) .. ": " .. JsonTexte(v))
            end
        end)
    end)
    return "{" .. table.concat(morceaux, ", ") .. "}"
end

-- ─────────────────────────────────────────────────────────────────────────
--  EXPORT DU CATALOGUE (circuits, planètes, véhicules, pilotes, capacités, affixes)
--  À appeler dans le fil du jeu, au menu principal (tout y est chargé).
-- ─────────────────────────────────────────────────────────────────────────
local function ExporterCatalogue()
    local lignes = { "{" }

    -- Une section JSON : une liste d'objets, un par ligne.
    -- `source` est soit un nom de classe (on prend tous ses objets),
    -- soit directement une liste d'objets.
    local function Section(nom, source, champs, derniere)
        local objets = source
        if type(source) == "string" then
            objets = FindAllOf(source) or {}
        end
        local elements = {}
        for _, o in ipairs(objets) do
            if EstValide(o) then
                local nomObjet = o:GetFName():ToString()
                if not nomObjet:find("^Default__") then
                    local morceaux = { '"chemin": ' .. JsonTexte(Chemin(o)),
                                       '"nom": ' .. JsonTexte(nomObjet) }
                    for cle, lecteur in pairs(champs) do
                        local ok, v = pcall(lecteur, o)
                        if ok and v ~= nil then
                            if type(v) == "string" then
                                v = JsonTexte(v)
                            elseif type(v) == "table" and v.json then
                                v = v.json          -- valeur déjà au format JSON
                            else
                                v = tostring(v)
                            end
                            table.insert(morceaux, '"' .. cle .. '": ' .. v)
                        end
                    end
                    table.insert(elements, "    {" .. table.concat(morceaux, ", ") .. "}")
                end
            end
        end
        table.insert(lignes, '  "' .. nom .. '": [')
        table.insert(lignes, table.concat(elements, ",\n"))
        table.insert(lignes, derniere and "  ]" or "  ],")
        return #elements
    end

    local nbC = Section("circuits", CONFIG.ClassesCatalogue.Circuits, {
        affiche = function(o) return Texte(o, "PlayerFacingName") end,
        affiche_src = function(o) return TexteSource(o, "PlayerFacingName") end,
        interne = function(o) return Texte(o, "InternalName") end,
        tag     = function(o) return Tag(o, "VehicleTypeTag") end,
        tours   = function(o) return o.DefaultLapCount end,
        p2p     = function(o) return o.bIsPointToPoint end,
        inverse = function(o) return o.bIsReverse end,
        mines   = function(o) return o.bHasMines end,
    })
    local nbP = Section("planetes", CONFIG.ClassesCatalogue.Planetes, {
        affiche = function(o) return Texte(o, "PlayerFacingName") end,
        affiche_src = function(o) return TexteSource(o, "PlayerFacingName") end,
    })
    local nbV = Section("vehicules", CONFIG.ClassesCatalogue.Vehicules, {
        affiche = function(o) return Texte(o, "PlayerFacingName") end,
        affiche_src = function(o) return TexteSource(o, "PlayerFacingName") end,
        tag     = function(o) return Tag(o, "ArchetypeTag") end,
    })
    local nbR = Section("pilotes", CONFIG.ClassesCatalogue.Pilotes, {
        affiche = function(o) return Texte(o, "CharacterName") end,
        affiche_src = function(o) return TexteSource(o, "CharacterName") end,
    })

    -- Capacités : classes Blueprint qui descendent de GfnAbility.
    -- Leur nom affiché se lit sur leur « objet par défaut » (CDO).
    local capacites, crashParNom = ListeCapacites()
    local nbA = Section("capacites", capacites, {
        affiche     = function(o) return Texte(o:GetCDO(), "PlayerFacingName") end,
        description = function(o) return Texte(o:GetCDO(), "Description") end,
        affiche_src     = function(o) return TexteSource(o:GetCDO(), "PlayerFacingName") end,
        description_src = function(o) return TexteSource(o:GetCDO(), "Description") end,
        niveau      = function(o) return o:GetCDO().AbilityLevel end,
        crash       = function(o) return crashParNom[o:GetFName():ToString()] == true end,
    })
    -- Affixes : nom, description brute (avec {perc}, {int}…) et les valeurs
    -- qui remplissent ces emplacements, comme le fait le jeu à l'affichage.
    local nbX = Section("affixes", CONFIG.ClasseAffixe, {
        affiche          = function(o) return Texte(o, "PlayerFacingName") end,
        description      = function(o) return Texte(o, "PlayerFacingDescription") end,
        description_def  = function(o) return Texte(o, "FaultyPlayerFacingDescription") end,
        affiche_src         = function(o) return TexteSource(o, "PlayerFacingName") end,
        description_src     = function(o) return TexteSource(o, "PlayerFacingDescription") end,
        description_def_src = function(o) return TexteSource(o, "FaultyPlayerFacingDescription") end,
        perc             = function(o) return CarteEnJson(o, "PercentProperties") end,
        int              = function(o) return CarteEnJson(o, "IntProperties") end,
        perc_def         = function(o) return CarteEnJson(o, "FaultyPercentProperties") end,
        int_def          = function(o) return CarteEnJson(o, "FaultyIntProperties") end,
        rarete           = function(o) return o.Rarity end,
        visible          = function(o) return o.bShowInBuild end,
    })

    -- Noms des stats et des raretés tels qu'affichés en jeu (VehicleUIConfig)
    local ui = FindFirstOf(CONFIG.ClasseConfigUI)
    local langueJeu, langueSource = LanguesDuJeu()
    local champsUI = { '"langue_jeu": ' .. JsonTexte(langueJeu), '"langue_source": ' .. JsonTexte(langueSource) }
    if EstValide(ui) then
        for _, c in ipairs({ { "stats", "PartStatNames" }, { "emplacements", "PartSlotNames" },
                             { "avance_stats", "AdvancedPartStatNames" },
                             { "avance_emplacements", "AdvancedPartSlotNames" },
                             { "raretes", "PartQualityNames" } }) do
            table.insert(champsUI, '"' .. c[1] .. '": ' .. CarteTextesEnJson(ui, c[2]))
            table.insert(champsUI, '"' .. c[1] .. '_src": ' .. CarteTextesEnJson(ui, c[2], true))
        end
        table.insert(champsUI, '"resilience": ' .. JsonTexte(Texte(ui, "ResilianceStatName")))
        table.insert(champsUI, '"resilience_src": ' .. JsonTexte(TexteSource(ui, "ResilianceStatName") or ""))
    else
        print("[PracticeMode]    VehicleUIConfig introuvable : la fenêtre gardera ses propres noms de stats\n")
    end
    print("[PracticeMode]    langues : jeu « " .. langueJeu .. " », textes d'origine « " .. langueSource .. " »\n")
    table.insert(lignes, '  "interface": {' .. table.concat(champsUI, ", ") .. "}")
    table.insert(lignes, "}")

    -- Écriture dans un fichier temporaire puis renommage : la fenêtre ne lit
    -- jamais un fichier à moitié écrit.
    local tmp = FICHIER_CATALOGUE .. ".tmp"
    local f = io.open(tmp, "w")
    if not f then
        Journal(Traduire("ecriture", tmp))
        return
    end
    f:write(table.concat(lignes, "\n"))
    f:close()
    os.remove(FICHIER_CATALOGUE)
    os.rename(tmp, FICHIER_CATALOGUE)
    -- 0 circuit = pas encore chargés : on réessaiera. 0 capacité : quelques
    -- nouveaux essais espacés (le menu finit peut-être de charger), pas plus.
    essaisCatalogue = essaisCatalogue + 1
    prochainEssaiCatalogue = os.clock() + CONFIG.Capacites_Intervalle
    catalogueExporte = nbC > 0 and (nbA > 0 or essaisCatalogue >= CONFIG.Capacites_Essais)
    Journal(Traduire("catalogue", nbC, nbP, nbV, nbR, nbA, nbX))
end

-- ─────────────────────────────────────────────────────────────────────────
--  ÉDITEUR DE BUILD
--  Remplit le build imposé par l'épreuve modèle avec les choix de la fenêtre.
--  Clés lues dans la commande (toutes facultatives) :
--      niveaux=0,3,10,0,5,2          un niveau (0 à 10) par emplacement de stat
--      capacites=<classe>|<classe>   jusqu'à 4 capacités (chemins de classes)
--      crash=<classe>                capacité de crash (vide = aucune)
--      affixes=<affixe>|<affixe>     affixes (chemins d'objets)
--      boost=1  ramjet=1  pannes=1   options (1 = oui, 0 = non)
--      crashs_illimites=1            coupe la santé du véhicule et du mode
-- ─────────────────────────────────────────────────────────────────────────

-- Écrit une ligne dans le journal d'UE4SS seulement (pas dans etat.txt).
local function Detail(message)
    print("[PracticeMode]    " .. message .. "\n")
end

-- « a|b|c » → { "a", "b", "c" }
local function Decouper(texte)
    local res = {}
    for morceau in (texte or ""):gmatch("[^|]+") do
        table.insert(res, morceau)
    end
    return res
end

-- Remplit une liste du jeu (TArray) avec des objets, dans l'ordre.
-- On vide d'abord, puis on écrit les cases 1, 2, 3… une par une : UE4SS
-- agrandit alors la liste d'une case à chaque fois, sans risque.
-- (Écrire directement en case 3 d'une liste vide déborde de la mémoire.)
local function RemplirListe(liste, objets)
    liste:Empty()
    for i, objet in ipairs(objets) do
        liste[i] = objet
    end
end

local function AppliquerBuild(choix, t, modele)
    -- Le build de l'épreuve n'est chargé en mémoire qu'avec l'épreuve : si
    -- besoin, on demande au jeu de le charger.
    local build = StaticFindObject(t.BuildModele)
    if not EstValide(build) then
        pcall(function() LoadAsset(t.BuildModele) end)
        build = StaticFindObject(t.BuildModele)
    end
    if not EstValide(build) then
        Journal(Traduire("build_charge", t.BuildModele))
        return nil
    end
    local bilan, erreurs = {}, {}

    -- Chaque étape est protégée : si l'une échoue, les autres continuent.
    local function Etape(cle, action)
        local nom = Traduire("etape_" .. cle)
        local ok, err = pcall(action)
        if ok then
            table.insert(bilan, nom)
        else
            table.insert(erreurs, nom)
            Detail("build, " .. cle .. " : ERREUR " .. tostring(err))
        end
    end

    -- 1. Niveaux des améliorations de stat (Add remplace la valeur existante)
    if choix.niveaux then
        Etape("niveaux", function()
            local niveaux = {}
            for n in choix.niveaux:gmatch("%d+") do
                table.insert(niveaux, math.min(10, tonumber(n)))
            end
            local carte = build[CONFIG.Build_Niveaux]
            -- Méthode 1 : Add(emplacement, niveau) (crée ou remplace l'entrée)
            local ok, err = pcall(function()
                for emplacement = 0, CONFIG.NbEmplacements - 1 do
                    if niveaux[emplacement + 1] then
                        carte:Add(emplacement, niveaux[emplacement + 1])
                    end
                end
            end)
            -- Méthode 2 (secours) : modifier les entrées déjà présentes une à une
            if not ok then
                Detail("niveaux : Add refusé (" .. tostring(err) .. "), essai par ForEach")
                carte:ForEach(function(cle, valeur)
                    local emplacement = cle:get()
                    if type(emplacement) == "number" and niveaux[emplacement + 1] then
                        valeur:set(niveaux[emplacement + 1])
                    end
                end)
            end
            Detail("niveaux = " .. choix.niveaux)
        end)
    end

    -- 2. Capacités actives
    if choix.capacites then
        Etape("capacites", function()
            local classes = {}
            for _, chemin in ipairs(Decouper(choix.capacites)) do
                local classe = StaticFindObject(chemin)
                if EstValide(classe) then
                    table.insert(classes, classe)
                else
                    Detail("capacité introuvable : " .. chemin)
                end
            end
            RemplirListe(build[CONFIG.Build_Capacites], classes)
            Detail(#classes .. " capacité(s)")
        end)
    end

    -- 3. Capacité de crash
    if choix.crash then
        Etape("crash", function()
            if choix.crash == "" then
                build[CONFIG.Build_Crash] = nil
            else
                local classe = StaticFindObject(choix.crash)
                if EstValide(classe) then
                    build[CONFIG.Build_Crash] = classe
                end
            end
        end)
    end

    -- 4. Affixes (items). On ouvre autant d'emplacements que nécessaire.
    if choix.affixes then
        Etape("affixes", function()
            local affixes = {}
            for _, chemin in ipairs(Decouper(choix.affixes)) do
                local affixe = StaticFindObject(chemin)
                if EstValide(affixe) then
                    table.insert(affixes, affixe)
                else
                    Detail("affixe introuvable : " .. chemin)
                end
            end
            RemplirListe(build[CONFIG.Build_Affixes], affixes)
            build[CONFIG.Build_AffixesAvion]:Empty()
            build[CONFIG.Build_SlotsOuverts] = math.max(#affixes, 4)
            build[CONFIG.Build_SlotsMax] = math.max(#affixes, 10)
            Detail(#affixes .. " affixe(s)")
        end)
    end

    -- 5. Options
    if choix.boost then
        Etape("boost", function() build[CONFIG.Build_Boost] = tonumber(choix.boost) or 1 end)
    end
    if choix.ramjet then
        Etape("ramjet", function() build[CONFIG.Build_Ramjet] = (choix.ramjet == "1") end)
    end
    if choix.pannes then
        Etape("pannes", function() build[CONFIG.Build_Pannes] = (choix.pannes == "1") end)
    end

    -- 6. Crashs illimités : santé coupée dans le build ET dans le mode
    if choix.crashs_illimites then
        Etape("illimites", function()
            local illimite = (choix.crashs_illimites == "1")
            build[CONFIG.Build_Sante] = not illimite
            modele[CONFIG.ProprieteMode][CONFIG.Mode_Sante] = not illimite
        end)
    end

    local message = Traduire("build_bilan", table.concat(bilan, ", "))
    if #erreurs > 0 then
        message = message .. Traduire("build_echec", table.concat(erreurs, ", "))
    end
    Detail(message)
    return build, message
end

-- ─────────────────────────────────────────────────────────────────────────
--  LANCER UNE COURSE À PARTIR D'UN CHOIX
--  choix = { type = "motojet", piste = "/Game/...", tours = 3, pilote = "/Game/...",
--            + les clés du build, voir l'éditeur de build ci-dessus }
-- ─────────────────────────────────────────────────────────────────────────
local function Lancer(choix)
    if not Autorise() then
        return
    end
    local t = CONFIG.Types[choix.type or ""]
    if not t then
        Journal(Traduire("type_inconnu", tostring(choix.type)))
        return
    end
    local archetype = Trouver(t.Archetype, "archétype")
    local modele    = Trouver(t.Modele, "épreuve modèle")
    local build     = Trouver(t.Build, "build")
    local piste     = Trouver(choix.piste, "circuit")
    if not (archetype and modele and build and piste) then
        return
    end

    -- Le circuit accepte-t-il ce type de véhicule ?
    local tagVehicule = Tag(modele, "VehicleTypeTag")
    local tagCircuit  = Tag(piste, "VehicleTypeTag")
    if not Compatible(tagVehicule, tagCircuit) then
        Journal(Traduire("incompatible", tagCircuit, tagVehicule))
        return
    end

    -- 1. Circuit et tours de l'épreuve modèle (en mémoire seulement)
    modele[CONFIG.ProprietePiste] = piste
    local tours = tonumber(choix.tours)
    if tours and tours >= 1 and tours <= 99 then
        modele[CONFIG.ProprieteTours] = math.floor(tours)
    end

    -- 2. Pilote du joueur (facultatif)
    if choix.pilote and choix.pilote ~= "" then
        local pilote = Trouver(choix.pilote, "pilote")
        local liste  = Trouver(CONFIG.ListePilotes, "liste des pilotes")
        if pilote and liste then
            liste[CONFIG.ProprietePilote] = pilote
        end
    end

    -- 3. Build (pièces, stats, options, crashs illimités)
    local buildChoisi, bilanBuild = AppliquerBuild(choix, t, modele)
    if buildChoisi then
        build = buildChoisi
    end

    -- 4. Mémoriser l'épreuve pour le restart (F6)
    local arcade = FindFirstOf(CONFIG.ClasseArcade)
    if EstValide(arcade) then
        arcade[CONFIG.ProprieteDerniere] = modele
    end
    dernierChoix = choix

    local resume = Traduire("resume", piste:GetFName():ToString(), tours or "?", choix.type)
    if bilanBuild then
        resume = resume .. " — " .. bilanBuild
    end

    -- 5. Lancement : depuis le menu principal avec LaunchQuickRace (testé),
    --    sinon (en course) par le voyage Arcade vers l'épreuve modifiée.
    local modeMenu = FindFirstOf(CONFIG.ClasseModeMenu)
    if EstValide(modeMenu) then
        if Appeler(modeMenu, CONFIG.FonctionLancer, archetype, modele, build) then
            Journal(Traduire("lancement", resume))
        end
    elseif EstValide(arcade) then
        if Appeler(arcade, CONFIG.FonctionVoyager, modele) then
            Journal(Traduire("changement", resume))
        end
    else
        Journal(Traduire("lancement_ko"))
    end
end

-- ─────────────────────────────────────────────────────────────────────────
--  ENREGISTREMENT DES TEMPS
-- ─────────────────────────────────────────────────────────────────────────
local UEHelpers = require("UEHelpers")

-- 75.169 → « 1:15.169 »
local function FormatTemps(secondes)
    if type(secondes) ~= "number" or secondes <= 0 then
        return "-"
    end
    local minutes = math.floor(secondes / 60)
    return string.format("%d:%06.3f", minutes, secondes - 60 * minutes)
end

-- Le composant de course du joueur local (nil au menu ou pendant un chargement)
local function ComposantCourseJoueur()
    local controleur = UEHelpers.GetPlayerController()
    if not EstValide(controleur) then
        return nil
    end
    local etat = controleur.PlayerState
    if not EstValide(etat) then
        return nil
    end
    local ok, composant = pcall(function() return etat[CONFIG.Chrono_Composant] end)
    if ok and EstValide(composant) then
        return composant
    end
    return nil
end

-- Ajoute une ligne à la fin d'un fichier ; écrit d'abord l'en-tête si le fichier est neuf.
local function AjouterLigne(chemin, entete, ligne)
    local existe = io.open(chemin, "r")
    if existe then
        existe:close()
    end
    local f = io.open(chemin, "a")
    if not f then
        return false
    end
    if not existe then
        f:write(entete .. "\n")
    end
    f:write(ligne .. "\n")
    f:close()
    return true
end

-- Écrit le temps d'une course terminée dans temps.txt et temps.csv
-- `avecSaveState` : vrai si l'on est revenu à un emplacement pendant la course
-- (le temps est alors noté « save state » et ne compte pas pour les records).
local function EnregistrerTemps(final, meilleur, tours, avecSaveState)
    local c = dernierChoix or {}
    local date = os.date("%Y-%m-%d %H:%M:%S")
    local listeTours = {}
    for _, t in ipairs(tours) do
        table.insert(listeTours, FormatTemps(t))
    end
    local champs = {
        date,
        c.nom_planete or "?",
        c.nom_circuit or Traduire("txt_hors_mod"),
        Traduire("txt_tours", tostring(c.tours or "?")),
        c.nom_vehicule or c.type or "?",
        c.nom_pilote or "?",
        FormatTemps(final) .. (avecSaveState and " (save state)" or ""),
        Traduire("txt_meilleur", FormatTemps(meilleur)),
        Traduire("txt_detail", #listeTours > 0 and table.concat(listeTours, "  ") or "-"),
        Traduire("txt_build", c.resume_build or "?"),
    }
    local okTxt = AjouterLigne(CONFIG.FichierTemps,
        Traduire("txt_entete"),
        table.concat(champs, " | "))
    -- Version tableur : séparateur « ; » (Excel en français), sans le mot « meilleur tour »
    -- (même ordre que l'en-tête CSV ci-dessous)
    local csv = { date, c.nom_planete or "", c.nom_circuit or "", tostring(c.tours or ""),
                  c.nom_vehicule or c.type or "", c.nom_pilote or "", FormatTemps(final),
                  string.format("%.3f", final or 0), FormatTemps(meilleur),
                  table.concat(listeTours, " "), c.resume_build or "", avecSaveState and "oui" or "non" }
    for i, v in ipairs(csv) do
        csv[i] = '"' .. tostring(v):gsub('"', '""') .. '"'
    end
    AjouterLigne(CONFIG.FichierTempsCsv,
        "Date;Planète;Circuit;Nb tours;Véhicule;Pilote;Temps;Secondes;Meilleur tour;Détail des tours;Build;Save state",
        table.concat(csv, ";"))
    local note = avecSaveState and Traduire("temps_ss") or ""
    if okTxt then
        Journal(Traduire("temps_ok", FormatTemps(final), FormatTemps(meilleur), note))
    else
        Journal(Traduire("temps_ko", FormatTemps(final), CONFIG.FichierTemps))
    end
end

-- ─────────────────────────────────────────────────────────────────────────
--  SAVE STATES : outils communs au chrono et aux touches F7/F8
-- ─────────────────────────────────────────────────────────────────────────
local CM_PAR_S_VERS_MPH = 0.0223694   -- Unreal compte en cm/s ; 1 cm/s = 0,0223694 mile/h
local emplacements = {}   -- [1 à 3] = { carte, position, rotation, mph }
local section = nil       -- chrono de section en cours (démarré par un retour F8)

-- Nom de la carte chargée (un emplacement ne sert que sur la carte où il a été pris)
local function NomCarte()
    local ok, nom = pcall(function() return UEHelpers.GetWorld():GetFName():ToString() end)
    return ok and nom or "?"
end

-- Horloge de la course (temps « serveur » du jeu, en secondes)
local function TempsServeur()
    local ok, t = pcall(function() return UEHelpers.GetWorld().GameState:GetServerWorldTimeSeconds() end)
    if ok and type(t) == "number" then
        return t
    end
    return nil
end

-- Joue un son d'interface du jeu (aucune erreur si ça échoue)
local function Son(nomFonction)
    pcall(function()
        local bibliotheque = StaticFindObject(CONFIG.BibliothequeSons)
        local pion = UEHelpers.GetPlayer()
        if EstValide(bibliotheque) and EstValide(pion) then
            bibliotheque[nomFonction](bibliotheque, pion)
        end
    end)
end

-- Écrit un temps de section dans temps/sections.txt
local function EnregistrerSection(s, arrivee, duree)
    local c = dernierChoix or {}
    local ligne = table.concat({
        os.date("%Y-%m-%d %H:%M:%S"),
        c.nom_planete or "?",
        c.nom_circuit or "?",
        c.nom_vehicule or c.type or "?",
        Traduire("sections_depart", s.emplacement),
        Traduire("sections_secteur", tostring(s.secteur), tostring(arrivee)),
        FormatTemps(duree),
    }, " | ")
    AjouterLigne(CONFIG.FichierSections, Traduire("sections_entete"), ligne)
    Journal(Traduire("section", s.emplacement, FormatTemps(duree), tostring(s.secteur), tostring(arrivee)))
    Son(CONFIG.Son_Section)
end

-- Suivi de la course en cours, mis à jour toutes les 0,5 s
local function NouveauSuivi()
    return { fini = false, dernierTour = -1, tours = {}, saveState = false }
end
local suivi = NouveauSuivi()

local function SurveillerChrono()
    local composant = ComposantCourseJoueur()
    if not composant then
        suivi = NouveauSuivi()   -- menu ou chargement (restart, changement de circuit)
        section = nil
        return
    end
    local fini = composant[CONFIG.Chrono_Fini] == true
    local precedent = composant[CONFIG.Chrono_Precedent]

    -- Nouvelle course (restart, changement de circuit) : la course n'est plus
    -- terminée alors qu'elle l'était → on repart de zéro.
    if suivi.fini and not fini then
        suivi = NouveauSuivi()
    end

    -- Un tour vient d'être bouclé : le « temps du tour précédent » a changé
    if type(precedent) == "number" and precedent > 0 and precedent ~= suivi.dernierTour then
        table.insert(suivi.tours, precedent)
        suivi.dernierTour = precedent
    end

    -- Chrono de section (après un retour F8). Au premier passage, on note le
    -- secteur où le véhicule a été replacé ; ensuite on attend qu'il change.
    if section then
        local secteur = composant[CONFIG.Chrono_Secteur]
        if section.secteur == nil then
            section.secteur = secteur
            Detail("section : départ dans le secteur " .. tostring(secteur))
        elseif secteur ~= section.secteur and secteur ~= 255 then
            local debut = composant[CONFIG.Chrono_DebutSecteur]
            if type(debut) == "number" and section.debut then
                EnregistrerSection(section, secteur, debut - section.debut)
            end
            section = nil
        elseif fini then
            local maintenant = TempsServeur()
            if maintenant and section.debut then
                EnregistrerSection(section, "arrivée", maintenant - section.debut)
            end
            section = nil
        end
    end

    -- Arrivée : la course vient de passer à « terminée »
    if fini and not suivi.fini then
        EnregistrerTemps(composant[CONFIG.Chrono_Final], composant[CONFIG.Chrono_Meilleur], suivi.tours,
                         suivi.saveState)
    end
    suivi.fini = fini
end

-- ─────────────────────────────────────────────────────────────────────────
--  SAVE STATES : F7 (sauvegarder) et F8 (revenir), 3 emplacements
-- ─────────────────────────────────────────────────────────────────────────

-- Rotation en degrés → quaternion (même formule que FRotator::Quaternion d'Unreal)
local function RotationVersQuaternion(r)
    local D = math.pi / 360   -- degrés → demi-angle en radians
    local SP, CP = math.sin(r.Pitch * D), math.cos(r.Pitch * D)
    local SY, CY = math.sin(r.Yaw * D), math.cos(r.Yaw * D)
    local SR, CR = math.sin(r.Roll * D), math.cos(r.Roll * D)
    return {
        X = CR * SP * SY - SR * CP * CY,
        Y = -CR * SP * CY - SR * CP * SY,
        Z = CR * CP * SY - SR * SP * CY,
        W = CR * CP * CY + SR * SP * SY,
    }
end

local function NomTouches(n)
    return Traduire("touches")[n] or "?"
end

-- Le « corps physique » du véhicule (son composant racine) et son nom de corps
local NOM_AUCUN = nil
local function Racine(pion)
    local ok, racine = pcall(function() return pion:K2_GetRootComponent() end)
    if ok and EstValide(racine) then
        return racine
    end
    return nil
end
local function NomAucun()
    if NOM_AUCUN == nil then
        NOM_AUCUN = FName("None")
    end
    return NOM_AUCUN
end

-- Vitesse actuelle du véhicule en km/h (pour le journal)
local function KmH(pion)
    local ok, v = pcall(function() return pion:GetVelocity() end)
    if not ok then
        return -1
    end
    return math.sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z) * CM_PAR_S_VERS_MPH * 1.609344
end

-- ── Boost : postcombustion (énergie) et ramjet (chaleur) ──
--
--   pion.VehicleState ─── BoostState        mode : postcombustion (2) ou ramjet (4)
--                     ├── AfterburnerState  0 prête, 1 refroidit, 2 se recharge
--                     ├── AfterburnerEnergy l'énergie de la jauge
--                     ├── RamjetState       0 pas prêt … 3 actif … 6 surchauffe, 7 explosé
--                     └── RamjetHeat, RamjetBypassHeat   les deux chaleurs
--
--   Pour les remettre : pion.BoostComponent:Server_ChangeState(mode)
--                       .Afterburner:Server_UpdateState(état, énergie)
--                       .Ramjet:Server_ChangeHeat({EngineHeat, BypassHeat})
--                       .Ramjet:Server_ChangeState(état)
-- (fonctions « Server_ » : en solo hors ligne, le jeu est son propre serveur,
-- elles s'exécutent directement sur la machine, comme la remise en place.)
local RAMJET_EXPLOSE = 7                   -- jamais rendu : ferait exploser le véhicule
local BOOST_ARRIVEE = { [1] = 2, [3] = 4 } -- « en passage vers » → mode d'arrivée

local function Nombre(x)
    return type(x) == "number" and string.format("%.3f", x) or tostring(x)
end

-- Lit l'état du boost du véhicule. Renvoie nil s'il est illisible.
local function LireBoost(pion)
    local etat = pion[CONFIG.Boost_Etat]
    if not EstValide(etat) then
        return nil
    end
    return {
        mode       = etat.BoostState,
        postEtat   = etat.AfterburnerState,
        energie    = etat.AfterburnerEnergy,
        ramjetEtat = etat.RamjetState,
        chaleur    = etat.RamjetHeat,
        derivation = etat.RamjetBypassHeat,
    }
end

local function DecrireBoost(b)
    if not b then
        return "boost illisible"
    end
    return string.format("mode %s, postcombustion état %s énergie %s, ramjet état %s chaleur %s / %s",
                         tostring(b.mode), tostring(b.postEtat), Nombre(b.energie),
                         tostring(b.ramjetEtat), Nombre(b.chaleur), Nombre(b.derivation))
end

-- Remet le boost sauvegardé. Chaque étape est essayée séparément et notée
-- dans le journal, pour savoir en jeu laquelle a marché.
local function RendreBoost(pion, b)
    if not (CONFIG.Boost_Actif and b) then
        return
    end
    local faits = {}
    local function Essayer(nom, f)
        local ok, err = pcall(f)
        table.insert(faits, nom .. (ok and " ok" or (" refusé (" .. tostring(err) .. ")")))
    end
    local boost = pion[CONFIG.Boost_Composant]
    if EstValide(boost) then
        local mode = BOOST_ARRIVEE[b.mode] or b.mode
        if mode ~= nil and boost.BoostState ~= mode then
            Essayer("mode " .. tostring(mode), function() boost:Server_ChangeState(mode) end)
        end
        local ramjet = boost.Ramjet
        if EstValide(ramjet) and b.chaleur ~= nil then
            Essayer("chaleur ramjet", function()
                ramjet:Server_ChangeHeat({ EngineHeat = b.chaleur, BypassHeat = b.derivation or 0 })
            end)
            if b.ramjetEtat ~= nil and b.ramjetEtat ~= RAMJET_EXPLOSE and ramjet.RamjetState ~= b.ramjetEtat then
                Essayer("état ramjet " .. tostring(b.ramjetEtat), function() ramjet:Server_ChangeState(b.ramjetEtat) end)
            end
        end
        local post = boost.Afterburner
        if EstValide(post) and b.energie ~= nil then
            Essayer("postcombustion", function() post:Server_UpdateState(b.postEtat or 0, b.energie) end)
        end
    else
        table.insert(faits, "composant de boost introuvable")
    end
    -- Écriture directe dans l'état du véhicule, au cas où les fonctions du
    -- jeu ne suffiraient pas (sans effet si le jeu recalcule ces valeurs)
    local etat = pion[CONFIG.Boost_Etat]
    if CONFIG.Boost_EcritureDirecte and EstValide(etat) then
        Essayer("écriture directe", function()
            if b.energie ~= nil then etat.AfterburnerEnergy = b.energie end
            if b.chaleur ~= nil then etat.RamjetHeat = b.chaleur end
            if b.derivation ~= nil then etat.RamjetBypassHeat = b.derivation end
        end)
    end
    Detail("boost rendu : " .. table.concat(faits, ", "))
end

-- Après le retour : relecture du boost (pour le journal). Avec la remise en
-- place du jeu (méthode « reset »), qui remet sa propre énergie de départ, on
-- rend le boost une seconde fois juste après.
local function SurveillerBoostApresRetour(n, e, methode)
    if not (CONFIG.Boost_Actif and e.boost) then
        return
    end
    if methode == "reset" then
        ExecuteWithDelay(50, function()
            ExecuteInGameThread(function() Proteger("boost après remise en place", function()
                local pion = UEHelpers.GetPlayer()
                if EstValide(pion) then
                    RendreBoost(pion, e.boost)
                end
            end) end)
        end)
    end
    ExecuteWithDelay(CONFIG.Boost_Verification, function()
        ExecuteInGameThread(function() Proteger("boost après retour", function()
            local pion = UEHelpers.GetPlayer()
            if EstValide(pion) then
                Detail(string.format("retour %d, +%d ms : %s (voulu : %s)", n, CONFIG.Boost_Verification,
                                     DecrireBoost(LireBoost(pion)), DecrireBoost(e.boost)))
            end
        end) end)
    end)
end

local function Sauver(n)
    if not Autorise() then
        return
    end
    local pion = UEHelpers.GetPlayer()
    if not EstValide(pion) then
        Journal(Traduire("sans_vehicule", n))
        Son(CONFIG.Son_Erreur)
        return
    end
    local pos = pion:K2_GetActorLocation()
    local rot = pion:K2_GetActorRotation()
    local vit = pion:GetVelocity()
    local mph = math.sqrt(vit.X * vit.X + vit.Y * vit.Y + vit.Z * vit.Z) * CM_PAR_S_VERS_MPH
    -- Rotation propre du véhicule (en degrés/s), si le corps est physique
    local rotationPhysique, physique = nil, false
    local racine = Racine(pion)
    if racine then
        pcall(function()
            physique = racine:IsSimulatingPhysics(NomAucun()) == true
            local w = racine:GetPhysicsAngularVelocityInDegrees(NomAucun())
            rotationPhysique = { X = w.X, Y = w.Y, Z = w.Z }
        end)
    end
    local boost = nil
    if CONFIG.Boost_Actif then
        local ok, lu = pcall(LireBoost, pion)
        boost = ok and lu or nil
    end
    emplacements[n] = {
        carte = NomCarte(),
        position = { X = pos.X, Y = pos.Y, Z = pos.Z },
        rotation = { Pitch = rot.Pitch, Yaw = rot.Yaw, Roll = rot.Roll },
        vitesse = { X = vit.X, Y = vit.Y, Z = vit.Z },   -- vecteur complet (direction + dérive)
        rotationPhysique = rotationPhysique,
        mph = mph,
        boost = boost,                                   -- nil si illisible
    }
    Journal(Traduire("sauvegarde", n, mph * 1.609344))
    Detail(string.format("emplacement %d : position %.0f %.0f %.0f, cap %.1f°, %.1f mph, corps physique : %s, carte %s",
                         n, pos.X, pos.Y, pos.Z, rot.Yaw, mph, tostring(physique), emplacements[n].carte))
    if CONFIG.Boost_Actif then
        Detail(string.format("emplacement %d : %s", n, DecrireBoost(boost)))
    end
    Son(CONFIG.Son_Sauvegarde)
end

-- Rend au véhicule la vitesse (et la rotation) de l'emplacement. Renvoie vrai si ça a marché.
local function RendreVitesse(pion, e)
    local racine = Racine(pion)
    if not racine then
        return false
    end
    local ok = pcall(function()
        racine:SetPhysicsLinearVelocity(e.vitesse, false, NomAucun())
        if e.rotationPhysique then
            racine:SetPhysicsAngularVelocityInDegrees(e.rotationPhysique, false, NomAucun())
        end
    end)
    return ok
end

-- Après un retour, le jeu peut encore « casser » la vitesse pendant quelques
-- instants : on revérifie à plusieurs moments et on la remet si elle est
-- tombée sous la moitié de la vitesse voulue. Tout est noté dans le journal.
local function SurveillerVitesseApresRetour(n, e)
    local voulue = e.mph * 1.609344
    for _, delai in ipairs(CONFIG.SaveState_Relances) do
        ExecuteWithDelay(delai, function()
            ExecuteInGameThread(function() Proteger("vitesse après retour", function()
                local pion = UEHelpers.GetPlayer()
                if not EstValide(pion) then
                    return
                end
                local avant = KmH(pion)
                local note = ""
                if avant < voulue * 0.5 then
                    note = RendreVitesse(pion, e) and string.format(" → remise à %.0f", KmH(pion)) or " → échec"
                end
                Detail(string.format("retour %d, +%d ms : %.0f km/h (voulu %.0f)%s", n, delai, avant, voulue, note))
            end) end)
        end)
    end
end

local function Charger(n)
    if not Autorise() then
        return
    end
    local e = emplacements[n]
    if not e then
        Journal(Traduire("vide", n, NomTouches(n):match("^[^/]+")))
        Son(CONFIG.Son_Erreur)
        return
    end
    if e.carte ~= NomCarte() then
        Journal(Traduire("autre_circuit", n))
        Son(CONFIG.Son_Erreur)
        return
    end
    local pion = UEHelpers.GetPlayer()
    if not EstValide(pion) then
        Journal(Traduire("sans_vehicule", n))
        return
    end
    local ok, err = false, nil
    local methode = CONFIG.SaveState_Methode

    -- Méthode « direct » : téléportation exacte puis vitesse physique rendue
    if methode == "direct" then
        ok, err = pcall(function()
            pion:K2_SetActorLocationAndRotation(e.position, e.rotation, false, {}, true)
        end)
        if ok and not RendreVitesse(pion, e) then
            Detail("retour direct : impossible de rendre la vitesse, essai par la remise en place du jeu")
            methode = "reset"
        elseif not ok then
            Detail("retour direct refusé (" .. tostring(err) .. "), essai par la remise en place du jeu")
            methode = "reset"
        end
    end

    -- Méthode « reset » : remise en place du jeu (comme après un crash)
    if methode == "reset" then
        local transform = {
            Rotation = RotationVersQuaternion(e.rotation),
            Translation = e.position,
            Scale3D = { X = 1, Y = 1, Z = 1 },
        }
        ok, err = pcall(function()
            local reset = pion[CONFIG.SaveState_Composant]
            reset[CONFIG.SaveState_Fonction](reset, transform, e.mph, CONFIG.SaveState_Protection,
                                             CONFIG.SaveState_AuSol, false, false)
        end)
        if not ok then
            -- Dernier secours : simple téléportation (sans la vitesse)
            Detail("retour : " .. CONFIG.SaveState_Fonction .. " refusé (" .. tostring(err) .. "), téléportation simple")
            ok, err = pcall(function() pion:K2_TeleportTo(e.position, e.rotation) end)
        end
    end
    if ok then
        Detail(string.format("retour %d par la méthode « %s » : %.0f km/h juste après", n, methode, KmH(pion)))
        Proteger("boost", RendreBoost, pion, e.boost)
        SurveillerVitesseApresRetour(n, e)
        SurveillerBoostApresRetour(n, e, methode)
    end
    if not ok then
        Journal(Traduire("retour_ko", n, tostring(err)))
        Son(CONFIG.Son_Erreur)
        return
    end
    suivi.saveState = true   -- cette course ne comptera pas pour les records
    section = { emplacement = n, debut = TempsServeur(), secteur = nil }
    Journal(Traduire("retour", n, e.mph * 1.609344))
end

-- ── Manette : croix bas / croix droite ──
-- Le contrôleur du joueur est gardé en mémoire (le rechercher 30 fois par
-- seconde coûterait cher) mais revérifié à chaque lecture, et recherché à
-- nouveau toutes les 3 s : un objet du jeu peut disparaître (changement de
-- carte) et son adresse être réutilisée par un autre objet.
local manette = { controleur = nil, classe = nil, trouveA = 0, enfonce = {} }

local function ControleurManette()
    local c = manette.controleur
    local maintenant = os.clock()
    local valide = c ~= nil and c:IsValid()
                   and c:GetClass():GetFName():ToString() == manette.classe
    if not valide or maintenant - manette.trouveA > 3 then
        c = UEHelpers.GetPlayerController()
        if not EstValide(c) then
            manette.controleur = nil
            return nil
        end
        manette.controleur, manette.trouveA = c, maintenant
        manette.classe = c:GetClass():GetFName():ToString()
    end
    return c
end

-- Vrai si l'on peut agir : en course, pas en pause, course pas terminée
local function EnCoursDeCourse(controleur)
    if not EstValide(UEHelpers.GetPlayer()) then
        return false
    end
    local ok, enPause = pcall(function()
        return UEHelpers.GetGameplayStatics():IsGamePaused(controleur:GetWorld())
    end)
    if ok and enPause then
        return false
    end
    local composant = ComposantCourseJoueur()
    if composant and composant[CONFIG.Chrono_Fini] == true then
        return false
    end
    return true
end

-- Une lecture de la manette : agit au moment où le bouton s'enfonce
local function LireManette()
    local controleur = ControleurManette()
    if not controleur then
        return
    end
    for _, b in ipairs({ { nom = CONFIG.Manette_Sauver, action = Sauver },
                         { nom = CONFIG.Manette_Charger, action = Charger } }) do
        local ok, enfonce = pcall(function()
            return controleur:IsInputKeyDown({ KeyName = FName(b.nom) })
        end)
        enfonce = ok and enfonce == true
        if enfonce and not manette.enfonce[b.nom] and EnCoursDeCourse(controleur) then
            b.action(CONFIG.Manette_Emplacement)
        end
        manette.enfonce[b.nom] = enfonce
    end
end

-- Associe une touche (avec ou sans Maj/Ctrl) à une action.
-- Précaution : on ne sait pas si UE4SS déclenche AUSSI la version « F7 seul »
-- quand on appuie sur Maj+F7. La version sans modificateur attend donc un
-- court instant (CONFIG.DelaiTouches) et n'agit que si aucune version avec
-- modificateur n'a été déclenchée entre-temps.
local touchesModifiees = {}
local function LierTouche(touche, modificateurs, action)
    if #modificateurs == 0 then
        RegisterKeyBind(touche, function()
            ExecuteWithDelay(CONFIG.DelaiTouches, function()
                if not touchesModifiees[touche] then
                    ExecuteInGameThread(function() Proteger("touche", action) end)
                end
            end)
        end)
    else
        RegisterKeyBind(touche, modificateurs, function()
            touchesModifiees[touche] = true
            ExecuteWithDelay(CONFIG.DelaiTouches * 3, function()
                touchesModifiees[touche] = false
            end)
            ExecuteInGameThread(function() Proteger("touche", action) end)
        end)
    end
end

-- ─────────────────────────────────────────────────────────────────────────
--  F6 : recommencer la course en cours
-- ─────────────────────────────────────────────────────────────────────────
local function Recommencer()
    if not Autorise() then
        return
    end
    local arcade = FindFirstOf(CONFIG.ClasseArcade)
    if not EstValide(arcade) then
        Journal(Traduire("f6_introuvable", CONFIG.ClasseArcade))
        return
    end
    if not EstValide(arcade[CONFIG.ProprieteDerniere]) then
        Journal(Traduire("f6_rien"))
        return
    end
    if Appeler(arcade, CONFIG.FonctionRecommencer) then
        Journal(Traduire("f6_ok"))
    end
end

-- ─────────────────────────────────────────────────────────────────────────
--  LECTURE DE commande.txt
--  Format : une ligne « clé=valeur » par réglage, ex. :
--      type=motojet
--      piste=/Game/Griffin/Gameplay/Events/Planets/Corgi/Loop_A/TRAK_COR_Loop_A_FWD.TRAK_COR_Loop_A_FWD
--      tours=2
--      pilote=/Game/Griffin/Narrative/CharacterDefs/Racers/DA_Racer_Star.DA_Racer_Star
--  Une ligne « action=catalogue » demande seulement un nouvel export.
-- ─────────────────────────────────────────────────────────────────────────
local function LireCommande()
    local f = io.open(FICHIER_COMMANDE, "r")
    if not f then
        return nil
    end
    local contenu = f:read("*a")
    f:close()
    os.remove(FICHIER_COMMANDE)   -- une commande n'est exécutée qu'une fois
    local choix = {}
    for ligne in contenu:gmatch("[^\r\n]+") do
        local cle, valeur = ligne:match("^%s*([%w_]+)%s*=%s*(.-)%s*$")
        if cle then
            choix[cle] = valeur
        end
    end
    return choix
end

-- Tâche de fond : toutes les 0,5 s, regarde s'il y a une commande, et
-- exporte le catalogue dès que le menu principal est atteint.
-- Ce fil ne touche JAMAIS aux objets du jeu : il renvoie tout le travail
-- dans le fil du jeu avec ExecuteInGameThread.
-- Vrai si l'on est sur la carte du menu principal. On ne se fie pas seulement
-- à FrontEndGameMode : après un passage au menu, il peut traîner en mémoire
-- pendant la course (cause du crash du 10/10 après un Ctrl+R en course).
local function AuMenuPrincipal()
    return NomCarte() == CONFIG.CarteMenu and EstValide(FindFirstOf(CONFIG.ClasseModeMenu))
end

LoopAsync(CONFIG.DelaiScrutation, function()
    LireLangue()
    local choix = LireCommande()
    ExecuteInGameThread(function()
        if not SessionProtegee() then
            if choix then
                Autorise()
            end
            return
        end
        if not catalogueExporte and os.clock() >= prochainEssaiCatalogue and AuMenuPrincipal() then
            Proteger("catalogue", ExporterCatalogue)
        end
        if choix then
            if choix.action == "catalogue" then
                if AuMenuPrincipal() then
                    Proteger("catalogue", ExporterCatalogue)
                else
                    Journal(Traduire("catalogue_menu"))
                end
            else
                Proteger("lancement", Lancer, choix)
            end
        end
        Proteger("chrono", SurveillerChrono)
    end)
    return false   -- false = continuer à boucler
end)

-- ─────────────────────────────────────────────────────────────────────────
--  TOUCHES
--  Les touches sont détectées en dehors du « fil » principal du jeu.
--  ExecuteInGameThread renvoie l'action dans le fil du jeu, seul endroit
--  où l'on peut appeler ses fonctions sans risque.
-- ─────────────────────────────────────────────────────────────────────────
RegisterKeyBind(CONFIG.ToucheRelancer, function()
    ExecuteInGameThread(function() Proteger("F5", function()
        if not Autorise() then
            return
        end
        if dernierChoix then
            Lancer(dernierChoix)
        else
            Journal(Traduire("f5_rien"))
        end
    end) end)
end)

RegisterKeyBind(CONFIG.ToucheRecommencer, function()
    ExecuteInGameThread(function() Proteger("F6", Recommencer) end)
end)

-- Save states : F7/F8, Maj+F7/Maj+F8, Ctrl+F7/Ctrl+F8 pour les emplacements 1, 2, 3
for n, t in ipairs(CONFIG.SaveState_Touches) do
    LierTouche(t.touche, t.modificateurs, function() Sauver(n) end)
    LierTouche(t.charger, t.modificateurs, function() Charger(n) end)
end

-- Save states à la manette (croix bas / droite), lus 30 fois par seconde.
-- Une erreur ici ne doit jamais arrêter la boucle ; elle n'est notée qu'une fois.
LoopAsync(CONFIG.Manette_Delai, function()
    ExecuteInGameThread(function() Proteger("manette", LireManette) end)
    return false
end)

LireLangue()
Journal(Traduire("charge", "0.9.4"))
