--[[
    PracticeMode : mode entraînement pour Star Wars: Galactic Racer
    =================================================================
    Version 2.0.0 (12/10/2026) : version publique (Nexus, après la 0.9.4,
    appelée v1.0 sur Nexus) = la 0.9.9 ci-dessous, plus : adversaires des
    courses de modules (pilotes de module), véhicule du pilote en
    contre-la-montre, compatibilité avec la mise à jour du jeu du 12/10/2026.

    Version 0.9.9 (12/10/2026) : tout le Lua du mod tourne dans le fil du
    jeu (voir FILS D'EXÉCUTION : piste n° 1 des plantages), vrais noms et
    valeurs des difficultés du jeu (Recrue, Pilote, As, Antagoniste), styles
    et buffs des pilotes chargés depuis le disque (une miette par objet),
    apparence du véhicule du pilote choisi (voir APPARENCE DU VÉHICULE DU
    PILOTE ; commentaire Nexus : tous les podracers identiques).

    Version 0.9.8 (12/10/2026) : classement en ligne, dans la FENÊTRE
    seulement (bouton « Publier ce temps », onglet « Classement ») : le mod
    ne change pas, il ne parle à aucun serveur. Seul ce numéro de version suit.

    Version 0.9.7 (11/10/2026) : difficulté des IA (Cadet, Pilote, As,
    Champion, voir « DIFFICULTÉ DES IA »), plus de freezes en course (joueur
    et carte trouvés sans parcourir les objets), LoadAsset coupé.

    Version 0.9.6 (11/10/2026) : adversaires IA (course personnalisée du jeu,
    LaunchCustomRace, voir « COURSE AVEC ADVERSAIRES IA »), build et buffs du
    pilote choisi (voir « STYLES DES PILOTES » et « BUFFS DU PILOTE »), place
    à l'arrivée et build complet noté avec chaque temps.

    Version 0.9.5 (11/10/2026) : verrou renforcé (Steam doit être hors ligne,
    en plus du pare-feu) et exploration en lecture seule des épreuves et des
    modes (préparation des adversaires IA, voir EXPLORATION).

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
-- Fichier de Steam qui dit si Steam est hors ligne (config/loginusers.vdf),
-- écrit lui aussi par le launcher à l'installation (voir SteamHorsLigne)
local FICHIER_STEAM = "ECRIT-PAR-LE-LAUNCHER"

local CONFIG = {
    -- Dossier partagé avec la fenêtre
    DossierEchange = DOSSIER_PRACTICEMODE .. "echange/",

    -- Fichiers des temps (hors du dossier du jeu : ils survivent à la fin de session)
    FichierTemps    = DOSSIER_PRACTICEMODE .. "temps/temps.txt",
    FichierTempsCsv = DOSSIER_PRACTICEMODE .. "temps/temps.csv",

    FichierSections = DOSSIER_PRACTICEMODE .. "temps/sections.txt",

    -- Verrou de sécurité : le mod ne fait RIEN tant que la session n'est pas
    -- protégée : pare-feu du launcher actif (echange/pare-feu.txt = « actif »)
    -- ET Steam hors ligne. Le jeu garde les temps faits hors ligne pour les
    -- envoyer plus tard aux classements : sans ces protections et la
    -- sauvegarde remise à la fin de session, un temps fait avec le mod
    -- pourrait partir en ligne. Ne pas désactiver.
    -- (11/10/2026 : fenêtre fermée pendant une session, puis jeu relancé avec
    -- Steam EN LIGNE : le pare-feu a tenu, d'où la 2e condition en plus.)
    Verrou          = true,
    Verrou_Relecture = 2,   -- secondes entre deux lectures de pare-feu.txt et de Steam
    Joueur_Recherche = 5,   -- secondes entre deux recherches de la GameInstance (si pas encore trouvée)

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
    Touches_Delai        = 20,      -- ms entre deux passages de la boucle des touches (LierTouche)

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
    Boost_EtatIntermediaire = true, -- postcombustion : passer par un autre état avant le bon (énergie)
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
    -- Exploration en lecture seule des épreuves et modes (préparation des
    -- adversaires IA, voir ExplorerEpreuves) → echange/epreuves.json
    -- 11/10/2026 : la 1re version a fait planter le jeu (UE4SS, lecture à
    -- l'adresse 0) juste après le catalogue, 2 fois sur 2, sans doute en lisant
    -- une référence « souple » (TSoftObjectPtr), un type qu'UE4SS ne gère pas.
    -- Désormais : aucune référence souple lue (comptées seulement), et chaque
    -- étape est notée dans echange/exploration-etape.txt AVANT d'être faite :
    -- si le jeu plante, la session suivante saute cette étape (voir EtapesInterdites).
    Exploration                  = true,
    Exploration_Souples          = false,   -- lire les TSoftObjectPtr : a fait planter le jeu
    Exploration_Rythmes          = false,   -- TMap de réglages contenant des TOptional : prudence
    Exploration_ClasseModes      = "GameModeVariantDef",
    Exploration_ClasseListes     = "GfnEventList",
    Exploration_ClassesEpreuves  = { "RaceEventDef", "ArcadeEventDef", "ShakedownEventDef",
                                     "VehicleTestEventDef", "PlaneMemoryRaceEventDef" },
    Exploration_ClassePilotes    = "RacerDef",                                   -- styles, traits
    Exploration_ClassesPilotesIA = { "PvpRacerSetup", "CampaignRacerSetup" },    -- builds par véhicule
    Exploration_ClasseParcours   = "PvpRunDef",                                  -- modes multijoueur
    Exploration_StyleJoueur      = "RacerStyle",                                 -- sur GfnPlayerState
    Exploration_Charger          = true,   -- charger un trait pas encore chargé, pour lire son nom
    -- Noms du jeu dans la langue de la fenêtre (voir TraduireCatalogue)
    Traduction           = true,
    Traduction_Attente   = 1000,   -- ms entre deux vérifications que les textes ont changé de langue
    Traduction_Essais    = 4,
    -- Textes dans leur langue d'origine (voir SourceDuTexte) : ne marche pas à
    -- travers UE4SS (11/10/2026 : renvoie le texte affiché) → remplacé par Traduction
    TextesSource         = false,
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

    -- Adversaires IA (v0.9.6) : la « course personnalisée » du jeu
    -- (FrontEndGameMode.LaunchCustomRace, la fonction du menu Quick Race des
    -- développeurs ; elle a bien du code dans la version vendue, vérifié le
    -- 11/10/2026). On lui donne un mode de course dont on règle la grille :
    -- joueur + N adversaires, tous du même type de véhicule que le joueur.
    -- Pas d'épreuve Arcade → pas de classement en ligne lié à la course.
    FonctionCourseIA = "LaunchCustomRace",   -- (archétype, mode, circuit, conditions, build, build debug)
    ModesIA = {
        standard = "/Game/Griffin/Gameplay/Campaign/GameModes/GMV_Race.GMV_Race",             -- grille « au choix du joueur »
        avion    = "/Game/Griffin/Gameplay/Campaign/GameModes/GMV_PlaneRaces.GMV_PlaneRaces", -- grille de modules
    },
    AdversairesMax   = 11,                    -- 12 véhicules au départ, comme la grille complète du jeu
    -- Adversaires des courses de modules (v0.9.9). LaunchCustomRace prend ses
    -- IA dans DA_CharacterList.Opponents : 11 pilotes de speeder, chacun avec
    -- son véhicule préféré, même sur un circuit de modules (vu le 12/10/2026 :
    -- motos et skimmers dans une course de pods). Pour une course de modules,
    -- le mod y met les pilotes de module des listes ci-dessous (sans le pilote
    -- du joueur), puis remet la liste du jeu au retour au menu.
    Adversaires_Liste   = "Opponents",
    Adversaires_Modules = { "PvpPlaneInstantActionPlayable", "PvpPlanePlayable" },
    Tours_Defaut     = "DefaultLapCount",     -- tours d'un circuit (LaunchCustomRace n'a pas de nombre de tours)
    Chrono_Position  = "EventPosition",       -- place du joueur dans la course

    -- Buffs du pilote (v0.9.6) : les traits de son style, ajoutés au joueur en
    -- course par la file d'attente du gestionnaire de passifs du jeu
    -- (PlayerState.PassiveManagerComponent.PassivesToAdd). Voir STYLES_PILOTES.
    Styles              = true,
    ClasseStyle         = "RacerStyle",
    Passifs_Composant   = "PassiveManagerComponent",
    Passifs_AAjouter    = "PassivesToAdd",
    Passifs_Liste       = "PassiveList",
    Passifs_Controle    = 2000,               -- ms : délai avant de vérifier que les buffs sont actifs
    -- LoadAsset d'UE4SS (charger depuis le disque un objet pas encore en
    -- mémoire). Coupé en v0.9.6/0.9.8 : suspect du plantage du 11/10/2026 à
    -- 19:20 (Lua corrompu, au menu). Sans lui, AUCUN build ni trait des
    -- styles n'était en mémoire au menu (0 sur 21 et 0 sur 50, le 11/10 à
    -- 21:10) : styles et buffs ne marchaient pas. RALLUMÉ en v0.9.9 :
    --   - LoadAsset marche dans ce jeu (build de l'épreuve contre-la-montre,
    --     chargé ainsi à chaque lancement depuis la v0.9.4) ;
    --   - le plantage de 19:20 ressemble à la course entre deux fils (voir
    --     FILS D'EXÉCUTION), corrigée en v0.9.9 ;
    --   - chaque objet a sa miette (ChargerProtege) : s'il fait planter le
    --     jeu, la session suivante saute cet objet seulement ;
    --   - au menu, quelques objets par passage (Chargement_ParPassage), pour
    --     ne pas figer le jeu d'un coup.
    ChargementAssets    = true,
    Chargement_ParPassage = 4,                -- objets chargés par passage de 0,5 s, au menu

    -- Apparence du véhicule du pilote choisi (v0.9.9). Commentaire Nexus :
    -- « tous les podracers sont le même véhicule ». L'épreuve modèle impose
    -- son véhicule, apparence comprise (EventMode.CustomVehicle.
    -- CustomisationPresetClass : référence souple, jamais lue). Chaque pilote
    -- a pourtant la sienne par type de véhicule : RacerDef.
    -- PreferredCustomisationForVehicleArchetype (références directes).
    -- Voir APPARENCE DU VÉHICULE DU PILOTE.
    Apparence            = true,
    -- Demander au jeu la recette du pilote (Client_SetOverrideVehicleRecipe) :
    -- COUPÉ. Essayé le 12/10/2026 : aucun effet (le véhicule est déjà construit).
    Apparence_Appliquer  = false,             -- false = seulement noter dans le journal
    Apparence_Archetypes = { voiture = 0, avion = 1, motojet = 2, skimmer = 3 },   -- EVehicleArchetype
    Apparence_Preferees  = "PreferredCustomisationForVehicleArchetype",            -- RacerDef → archétype → recette
    Apparence_Etat       = "EventRecipeState_Replication",                         -- GameState → Racers
    Apparence_Composant  = "VehicleCustomisationComponent",                       -- PlayerState → composant
    Apparence_Fonction   = "Client_SetOverrideVehicleRecipe",                     -- (classe de recette)
    -- Couper le véhicule imposé par l'épreuve modèle (contre-la-montre) quand le
    -- pilote a le sien : COUPÉ. Essayé le 12/10/2026 : le jeu prend alors le
    -- véhicule de la campagne du joueur (un landspeeder dans une course de pods).
    -- En contre-la-montre, tous les pilotes gardent donc le véhicule de l'épreuve.
    Apparence_CouperImpose   = false,
    -- Contre-la-montre en MODULE avec un pilote qui a son propre pod, lancé du
    -- menu : course personnalisée seule (LaunchCustomRace, grille = le joueur),
    -- comme une course avec IA, où le jeu donne bien au joueur le pod de son
    -- pilote (vu le 12/10/2026 : Onion → PRE_Plane_Dearc). Pas d'épreuve
    -- Arcade, donc F6 → « Recommencer » du menu pause. Commentaire Nexus :
    -- « tous les podracers sont le même véhicule ».
    Modules_CourseSeule      = true,
    Apparence_VehiculeImpose = "bUseCustomVehicle",                               -- EventMode de l'épreuve
    Apparence_Controle   = 2000,              -- ms : relecture après la demande

    -- Difficulté des IA (v0.9.7) : les 4 du mode histoire (Recrue, Pilote, As,
    -- Antagoniste ; en anglais Cadet, Pilot, Ace, Champion, d'où les clés
    -- ci-dessous), pour les courses avec adversaires. Le mod change les réglages
    -- « Ai… » de la base de réglages de course (URaceTuneData), commune au
    -- joueur et aux IA, juste avant le lancement, et la remet comme avant au
    -- retour au menu. Voir DIFFICULTÉ DES IA.
    Difficulte            = true,
    Difficulte_Liste      = "CampaignDifficulties",       -- GameInstance → les 4 difficultés du mode histoire
    Difficulte_Composant  = "FallbackGameTuneComponent",  -- GameInstance → son GameTuneComponent
    Difficulte_Base       = "RaceTuneData",               -- GameTuneComponent → sa base (URaceTuneData)
    Difficulte_ClasseBase = "RaceTuneData",               -- classe de ces bases (toutes celles en mémoire)
    Difficulte_ClasseDef  = "CampaignDifficultyDef",      -- (noms dans la langue de la fenêtre)
    -- Écarts appliqués à la base, par niveau. Un réglage « …Multiplier » est
    -- multiplié, les autres (« …Modifier », en secondes) reçoivent un ajout :
    --   AiMaxTimeAheadModifier, AiMinTimeAheadModifier : avance permise aux IA sur le joueur
    --   AiAggressionVPlayerChanceMultiplier, …CooldownMultiplier : agressivité envers le joueur
    --   AiAbilityChanceMultiplier : utilisation de leurs capacités
    -- Calées sur le jeu (v0.9.9, d'après echange\difficultes.json du 11/10/2026).
    -- En course libre, seule Recrue change vraiment les IA dans le jeu : sa
    -- faveur (TNS_Diff_AiEasy) fait AiMaxTimeAheadMultiplier ×0,65 et
    -- AiMinTimeAheadModifier −3 s, repris tels quels. As (+4) et Antagoniste
    -- ne touchent que la puissance des IA de la campagne (AiPowerLevelModifier)
    -- et des passifs des adversaires (illisibles) : le mod les remplace par une
    -- avance et une agressivité qui suivent les barres affichées par le jeu
    -- (compétence 0,25 / 0,5 / 0,8 / 1 ; agression 0,25 / 0,5 / 0,5 / 1).
    Difficulte_Niveaux = {
        cadet    = { AiMaxTimeAheadMultiplier = 0.65, AiMinTimeAheadModifier = -3.0,
                     AiAggressionVPlayerChanceMultiplier = 0.5, AiAggressionVPlayerCooldownMultiplier = 1.5,
                     AiAbilityChanceMultiplier = 0.5 },
        pilote   = {},
        as       = { AiMaxTimeAheadModifier = 1.0, AiMinTimeAheadModifier = 1.0,
                     AiAbilityChanceMultiplier = 1.25 },
        champion = { AiMaxTimeAheadModifier = 2.0, AiMinTimeAheadModifier = 2.0,
                     AiAggressionVPlayerChanceMultiplier = 2.0, AiAggressionVPlayerCooldownMultiplier = 0.5,
                     AiAbilityChanceMultiplier = 1.5 },
    },

    -- Touches
    ToucheRelancer    = Key.F5,
    ToucheRecommencer = Key.F6,

    -- Délai entre deux lectures de commande.txt (millisecondes)
    DelaiScrutation = 500,
}

local FICHIER_CATALOGUE = CONFIG.DossierEchange .. "catalogue.json"
local FICHIER_COMMANDE  = CONFIG.DossierEchange .. "commande.txt"
local FICHIER_ETAT      = CONFIG.DossierEchange .. "etat.txt"

-- ─────────────────────────────────────────────────────────────────────────
--  STYLES DES PILOTES (v0.9.6)
--  Chaque pilote a un « style » (RacerStyle) : ses traits (buffs passifs),
--  ses capacités de départ et, en multijoueur, un build imposé avec ses
--  vraies stats. Le style lui-même se lit sans souci (RacerDef →
--  PvpRacerStyles / CampaignRacerStyle), mais ce qu'il contient est rangé
--  en références « souples », qu'UE4SS ne sait pas lire sans faire planter
--  le jeu. Ce contenu est donc relevé hors du jeu, en lecture seule
--  (outils/styles_pilotes.py), et recopié ci-dessous.
-- ─────────────────────────────────────────────────────────────────────────
-- DEBUT STYLES_PILOTES (généré par outils/styles_pilotes.py, ne pas modifier à la main)
local STYLES_PILOTES = {
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Abilities_Lv1.CAM_Style_Abilities_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Mine/BP_Ability_Mine.BP_Ability_Mine_C", "/Game/Griffin/Gameplay/Abilities/Repair/BP_Ability_Repair.BP_Ability_Repair_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithMine.TRT_StartWithMine", "/Game/Griffin/Gameplay/Passives/TRT_StartWithRepair.TRT_StartWithRepair" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Abilities_Lv2.CAM_Style_Abilities_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Mine/BP_Ability_Mine.BP_Ability_Mine_C", "/Game/Griffin/Gameplay/Abilities/Repair/BP_Ability_Repair.BP_Ability_Repair_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithMine.TRT_StartWithMine", "/Game/Griffin/Gameplay/Passives/TRT_StartWithRepair.TRT_StartWithRepair", "/Game/Griffin/Gameplay/Passives/TRT_NoEnergyGainOverchargeImproved.TRT_NoEnergyGainOverchargeImproved" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Abilities_Lv3.CAM_Style_Abilities_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Mine/BP_Ability_Mine.BP_Ability_Mine_C", "/Game/Griffin/Gameplay/Abilities/Repair/BP_Ability_Repair.BP_Ability_Repair_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithMine.TRT_StartWithMine", "/Game/Griffin/Gameplay/Passives/TRT_StartWithRepair.TRT_StartWithRepair", "/Game/Griffin/Gameplay/Passives/TRT_NoEnergyGainOverchargeImproved.TRT_NoEnergyGainOverchargeImproved", "/Game/Griffin/Gameplay/Passives/TRT_AbilitiesReduceAbilityCooldowns.TRT_AbilitiesReduceAbilityCooldowns" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Afterburner_Lv1.CAM_Style_Afterburner_Lv1"] = {
        build = nil,
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StrongerAfterburner.TRT_StrongerAfterburner", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerLastsLonger.TRT_AfterburnerLastsLonger" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Afterburner_Lv2.CAM_Style_Afterburner_Lv2"] = {
        build = nil,
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StrongerAfterburner.TRT_StrongerAfterburner", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerLastsLonger.TRT_AfterburnerLastsLonger", "/Game/Griffin/Gameplay/Passives/TRT_RefillAfterburnerOnOvertake.TRT_RefillAfterburnerOnOvertake" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Afterburner_Lv3.CAM_Style_Afterburner_Lv3"] = {
        build = nil,
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StrongerAfterburner.TRT_StrongerAfterburner", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerLastsLonger.TRT_AfterburnerLastsLonger", "/Game/Griffin/Gameplay/Passives/TRT_RefillAfterburnerOnOvertake.TRT_RefillAfterburnerOnOvertake", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerRefillOnAirtimeAndAdvancedCorner.TRT_AfterburnerRefillOnAirtimeAndAdvancedCorner" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Airborne_Lv1.CAM_Style_Airborne_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Shockwave/BP_Ability_Shockwave_Punch.BP_Ability_Shockwave_Punch_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithVectoredShockwave.TRT_StartWithVectoredShockwave", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerRefillOnPerfectLanding.TRT_AfterburnerRefillOnPerfectLanding" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Airborne_Lv2.CAM_Style_Airborne_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Shockwave/BP_Ability_Shockwave_Punch.BP_Ability_Shockwave_Punch_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithVectoredShockwave.TRT_StartWithVectoredShockwave", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerRefillOnPerfectLanding.TRT_AfterburnerRefillOnPerfectLanding", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerPowerStacksWhenAirborne.TRT_AfterburnerPowerStacksWhenAirborne" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Airborne_Lv3.CAM_Style_Airborne_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Shockwave/BP_Ability_Shockwave_Punch.BP_Ability_Shockwave_Punch_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithVectoredShockwave.TRT_StartWithVectoredShockwave", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerRefillOnPerfectLanding.TRT_AfterburnerRefillOnPerfectLanding", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerPowerStacksWhenAirborne.TRT_AfterburnerPowerStacksWhenAirborne", "/Game/Griffin/Gameplay/Passives/TRT_AllLandingsArePerfect.TRT_AllLandingsArePerfect" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Antagonist_Lv1.CAM_Style_Antagonist_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Disruptor/BP_Ability_Disruptor.BP_Ability_Disruptor_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithDisruptor.TRT_StartWithDisruptor", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForAbilityHits.TRT_EnergyForAbilityHits" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Antagonist_Lv2.CAM_Style_Antagonist_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Disruptor/BP_Ability_Disruptor.BP_Ability_Disruptor_C", "/Game/Griffin/Gameplay/Abilities/Shockwave/BP_Ability_Shockwave.BP_Ability_Shockwave_C", "/Game/Griffin/Gameplay/Abilities/Mine/BP_Ability_Mine.BP_Ability_Mine_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithDisruptor.TRT_StartWithDisruptor", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForAbilityHits.TRT_EnergyForAbilityHits", "/Game/Griffin/Gameplay/Passives/TRT_StartWithAbilities.TRT_StartWithAbilities" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Antagonist_Lv3.CAM_Style_Antagonist_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Disruptor/BP_Ability_Disruptor.BP_Ability_Disruptor_C", "/Game/Griffin/Gameplay/Abilities/Shockwave/BP_Ability_Shockwave.BP_Ability_Shockwave_C", "/Game/Griffin/Gameplay/Abilities/Mine/BP_Ability_Mine.BP_Ability_Mine_C", "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent_Flame.BP_Ability_Vent_Flame_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithDisruptor.TRT_StartWithDisruptor", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForAbilityHits.TRT_EnergyForAbilityHits", "/Game/Griffin/Gameplay/Passives/TRT_StartWithAbilities.TRT_StartWithAbilities", "/Game/Griffin/Gameplay/Passives/TRT_StartWithFlameVent.TRT_StartWithFlameVent" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Battling_Lv1.CAM_Style_Battling_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Disruptor/BP_Ability_Disruptor.BP_Ability_Disruptor_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithDisruptor.TRT_StartWithDisruptor", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForTakedowns.TRT_EnergyForTakedowns" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Battling_Lv2.CAM_Style_Battling_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Disruptor/BP_Ability_Disruptor.BP_Ability_Disruptor_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithDisruptor.TRT_StartWithDisruptor", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForTakedowns.TRT_EnergyForTakedowns", "/Game/Griffin/Gameplay/Passives/TRT_SurgeForTakedowns.TRT_SurgeForTakedowns" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Battling_Lv3.CAM_Style_Battling_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Disruptor/BP_Ability_Disruptor.BP_Ability_Disruptor_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithDisruptor.TRT_StartWithDisruptor", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForTakedowns.TRT_EnergyForTakedowns", "/Game/Griffin/Gameplay/Passives/TRT_SurgeForTakedowns.TRT_SurgeForTakedowns", "/Game/Griffin/Gameplay/Passives/TRT_SurgeForTakedownsUpgrade.TRT_SurgeForTakedownsUpgrade" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Burning_Lv1.CAM_Style_Burning_Lv1"] = {
        build = nil,
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StrongerAfterBurnerAndRamjetWhenBurning.TRT_StrongerAfterBurnerAndRamjetWhenBurning", "/Game/Griffin/Gameplay/Passives/TRT_GainBurningWhenRamjet.TRT_GainBurningWhenRamjet" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Burning_Lv2.CAM_Style_Burning_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent_Flame.BP_Ability_Vent_Flame_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StrongerAfterBurnerAndRamjetWhenBurning.TRT_StrongerAfterBurnerAndRamjetWhenBurning", "/Game/Griffin/Gameplay/Passives/TRT_GainBurningWhenRamjet.TRT_GainBurningWhenRamjet", "/Game/Griffin/Gameplay/Passives/TRT_StartWithFlameVent.TRT_StartWithFlameVent" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Burning_Lv3.CAM_Style_Burning_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent_Flame.BP_Ability_Vent_Flame_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StrongerAfterBurnerAndRamjetWhenBurning.TRT_StrongerAfterBurnerAndRamjetWhenBurning", "/Game/Griffin/Gameplay/Passives/TRT_GainBurningWhenRamjet.TRT_GainBurningWhenRamjet", "/Game/Griffin/Gameplay/Passives/TRT_StartWithFlameVent.TRT_StartWithFlameVent", "/Game/Griffin/Gameplay/Passives/TRT_BurningInfiniteRamjetAndAfterburner.TRT_BurningInfiniteRamjetAndAfterburner" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Cooling_Lv1.CAM_Style_Cooling_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent.BP_Ability_Vent_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithVent.TRT_StartWithVent", "/Game/Griffin/Gameplay/Passives/TRT_ImprovedCooling.TRT_ImprovedCooling" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Cooling_Lv2.CAM_Style_Cooling_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent.BP_Ability_Vent_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithVent.TRT_StartWithVent", "/Game/Griffin/Gameplay/Passives/TRT_ImprovedCooling.TRT_ImprovedCooling", "/Game/Griffin/Gameplay/Passives/TRT_GainCooledWhenInFirstPlace.TRT_GainCooledWhenInFirstPlace" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Cooling_Lv3.CAM_Style_Cooling_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent.BP_Ability_Vent_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithVent.TRT_StartWithVent", "/Game/Griffin/Gameplay/Passives/TRT_ImprovedCooling.TRT_ImprovedCooling", "/Game/Griffin/Gameplay/Passives/TRT_GainCooledWhenInFirstPlace.TRT_GainCooledWhenInFirstPlace", "/Game/Griffin/Gameplay/Passives/TRT_GainCooledWhenInPodium.TRT_GainCooledWhenInPodium" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Default.CAM_Style_Default"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Shield/BP_Ability_Shield.BP_Ability_Shield_C" },
        traits = {},
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Defence_Lv1.CAM_Style_Defence_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Shield/BP_Ability_Shield.BP_Ability_Shield_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithShield.TRT_StartWithShield", "/Game/Griffin/Gameplay/Passives/TRT_BetterTopSpeedWhenNoCrashes.TRT_BetterTopSpeedWhenNoCrashes" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Defence_Lv2.CAM_Style_Defence_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Shield/BP_Ability_Shield.BP_Ability_Shield_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithShield.TRT_StartWithShield", "/Game/Griffin/Gameplay/Passives/TRT_BetterTopSpeedWhenNoCrashesDummy.TRT_BetterTopSpeedWhenNoCrashesDummy", "/Game/Griffin/Gameplay/Passives/TRT_BetterTopSpeedWhenNoCrashesUpgrade.TRT_BetterTopSpeedWhenNoCrashesUpgrade" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Defence_Lv3.CAM_Style_Defence_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Shield/BP_Ability_Shield.BP_Ability_Shield_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithShield.TRT_StartWithShield", "/Game/Griffin/Gameplay/Passives/TRT_BetterTopSpeedWhenNoCrashesDummy.TRT_BetterTopSpeedWhenNoCrashesDummy", "/Game/Griffin/Gameplay/Passives/TRT_BetterTopSpeedWhenNoCrashesUpgrade.TRT_BetterTopSpeedWhenNoCrashesUpgrade", "/Game/Griffin/Gameplay/Passives/TRT_GainSurgeOnShieldLoss.TRT_GainSurgeOnShieldLoss" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Drafting_Lv1.CAM_Style_Drafting_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Surge/BP_Ability_Surge.BP_Ability_Surge_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithSurge.TRT_StartWithSurge", "/Game/Griffin/Gameplay/Passives/TRT_BetterDrafting.TRT_BetterDrafting" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Drafting_Lv2.CAM_Style_Drafting_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Surge/BP_Ability_Surge.BP_Ability_Surge_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithSurge.TRT_StartWithSurge", "/Game/Griffin/Gameplay/Passives/TRT_BetterDrafting.TRT_BetterDrafting", "/Game/Griffin/Gameplay/Passives/TRT_LongerDrafting.TRT_LongerDrafting" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Drafting_Lv3.CAM_Style_Drafting_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Surge/BP_Ability_Surge.BP_Ability_Surge_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithSurge.TRT_StartWithSurge", "/Game/Griffin/Gameplay/Passives/TRT_BetterDrafting.TRT_BetterDrafting", "/Game/Griffin/Gameplay/Passives/TRT_LongerDrafting.TRT_LongerDrafting", "/Game/Griffin/Gameplay/Passives/TRT_BiggerDraftingZones.TRT_BiggerDraftingZones" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Frozen_Lv1.CAM_Style_Frozen_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent_Freezing.BP_Ability_Vent_Freezing_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithFrozenVent.TRT_StartWithFrozenVent", "/Game/Griffin/Gameplay/Passives/TRT_FrozenRamjetNoHeat.TRT_FrozenRamjetNoHeat" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Frozen_Lv2.CAM_Style_Frozen_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent_Freezing.BP_Ability_Vent_Freezing_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithFrozenVent.TRT_StartWithFrozenVent", "/Game/Griffin/Gameplay/Passives/TRT_FrozenRamjetNoHeat.TRT_FrozenRamjetNoHeat", "/Game/Griffin/Gameplay/Passives/TRT_OnFrozenGainShield.TRT_OnFrozenGainShield" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Frozen_Lv3.CAM_Style_Frozen_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent_Freezing.BP_Ability_Vent_Freezing_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithFrozenVent.TRT_StartWithFrozenVent", "/Game/Griffin/Gameplay/Passives/TRT_FrozenRamjetNoHeat.TRT_FrozenRamjetNoHeat", "/Game/Griffin/Gameplay/Passives/TRT_OnFrozenGainShield.TRT_OnFrozenGainShield", "/Game/Griffin/Gameplay/Passives/TRT_FrozenDoubleDuration.TRT_FrozenDoubleDuration" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Malfunction_Lv1.CAM_Style_Malfunction_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Repair/BP_Ability_Repair.BP_Ability_Repair_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithRepair.TRT_StartWithRepair", "/Game/Griffin/Gameplay/Passives/TRT_SurgeWhenSysMalfRecovery.TRT_SurgeWhenSysMalfRecovery" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Malfunction_Lv2.CAM_Style_Malfunction_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Repair/BP_Ability_Repair.BP_Ability_Repair_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithRepair.TRT_StartWithRepair", "/Game/Griffin/Gameplay/Passives/TRT_SurgeWhenSysMalfRecovery.TRT_SurgeWhenSysMalfRecovery", "/Game/Griffin/Gameplay/Passives/TRT_RecoverFromSysMalfFaster.TRT_RecoverFromSysMalfFaster" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Malfunction_Lv3.CAM_Style_Malfunction_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Repair/BP_Ability_Repair.BP_Ability_Repair_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithRepair.TRT_StartWithRepair", "/Game/Griffin/Gameplay/Passives/TRT_SurgeWhenSysMalfRecovery.TRT_SurgeWhenSysMalfRecovery", "/Game/Griffin/Gameplay/Passives/TRT_RecoverFromSysMalfFaster.TRT_RecoverFromSysMalfFaster", "/Game/Griffin/Gameplay/Passives/TRT_MalfunctionRepairOnRecovery.TRT_MalfunctionRepairOnRecovery" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Ramjet_Lv1.CAM_Style_Ramjet_Lv1"] = {
        build = nil,
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_CriticalRamjetPower.TRT_CriticalRamjetPower", "/Game/Griffin/Gameplay/Passives/TRT_RamjetExtendedAlarm.TRT_RamjetExtendedAlarm" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Ramjet_Lv2.CAM_Style_Ramjet_Lv2"] = {
        build = nil,
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_CriticalRamjetPower.TRT_CriticalRamjetPower", "/Game/Griffin/Gameplay/Passives/TRT_RamjetExtendedAlarm.TRT_RamjetExtendedAlarm", "/Game/Griffin/Gameplay/Passives/TRT_RamjetExtendedAlarmUpgrade.TRT_RamjetExtendedAlarmUpgrade" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Ramjet_Lv3.CAM_Style_Ramjet_Lv3"] = {
        build = nil,
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_CriticalRamjetPower.TRT_CriticalRamjetPower", "/Game/Griffin/Gameplay/Passives/TRT_RamjetExtendedAlarm.TRT_RamjetExtendedAlarm", "/Game/Griffin/Gameplay/Passives/TRT_RamjetExtendedAlarmUpgrade.TRT_RamjetExtendedAlarmUpgrade", "/Game/Griffin/Gameplay/Passives/TRT_RamjetReEngageAfterRelease.TRT_RamjetReEngageAfterRelease" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Struggling_Lv1.CAM_Style_Struggling_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Autopilot/BP_Ability_Autopilot.BP_Ability_Autopilot_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithAutopilot.TRT_StartWithAutopilot", "/Game/Griffin/Gameplay/Passives/TRT_OneMoreCrash.TRT_OneMoreCrash" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Struggling_Lv2.CAM_Style_Struggling_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Autopilot/BP_Ability_Autopilot.BP_Ability_Autopilot_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithAutopilot.TRT_StartWithAutopilot", "/Game/Griffin/Gameplay/Passives/TRT_OneMoreCrash.TRT_OneMoreCrash", "/Game/Griffin/Gameplay/Passives/TRT_AfterCrashGainSurge.TRT_AfterCrashGainSurge" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Struggling_Lv3.CAM_Style_Struggling_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Autopilot/BP_Ability_Autopilot.BP_Ability_Autopilot_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithAutopilot.TRT_StartWithAutopilot", "/Game/Griffin/Gameplay/Passives/TRT_OneMoreCrash.TRT_OneMoreCrash", "/Game/Griffin/Gameplay/Passives/TRT_AfterCrashGainSurge.TRT_AfterCrashGainSurge", "/Game/Griffin/Gameplay/Passives/TRT_CoolingAtBack_Campaign.TRT_CoolingAtBack_Campaign" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Surging_Lv1.CAM_Style_Surging_Lv1"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Surge/BP_Ability_Surge_Overtake.BP_Ability_Surge_Overtake_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWtihOvertakingSurge.TRT_StartWtihOvertakingSurge", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForOvertakes.TRT_EnergyForOvertakes" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Surging_Lv2.CAM_Style_Surging_Lv2"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Surge/BP_Ability_Surge_Overtake.BP_Ability_Surge_Overtake_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWtihOvertakingSurge.TRT_StartWtihOvertakingSurge", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForOvertakes.TRT_EnergyForOvertakes", "/Game/Griffin/Gameplay/Passives/TRT_SurgeMoreTopspeed_Trigger.TRT_SurgeMoreTopspeed_Trigger" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/CAM_Style_Surging_Lv3.CAM_Style_Surging_Lv3"] = {
        build = nil,
        capacites = { "/Game/Griffin/Gameplay/Abilities/Surge/BP_Ability_Surge_Overtake.BP_Ability_Surge_Overtake_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWtihOvertakingSurge.TRT_StartWtihOvertakingSurge", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForOvertakes.TRT_EnergyForOvertakes", "/Game/Griffin/Gameplay/Passives/TRT_SurgeMoreTopspeed_Trigger.TRT_SurgeMoreTopspeed_Trigger", "/Game/Griffin/Gameplay/Passives/TRT_SurgeTopSpeedSnowball_Trigger.TRT_SurgeTopSpeedSnowball_Trigger" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/Pvp_IA_Plane_Cabbage.Pvp_IA_Plane_Cabbage"] = {
        build = "/Game/Griffin/Gameplay/Campaign/Builds/PlaneMemories/VBD_MP_CabbageCretornis.VBD_MP_CabbageCretornis",
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_Plane_CabbageCretornis_1.TRT_Plane_CabbageCretornis_1", "/Game/Griffin/Gameplay/Passives/TRT_Plane_CabbageCretornis_2.TRT_Plane_CabbageCretornis_2" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/Pvp_IA_Plane_Celery.Pvp_IA_Plane_Celery"] = {
        build = "/Game/Griffin/Gameplay/Campaign/Builds/PlaneMemories/VBD_MP_CeleryHexing.VBD_MP_CeleryHexing",
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_Plane_CeleryHexing_1.TRT_Plane_CeleryHexing_1", "/Game/Griffin/Gameplay/Passives/TRT_Plane_CeleryHexing_2.TRT_Plane_CeleryHexing_2" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/Pvp_IA_Plane_Garlic.Pvp_IA_Plane_Garlic"] = {
        build = "/Game/Griffin/Gameplay/Campaign/Builds/PlaneMemories/VBD_MP_GarlicSordes.VBD_MP_GarlicSordes",
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_Plane_GarlicSordes_1.TRT_Plane_GarlicSordes_1", "/Game/Griffin/Gameplay/Passives/TRT_Plane_GarlicSordes_2.TRT_Plane_GarlicSordes_2" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/Pvp_IA_Plane_Onion.Pvp_IA_Plane_Onion"] = {
        build = "/Game/Griffin/Gameplay/Campaign/Builds/PlaneMemories/VBD_MP_OnionDearc.VBD_MP_OnionDearc",
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_Plane_OnionDearc_1.TRT_Plane_OnionDearc_1", "/Game/Griffin/Gameplay/Passives/TRT_Plane_OnionDearc_2.TRT_Plane_OnionDearc_2" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/Pvp_IA_Plane_Pepper.Pvp_IA_Plane_Pepper"] = {
        build = "/Game/Griffin/Gameplay/Campaign/Builds/PlaneMemories/VBD_MP_PepperTarchia.VBD_MP_PepperTarchia",
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_Plane_PepperTarchia_1.TRT_Plane_PepperTarchia_1", "/Game/Griffin/Gameplay/Passives/TRT_Plane_PepperTarchia_2.TRT_Plane_PepperTarchia_2" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/Pvp_IA_Plane_Swede.Pvp_IA_Plane_Swede"] = {
        build = "/Game/Griffin/Gameplay/Campaign/Builds/PlaneMemories/VBD_MP_SwedeNesodon.VBD_MP_SwedeNesodon",
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_Plane_SwedeNesodon_1.TRT_Plane_SwedeNesodon_1", "/Game/Griffin/Gameplay/Passives/TRT_Plane_SwedeNesodon_2.TRT_Plane_SwedeNesodon_2" },
    },
    ["/Game/Griffin/Gameplay/Campaign/Loadouts/RacerStyles/Pvp_Style_PlaneMemory.Pvp_Style_PlaneMemory"] = {
        build = "/Game/Griffin/Gameplay/Campaign/Builds/PlaneMemories/VBD_MP_PlaneTour.VBD_MP_PlaneTour",
        capacites = {},
        traits = {},
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Abilities.Pvp_Style_Abilities"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Professional.VBD_PvP_IA_Professional",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Mine/BP_Ability_Mine.BP_Ability_Mine_C", "/Game/Griffin/Gameplay/Abilities/Repair/BP_Ability_Repair.BP_Ability_Repair_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithMine.TRT_StartWithMine", "/Game/Griffin/Gameplay/Passives/TRT_StartWithRepair.TRT_StartWithRepair", "/Game/Griffin/Gameplay/Passives/TRT_NoEnergyGainOverchargeImproved.TRT_NoEnergyGainOverchargeImproved" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Afterburner.Pvp_Style_Afterburner"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Veteran.VBD_PvP_IA_Veteran",
        capacites = {},
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StrongerAfterburner.TRT_StrongerAfterburner", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerLastsLonger.TRT_AfterburnerLastsLonger", "/Game/Griffin/Gameplay/Passives/TRT_RefillAfterburnerOnOvertake.TRT_RefillAfterburnerOnOvertake" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Airborne.Pvp_Style_Airborne"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Star.VBD_PvP_IA_Star",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Shockwave/BP_Ability_Shockwave_Punch.BP_Ability_Shockwave_Punch_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithVectoredShockwave.TRT_StartWithVectoredShockwave", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerRefillOnPerfectLanding.TRT_AfterburnerRefillOnPerfectLanding", "/Game/Griffin/Gameplay/Passives/TRT_AfterburnerPowerStacksWhenAirborne.TRT_AfterburnerPowerStacksWhenAirborne" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Antagonist.Pvp_Style_Antagonist"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_DarkEnigma.VBD_PvP_IA_DarkEnigma",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Disruptor/BP_Ability_Disruptor.BP_Ability_Disruptor_C", "/Game/Griffin/Gameplay/Abilities/Shockwave/BP_Ability_Shockwave.BP_Ability_Shockwave_C", "/Game/Griffin/Gameplay/Abilities/Mine/BP_Ability_Mine.BP_Ability_Mine_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithDisruptor.TRT_StartWithDisruptor", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForAbilityHits.TRT_EnergyForAbilityHits", "/Game/Griffin/Gameplay/Passives/TRT_StartWithAbilities.TRT_StartWithAbilities" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Battling.Pvp_Style_Battling"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Mercenary.VBD_PvP_IA_Mercenary",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Disruptor/BP_Ability_Disruptor.BP_Ability_Disruptor_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithDisruptor.TRT_StartWithDisruptor", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForTakedowns.TRT_EnergyForTakedowns", "/Game/Griffin/Gameplay/Passives/TRT_SurgeForTakedowns.TRT_SurgeForTakedowns" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Battling_FlameVent.Pvp_Style_Battling_FlameVent"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Mercenary.VBD_PvP_IA_Mercenary",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent_Flame.BP_Ability_Vent_Flame_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithFlameVent.TRT_StartWithFlameVent", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForTakedowns.TRT_EnergyForTakedowns", "/Game/Griffin/Gameplay/Passives/TRT_SurgeForTakedowns.TRT_SurgeForTakedowns" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Burning.Pvp_Style_Burning"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Rager.VBD_PvP_IA_Rager",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent_Flame.BP_Ability_Vent_Flame_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithFlameVent.TRT_StartWithFlameVent", "/Game/Griffin/Gameplay/Passives/TRT_StrongerAfterBurnerAndRamjetWhenBurning.TRT_StrongerAfterBurnerAndRamjetWhenBurning", "/Game/Griffin/Gameplay/Passives/TRT_GainBurningWhenRamjet.TRT_GainBurningWhenRamjet" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Cooling.Pvp_Style_Cooling"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_DarkEnigma.VBD_PvP_IA_DarkEnigma",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Vent/BP_Ability_Vent.BP_Ability_Vent_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithVent.TRT_StartWithVent", "/Game/Griffin/Gameplay/Passives/TRT_ImprovedCooling.TRT_ImprovedCooling", "/Game/Griffin/Gameplay/Passives/TRT_GainCooledWhenInFirstPlace.TRT_GainCooledWhenInFirstPlace" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Defence.Pvp_Style_Defence"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Strength.VBD_PvP_IA_Strength",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Shield/BP_Ability_Shield.BP_Ability_Shield_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithShield.TRT_StartWithShield", "/Game/Griffin/Gameplay/Passives/TRT_BetterTopSpeedWhenNoCrashes.TRT_BetterTopSpeedWhenNoCrashes", "/Game/Griffin/Gameplay/Passives/TRT_GainSurgeOnShieldLoss.TRT_GainSurgeOnShieldLoss" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Drafting.Pvp_Style_Drafting"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Thrall.VBD_PvP_IA_Thrall",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Surge/BP_Ability_Surge.BP_Ability_Surge_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithSurge.TRT_StartWithSurge", "/Game/Griffin/Gameplay/Passives/TRT_BetterDrafting.TRT_BetterDrafting", "/Game/Griffin/Gameplay/Passives/TRT_LongerDrafting.TRT_LongerDrafting" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Malfunction.Pvp_Style_Malfunction"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Honour.VBD_PvP_IA_Honour",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Repair/BP_Ability_Repair.BP_Ability_Repair_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithRepair.TRT_StartWithRepair", "/Game/Griffin/Gameplay/Passives/TRT_SurgeWhenSysMalfRecovery.TRT_SurgeWhenSysMalfRecovery", "/Game/Griffin/Gameplay/Passives/TRT_RecoverFromSysMalfFaster.TRT_RecoverFromSysMalfFaster" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Ramjet.Pvp_Style_Ramjet"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Protege.VBD_PvP_IA_Protege",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Surge/BP_Ability_Surge.BP_Ability_Surge_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithSurge.TRT_StartWithSurge", "/Game/Griffin/Gameplay/Passives/TRT_CriticalRamjetPower.TRT_CriticalRamjetPower", "/Game/Griffin/Gameplay/Passives/TRT_RamjetExtendedAlarm.TRT_RamjetExtendedAlarm" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Struggling.Pvp_Style_Struggling"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Nomad.VBD_PvP_IA_Nomad",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Autopilot/BP_Ability_Autopilot.BP_Ability_Autopilot_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWithAutopilot.TRT_StartWithAutopilot", "/Game/Griffin/Gameplay/Passives/TRT_CoolingAtBack.TRT_CoolingAtBack", "/Game/Griffin/Gameplay/Passives/TRT_AfterCrashGainSurge.TRT_AfterCrashGainSurge" },
    },
    ["/Game/Griffin/Gameplay/PvpFlow/RacerStyles/Pvp_Style_Surging.Pvp_Style_Surging"] = {
        build = "/Game/Griffin/Vehicles/Common/Upgrades/BuildDefinitions/InstantActionProfiles/VBD_PvP_IA_Ghost.VBD_PvP_IA_Ghost",
        capacites = { "/Game/Griffin/Gameplay/Abilities/Surge/BP_Ability_Surge_Overtake.BP_Ability_Surge_Overtake_C" },
        traits = { "/Game/Griffin/Gameplay/Passives/TRT_StartWtihOvertakingSurge.TRT_StartWtihOvertakingSurge", "/Game/Griffin/Gameplay/Passives/TRT_EnergyForOvertakes.TRT_EnergyForOvertakes", "/Game/Griffin/Gameplay/Passives/TRT_SurgeMoreTopspeed_Trigger.TRT_SurgeMoreTopspeed_Trigger" },
    },
}
-- FIN STYLES_PILOTES

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
    verrou_steam     = { fr = "PracticeMode est inactif : Steam est EN LIGNE. Ferme le jeu, passe Steam hors ligne, "
                               .. "et termine la session dans la fenêtre PracticeMode avant tout multi.",
                         en = "PracticeMode is inactive: Steam is ONLINE. Close the game, put Steam offline, "
                               .. "and end the session in the PracticeMode window before any multiplayer." },
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
    -- Adversaires IA (v0.9.6)
    ia_menu          = { fr = "course avec adversaires : elle se lance depuis le menu principal du jeu. "
                               .. "Quitte la course (menu pause), puis clique à nouveau sur « Lancer la course ».",
                         en = "race with opponents: it starts from the game's main menu. "
                               .. "Quit the race (pause menu), then click \"Start race\" again." },
    ia_mode          = { fr = "mode de course introuvable : %s", en = "race mode not found: %s" },
    ia_grille        = { fr = "grille : joueur + %d adversaire(s) (lu : %s)", en = "grid: player + %d opponent(s) (read: %s)" },
    ia_resume        = { fr = "%d adversaire(s)", en = "%d opponent(s)" },
    f6_perso         = { fr = "F6 : course personnalisée (pod du pilote) → utilise « Recommencer » dans le menu pause du jeu",
                         en = "F6: custom race (racer's own pod) → use \"Retry\" in the game's pause menu" },
    module_seul      = { fr = "seul, avec le pod du pilote", en = "alone, with the racer's own pod" },
    module_seul_course = { fr = "pod du pilote : seulement en lançant depuis le menu principal (ici, pod de l'épreuve)",
                           en = "racer's own pod: only when launched from the main menu (here, the event's pod)" },
    f6_ia            = { fr = "F6 : course avec adversaires → utilise « Recommencer » dans le menu pause du jeu",
                         en = "F6: race with opponents → use \"Retry\" in the game's pause menu" },
    -- Buffs du pilote (v0.9.6)
    buffs_ok         = { fr = "buffs du pilote : %d trait(s) ajouté(s) (%s)", en = "racer buffs: %d trait(s) added (%s)" },
    buffs_actifs     = { fr = "buffs du pilote actifs : %d passif(s) sur le véhicule (avant : %d)",
                         en = "racer buffs active: %d passive(s) on the vehicle (before: %d)" },
    buffs_ko         = { fr = "buffs du pilote : impossible de les ajouter (%s)", en = "racer buffs: could not add them (%s)" },
    buffs_interdits  = { fr = "buffs du pilote désactivés : ils ont fait planter le jeu la dernière fois",
                         en = "racer buffs disabled: they crashed the game last time" },
    -- Adversaires des courses de modules (v0.9.9)
    ia_modules       = { fr = "adversaires : %d pilote(s) de module à la place des %d pilotes de speeder du jeu (%s)",
                         en = "opponents: %d pod racer(s) instead of the game's %d speeder racers (%s)" },
    ia_modules_max   = { fr = "adversaires : %d demandés, mais seulement %d pilotes de module (sans le vôtre) : %d de mis",
                         en = "opponents: %d requested, but only %d pod racers (yours excluded): %d used" },
    ia_modules_ko    = { fr = "adversaires : pilotes de module introuvables, ceux du jeu sont gardés (speeders)",
                         en = "opponents: pod racers not found, the game's ones are kept (speeders)" },
    ia_modules_remis = { fr = "adversaires : liste du jeu remise (%d pilotes)",
                         en = "opponents: the game's list restored (%d racers)" },
    ia_modules_remis_ko = { fr = "adversaires : la liste du jeu (%d pilotes) n'a pas pu être remise",
                            en = "opponents: the game's list (%d racers) could not be restored" },
    -- Apparence du véhicule du pilote (v0.9.9)
    apparence_ok     = { fr = "véhicule du pilote : apparence « %s » demandée au jeu",
                         en = "racer's vehicle: look \"%s\" requested from the game" },
    apparence_ko     = { fr = "véhicule du pilote : le jeu refuse l'apparence « %s »",
                         en = "racer's vehicle: the game refuses the look \"%s\"" },
    apparence_aucune = { fr = "véhicule du pilote : %s n'a pas d'apparence propre pour ce véhicule (celle de l'épreuve est gardée)",
                         en = "racer's vehicle: %s has no own look for this vehicle (the event's look is kept)" },
    apparence_sans_impose = { fr = "véhicule du pilote : celui de l'épreuve n'est plus imposé (le pilote a le sien : %s)",
                              en = "racer's vehicle: the event's vehicle is no longer imposed (the racer has their own: %s)" },
    apparence_impose_ko = { fr = "véhicule du pilote : impossible de couper le véhicule imposé par l'épreuve (%s)",
                            en = "racer's vehicle: could not turn off the event's imposed vehicle (%s)" },
    apparence_interdite = { fr = "apparence du véhicule du pilote désactivée : elle a fait planter le jeu la dernière fois",
                            en = "racer's vehicle look disabled: it crashed the game last time" },
    buffs_absents    = { fr = "buffs du pilote : aucun de ses %d trait(s) n'a pu être trouvé ni chargé, rien ajouté",
                         en = "racer buffs: none of the %d trait(s) could be found or loaded, nothing added" },
    styles_charges   = { fr = "styles des pilotes : %d objet(s) chargé(s) depuis le disque (sur %d) en %d passage(s), %d introuvable(s), %d sauté(s) (plantage d'une session précédente)",
                         en = "racer styles: %d object(s) loaded from disk (of %d) in %d pass(es), %d not found, %d skipped (crash in a previous session)" },
    styles           = { fr = "styles des pilotes : %d style(s), %d build(s), %d trait(s) lus",
                         en = "racer styles: %d style(s), %d build(s), %d trait(s) read" },
    styles_memoire   = { fr = "styles des pilotes : en mémoire au menu, %d build(s) sur %d et %d trait(s) sur %d (LoadAsset : %s)",
                         en = "racer styles: in memory at the menu, %d build(s) of %d and %d trait(s) of %d (LoadAsset: %s)" },
    txt_position     = { fr = "place %s/%s", en = "position %s/%s" },
    -- Difficulté des IA (v0.9.7)
    difficultes      = { fr = "difficultés du mode histoire : %d lue(s) → echange/difficultes.json",
                         en = "story mode difficulties: %d read → echange/difficultes.json" },
    difficulte_base  = { fr = "base de réglages %s : %s", en = "tune base %s: %s" },
    ia_difficulte    = { fr = "difficulté %s", en = "difficulty %s" },
    difficulte_ok    = { fr = "difficulté des IA « %s » : %s", en = "AI difficulty \"%s\": %s" },
    difficulte_ko    = { fr = "difficulté des IA : réglages de course introuvables, IA du jeu sans changement",
                         en = "AI difficulty: race tune data not found, game AI unchanged" },
    difficulte_remise = { fr = "difficulté des IA : réglages du jeu remis (%s)", en = "AI difficulty: game settings restored (%s)" },
    difficulte_course = { fr = "difficulté des IA, en course : base du joueur %s ; bases des IA %s",
                          en = "AI difficulty, in race: player's base %s; AI bases %s" },
    resultats_ia     = { fr = "arrivée : %s", en = "finish: %s" },
    txt_vous         = { fr = "vous", en = "you" },
    pas_arrives      = { fr = "pas encore arrivés : %d", en = "not finished yet: %d" },
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
--   Steam ──► config/loginusers.vdf (hors ligne ?) ──────────────────────┤
--                                                                        │
--   mod : chaque action (F5, F6, F7/F8, manette, lancement) ◄── lit ─────┘
--         pare-feu actif ET Steam hors ligne ? oui → l'action se fait ;
--         non → message (qui dit lequel manque), rien d'autre
-- ─────────────────────────────────────────────────────────────────────────
local FICHIER_PARE_FEU = CONFIG.DossierEchange .. "pare-feu.txt"
local verrou = { protege = false, raison = "verrou", luA = nil, messageA = nil }

-- Steam hors ligne ? Steam l'écrit dans loginusers.vdf : on prend le compte
-- connecté le plus récemment (plus grand « Timestamp ») et sa valeur
-- « WantsOfflineMode » (même règle que la fenêtre, session.py). Fichier
-- illisible = on ne sait pas = pas hors ligne.
local function SteamHorsLigne()
    local f = io.open(FICHIER_STEAM, "r")
    if not f then
        return false
    end
    local contenu = f:read("*a") or ""
    f:close()
    local plusRecent, horsLigne = -1, false
    for bloc in contenu:gmatch("{([^{}]*)}") do
        local temps = tonumber(bloc:match('"Timestamp"%s+"(%d+)"'))
        if temps and temps > plusRecent then
            plusRecent = temps
            horsLigne = bloc:match('"WantsOfflineMode"%s+"1"') ~= nil
        end
    end
    return horsLigne
end

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
        if etat ~= "actif" then
            verrou.protege, verrou.raison = false, "verrou"
        elseif not SteamHorsLigne() then
            verrou.protege, verrou.raison = false, "verrou_steam"
        else
            verrou.protege = true
        end
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

-- ─────────────────────────────────────────────────────────────────────────
--  FILS D'EXÉCUTION (v0.9.9) : tout le Lua du mod tourne dans le fil du jeu
--
--  Vérifié dans le code d'UE4SS (LuaMod.cpp, version 5e627997 installée) :
--    fil du jeu  ── ExecuteInGameThread, ExecuteInGameThreadWithDelay,
--                   LoopInGameThreadWithDelay (rappels SANS verrou)
--    fil « async » ── LoopAsync, ExecuteWithDelay : rappels SANS verrou
--    fil des touches ── RegisterKeyBind : rappels AVEC verrou
--  Le Lua n'accepte qu'un fil à la fois : jusqu'à la v0.9.8, la boucle de
--  0,5 s, la manette et les délais tournaient sur le fil « async » pendant
--  que le fil du jeu exécutait aussi du Lua. Tables abîmées → plantages
--  dans luaH_getshortstr (11/10 19:20) et erreurs « Ref was not function ».
--  UE4SS déclare d'ailleurs LoopAsync dépassée depuis le système ci-dessous.
--
--    PlusTard(ms, f) : f une fois, dans le fil du jeu, après ms
--    Boucler(ms, f)  : f toutes les ms, dans le fil du jeu, sans fin
--  (Repli sur l'ancien fonctionnement si UE4SS est trop ancien.)
--  Les touches : voir LierTouche, leur rappel ne fait que lever un drapeau.
-- ─────────────────────────────────────────────────────────────────────────
local function PlusTard(ms, f)
    if ExecuteInGameThreadWithDelay then
        ExecuteInGameThreadWithDelay(ms, f)
    else
        ExecuteWithDelay(ms, function() ExecuteInGameThread(f) end)
    end
end

local function Boucler(ms, f)
    if LoopInGameThreadWithDelay then
        LoopInGameThreadWithDelay(ms, f)
    else
        LoopAsync(ms, function()
            ExecuteInGameThread(f)
            return false   -- false = continuer à boucler
        end)
    end
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
        Journal(Traduire(verrou.raison))
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

-- Comme Trouver, mais charge l'objet s'il n'est pas encore en mémoire, et
-- sans message (nil s'il n'existe pas). Sert au mode de jeu des courses avec
-- IA. (Builds et traits des styles : ChargerProtege, avec une miette par objet.)
local function ChargerObjet(chemin)
    if not chemin or chemin == "" then
        return nil
    end
    local objet = StaticFindObject(chemin)
    -- Pas en mémoire : LoadAsset seulement s'il est autorisé (voir
    -- CONFIG.ChargementAssets ; pcall ne protège pas d'un plantage d'UE4SS)
    if not EstValide(objet) and CONFIG.ChargementAssets then
        pcall(function() LoadAsset(chemin) end)
        objet = StaticFindObject(chemin)
    end
    return EstValide(objet) and objet or nil
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
    -- (même chose si les noms des stats du jeu, VehicleUIConfig, ne sont pas encore chargés)
    local complet = nbA > 0 and EstValide(ui)
    catalogueExporte = nbC > 0 and (complet or essaisCatalogue >= CONFIG.Capacites_Essais)
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
--            adversaires = 0 à 11 (0 = seul, contre-la-montre),
--            + les clés du build, voir l'éditeur de build ci-dessus }
-- ─────────────────────────────────────────────────────────────────────────
local LancerAvecAdversaires   -- course avec IA : définie plus bas (elle a besoin de NomCarte)
local AuMenuPourIA            -- idem : vrai si l'on est au menu principal du jeu
local AppliquerDifficulte     -- difficulté des IA (v0.9.7) : définies plus bas, voir DIFFICULTÉ DES IA
local RestaurerDifficulte
local RestaurerAdversaires    -- adversaires des courses de modules (v0.9.9) : défini plus bas

-- Nombre d'adversaires demandé (0 = contre-la-montre seul)
local function NombreAdversaires(choix)
    local n = math.floor(tonumber(choix and choix.adversaires or "0") or 0)
    return math.max(0, math.min(CONFIG.AdversairesMax, n))
end

-- Nombre de tours d'un circuit changé pour une course avec IA (voir
-- LancerAvecAdversaires) : remis à l'origine au lancement suivant.
local toursModifies = {}   -- chemin du circuit → { objet = circuit, origine = tours }
-- La recette préférée d'un pilote pour un archétype (EVehicleArchetype)
local function RecettePilote(pilote, archetype)
    local recette = nil
    pcall(function()
        pilote[CONFIG.Apparence_Preferees]:ForEach(function(k, v)
            if k:get() == archetype then
                recette = v:get()
            end
        end)
    end)
    return (recette ~= nil and EstValide(recette)) and recette or nil
end

-- Véhicule imposé par l'épreuve modèle (v0.9.9). En course avec IA (rien
-- d'imposé), le jeu donne au joueur le véhicule de son pilote ; en
-- contre-la-montre, celui de l'épreuve (12/10/2026 : Sebulba, Ben, Onion,
-- Nesodon… tous en PRE_Plane_MythP3). Quand le pilote choisi a son propre
-- véhicule pour ce type, le mod coupe EventMode.bUseCustomVehicle de
-- l'épreuve modèle ; remis à l'origine au lancement suivant.
local vehiculeImpose = nil   -- { mode = EventMode de l'épreuve, origine = valeur du jeu }
local function RestaurerVehiculeImpose()
    local v = vehiculeImpose
    vehiculeImpose = nil
    if v then
        pcall(function()
            if v.mode:IsValid() then
                v.mode[CONFIG.Apparence_VehiculeImpose] = v.origine
            end
        end)
    end
end

local function RestaurerTours()
    for _, e in pairs(toursModifies) do
        if EstValide(e.objet) then
            pcall(function() e.objet[CONFIG.Tours_Defaut] = e.origine end)
        end
    end
    toursModifies = {}
end

local function Lancer(choix)
    if not Autorise() then
        return
    end
    -- Course avec IA demandée hors du menu : refusée AVANT de toucher à quoi
    -- que ce soit (la course en cours garde son choix, ses buffs, ses tours)
    if NombreAdversaires(choix) > 0 and not AuMenuPourIA() then
        Journal(Traduire("ia_menu"))
        return
    end
    RestaurerTours()
    RestaurerDifficulte()
    RestaurerAdversaires()
    RestaurerVehiculeImpose()
    -- La difficulté des IA ne sert qu'avec des adversaires : en contre-la-montre,
    -- elle n'est pas notée (les records seuls ne sont pas séparés par difficulté)
    if NombreAdversaires(choix) == 0 then
        choix.difficulte, choix.nom_difficulte = nil, nil
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

    -- 2b. Contre-la-montre : le véhicule du pilote plutôt que celui de
    --     l'épreuve, s'il en a un pour ce type (v0.9.9, commentaire Nexus)
    if CONFIG.Apparence and CONFIG.Apparence_CouperImpose and choix.pilote and choix.pilote ~= ""
       and NombreAdversaires(choix) == 0 then
        local pilote = StaticFindObject(choix.pilote)
        local typeVehicule = CONFIG.Apparence_Archetypes[choix.type or ""]
        local recette = (EstValide(pilote) and typeVehicule) and RecettePilote(pilote, typeVehicule) or nil
        if recette then
            local ok = pcall(function()
                local mode = modele[CONFIG.ProprieteMode]
                vehiculeImpose = { mode = mode, origine = mode[CONFIG.Apparence_VehiculeImpose] }
                mode[CONFIG.Apparence_VehiculeImpose] = false
            end)
            local okNom, nom = pcall(function() return recette:GetFName():ToString() end)
            Detail(Traduire(ok and "apparence_sans_impose" or "apparence_impose_ko", okNom and nom or "?"))
        end
    end

    -- 3. Build (pièces, stats, options, crashs illimités)
    local buildChoisi, bilanBuild = AppliquerBuild(choix, t, modele)
    if buildChoisi then
        build = buildChoisi
    end

    local resume = Traduire("resume", piste:GetFName():ToString(), tours or "?", choix.type)
    if bilanBuild then
        resume = resume .. " — " .. bilanBuild
    end

    -- Course avec adversaires IA : autre fonction de lancement (voir plus bas)
    local adversaires = NombreAdversaires(choix)
    -- Module seul avec un pilote qui a son pod (v2.0.0) : même lancement, sans
    -- adversaire, pour avoir le pod du pilote (voir CONFIG.Modules_CourseSeule)
    if adversaires == 0 and CONFIG.Modules_CourseSeule and choix.type == "avion"
       and choix.pilote and choix.pilote ~= "" then
        local pilote = StaticFindObject(choix.pilote)
        local typeModule = CONFIG.Apparence_Archetypes.avion
        if EstValide(pilote) and RecettePilote(pilote, typeModule) then
            if AuMenuPourIA() then
                choix.course_seule = true
                if LancerAvecAdversaires(choix, archetype, piste, build, tours, 0, resume) then
                    dernierChoix = choix
                end
                return
            end
            Journal(Traduire("module_seul_course"))   -- (en course : l'épreuve, et son pod)
        end
    end
    if adversaires > 0 then
        if LancerAvecAdversaires(choix, archetype, piste, build, tours, adversaires, resume) then
            dernierChoix = choix
        end
        return
    end

    -- 4. Mémoriser l'épreuve pour le restart (F6)
    local arcade = FindFirstOf(CONFIG.ClasseArcade)
    if EstValide(arcade) then
        arcade[CONFIG.ProprieteDerniere] = modele
    end
    dernierChoix = choix

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

-- ── Joueur et monde, sans parcourir tous les objets du jeu ──
-- UEHelpers.GetPlayerController (et GetPlayer, GetWorld, qui l'appellent)
-- fait un FindAllOf("PlayerController") : il parcourt TOUS les objets du jeu
-- (bien plus de 100 000 en course avec 11 adversaires). Le mod en faisait
-- jusqu'à 6 d'affilée toutes les 0,5 s : c'était la cause des petits freezes
-- en course (11/10/2026). Chemin direct, relu à chaque fois (jamais périmé) :
--
--   GameInstance (une seule pour toute la partie, cherchée une fois)
--     └── LocalPlayers[1] ── PlayerController ─┬── Pawn        (le véhicule)
--                                              └── GetWorld()  (la carte)
--
-- Sans GameInstance, l'ancienne méthode (UEHelpers) sert de secours.
local acces = { instance = nil, chercheA = nil, note = false }

local function InstanceJeu()
    if EstValide(acces.instance) then
        return acces.instance
    end
    acces.instance = nil
    -- (FindFirstOf parcourt les objets : pas plus d'une fois toutes les quelques secondes)
    local maintenant = os.clock()
    if acces.chercheA == nil or maintenant - acces.chercheA >= CONFIG.Joueur_Recherche then
        acces.chercheA = maintenant
        local ok, inst = pcall(FindFirstOf, "GameInstance")
        if ok and EstValide(inst) then
            acces.instance = inst
            if not acces.note then
                acces.note = true
                Detail("joueur et carte : accès direct par la GameInstance (sans parcourir les objets)")
            end
        end
    end
    return acces.instance
end

-- Le contrôleur du joueur local (nil s'il n'y en a pas, pendant un chargement)
local function Controleur()
    local instance = InstanceJeu()
    if not instance then
        return UEHelpers.GetPlayerController()   -- secours (lent)
    end
    local ok, c = pcall(function()
        local x = instance.LocalPlayers[1].PlayerController
        return EstValide(x) and x or nil
    end)
    return ok and c or nil
end

-- Le véhicule du joueur (nil au menu ou pendant un chargement)
local function Pion()
    if not InstanceJeu() then
        return UEHelpers.GetPlayer()             -- secours (lent)
    end
    local c = Controleur()
    if not c then
        return nil
    end
    local ok, p = pcall(function()
        local x = c.Pawn
        return EstValide(x) and x or nil
    end)
    return ok and p or nil
end

-- Le monde (la carte chargée)
local function Monde()
    local instance = InstanceJeu()
    if not instance then
        return UEHelpers.GetWorld()              -- secours (lent)
    end
    local source = Controleur() or instance
    local ok, w = pcall(function()
        local x = source:GetWorld()
        return EstValide(x) and x or nil
    end)
    return ok and w or nil
end

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
    local controleur = Controleur()
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

-- Le build complet de la course, pour la fenêtre (onglet Mes temps : clic sur
-- une ligne → détail). Mêmes clés que la commande : « niveaux=0,3,…;capacites=… ».
-- (les chemins d'objets ne contiennent ni « ; » ni « = »)
local CLES_DETAIL = { "niveaux", "capacites", "crash", "affixes", "boost", "ramjet", "pannes",
                      "crashs_illimites", "style", "traits", "adversaires", "difficulte" }
local function DetailBuild(c, position)
    local morceaux = {}
    for _, cle in ipairs(CLES_DETAIL) do
        if c[cle] ~= nil and c[cle] ~= "" then
            table.insert(morceaux, cle .. "=" .. tostring(c[cle]))
        end
    end
    if position then
        table.insert(morceaux, "position=" .. tostring(position))
    end
    return table.concat(morceaux, ";")
end

-- Écrit le temps d'une course terminée dans temps.txt et temps.csv
-- `avecSaveState` : vrai si l'on est revenu à un emplacement pendant la course
-- (le temps est alors noté « save state » et ne compte pas pour les records).
-- `position` : place à l'arrivée (courses avec adversaires seulement)
local function EnregistrerTemps(final, meilleur, tours, avecSaveState, position)
    local c = dernierChoix or {}
    local date = os.date("%Y-%m-%d %H:%M:%S")
    local listeTours = {}
    for _, t in ipairs(tours) do
        table.insert(listeTours, FormatTemps(t))
    end
    local adversaires = NombreAdversaires(c)
    if adversaires == 0 then
        position = nil
    end
    local place = position and Traduire("txt_position", tostring(position), tostring(adversaires + 1)) or nil
    if place and c.nom_difficulte and c.nom_difficulte ~= "" then
        place = place .. ", " .. c.nom_difficulte
    end
    local champs = {
        date,
        c.nom_planete or "?",
        c.nom_circuit or Traduire("txt_hors_mod"),
        Traduire("txt_tours", tostring(c.tours or "?")),
        c.nom_vehicule or c.type or "?",
        c.nom_pilote or "?",
        FormatTemps(final) .. (avecSaveState and " (save state)" or "") .. (place and ("  [" .. place .. "]") or ""),
        Traduire("txt_meilleur", FormatTemps(meilleur)),
        Traduire("txt_detail", #listeTours > 0 and table.concat(listeTours, "  ") or "-"),
        Traduire("txt_build", c.resume_build or "?"),
    }
    local okTxt = AjouterLigne(CONFIG.FichierTemps,
        Traduire("txt_entete"),
        table.concat(champs, " | "))
    -- Version tableur : séparateur « ; » (Excel en français), sans le mot « meilleur tour »
    -- (même ordre que l'en-tête CSV ci-dessous). La dernière colonne (v0.9.6) est
    -- absente des fichiers plus anciens : la fenêtre la retrouve quand même.
    local csv = { date, c.nom_planete or "", c.nom_circuit or "", tostring(c.tours or ""),
                  c.nom_vehicule or c.type or "", c.nom_pilote or "", FormatTemps(final),
                  string.format("%.3f", final or 0), FormatTemps(meilleur),
                  table.concat(listeTours, " "), c.resume_build or "", avecSaveState and "oui" or "non",
                  DetailBuild(c, position) }
    for i, v in ipairs(csv) do
        csv[i] = '"' .. tostring(v):gsub('"', '""') .. '"'
    end
    AjouterLigne(CONFIG.FichierTempsCsv,
        "Date;Planète;Circuit;Nb tours;Véhicule;Pilote;Temps;Secondes;Meilleur tour;Détail des tours;Build;Save state;Détail du build",
        table.concat(csv, ";"))
    local note = (avecSaveState and Traduire("temps_ss") or "") .. (place and ("  [" .. place .. "]") or "")
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
    local ok, nom = pcall(function() return Monde():GetFName():ToString() end)
    return ok and nom or "?"
end

-- Horloge de la course (temps « serveur » du jeu, en secondes)
local function TempsServeur()
    local ok, t = pcall(function() return Monde().GameState:GetServerWorldTimeSeconds() end)
    if ok and type(t) == "number" then
        return t
    end
    return nil
end

-- Joue un son d'interface du jeu (aucune erreur si ça échoue)
local function Son(nomFonction)
    pcall(function()
        local bibliotheque = StaticFindObject(CONFIG.BibliothequeSons)
        local pion = Pion()
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

-- Course avec IA : à l'arrivée du joueur, la place et le temps de chacun
-- (ceux qui ont déjà fini), pour comparer les difficultés. Journal seulement.
local function NoterResultatsIA()
    local function Lire(f)   -- (Lire est définie plus bas dans le fichier)
        local ok, v = pcall(f)
        return ok and v or nil
    end
    local monde = Monde()
    local joueur = Lire(function() return Controleur().PlayerState:GetAddress() end)
    local arrives, restants = {}, 0
    pcall(function()
        monde.GameState.Racers:ForEach(function(_, e)
            local etat = e:get()
            if etat == nil or not EstValide(etat) then
                return
            end
            local composant = Lire(function() return etat[CONFIG.Chrono_Composant] end)
            local place = composant and Lire(function() return composant[CONFIG.Chrono_Position] end)
            local temps = composant and Lire(function() return composant[CONFIG.Chrono_Final] end)
            if type(place) == "number" and place > 0 and type(temps) == "number" and temps > 0 then
                local nom = etat:GetAddress() == joueur and Traduire("txt_vous")
                            or Lire(function() return ChaineLua(etat:GetPlayerName()) end) or "?"
                table.insert(arrives, { place = place, texte = string.format("%d. %s %s", place, nom, FormatTemps(temps)) })
            else
                restants = restants + 1
            end
        end)
    end)
    if #arrives == 0 then
        return
    end
    table.sort(arrives, function(a, b) return a.place < b.place end)
    local morceaux = {}
    for _, x in ipairs(arrives) do
        table.insert(morceaux, x.texte)
    end
    if restants > 0 then
        table.insert(morceaux, Traduire("pas_arrives", restants))
    end
    Detail(Traduire("resultats_ia", table.concat(morceaux, " — ")))
end

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
        local position = nil
        pcall(function() position = composant[CONFIG.Chrono_Position] end)
        EnregistrerTemps(composant[CONFIG.Chrono_Final], composant[CONFIG.Chrono_Meilleur], suivi.tours,
                         suivi.saveState, type(position) == "number" and position > 0 and position or nil)
        if NombreAdversaires(dernierChoix) > 0 then
            Proteger("résultats des IA", NoterResultatsIA)
        end
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
local POST_REFROIDIT, POST_RECHARGE = 1, 2 -- états de la postcombustion (Cooldown, Recovering)

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
            local voulu = b.postEtat or 0
            -- L'énergie est un champ natif d'UAfterburner, invisible pour Lua :
            -- seule Server_UpdateState peut la changer. Le jeu ignore peut-être
            -- un appel qui ne change pas d'état : on passe donc d'abord par un
            -- AUTRE état (jamais 0 « Active », pour ne pas déclencher le boost),
            -- puis on revient au bon état avec la bonne énergie.
            if CONFIG.Boost_EtatIntermediaire then
                local autre = (voulu == POST_RECHARGE) and POST_REFROIDIT or POST_RECHARGE
                Essayer("postcombustion via état " .. autre, function() post:Server_UpdateState(autre, b.energie) end)
            end
            Essayer("postcombustion", function() post:Server_UpdateState(voulu, b.energie) end)
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
        PlusTard(50, function() Proteger("boost après remise en place", function()
            local pion = Pion()
            if EstValide(pion) then
                RendreBoost(pion, e.boost)
            end
        end) end)
    end
    PlusTard(CONFIG.Boost_Verification, function() Proteger("boost après retour", function()
        local pion = Pion()
        if EstValide(pion) then
            Detail(string.format("retour %d, +%d ms : %s (voulu : %s)", n, CONFIG.Boost_Verification,
                                 DecrireBoost(LireBoost(pion)), DecrireBoost(e.boost)))
        end
    end) end)
end

local function Sauver(n)
    if not Autorise() then
        return
    end
    local pion = Pion()
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
        PlusTard(delai, function() Proteger("vitesse après retour", function()
            local pion = Pion()
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
    local pion = Pion()
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
        c = Controleur()
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
    if not EstValide(Pion()) then
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

-- Associe une touche (avec ou sans Maj/Ctrl) à une action (v0.9.9).
-- UE4SS lit le clavier sur son propre fil (voir FILS D'EXÉCUTION) : le rappel
-- ne fait QUE lever le drapeau de la touche, un champ qui existe déjà, sans
-- créer le moindre objet Lua (donc sans réveiller le ramasse-miettes du Lua
-- sur ce fil). La boucle des touches (TraiterTouches), dans le fil du jeu,
-- fait l'action.
--
--    touche ──► fil des touches : t.appuye = true
--                                     │
--               fil du jeu, toutes les 20 ms : TraiterTouches → action
--
-- UE4SS compare les modificateurs exactement (Input/Handler.cpp) : Maj+F7 ne
-- déclenche pas « F7 seul ». L'ancienne attente de 80 ms ne sert plus.
local touchesLiees = {}
local function LierTouche(touche, modificateurs, action, nom)
    local t = { appuye = false, action = action, nom = nom or "touche" }
    table.insert(touchesLiees, t)
    local function Rappel()
        t.appuye = true
    end
    if #modificateurs == 0 then
        RegisterKeyBind(touche, Rappel)
    else
        RegisterKeyBind(touche, modificateurs, Rappel)
    end
end

-- Boucle des touches (fil du jeu) : l'action de chaque touche appuyée
local function TraiterTouches()
    for _, t in ipairs(touchesLiees) do
        if t.appuye then
            t.appuye = false
            Proteger(t.nom, t.action)
        end
    end
end

-- ─────────────────────────────────────────────────────────────────────────
--  COURSE AVEC ADVERSAIRES IA (v0.9.6)
--  FrontEndGameMode.LaunchCustomRace(archétype, mode, circuit, conditions,
--  build, build debug), la « course rapide » des développeurs :
--
--    mode = GameModeVariantDef, sa grille de départ (GridMakeup.Entries) :
--        GMV_Race        { au choix du joueur (4) × 5 }  → on écrit 1 + N
--        GMV_PlaneRaces  { module (1) × 6 }              → idem
--    circuit .DefaultLapCount ← tours voulus (la fonction n'a pas de nombre
--        de tours ; remis à l'origine au lancement suivant, voir RestaurerTours)
--    conditions : tag vide (celles du circuit)
--    build : le build rempli par l'éditeur, comme pour le contre-la-montre
--    build debug : aucun
--
--  Seulement depuis le menu principal : la fonction appartient au mode de jeu
--  du menu. Tout est en mémoire : le jeu redevient normal à sa fermeture.
-- ─────────────────────────────────────────────────────────────────────────

-- Règle la grille d'un mode : joueur + n adversaires (première ligne de la
-- grille). Renvoie la grille relue, pour le journal (« 4×6 »).
local function ReglerGrille(mode, n)
    local entrees = mode.GridMakeup.Entries
    entrees[1].NumEntrants = n + 1
    local lu = {}
    entrees:ForEach(function(_, e)
        local s = e:get()
        table.insert(lu, tostring(s.EntryType) .. "×" .. tostring(s.NumEntrants))
    end)
    return table.concat(lu, ", ")
end

AuMenuPourIA = function()
    return NomCarte() == CONFIG.CarteMenu and EstValide(FindFirstOf(CONFIG.ClasseModeMenu))
end

-- Adversaires des courses de modules (v0.9.9) :
--
--    DA_CharacterList.Opponents  (11 pilotes de speeder : motos, skimmers, voitures)
--         │  remplacée le temps de la course par
--         ▼
--    PvpPlaneInstantActionPlayable + PvpPlanePlayable  (pilotes de module,
--    jeunes puis âgés, sans le pilote du joueur ni doublon)
--
-- La liste du jeu est gardée et remise au retour au menu (SuivreAdversaires),
-- au lancement suivant, ou aussitôt si le lancement échoue.
local adversairesOrigine = nil   -- { liste = DA_CharacterList, elements = { pilotes du jeu } }
local adversairesEtat = nil      -- "attente" (au menu) puis "course"

local function RemplirTableau(tableau, elements)
    tableau:Empty()
    for i, o in ipairs(elements) do
        tableau[i] = o   -- une case après l'autre (voir le piège TArray d'UE4SS)
    end
end

RestaurerAdversaires = function()
    local o = adversairesOrigine
    adversairesOrigine, adversairesEtat = nil, nil
    if o and EstValide(o.liste) then
        local ok = pcall(function() RemplirTableau(o.liste[CONFIG.Adversaires_Liste], o.elements) end)
        Detail(Traduire(ok and "ia_modules_remis" or "ia_modules_remis_ko", #o.elements))
    end
end

-- Met les pilotes de module comme adversaires. Renvoie leur nombre, ou nil
-- si la liste du jeu n'a pas pu être changée.
local function MettreAdversairesModules(pilote)
    local liste = StaticFindObject(CONFIG.ListePilotes)
    if not EstValide(liste) then
        return nil
    end
    local joueur = EstValide(pilote) and pilote:GetAddress() or nil
    local modules, vus = {}, {}
    for _, nomListe in ipairs(CONFIG.Adversaires_Modules) do
        pcall(function()
            liste[nomListe]:ForEach(function(_, e)
                local p = e:get()
                if p ~= nil and EstValide(p) then
                    local adresse = p:GetAddress()
                    if adresse ~= joueur and not vus[adresse] then
                        vus[adresse] = true
                        table.insert(modules, p)
                    end
                end
            end)
        end)
    end
    if #modules == 0 then
        return nil
    end
    local elements = {}
    local ok = pcall(function()
        liste[CONFIG.Adversaires_Liste]:ForEach(function(_, e)
            table.insert(elements, e:get())
        end)
    end)
    if not ok then
        return nil
    end
    adversairesOrigine = { liste = liste, elements = elements }
    adversairesEtat = "attente"
    if not pcall(function() RemplirTableau(liste[CONFIG.Adversaires_Liste], modules) end) then
        RestaurerAdversaires()
        return nil
    end
    local noms = {}
    for _, p in ipairs(modules) do
        local okNom, nom = pcall(function() return p:GetFName():ToString() end)
        table.insert(noms, okNom and nom or "?")
    end
    Detail(Traduire("ia_modules", #modules, #elements, table.concat(noms, ", ")))
    return #modules
end

-- Boucle principale : liste du jeu remise au retour au menu après la course
local function SuivreAdversaires()
    if not adversairesEtat then
        return
    end
    local auMenu = NomCarte() == CONFIG.CarteMenu
    if adversairesEtat == "attente" and not auMenu then
        adversairesEtat = "course"
    elseif adversairesEtat == "course" and auMenu then
        RestaurerAdversaires()
    end
end

-- Renvoie vrai si la course est lancée
LancerAvecAdversaires = function(choix, archetype, piste, build, tours, adversaires, resume)
    local modeMenu = FindFirstOf(CONFIG.ClasseModeMenu)
    if not AuMenuPourIA() then
        Journal(Traduire("ia_menu"))
        return false
    end
    local cheminMode = (choix.type == "avion") and CONFIG.ModesIA.avion or CONFIG.ModesIA.standard
    local mode = ChargerObjet(cheminMode)
    if not mode then
        Journal(Traduire("ia_mode", cheminMode))
        return false
    end
    -- Course de modules : des pilotes de module comme adversaires (v0.9.9)
    if choix.type == "avion" and adversaires > 0 then
        local n = MettreAdversairesModules(choix.pilote and StaticFindObject(choix.pilote) or nil)
        if n and adversaires > n then
            Detail(Traduire("ia_modules_max", adversaires, n, n))
            adversaires = n
        elseif not n then
            Detail(Traduire("ia_modules_ko"))
        end
    end
    local ok, lu = pcall(ReglerGrille, mode, adversaires)
    Detail(Traduire("ia_grille", adversaires, ok and lu or ("ERREUR " .. tostring(lu))))

    -- Nombre de tours : LaunchCustomRace prend celui du circuit
    if tours and tours >= 1 and tours <= 99 then
        pcall(function()
            local chemin = Chemin(piste)
            if not toursModifies[chemin] then
                toursModifies[chemin] = { objet = piste, origine = piste[CONFIG.Tours_Defaut] }
            end
            piste[CONFIG.Tours_Defaut] = math.floor(tours)
        end)
    end

    -- Appel. Le dernier paramètre (build debug) est vide : nil, ou à défaut
    -- un objet « invalide » d'UE4SS (pointeur nul), selon ce qu'il accepte.
    local conditions = { TagName = FName("None") }
    resume = resume .. " — " .. (adversaires > 0 and Traduire("ia_resume", adversaires) or Traduire("module_seul"))
    if AppliquerDifficulte(choix) then
        resume = resume .. ", " .. Traduire("ia_difficulte", choix.nom_difficulte or choix.difficulte)
    end
    local fonction = CONFIG.FonctionCourseIA
    local okAppel, erreur = pcall(function()
        modeMenu[fonction](modeMenu, archetype, mode, piste, conditions, build, nil)
    end)
    if not okAppel and type(CreateInvalidObject) == "function" then
        Detail("LaunchCustomRace avec nil refusé (" .. tostring(erreur) .. "), essai avec un objet vide")
        okAppel, erreur = pcall(function()
            modeMenu[fonction](modeMenu, archetype, mode, piste, conditions, build, CreateInvalidObject())
        end)
    end
    if okAppel then
        Journal(Traduire("lancement", resume))
    else
        RestaurerDifficulte()
        RestaurerAdversaires()
        Journal(Traduire("erreur_pendant", fonction, tostring(erreur)))
    end
    return okAppel
end

-- ─────────────────────────────────────────────────────────────────────────
--  F6 : recommencer la course en cours
-- ─────────────────────────────────────────────────────────────────────────
local function Recommencer()
    if not Autorise() then
        return
    end
    -- Une course avec adversaires n'est pas une épreuve Arcade : le restart
    -- Arcade relancerait le dernier contre-la-montre à la place.
    if NombreAdversaires(dernierChoix) > 0 then
        Journal(Traduire("f6_ia"))
        return
    end
    if dernierChoix and dernierChoix.course_seule then
        Journal(Traduire("f6_perso"))
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

-- ─────────────────────────────────────────────────────────────────────────
--  EXPLORATION (lecture seule) : préparation des « adversaires IA »
--  Une fois par session, au menu principal, juste après le catalogue, on
--  relève SANS RIEN MODIFIER :
--
--    modes     GameModeVariantDef : mode de course + grille de départ
--              (ex. course par équipes, 1 joueur + 11 motojets IA)
--    listes    GfnEventList : modes et planètes de la course rapide du jeu
--    epreuves  RaceEventDef et ses filles (ArcadeEventDef…) : mode, grille,
--              adversaires imposés (pilote, véhicule, build, réglages d'IA),
--              classement en ligne lié
--    fonctions LaunchCustomRace / LaunchQuickRace existent-elles ?
--
--  Résultat : echange/epreuves.json, et un résumé dans le journal d'UE4SS.
-- ─────────────────────────────────────────────────────────────────────────
local epreuvesExplorees = false

-- Valeur lue sans jamais faire échouer l'exploration (nil si illisible)
local function Lire(f)
    local ok, v = pcall(f)
    if ok then
        return v
    end
    return nil
end

local function JsonValeur(v)
    if v == nil then
        return "null"
    elseif type(v) == "number" or type(v) == "boolean" then
        return tostring(v)
    end
    return JsonTexte(tostring(v))
end

local function NomDe(o)
    return Lire(function() return o:GetFName():ToString() end) or "?"
end

local function ClasseDe(o)
    return Lire(function() return o:GetClass():GetFName():ToString() end) or "?"
end

-- Chemin d'une référence « souple » (TSoftObjectPtr : l'objet n'est pas
-- forcément chargé). UE4SS ne l'expose pas toujours de la même façon : on
-- essaie plusieurs lectures, et on note le type si aucune ne marche.
local function CheminSouple(v)
    if v == nil or not CONFIG.Exploration_Souples then
        return nil
    end
    local essais = {
        function() return v:ToString() end,
        function() return v.ObjectID.AssetPath.PackageName:ToString() .. "." .. v.ObjectID.AssetPath.AssetName:ToString() end,
        function() return v.ObjectID.AssetPathName:ToString() end,
        function() local o = v:get(); return EstValide(o) and Chemin(o) or nil end,
        function() return EstValide(v) and Chemin(v) or nil end,
    }
    for _, essai in ipairs(essais) do
        local ok, r = pcall(essai)
        if ok and type(r) == "string" and r ~= "" and r ~= "None.None" then
            return r
        end
    end
    return "?(" .. type(v) .. ")"
end

-- Lecture d'une propriété « souple » (TSoftObjectPtr / TSoftClassPtr) : seulement
-- si CONFIG.Exploration_Souples, car LIRE la propriété suffit peut-être à faire
-- planter UE4SS (11/10/2026). Sinon : nil, sans y toucher.
local function DuSouple(f)
    if not CONFIG.Exploration_Souples then
        return nil
    end
    return Lire(f)
end

-- Nombre d'éléments d'une liste (TArray), sans créer les éléments eux-mêmes
-- (« # » ne lit que le compteur : sans danger même pour des références souples)
local function Nombre(f)
    return Lire(function() return #f() end)
end

-- Grille de départ (FRaceGridMakeup) : [{"type": 2, "nombre": 11}, …]
-- (type = ERaceGridEntryType : 0 voiture, 1 module, 2 motojet, 3 skimmer, 4 au choix du joueur)
local function GrilleJson(grille)
    local morceaux = {}
    pcall(function()
        grille.Entries:ForEach(function(_, e)
            local s = e:get()
            table.insert(morceaux, '{"type": ' .. JsonValeur(Lire(function() return s.EntryType end))
                .. ', "nombre": ' .. JsonValeur(Lire(function() return s.NumEntrants end)) .. "}")
        end)
    end)
    return "[" .. table.concat(morceaux, ", ") .. "]"
end

-- Adversaires imposés par une épreuve (CustomOpponents)
local function AdversairesJson(epreuve)
    local morceaux = {}
    pcall(function()
        epreuve.CustomOpponents:ForEach(function(_, e)
            local s = e:get()
            local rythmes = {}
            if CONFIG.Exploration_Rythmes then
                pcall(function()
                    s.AIState.GameModePacingConfigs:ForEach(function(cle, _)
                        table.insert(rythmes, JsonValeur(Lire(function() return cle:get() end)))
                    end)
                end)
            end
            table.insert(morceaux, "{" .. table.concat({
                '"pilote": ' .. JsonValeur(CheminSouple(DuSouple(function() return s.Driver end))),
                '"type": ' .. JsonValeur(Lire(function() return s.vehicleType end)),
                '"build": ' .. JsonValeur(CheminSouple(DuSouple(function() return s.vehicleBuild end))),
                '"agressivite": ' .. JsonValeur(Lire(function() return s.AIState.RacerAggressionLevel.RowName:ToString() end)),
                '"rythme_par_mode": [' .. table.concat(rythmes, ", ") .. "]",
            }, ", ") .. "}")
        end)
    end)
    return "[" .. table.concat(morceaux, ", ") .. "]", #morceaux
end

local function EpreuveJson(epreuve)
    local mode = Lire(function() return epreuve[CONFIG.ProprieteMode] end)
    local modeValide = mode ~= nil and EstValide(mode)
    local function DuMode(f)   -- (garde les « false » : pas de « a and b or c » ici)
        if modeValide then
            return Lire(f)
        end
        return nil
    end
    local adversaires, nbAdversaires = AdversairesJson(epreuve)
    local champs = {
        '"chemin": ' .. JsonValeur(Lire(function() return Chemin(epreuve) end)),
        '"nom": ' .. JsonTexte(NomDe(epreuve)),
        '"classe": ' .. JsonTexte(ClasseDe(epreuve)),
        '"affiche": ' .. JsonTexte(Texte(epreuve, "PlayerFacingName")),
        '"circuit": ' .. JsonValeur(Lire(function() local c = epreuve.TrackDef; return EstValide(c) and NomDe(c) or nil end)),
        '"tours": ' .. JsonValeur(Lire(function() return epreuve.LapCount end)),
        '"vehicule": ' .. JsonTexte(Tag(epreuve, "VehicleTypeTag")),
        '"categorie": ' .. JsonValeur(Lire(function() return epreuve.Category end)),
        '"mode_classe": ' .. JsonValeur(modeValide and ClasseDe(mode) or nil),
        '"mode": ' .. JsonValeur(DuMode(function() return mode.RaceEventModeType end)),
        '"vehicule_impose": ' .. JsonValeur(DuMode(function() return mode.bUseCustomVehicle end)),
        '"sante": ' .. JsonValeur(DuMode(function() return mode.bUsePlayerHealth end)),
        '"classement": ' .. JsonValeur(DuMode(function() local l = mode.Leaderboard; return EstValide(l) and NomDe(l) or nil end)),
        '"grille_nom": ' .. JsonValeur(Lire(function() return epreuve.GridMakeup.PlayerFacingName:ToString() end)),
        '"grille": ' .. GrilleJson(Lire(function() return epreuve.GridMakeup end)),
        '"adversaires": ' .. adversaires,
    }
    return "    {" .. table.concat(champs, ", ") .. "}", nbAdversaires, DuMode(function() return mode.RaceEventModeType end)
end

local function ModeJson(m)
    return "    {" .. table.concat({
        '"chemin": ' .. JsonValeur(Lire(function() return Chemin(m) end)),
        '"nom": ' .. JsonTexte(NomDe(m)),
        '"affiche": ' .. JsonTexte(Texte(m, "PlayerFacingName")),
        '"mode": ' .. JsonValeur(Lire(function() return m.GameMode end)),
        '"grille_nom": ' .. JsonValeur(Lire(function() return m.GridMakeup.PlayerFacingName:ToString() end)),
        '"grille": ' .. GrilleJson(Lire(function() return m.GridMakeup end)),
    }, ", ") .. "}"
end

local function ListeJson(l)
    local modes, planetes, ensembles, rapides = {}, {}, {}, {}
    pcall(function()
        l.QuickRaceGameModes:ForEach(function(_, e)
            local o = e:get()
            table.insert(modes, JsonTexte(EstValide(o) and NomDe(o) or "?"))
        end)
    end)
    if CONFIG.Exploration_Souples then   -- (liste de références souples : sinon seulement comptée)
        pcall(function()
            l.QuickRacePlanets:ForEach(function(_, e)
                table.insert(planetes, JsonValeur(CheminSouple(Lire(function() return e:get() end))))
            end)
        end)
    end
    pcall(function()
        l.AllEventSets:ForEach(function(_, e)
            local s = e:get()
            local n = 0
            pcall(function() s.Events:ForEach(function() n = n + 1 end) end)
            table.insert(ensembles, '{"nom": ' .. JsonValeur(Lire(function() return s.PlayerFacingName:ToString() end))
                .. ', "epreuves": ' .. n .. "}")
        end)
    end)
    pcall(function()
        l.QuickPlayEvents:ForEach(function(_, e)
            local o = e:get()
            table.insert(rapides, JsonTexte(EstValide(o) and NomDe(o) or "?"))
        end)
    end)
    return "    {" .. table.concat({
        '"chemin": ' .. JsonValeur(Lire(function() return Chemin(l) end)),
        '"modes_course_rapide": [' .. table.concat(modes, ", ") .. "]",
        '"planetes_course_rapide": [' .. table.concat(planetes, ", ") .. "]",
        '"nb_planetes_course_rapide": ' .. JsonValeur(Nombre(function() return l.QuickRacePlanets end)),
        '"ensembles": [' .. table.concat(ensembles, ", ") .. "]",
        '"epreuves_jeu_rapide": [' .. table.concat(rapides, ", ") .. "]",
    }, ", ") .. "}"
end

-- ── Pilotes : leurs « styles » (capacités, traits, build) et leurs builds d'IA ──
--   RacerDef ─┬─ CampaignRacerStyle ──► RacerStyle : StandardAbilities, Traits,
--             └─ PvpRacerStyles[mode] ─►             BuildUpgradePriority, VehicleBuildOverride
--   PvpRacerSetup / CampaignRacerSetup ─► Build (RacerBuildDef) ─► un build par type de véhicule

-- Un build du jeu (VehicleBuildDef) : niveaux, capacités, crash, affixes (chemins
-- d'objets, comme dans le catalogue, pour pouvoir le recharger dans la fenêtre)
local function BuildJson(b)
    if b == nil or not EstValide(b) then
        return "null"
    end
    local niveaux, capacites, affixes = {}, {}, {}
    pcall(function()
        b.SlotToUpgradeLevelMap:ForEach(function(k, v)
            table.insert(niveaux, '"' .. tostring(Lire(function() return k:get() end)) .. '": '
                .. JsonValeur(Lire(function() return v:get() end)))
        end)
    end)
    pcall(function()
        b.AbilitySlots:ForEach(function(_, e)
            local c = e:get()
            table.insert(capacites, JsonValeur(EstValide(c) and Lire(function() return Chemin(c) end) or nil))
        end)
    end)
    pcall(function()
        b.Affixes:ForEach(function(_, e)
            local a = e:get()
            table.insert(affixes, JsonValeur(EstValide(a) and Lire(function() return Chemin(a) end) or nil))
        end)
    end)
    return "{" .. table.concat({
        '"chemin": ' .. JsonValeur(Lire(function() return Chemin(b) end)),
        '"niveaux": {' .. table.concat(niveaux, ", ") .. "}",
        '"capacites": [' .. table.concat(capacites, ", ") .. "]",
        '"crash": ' .. JsonValeur(Lire(function() local c = b.CrashAbility; return EstValide(c) and Chemin(c) or nil end)),
        '"affixes": [' .. table.concat(affixes, ", ") .. "]",
        '"ramjet": ' .. JsonValeur(Lire(function() return b.RamjetInstalled end)),
        '"boost": ' .. JsonValeur(Lire(function() return b.BasicBoostType end)),
        '"pannes": ' .. JsonValeur(Lire(function() return b.CriticalMalfunctions end)),
    }, ", ") .. "}"
end

-- Un trait (passif propre au pilote) : chemin, et s'il est chargé (ou
-- chargeable), son nom, sa description et ses valeurs ({perc}, {int}…)
local function TraitJson(souple)
    local chemin = CheminSouple(souple)
    local trait = Lire(function() local o = souple:get(); return EstValide(o) and o or nil end)
    if not trait and CONFIG.Exploration_Charger and chemin and chemin:sub(1, 1) == "/" then
        trait = Lire(function() local o = StaticFindObject(chemin); return EstValide(o) and o or nil end)
            or Lire(function() local o = LoadAsset(chemin); return EstValide(o) and o or nil end)
    end
    local champs = { '"chemin": ' .. JsonValeur(chemin) }
    if trait then
        table.insert(champs, '"affiche": ' .. JsonTexte(Texte(trait, "PlayerFacingName")))
        table.insert(champs, '"description": ' .. JsonTexte(Texte(trait, "PlayerFacingDescription")))
        table.insert(champs, '"affiche_src": ' .. JsonValeur(TexteSource(trait, "PlayerFacingName")))
        table.insert(champs, '"description_src": ' .. JsonValeur(TexteSource(trait, "PlayerFacingDescription")))
        table.insert(champs, '"perc": ' .. CarteEnJson(trait, "DescriptionPercentParameters").json)
        table.insert(champs, '"int": ' .. CarteEnJson(trait, "DescriptionIntParameters").json)
    end
    return "{" .. table.concat(champs, ", ") .. "}"
end

local function StyleJson(style)
    if style == nil or not EstValide(style) then
        return "null"
    end
    local capacites, traits, priorites = {}, {}, {}
    if CONFIG.Exploration_Souples then   -- (listes de références souples : sinon seulement comptées)
        pcall(function()
            style.StandardAbilities:ForEach(function(_, e)
                table.insert(capacites, JsonValeur(CheminSouple(Lire(function() return e:get() end))))
            end)
        end)
        pcall(function()
            style.Traits:ForEach(function(_, e)
                table.insert(traits, TraitJson(e:get()))
            end)
        end)
    end
    pcall(function()
        style.BuildUpgradePriority:ForEach(function(_, e)
            local etape = {}
            pcall(function()
                e:get().UpgradeSlotDistribution:ForEach(function(_, d)
                    local s = d:get()
                    table.insert(etape, '{"emplacement": ' .. JsonValeur(Lire(function() return s.Slot end))
                        .. ', "part": ' .. JsonValeur(Lire(function() return s.StatDistribution end)) .. "}")
                end)
            end)
            table.insert(priorites, "[" .. table.concat(etape, ", ") .. "]")
        end)
    end)
    return "{" .. table.concat({
        '"chemin": ' .. JsonValeur(Lire(function() return Chemin(style) end)),
        '"nom": ' .. JsonTexte(NomDe(style)),
        '"affiche": ' .. JsonTexte(Texte(style, "PlayerFacingName")),
        '"description": ' .. JsonTexte(Texte(style, "PlayerFacingDescription")),
        '"rang": ' .. JsonValeur(Lire(function() return style.Rank end)),
        '"capacites": [' .. table.concat(capacites, ", ") .. "]",
        '"nb_capacites": ' .. JsonValeur(Nombre(function() return style.StandardAbilities end)),
        '"traits": [' .. table.concat(traits, ", ") .. "]",
        '"nb_traits": ' .. JsonValeur(Nombre(function() return style.Traits end)),
        '"priorites_stats": [' .. table.concat(priorites, ", ") .. "]",
        '"build_impose": ' .. JsonValeur(CheminSouple(DuSouple(function() return style.VehicleBuildOverride end))),
    }, ", ") .. "}"
end

local function PiloteJson(p)
    local pvp = {}
    pcall(function()
        p.PvpRacerStyles:ForEach(function(k, v)
            table.insert(pvp, '{"mode": ' .. JsonValeur(Lire(function() return k:get() end))
                .. ', "style": ' .. StyleJson(Lire(function() return v:get() end)) .. "}")
        end)
    end)
    return "    {" .. table.concat({
        '"chemin": ' .. JsonValeur(Lire(function() return Chemin(p) end)),
        '"nom": ' .. JsonTexte(NomDe(p)),
        '"affiche": ' .. JsonTexte(Texte(p, "CharacterName")),
        '"vehicule_prefere": ' .. JsonValeur(Lire(function() return p.PreferredVehicleType end)),
        '"style_campagne": ' .. StyleJson(Lire(function() return p.CampaignRacerStyle end)),
        '"styles_multi": [' .. table.concat(pvp, ", ") .. "]",
    }, ", ") .. "}"
end

-- Pilote de l'IA du jeu (PvpRacerSetup, CampaignRacerSetup) : son build par type de véhicule
local function PiloteIAJson(s)
    local builds = Lire(function() return s.Build end)
    local function Pour(champ)
        return BuildJson(Lire(function() return builds[champ] end))
    end
    return "    {" .. table.concat({
        '"chemin": ' .. JsonValeur(Lire(function() return Chemin(s) end)),
        '"classe": ' .. JsonTexte(ClasseDe(s)),
        '"pilote": ' .. JsonValeur(Lire(function() local c = s.Character; return EstValide(c) and Chemin(c) or nil end)),
        '"builds": {' .. table.concat({ '"voiture": ' .. Pour("CarBuild"), '"motojet": ' .. Pour("BikeBuild"),
                                        '"skimmer": ' .. Pour("SkimmerBuild"), '"module": ' .. Pour("PlaneBuild") }, ", ")
            .. "}",
    }, ", ") .. "}"
end

local function ParcoursJson(r)
    local styles = {}
    pcall(function()
        r.AvailableRacerStyles:ForEach(function(_, e)
            local o = e:get()
            table.insert(styles, JsonTexte(EstValide(o) and NomDe(o) or "?"))
        end)
    end)
    return "    {" .. table.concat({
        '"chemin": ' .. JsonValeur(Lire(function() return Chemin(r) end)),
        '"affiche": ' .. JsonTexte(Texte(r, "PlayerFacingName")),
        '"vehicule_impose": ' .. JsonValeur(Lire(function() return r.ForceVehicleTypeOnAllPlayers end)),
        '"styles": [' .. table.concat(styles, ", ") .. "]",
    }, ", ") .. "}"
end

-- En course : quel style le jeu a-t-il mis sur le PlayerState du joueur ?
-- (lecture seule, noté une fois par carte : on saura si l'Arcade s'en sert)
local styleNoteSurCarte = nil
local function NoterStyleDuJoueur()
    local carte = NomCarte()
    if carte == styleNoteSurCarte or carte == CONFIG.CarteMenu then
        return
    end
    local controleur = Controleur()
    if not EstValide(controleur) or not EstValide(controleur.PlayerState) then
        return
    end
    styleNoteSurCarte = carte
    local style = Lire(function() return controleur.PlayerState[CONFIG.Exploration_StyleJoueur] end)
    Detail("exploration : style du joueur sur " .. carte .. " = "
           .. (style ~= nil and EstValide(style) and NomDe(style) or "aucun"))
end

-- ── Miettes contre les plantages ──
--   avant chaque étape : echange/exploration-etape.txt = nom de l'étape
--   exploration finie   : le fichier est effacé
--   session suivante    : s'il est encore là, cette étape a fait planter le
--                         jeu → ajoutée à exploration-interdites.txt, et sautée
--                         désormais (on ne plante jamais deux fois au même endroit)
local FICHIER_ETAPE = CONFIG.DossierEchange .. "exploration-etape.txt"
local FICHIER_INTERDITES = CONFIG.DossierEchange .. "exploration-interdites.txt"

local function EtapesInterdites()
    local interdites = {}
    local f = io.open(FICHIER_INTERDITES, "r")
    if f then
        for ligne in f:lines() do
            if ligne ~= "" then
                interdites[ligne] = true
            end
        end
        f:close()
    end
    local m = io.open(FICHIER_ETAPE, "r")
    if m then
        local etape = (m:read("*l") or ""):match("^%s*(.-)%s*$")
        m:close()
        os.remove(FICHIER_ETAPE)
        if etape ~= "" and not interdites[etape] then
            interdites[etape] = true
            local a = io.open(FICHIER_INTERDITES, "a")
            if a then
                a:write(etape .. "\n")
                a:close()
            end
            Detail("exploration : l'étape « " .. etape .. " » a fait planter le jeu la dernière fois : elle est sautée désormais")
        end
    end
    return interdites
end

local function EcrireMiette(etape)
    local f = io.open(FICHIER_ETAPE, "w")
    if f then
        f:write(etape)
        f:close()
    end
end

local function Miette(etape)
    EcrireMiette(etape)
    Detail("exploration : étape « " .. etape .. " »")
end

-- Les étapes interdites ne sont lues qu'une fois par session, au premier
-- besoin : c'est là qu'est consommée la miette d'un plantage précédent.
local interditesSession = nil
local function Interdites()
    if interditesSession == nil then
        interditesSession = EtapesInterdites()
    end
    return interditesSession
end

-- Charge un objet (build, trait…) depuis le disque s'il n'est pas déjà en
-- mémoire (v0.9.9). Chaque chargement a sa miette « charger <chemin> » : s'il
-- fait planter le jeu, la session suivante saute CET objet seulement.
-- `apres` : la miette de l'étape en cours, remise après le chargement (une
-- seule miette à la fois) ; sinon la miette est effacée.
local function ChargerProtege(chemin, apres)
    if not chemin or chemin == "" then
        return nil
    end
    local objet = StaticFindObject(chemin)
    if EstValide(objet) then
        return objet
    end
    local etape = "charger " .. chemin
    if not CONFIG.ChargementAssets or Interdites()[etape] then
        return nil
    end
    EcrireMiette(etape)
    pcall(function() LoadAsset(chemin) end)
    if apres then
        EcrireMiette(apres)
    else
        os.remove(FICHIER_ETAPE)
    end
    objet = StaticFindObject(chemin)
    return EstValide(objet) and objet or nil
end

-- Vrai si le chargement de cet objet a fait planter une session précédente
local function ChargementInterdit(chemin)
    return Interdites()["charger " .. chemin] == true
end

local function ExplorerEpreuves()
    local interdites = Interdites()
    local function Liste(classes, convertir)
        local vus, elements = {}, {}
        for _, classe in ipairs(classes) do
            for _, o in ipairs(FindAllOf(classe) or {}) do
                if EstValide(o) and not NomDe(o):find("^Default__") then
                    local chemin = Lire(function() return Chemin(o) end) or tostring(o)
                    if not vus[chemin] then
                        vus[chemin] = true
                        table.insert(elements, { convertir(o) })
                    end
                end
            end
        end
        return elements
    end
    local sautees = {}
    local function Etape(nom, classes, convertir)
        if interdites[nom] then
            table.insert(sautees, JsonTexte(nom))
            return {}
        end
        Miette(nom)
        return Liste(classes, convertir)
    end
    local modes = Etape("modes", { CONFIG.Exploration_ClasseModes }, ModeJson)
    local listes = Etape("listes", { CONFIG.Exploration_ClasseListes }, ListeJson)
    local epreuves = Etape("epreuves", CONFIG.Exploration_ClassesEpreuves, EpreuveJson)
    local pilotes = Etape("pilotes", { CONFIG.Exploration_ClassePilotes }, PiloteJson)
    local pilotesIA = Etape("pilotes_ia", CONFIG.Exploration_ClassesPilotesIA, PiloteIAJson)
    local parcours = Etape("parcours", { CONFIG.Exploration_ClasseParcours }, ParcoursJson)
    Miette("ecriture")

    -- Résumé : nombre d'épreuves par mode, et celles qui imposent des adversaires
    local parMode, avecAdversaires = {}, 0
    for _, e in ipairs(epreuves) do
        local cle = tostring(e[3])
        parMode[cle] = (parMode[cle] or 0) + 1
        if (e[2] or 0) > 0 then
            avecAdversaires = avecAdversaires + 1
        end
    end
    local resume = {}
    for mode, n in pairs(parMode) do
        table.insert(resume, "mode " .. mode .. " : " .. n)
    end
    table.sort(resume)

    local fonctions = {}
    for _, nom in ipairs({ "LaunchCustomRace", "LaunchQuickRace" }) do
        local f = StaticFindObject("/Script/Griffin." .. CONFIG.ClasseModeMenu .. ":" .. nom)
        table.insert(fonctions, '"' .. nom .. '": ' .. tostring(EstValide(f)))
    end
    local function Bloc(elements)
        local t = {}
        for _, e in ipairs(elements) do
            table.insert(t, e[1])
        end
        return table.concat(t, ",\n")
    end
    local contenu = table.concat({
        "{",
        '  "modes": [', Bloc(modes), "  ],",
        '  "listes": [', Bloc(listes), "  ],",
        '  "epreuves": [', Bloc(epreuves), "  ],",
        '  "pilotes": [', Bloc(pilotes), "  ],",
        '  "pilotes_ia": [', Bloc(pilotesIA), "  ],",
        '  "parcours_multi": [', Bloc(parcours), "  ],",
        '  "etapes_sautees": [' .. table.concat(sautees, ", ") .. "],",
        '  "fonctions": {' .. table.concat(fonctions, ", ") .. "}",
        "}",
    }, "\n")
    local fichier = CONFIG.DossierEchange .. "epreuves.json"
    local f = io.open(fichier .. ".tmp", "w")
    if not f then
        Detail("exploration : impossible d'écrire " .. fichier)
        os.remove(FICHIER_ETAPE)   -- (ce n'est pas un plantage)
        return
    end
    f:write(contenu)
    f:close()
    os.remove(fichier)
    os.rename(fichier .. ".tmp", fichier)
    os.remove(FICHIER_ETAPE)   -- exploration finie sans plantage
    Detail(string.format("exploration : %d modes, %d listes, %d épreuves (%s), dont %d avec adversaires imposés ; "
                         .. "%d pilotes, %d pilotes IA, %d parcours multi ; %s",
                         #modes, #listes, #epreuves, table.concat(resume, ", "), avecAdversaires,
                         #pilotes, #pilotesIA, #parcours, table.concat(fonctions, ", ")))
end

-- ─────────────────────────────────────────────────────────────────────────
--  STYLES DES PILOTES → echange/styles.json (v0.9.6), au menu principal
--  Pour chaque pilote, ses styles (multijoueur par mode, campagne) ; pour
--  chaque style, son nom, sa description, son build (stats, capacités, crash,
--  affixes) et ses traits (buffs) avec leur description. Le contenu des
--  styles vient de STYLES_PILOTES (voir en haut). La fenêtre s'en sert pour
--  remplir l'onglet Build quand on choisit un pilote.
--     "pilotes": [{"chemin": …, "styles": {"5": <style>, "2": …, "campagne": …}}]
--     (modes : 2 tournoi solo, 3 tournoi de modules, 5 action instantanée,
--      6 action instantanée en module)
-- ─────────────────────────────────────────────────────────────────────────
local stylesExportes = false

-- Nom de l'étape pour la miette de l'écriture de styles.json (lecture de ce
-- qui est en mémoire seulement : les chargements ont chacun leur miette)
local ETAPE_STYLES = "styles"

-- Pilotes → leurs styles (références directes : lisibles sans risque).
-- Rend les lignes JSON des pilotes et les styles utilisés (chemin → objet).
local function PilotesEtStyles()
    local pilotes, utilises = {}, {}
    for _, p in ipairs(FindAllOf(CONFIG.ClassesCatalogue.Pilotes) or {}) do
        if EstValide(p) and not NomDe(p):find("^Default__") then
            local styles = {}
            local function Noter(cle, s)
                if s ~= nil and EstValide(s) then
                    local chemin = Lire(function() return Chemin(s) end)
                    if chemin then
                        table.insert(styles, JsonTexte(cle) .. ": " .. JsonTexte(chemin))
                        utilises[chemin] = s
                    end
                end
            end
            pcall(function()
                p.PvpRacerStyles:ForEach(function(k, v)
                    Noter(tostring(k:get()), v:get())
                end)
            end)
            Noter("campagne", Lire(function() return p.CampaignRacerStyle end))
            table.insert(pilotes, '    {"chemin": ' .. JsonValeur(Lire(function() return Chemin(p) end))
                .. ', "styles": {' .. table.concat(styles, ", ") .. "}}")
        end
    end
    return pilotes, utilises
end

-- Au menu (v0.9.9) : charge peu à peu les builds et traits des styles
-- utilisés qui ne sont pas en mémoire, Chargement_ParPassage par passage de
-- la boucle (0,5 s). Vrai quand tout a été essayé.
--
--   passage 1 : liste des chemins (STYLES_PILOTES des styles utilisés)
--   passage 2, 3… : 4 chargements (chacun avec sa miette), puis on rend la main
--   dernier passage : vrai → ExporterStyles écrit styles.json
-- Chaque objet est LU aussitôt chargé (ou trouvé) et son JSON est gardé dans
-- `json` : le jeu décharge ce qu'il n'utilise pas (ramasse-miettes d'Unreal).
-- Le 12/10 à 16:50, sans cette précaution, il ne restait que 14 builds sur
-- 21 et 29 traits sur 50 au moment d'écrire styles.json.
local chargementStyles = nil   -- { liste, builds, json, i, charges, introuvables, sautes, passages }

-- Un trait d'un style : son JSON pour styles.json
local function TraitStyleJson(o, chemin)
    return "    {" .. table.concat({
        '"chemin": ' .. JsonTexte(chemin),
        '"nom": ' .. JsonTexte(NomDe(o)),
        '"affiche": ' .. JsonTexte(Texte(o, "PlayerFacingName")),
        '"description": ' .. JsonTexte(Texte(o, "PlayerFacingDescription")),
        '"perc": ' .. CarteEnJson(o, "DescriptionPercentParameters").json,
        '"int": ' .. CarteEnJson(o, "DescriptionIntParameters").json,
    }, ", ") .. "}"
end

local function ChargerStylesPeuAPeu()
    local c = chargementStyles
    if not c then
        c = { liste = {}, builds = {}, json = {}, i = 1, charges = 0, introuvables = 0, sautes = 0, passages = 0 }
        chargementStyles = c
        local vus = {}
        local function Ajouter(chemin)
            if chemin and chemin ~= "" and not vus[chemin] then
                vus[chemin] = true
                table.insert(c.liste, chemin)
            end
        end
        local _, utilises = PilotesEtStyles()
        for chemin in pairs(utilises) do
            local contenu = STYLES_PILOTES[chemin] or {}
            if contenu.build then
                c.builds[contenu.build] = true
            end
            Ajouter(contenu.build)
            for _, t in ipairs(contenu.traits or {}) do
                Ajouter(t)
            end
        end
        table.sort(c.liste)   -- (même ordre à chaque session)
        return false
    end
    c.passages = c.passages + 1
    local faits = 0
    while c.i <= #c.liste and faits < CONFIG.Chargement_ParPassage do
        local chemin = c.liste[c.i]
        c.i = c.i + 1
        local o = StaticFindObject(chemin)
        if not EstValide(o) then
            o = nil
            if ChargementInterdit(chemin) then
                c.sautes = c.sautes + 1
            else
                faits = faits + 1
                o = ChargerProtege(chemin)
                if o then
                    c.charges = c.charges + 1
                else
                    c.introuvables = c.introuvables + 1
                end
            end
        end
        if o then   -- lu tout de suite, avant que le jeu ne le décharge
            c.json[chemin] = c.builds[chemin] and BuildJson(o) or TraitStyleJson(o, chemin)
        end
    end
    if c.i <= #c.liste then
        return false
    end
    Detail(Traduire("styles_charges", c.charges, #c.liste, c.passages, c.introuvables, c.sautes))
    return true
end

local function ExporterStyles()
    if not CONFIG.Styles or Interdites()[ETAPE_STYLES] then
        stylesExportes = true
        return
    end
    -- 0. Les builds et traits pas encore en mémoire, peu à peu (v0.9.9)
    if CONFIG.ChargementAssets and not ChargerStylesPeuAPeu() then
        return   -- la suite au prochain passage
    end
    stylesExportes = true   -- une seule fois par session, même en cas d'échec
    Miette(ETAPE_STYLES)
    -- 1. Pilotes → leurs styles
    local pilotes, utilises = PilotesEtStyles()
    -- 2. Styles utilisés par les pilotes, et leurs traits : contenu lu au
    -- chargement (ChargerStylesPeuAPeu), sinon ce qui est en mémoire. Rien
    -- n'est chargé ici.
    local lus = chargementStyles and chargementStyles.json or {}
    local function EnMemoire(chemin)
        local o = chemin and chemin ~= "" and StaticFindObject(chemin) or nil
        return EstValide(o) and o or nil
    end
    local styles, traits, traitsVus, nbBuilds = {}, {}, {}, 0
    local buildsDemandes, traitsDemandes = 0, 0   -- (pour le journal : combien sont en mémoire)
    for chemin, s in pairs(utilises) do
        local contenu = STYLES_PILOTES[chemin] or {}
        if contenu.build then
            buildsDemandes = buildsDemandes + 1
        end
        local buildJson = contenu.build and lus[contenu.build]
        if buildJson then
            nbBuilds = nbBuilds + 1
        else
            local build = EnMemoire(contenu.build)
            if build then
                nbBuilds = nbBuilds + 1
            end
            buildJson = BuildJson(build)
        end
        local listeTraits, capacites = {}, {}
        for _, t in ipairs(contenu.traits or {}) do
            table.insert(listeTraits, JsonTexte(t))
            if not traitsVus[t] then
                traitsVus[t] = true
                traitsDemandes = traitsDemandes + 1
                local json = lus[t]
                if not json then
                    local o = EnMemoire(t)
                    json = o and TraitStyleJson(o, t)
                end
                if json then
                    table.insert(traits, json)
                end
            end
        end
        for _, c in ipairs(contenu.capacites or {}) do
            table.insert(capacites, JsonTexte(c))
        end
        table.insert(styles, "    {" .. table.concat({
            '"chemin": ' .. JsonTexte(chemin),
            '"nom": ' .. JsonTexte(NomDe(s)),
            '"affiche": ' .. JsonTexte(Texte(s, "PlayerFacingName")),
            '"description": ' .. JsonTexte(Texte(s, "PlayerFacingDescription")),
            '"rang": ' .. JsonValeur(Lire(function() return s.Rank end)),
            '"build": ' .. buildJson,
            '"build_chemin": ' .. JsonValeur(contenu.build),   -- (même si le build n'est pas en mémoire)
            '"capacites": [' .. table.concat(capacites, ", ") .. "]",
            '"traits": [' .. table.concat(listeTraits, ", ") .. "]",
        }, ", ") .. "}")
    end
    local contenu = table.concat({
        "{",
        '  "pilotes": [', table.concat(pilotes, ",\n"), "  ],",
        '  "styles": [', table.concat(styles, ",\n"), "  ],",
        '  "traits": [', table.concat(traits, ",\n"), "  ]",
        "}",
    }, "\n")
    local fichier = CONFIG.DossierEchange .. "styles.json"
    local f = io.open(fichier .. ".tmp", "w")
    if f then
        f:write(contenu)
        f:close()
        os.remove(fichier)
        os.rename(fichier .. ".tmp", fichier)
    end
    os.remove(FICHIER_ETAPE)   -- fini sans plantage
    Detail(Traduire("styles", #styles, nbBuilds, #traits))
    Detail(Traduire("styles_memoire", nbBuilds, buildsDemandes, #traits, traitsDemandes,
                    CONFIG.ChargementAssets and "oui" or "non"))
end

-- ─────────────────────────────────────────────────────────────────────────
--  DIFFICULTÉ DES IA (v0.9.7) : Cadet, Pilote, As, Champion
--
--  Comment le jeu règle ses IA (en-têtes : rapports ia, ia-suite, ia-tune) :
--
--    contrôleur (joueur ou IA) ── GameTuneComponent ─┬─ RaceTuneData : base commune
--                                                    │    └─ Config : AiMaxTimeAheadModifier…
--                                                    └─ TuneSets appliqués (par des passifs)
--    réglages lus par le jeu = base + opérations des TuneSets
--
--    GameInstance ── CampaignDifficulties : les 4 difficultés du mode histoire
--                      ├─ FavoursToApply (faveurs = passifs) ── PassiveRule
--                      │    └─ TuneSetsToApply ── Operations (catégorie, propriété, valeur)
--                      └─ OpponentPassives : références souples, JAMAIS lues (comptées)
--
--  1. Au menu, une fois par session : les difficultés et ce que leurs faveurs
--     changent → echange/difficultes.json et le journal (lecture seule).
--  2. Au lancement d'une course avec IA : les « Ai… » de chaque base sont
--     réglés selon CONFIG.Difficulte_Niveaux, valeurs d'origine gardées.
--     Remis comme avant au retour au menu, ou au lancement suivant.
--  3. En course, une fois : la base de chaque contrôleur (joueur, IA), pour
--     vérifier que c'est bien celle qui a été réglée.
-- ─────────────────────────────────────────────────────────────────────────
local CHAMPS_IA = { "AiMaxTimeAheadModifier", "AiMinTimeAheadModifier", "AiMaxTimeAheadMultiplier",
                    "AiMinTimeAheadMultiplier", "AiTimeAheadSlowdownModifier",
                    "AiAggressionVPlayerCooldownMultiplier", "AiAggressionVPlayerChanceMultiplier",
                    "AiCountdownToSlamPlayerModifier", "AiAbilityChanceMultiplier" }

local function Chiffre(x)
    return type(x) == "number" and string.format("%.2f", x) or tostring(x)
end

-- Niveau (cadet, pilote, as, champion) d'une difficulté du jeu, d'après son
-- nom interne ou affiché. Relevé en jeu le 11/10/2026 :
--   CAM_DIFF_Easy      = Recrue (fr) / Cadet (en)        → cadet
--   CAM_DIFF_Normal    = Pilote / Pilot                  → pilote
--   CAM_DIFF_Hard      = As / Ace                        → as
--   CAM_DIFF_Nightmare = Antagoniste / Champion          → champion
-- (les boutons du menu du jeu disent aussi Rookie, Racer, Ace, Champion)
local function NiveauDifficulte(nom)
    local n = (nom or ""):lower()
    if n:find("easy") or n:find("rookie") or n:find("cadet") or n:find("recrue") then
        return "cadet"
    elseif n:find("nightmare") or n:find("champion") or n:find("antagon") then
        return "champion"
    elseif n:find("normal") or n:find("racer") or n:find("pilot") then
        return "pilote"
    elseif n:find("hard") or n:find("ace") or n:find("%f[%a]as%f[%A]") then
        return "as"
    end
    return nil
end

-- Les bases de réglages de course : celle du GameTuneComponent de secours de
-- la GameInstance, puis toutes celles en mémoire (au cas où les IA en ont une
-- autre). FindAllOf : seulement au menu (export, lancement), jamais en boucle.
local function BasesDeReglages()
    local bases, vues = {}, {}
    local function Ajouter(b)
        if b ~= nil and EstValide(b) and not NomDe(b):find("^Default__") then
            local adresse = b:GetAddress()
            if not vues[adresse] then
                vues[adresse] = true
                table.insert(bases, b)
            end
        end
    end
    local instance = InstanceJeu()
    if instance then
        Ajouter(Lire(function() return instance[CONFIG.Difficulte_Composant][CONFIG.Difficulte_Base] end))
    end
    for _, b in ipairs(FindAllOf(CONFIG.Difficulte_ClasseBase) or {}) do
        Ajouter(b)
    end
    return bases
end

local function ValeursIA(base)
    local v = {}
    pcall(function()
        local config = base.Config
        for _, champ in ipairs(CHAMPS_IA) do
            v[champ] = Lire(function() return config[champ] end)
        end
    end)
    return v
end

local function ValeursJson(v)
    local morceaux = {}
    for _, champ in ipairs(CHAMPS_IA) do
        table.insert(morceaux, JsonTexte(champ) .. ": " .. JsonValeur(v[champ]))
    end
    return "{" .. table.concat(morceaux, ", ") .. "}"
end

-- Les opérations d'une liste de réglages (TuneSet). Celles sur un réglage
-- « Ai… » sont aussi notées dans `reglagesIA`, pour le journal.
local function OperationsJson(tuneSet, champ, reglagesIA)
    local ops = {}
    pcall(function()
        tuneSet[champ]:ForEach(function(_, e)
            local op = e:get()
            local propriete = Lire(function() return op.Property:ToString() end) or "?"
            local operation = Lire(function() return op.Operation end)
            local flottant = Lire(function() return op.FloatParam end)
            local entier = Lire(function() return op.IntParam end)
            table.insert(ops, "{" .. table.concat({
                '"categorie": ' .. JsonValeur(Lire(function() return op.Category:ToString() end)),
                '"propriete": ' .. JsonTexte(propriete),
                '"operation": ' .. JsonValeur(operation),
                '"flottant": ' .. JsonValeur(flottant),
                '"entier": ' .. JsonValeur(entier),
                '"priorite": ' .. JsonValeur(Lire(function() return op.Priority end)),
            }, ", ") .. "}")
            if propriete:find("^Ai") then
                table.insert(reglagesIA, string.format("%s op%s %s/%s", propriete, tostring(operation),
                                                       Chiffre(flottant), tostring(entier)))
            end
        end)
    end)
    return "[" .. table.concat(ops, ", ") .. "]"
end

-- Une faveur (passif) : nom, description, et pour chaque règle, ses TuneSets
-- (avec leurs opérations) et ses autres effets (classes seulement)
local function FaveurJson(f, reglagesIA)
    local regles = {}
    pcall(function()
        f.PassiveRule:ForEach(function(_, e)
            local r = e:get()
            local tunes, autres = {}, {}
            pcall(function()
                r.TuneSetsToApply:ForEach(function(_, t)
                    local ts = t:get()
                    if ts ~= nil and EstValide(ts) then
                        table.insert(tunes, "{" .. table.concat({
                            '"nom": ' .. JsonTexte(NomDe(ts)),
                            '"operations": ' .. OperationsJson(ts, "Operations", reglagesIA),
                            '"operations_module": ' .. OperationsJson(ts, "PlaneOperations", reglagesIA),
                            '"operations_vehicule": ' .. OperationsJson(ts, "CoreVehicleOperations", reglagesIA),
                        }, ", ") .. "}")
                    end
                end)
            end)
            for _, champ in ipairs({ "Requirements", "OneTimeEffects", "TrackedEffects" }) do
                pcall(function()
                    r[champ]:ForEach(function(_, x)
                        local o = x:get()
                        if o ~= nil and EstValide(o) then
                            table.insert(autres, JsonTexte(champ .. " : " .. ClasseDe(o)))
                        end
                    end)
                end)
            end
            table.insert(regles, '{"tunesets": [' .. table.concat(tunes, ", ") .. '], "autres": ['
                                 .. table.concat(autres, ", ") .. "]}")
        end)
    end)
    return "{" .. table.concat({
        '"chemin": ' .. JsonValeur(Lire(function() return Chemin(f) end)),
        '"nom": ' .. JsonTexte(NomDe(f)),
        '"affiche": ' .. JsonTexte(Texte(f, "PlayerFacingName")),
        '"description": ' .. JsonTexte(Texte(f, "PlayerFacingDescription")),
        '"perc": ' .. CarteEnJson(f, "DescriptionPercentParameters").json,
        '"int": ' .. CarteEnJson(f, "DescriptionIntParameters").json,
        '"negative": ' .. JsonValeur(Lire(function() return f.bIsNegative end)),
        '"regles": [' .. table.concat(regles, ", ") .. "]",
    }, ", ") .. "}"
end

local function BarresJson(d)
    local barres = {}
    pcall(function()
        d.Bars:ForEach(function(_, e)
            local b = e:get()
            table.insert(barres, "{" .. table.concat({
                '"titre": ' .. JsonTexte(Lire(function() return b.Title:ToString() end) or ""),
                '"description": ' .. JsonTexte(Lire(function() return b.Description:ToString() end) or ""),
                '"valeur": ' .. JsonValeur(Lire(function() return b.BarAmount end)),
            }, ", ") .. "}")
        end)
    end)
    return "[" .. table.concat(barres, ", ") .. "]"
end

-- 1. Au menu : les difficultés du mode histoire → echange/difficultes.json
local difficultesExportees = false

local function ExporterDifficultes()
    difficultesExportees = true   -- une seule fois par session, même en cas d'échec
    if not CONFIG.Difficulte or Interdites()["difficultes"] then
        return
    end
    local instance = InstanceJeu()
    if not instance then
        return
    end
    Miette("difficultes")
    local entrees = {}
    pcall(function()
        instance[CONFIG.Difficulte_Liste]:ForEach(function(_, e)
            local d = e:get()
            if d == nil or not EstValide(d) then
                return
            end
            local nom, affiche = NomDe(d), Texte(d, "PlayerFacingName")
            local faveurs, reglagesIA = {}, {}
            pcall(function()
                d.FavoursToApply:ForEach(function(_, x)
                    local f = x:get()
                    if f ~= nil and EstValide(f) then
                        table.insert(faveurs, FaveurJson(f, reglagesIA))
                    end
                end)
            end)
            table.insert(entrees, { nom = nom, affiche = affiche, niveau = NiveauDifficulte(nom) or NiveauDifficulte(affiche),
                                    objet = d, faveurs = faveurs, reglagesIA = reglagesIA })
        end)
    end)
    -- Niveaux pas reconnus aux noms : l'ordre du jeu (du plus facile au plus
    -- dur), sans prendre un niveau déjà reconnu ailleurs
    if #entrees == 4 then
        local pris = {}
        for _, x in ipairs(entrees) do
            if x.niveau then pris[x.niveau] = true end
        end
        for i, niveau in ipairs({ "cadet", "pilote", "as", "champion" }) do
            if not entrees[i].niveau and not pris[niveau] then
                entrees[i].niveau = niveau
                pris[niveau] = true
            end
        end
    end
    local morceaux = {}
    for _, x in ipairs(entrees) do
        local d = x.objet
        local adversaires = Nombre(function() return d.OpponentPassives end)   -- (compter seulement)
        table.insert(morceaux, "    {" .. table.concat({
            '"niveau": ' .. JsonValeur(x.niveau),
            '"chemin": ' .. JsonValeur(Lire(function() return Chemin(d) end)),
            '"nom": ' .. JsonTexte(x.nom),
            '"affiche": ' .. JsonTexte(x.affiche),
            '"nom_precis": ' .. JsonTexte(Texte(d, "PreciseName")),
            '"description": ' .. JsonTexte(Texte(d, "Description")),
            '"barres": ' .. BarresJson(d),
            '"gauntlet": ' .. JsonValeur(Lire(function() return d.bIsGauntlet end)),
            '"crashs_remis_au_depart": ' .. JsonValeur(Lire(function() return d.bDoesCrashAllowanceResetAtRaceStart end)),
            '"passifs_adversaires": ' .. JsonValeur(adversaires),
            '"faveurs": [' .. table.concat(x.faveurs, ", ") .. "]",
        }, ", ") .. "}")
        Detail(string.format("difficulté « %s » (%s, niveau %s) : %d faveur(s), %s passif(s) des adversaires, réglages IA : %s",
                             x.affiche, x.nom, tostring(x.niveau), #x.faveurs, tostring(adversaires),
                             #x.reglagesIA > 0 and table.concat(x.reglagesIA, ", ") or "aucun"))
    end
    local bases = {}
    for _, b in ipairs(BasesDeReglages()) do
        local v = ValeursIA(b)
        table.insert(bases, "    {" .. '"nom": ' .. JsonTexte(NomDe(b)) .. ', "chemin": '
                            .. JsonValeur(Lire(function() return Chemin(b) end)) .. ', "valeurs": ' .. ValeursJson(v) .. "}")
        local lu = {}
        for _, champ in ipairs(CHAMPS_IA) do
            table.insert(lu, champ .. " " .. Chiffre(v[champ]))
        end
        Detail(Traduire("difficulte_base", NomDe(b), table.concat(lu, ", ")))
    end
    -- Ce que le mod change pour chaque niveau (affiché par la fenêtre)
    local reglages = {}
    for _, niveau in ipairs({ "cadet", "pilote", "as", "champion" }) do
        local ecarts, champs = CONFIG.Difficulte_Niveaux[niveau] or {}, {}
        for _, champ in ipairs(CHAMPS_IA) do
            if type(ecarts[champ]) == "number" then
                table.insert(champs, JsonTexte(champ) .. ": " .. JsonValeur(ecarts[champ]))
            end
        end
        table.insert(reglages, "    " .. JsonTexte(niveau) .. ": {" .. table.concat(champs, ", ") .. "}")
    end
    local fichier = CONFIG.DossierEchange .. "difficultes.json"
    local f = io.open(fichier .. ".tmp", "w")
    if f then
        f:write("{\n  \"difficultes\": [\n" .. table.concat(morceaux, ",\n") .. "\n  ],\n  \"bases\": [\n"
                .. table.concat(bases, ",\n") .. "\n  ],\n  \"reglages_mod\": {\n"
                .. table.concat(reglages, ",\n") .. "\n  }\n}")
        f:close()
        os.remove(fichier)
        os.rename(fichier .. ".tmp", fichier)
    end
    os.remove(FICHIER_ETAPE)   -- fini sans plantage
    Detail(Traduire("difficultes", #entrees))
end

-- 2. Au lancement d'une course avec IA
local reglagesModifies = {}   -- adresse de la base → { objet, origine = { réglage → valeur } }
local difficulteEnCours = nil -- { niveau, etat = "attente" (menu) puis "course" }

RestaurerDifficulte = function()
    local remises = {}
    for _, e in pairs(reglagesModifies) do
        if EstValide(e.objet) then
            pcall(function()
                local config = e.objet.Config
                for champ, valeur in pairs(e.origine) do
                    config[champ] = valeur
                end
            end)
            table.insert(remises, NomDe(e.objet))
        end
    end
    if #remises > 0 then
        Detail(Traduire("difficulte_remise", table.concat(remises, ", ")))
    end
    reglagesModifies = {}
    difficulteEnCours = nil
end

-- Renvoie vrai si une difficulté est appliquée
AppliquerDifficulte = function(choix)
    local niveau = choix and choix.difficulte or ""
    local ecarts = CONFIG.Difficulte_Niveaux[niveau]
    if not (CONFIG.Difficulte and ecarts) then
        return false   -- « jeu » : réglages du jeu, rien à changer
    end
    local bases = BasesDeReglages()
    if #bases == 0 then
        Journal(Traduire("difficulte_ko"))
        return false
    end
    local parBase = {}   -- « RTD_X : réglage avant → après, … » pour le journal
    for _, base in ipairs(bases) do
        local changes = {}
        pcall(function()
            local config = base.Config
            local e = { objet = base, origine = {} }
            for _, champ in ipairs(CHAMPS_IA) do
                e.origine[champ] = config[champ]
            end
            reglagesModifies[base:GetAddress()] = e
            for _, champ in ipairs(CHAMPS_IA) do
                local ecart, origine = ecarts[champ], e.origine[champ]
                if type(ecart) == "number" and type(origine) == "number" then
                    local valeur = champ:find("Multiplier$") and origine * ecart or origine + ecart
                    config[champ] = valeur
                    table.insert(changes, string.format("%s %s → %s", champ, Chiffre(origine), Chiffre(valeur)))
                end
            end
        end)
        table.insert(parBase, NomDe(base) .. " : " .. (#changes > 0 and table.concat(changes, ", ") or "réglages du jeu"))
    end
    difficulteEnCours = { niveau = niveau, etat = "attente" }
    Detail(Traduire("difficulte_ok", choix.nom_difficulte or niveau, table.concat(parBase, " ; ")))
    return true
end

-- 3. En course : base de chaque contrôleur (une fois par course), et remise
-- comme avant au retour au menu
local basesNoteesPour = nil   -- PlayerState (adresse) de la course déjà notée

local function NoterBasesEnCourse()
    local c = Controleur()
    if not (c and EstValide(c.PlayerState) and Pion()) then
        return
    end
    local adresse = c.PlayerState:GetAddress()
    if basesNoteesPour == adresse then
        return
    end
    basesNoteesPour = adresse
    local function BaseDe(controleur)
        local base = Lire(function() return controleur.GameTuneComponent[CONFIG.Difficulte_Base] end)
        return (base ~= nil and EstValide(base)) and NomDe(base) or "?"
    end
    local basesIA, nbIA = {}, 0
    pcall(function()
        Monde().GameState.Racers:ForEach(function(_, e)
            local etat = e:get()
            if etat ~= nil and EstValide(etat) and etat:GetAddress() ~= adresse then
                local controleur = Lire(function() return etat:GetOwner() end)
                if controleur ~= nil and EstValide(controleur) then
                    nbIA = nbIA + 1
                    local nom = BaseDe(controleur)
                    basesIA[nom] = (basesIA[nom] or 0) + 1
                end
            end
        end)
    end)
    local resume = {}
    for nom, n in pairs(basesIA) do
        table.insert(resume, nom .. " ×" .. n)
    end
    table.sort(resume)
    Detail(Traduire("difficulte_course", BaseDe(c), nbIA > 0 and table.concat(resume, ", ") or "?"))
end

local function SuivreDifficulte()
    if not difficulteEnCours then
        return
    end
    local auMenu = NomCarte() == CONFIG.CarteMenu
    if difficulteEnCours.etat == "attente" and not auMenu then
        difficulteEnCours.etat = "course"
    elseif difficulteEnCours.etat == "course" then
        if auMenu then
            RestaurerDifficulte()
        else
            NoterBasesEnCourse()
        end
    end
end

-- ─────────────────────────────────────────────────────────────────────────
--  BUFFS DU PILOTE EN COURSE (v0.9.6)
--  La fenêtre envoie les traits du style du pilote (traits=<chemin>|<chemin>).
--  Une fois par course chargée, on les met dans la file d'attente du
--  gestionnaire de passifs du joueur ; le jeu les ajoute lui-même ensuite,
--  comme les traits de la campagne ou du multijoueur :
--     PlayerState.PassiveManagerComponent.PassivesToAdd  ← traits
--  Protégé par une miette (« buffs ») : en cas de plantage, la session
--  suivante ne les ajoute plus et le dit.
-- ─────────────────────────────────────────────────────────────────────────
local buffsPour = nil   -- PlayerState (adresse) qui a déjà reçu les buffs

local function AppliquerBuffs()
    if NomCarte() == CONFIG.CarteMenu then
        buffsPour = nil
        return
    end
    local c = dernierChoix
    if not (CONFIG.Styles and c and c.traits and c.traits ~= "") then
        return
    end
    local controleur = Controleur()
    if not EstValide(controleur) or not EstValide(controleur.PlayerState) or not EstValide(Pion()) then
        return
    end
    local etat = controleur.PlayerState
    local adresse = etat:GetAddress()
    if buffsPour == adresse then
        return
    end
    buffsPour = adresse
    if Interdites()["buffs"] then
        Journal(Traduire("buffs_interdits"))
        return
    end
    local gestionnaire = etat[CONFIG.Passifs_Composant]
    if not EstValide(gestionnaire) then
        Journal(Traduire("buffs_ko", CONFIG.Passifs_Composant))
        return
    end
    -- Miette posée AVANT de chercher les traits : si leur chargement fait
    -- planter le jeu, la session suivante le saura aussi
    Miette("buffs")
    local traits, noms = {}, {}
    for _, chemin in ipairs(Decouper(c.traits)) do
        local o = ChargerProtege(chemin, "buffs")   -- (la miette « buffs » est remise après)
        if o then
            table.insert(traits, o)
            table.insert(noms, Texte(o, "PlayerFacingName"))
        else
            Detail("trait introuvable (ni en mémoire, ni chargeable) : " .. chemin)
        end
    end
    if #traits == 0 then
        os.remove(FICHIER_ETAPE)   -- (ce n'est pas un plantage)
        Journal(Traduire("buffs_absents", #Decouper(c.traits)))
        return
    end
    local avant = 0
    pcall(function() avant = #gestionnaire[CONFIG.Passifs_Liste] end)
    local ok, err = pcall(function()
        local file = gestionnaire[CONFIG.Passifs_AAjouter]
        for _, o in ipairs(traits) do
            file[#file + 1] = o   -- ajout en fin de liste, une case à la fois
        end
    end)
    if not ok then
        os.remove(FICHIER_ETAPE)
        Journal(Traduire("buffs_ko", tostring(err)))
        return
    end
    Journal(Traduire("buffs_ok", #traits, table.concat(noms, ", ")))
    -- Contrôle : le jeu a-t-il pris les traits ? (et pas de plantage → miette retirée)
    PlusTard(CONFIG.Passifs_Controle, function()
        Proteger("buffs", function()
            os.remove(FICHIER_ETAPE)
            if EstValide(gestionnaire) then
                local apres = #gestionnaire[CONFIG.Passifs_Liste]
                Detail(Traduire("buffs_actifs", apres, avant))
            end
        end)
    end)
end

-- ─────────────────────────────────────────────────────────────────────────
--  APPARENCE DU VÉHICULE DU PILOTE (v0.9.9)
--  Commentaire Nexus : « quel que soit le podracer choisi, c'est le même
--  véhicule ». L'épreuve modèle impose son véhicule et son apparence ; le
--  mod ne changeait que le personnage.
--
--    RacerDef (pilote choisi)
--      └─ PreferredCustomisationForVehicleArchetype : archétype → « recette »
--         (classe UCstVehiclePresetRecipe : pièces, couleurs du véhicule)
--    GameState.EventRecipeState_Replication.Racers : la recette donnée par le
--         jeu à chaque pilote de la course (lue pour le journal)
--    PlayerState.VehicleCustomisationComponent
--      └─ Client_SetOverrideVehicleRecipe(recette) : fonction du jeu qui
--         impose une recette au véhicule du joueur
--
--  En course, une fois par course chargée, APRÈS les buffs (une seule miette
--  à la fois) : journal des recettes, puis, si le joueur n'a pas celle de son
--  pilote, la demande au jeu, relue 2 s plus tard. Miette « apparence » : en
--  cas de plantage, la session suivante ne le refait plus et le dit.
-- ─────────────────────────────────────────────────────────────────────────
local apparencePour = nil   -- PlayerState (adresse) déjà traité

local function NomClasse(c)
    return (c ~= nil and EstValide(c)) and NomDe(c) or "aucune"
end

-- (RecettePilote : définie plus haut, avant Lancer qui s'en sert aussi)

-- Le build que le jeu a donné au joueur (PlayerState.RacerBuildState.
-- VehicleBuilds[].VehicleBuildDef, lecture seule) : sert à vérifier que le
-- build de la fenêtre est bien utilisé, avec ou sans véhicule imposé.
local function BuildDuJoueur(etat)
    local lignes = {}
    pcall(function()
        etat.RacerBuildState.VehicleBuilds:ForEach(function(_, e)
            local b = e:get()
            table.insert(lignes, string.format("%s (type %s, %s capacité(s))",
                NomClasse(Lire(function() return b.VehicleBuildDef end)),
                tostring(Lire(function() return b.BuildArchetype end)),
                tostring(Lire(function() return #b.AbilitySlots end) or "?")))
        end)
    end)
    return #lignes > 0 and table.concat(lignes, " — ") or "rien lu"
end

-- Les recettes données par le jeu aux pilotes de la course : texte pour le
-- journal, et celle du joueur
local function RecettesDeLaCourse(adresseJoueur)
    local lignes, duJoueur = {}, nil
    pcall(function()
        Monde().GameState[CONFIG.Apparence_Etat].Racers:ForEach(function(_, e)
            local r = e:get()
            local joueur = Lire(function() return r.Player end)
            local estJoueur = joueur ~= nil and EstValide(joueur) and joueur:GetAddress() == adresseJoueur
            local recette = Lire(function() return r.VehicleCustomisation end)
            if estJoueur then
                duJoueur = recette
            end
            table.insert(lignes, string.format("%s%s (type %s) : %s", estJoueur and "vous, " or "",
                                               NomClasse(Lire(function() return r.Pilot end)),
                                               tostring(Lire(function() return r.vehicleType end)), NomClasse(recette)))
        end)
    end)
    return lignes, duJoueur
end

local apparenceAttente = 0  -- passages passés à attendre la fin des buffs

local function AppliquerApparence()
    if NomCarte() == CONFIG.CarteMenu then
        apparencePour = nil
        return
    end
    local c = dernierChoix
    if not (CONFIG.Apparence and c and c.pilote and c.pilote ~= "") then
        return
    end
    -- Les buffs (miette « buffs », ou un de leurs chargements) sont en cours :
    -- on attend qu'ils finissent (au plus 20 passages, 10 s)
    local f = io.open(FICHIER_ETAPE, "r")
    local enCours = f and f:read("*l") or ""
    if f then
        f:close()
    end
    if (enCours == "buffs" or enCours:find("^charger ")) and apparenceAttente < 20 then
        apparenceAttente = apparenceAttente + 1
        return
    end
    apparenceAttente = 0
    local controleur = Controleur()
    if not EstValide(controleur) or not EstValide(controleur.PlayerState) or not EstValide(Pion()) then
        return
    end
    local etat = controleur.PlayerState
    local adresse = etat:GetAddress()
    if apparencePour == adresse then
        return
    end
    apparencePour = adresse
    if Interdites()["apparence"] then
        Journal(Traduire("apparence_interdite"))
        return
    end
    Miette("apparence")
    -- 1. Ce que le jeu a donné à chaque pilote (lecture seule)
    local lignes, actuelle = RecettesDeLaCourse(adresse)
    Detail("apparence des véhicules de la course : " .. (#lignes > 0 and table.concat(lignes, " — ") or "rien lu"))
    Detail("build du joueur selon le jeu : " .. BuildDuJoueur(etat))
    -- 2. Celle du pilote choisi
    local pilote = StaticFindObject(c.pilote)
    local archetype = CONFIG.Apparence_Archetypes[c.type or ""]
    local voulue = (EstValide(pilote) and archetype) and RecettePilote(pilote, archetype) or nil
    if not voulue then
        os.remove(FICHIER_ETAPE)
        Journal(Traduire("apparence_aucune", EstValide(pilote) and NomDe(pilote) or tostring(c.pilote)))
        return
    end
    if actuelle ~= nil and EstValide(actuelle) and actuelle:GetAddress() == voulue:GetAddress() then
        os.remove(FICHIER_ETAPE)
        Detail("apparence : le véhicule a déjà celle du pilote (" .. NomDe(voulue) .. ")")
        return
    end
    local composant = Lire(function() return etat[CONFIG.Apparence_Composant] end)
    if not CONFIG.Apparence_Appliquer or not EstValide(composant) then
        os.remove(FICHIER_ETAPE)
        Detail(string.format("apparence : celle du pilote serait %s (demande %s)", NomDe(voulue),
                             CONFIG.Apparence_Appliquer and "impossible : composant introuvable" or "coupée"))
        return
    end
    local ok = Appeler(composant, CONFIG.Apparence_Fonction, voulue)
    Journal(Traduire(ok and "apparence_ok" or "apparence_ko", NomDe(voulue)))
    -- Relecture (pour le journal) ; pas de plantage → miette retirée
    PlusTard(CONFIG.Apparence_Controle, function()
        Proteger("apparence", function()
            os.remove(FICHIER_ETAPE)
            local apres = RecettesDeLaCourse(adresse)
            Detail(string.format("apparence, %d ms après : %s", CONFIG.Apparence_Controle,
                                 #apres > 0 and table.concat(apres, " — ") or "rien lu"))
        end)
    end)
end

-- ─────────────────────────────────────────────────────────────────────────
--  NOMS DU JEU DANS LA LANGUE DE LA FENÊTRE (v0.9.5)
--  Le jeu n'affiche ses textes que dans SA langue, et lire leur version
--  d'origine ne marche pas à travers UE4SS : il reconstruit le texte à partir
--  de sa version affichée (essai du 11/10/2026 : « Champs de guerre » des
--  deux côtés). On fait donc comme le menu Options du jeu :
--
--     langue du jeu ──► langue de la fenêtre (non enregistrée)
--     attente que les textes changent (quelques noms de circuits témoins)
--     lecture des noms et descriptions ──► echange/catalogue-<langue>.json
--     langue du jeu ◄── remise comme avant
--
--  Seulement au menu principal, une fois par langue et par session, et
--  seulement si la fenêtre n'est pas dans la langue du jeu. Le menu s'affiche
--  dans l'autre langue pendant 1 à 3 s. Protégé par les miettes (« traduction »).
-- ─────────────────────────────────────────────────────────────────────────
local traduction = { enCours = false, faites = {} }

local function CodeLangue(texte)
    return (texte or ""):sub(1, 2):lower()
end

-- Quelques noms de circuits : s'ils changent, la nouvelle langue est chargée
local function Temoins()
    local temoins = {}
    for _, c in ipairs(FindAllOf(CONFIG.ClassesCatalogue.Circuits) or {}) do
        if #temoins >= 30 then
            break
        end
        if EstValide(c) then
            table.insert(temoins, { objet = c, texte = Texte(c, "PlayerFacingName") })
        end
    end
    return temoins
end

local function TemoinsChanges(temoins)
    local n = 0
    for _, e in ipairs(temoins) do
        if EstValide(e.objet) and Texte(e.objet, "PlayerFacingName") ~= e.texte then
            n = n + 1
        end
    end
    return n
end

-- Écrit les textes (dans la langue actuelle du jeu) de tout ce que montre la
-- fenêtre, rangés par chemin d'objet. Renvoie le nombre d'objets écrits.
local function EcrireTraduction(code)
    local objets = {}
    local function Ajouter(o, chemin, textes)
        local morceaux = {}
        for cle, valeur in pairs(textes) do
            if valeur ~= "" then
                table.insert(morceaux, '"' .. cle .. '": ' .. JsonTexte(valeur))
            end
        end
        if chemin and #morceaux > 0 then
            table.insert(objets, "    " .. JsonTexte(chemin) .. ": {" .. table.concat(morceaux, ", ") .. "}")
        end
    end
    -- (chaque objet est protégé à part : un objet illisible ne gâche pas les autres)
    local function Parcourir(classe, champs)
        for _, o in ipairs(FindAllOf(classe) or {}) do
            pcall(function()
                if EstValide(o) and not NomDe(o):find("^Default__") then
                    local textes = {}
                    for cle, propriete in pairs(champs) do
                        textes[cle] = Texte(o, propriete)
                    end
                    Ajouter(o, Lire(function() return Chemin(o) end), textes)
                end
            end)
        end
    end
    Parcourir(CONFIG.ClassesCatalogue.Circuits, { affiche = "PlayerFacingName" })
    Parcourir(CONFIG.ClassesCatalogue.Planetes, { affiche = "PlayerFacingName" })
    Parcourir(CONFIG.ClassesCatalogue.Vehicules, { affiche = "PlayerFacingName" })
    Parcourir(CONFIG.ClassesCatalogue.Pilotes, { affiche = "CharacterName" })
    Parcourir(CONFIG.ClasseAffixe, { affiche = "PlayerFacingName", description = "PlayerFacingDescription",
                                     description_def = "FaultyPlayerFacingDescription" })
    -- Styles des pilotes et leurs traits (chargés juste avant par ExporterStyles)
    Parcourir(CONFIG.ClasseStyle, { affiche = "PlayerFacingName", description = "PlayerFacingDescription" })
    -- Difficultés du mode histoire (v0.9.7)
    Parcourir(CONFIG.Difficulte_ClasseDef, { affiche = "PlayerFacingName", description = "Description" })
    local traitsVus = {}
    for _, s in pairs(STYLES_PILOTES) do
        for _, chemin in ipairs(s.traits or {}) do
            if not traitsVus[chemin] then
                traitsVus[chemin] = true
                pcall(function()
                    local o = StaticFindObject(chemin)
                    if EstValide(o) then
                        Ajouter(o, chemin, { affiche = Texte(o, "PlayerFacingName"),
                                             description = Texte(o, "PlayerFacingDescription") })
                    end
                end)
            end
        end
    end
    -- Capacités : textes sur l'objet par défaut (CDO), rangés sous le chemin de la classe
    for _, classe in ipairs((ListeCapacites())) do
        pcall(function()
            local cdo = classe:GetCDO()
            if cdo ~= nil and EstValide(cdo) then
                Ajouter(classe, Lire(function() return Chemin(classe) end),
                        { affiche = Texte(cdo, "PlayerFacingName"), description = Texte(cdo, "Description") })
            end
        end)
    end
    local ui = FindFirstOf(CONFIG.ClasseConfigUI)
    local champsUI = {}
    if EstValide(ui) then
        for _, c in ipairs({ { "stats", "PartStatNames" }, { "emplacements", "PartSlotNames" },
                             { "avance_stats", "AdvancedPartStatNames" },
                             { "avance_emplacements", "AdvancedPartSlotNames" },
                             { "raretes", "PartQualityNames" } }) do
            table.insert(champsUI, '"' .. c[1] .. '": ' .. CarteTextesEnJson(ui, c[2]))
        end
        table.insert(champsUI, '"resilience": ' .. JsonTexte(Texte(ui, "ResilianceStatName")))
    end
    local fichier = CONFIG.DossierEchange .. "catalogue-" .. code .. ".json"
    local f = io.open(fichier .. ".tmp", "w")
    if not f then
        return 0
    end
    f:write("{\n  \"langue\": " .. JsonTexte(code) .. ",\n  \"objets\": {\n" .. table.concat(objets, ",\n")
            .. "\n  },\n  \"interface\": {" .. table.concat(champsUI, ", ") .. "}\n}")
    f:close()
    os.remove(fichier)
    os.rename(fichier .. ".tmp", fichier)
    return #objets
end

local function TraduireCatalogue(code)
    local bib = Bibliotheque(CONFIG.BibliothequeLangues)
    local origine = bib and Lire(function() return ChaineLua(bib:GetCurrentLanguage()) end)
    if not origine or origine == "" then
        return
    end
    traduction.enCours = true
    traduction.faites[code] = true   -- une seule tentative par langue et par session
    Miette("traduction")
    local temoins = Temoins()
    local function Finir(message)
        pcall(function() bib:SetCurrentLanguage(origine, false) end)   -- TOUJOURS remise
        os.remove(FICHIER_ETAPE)
        traduction.enCours = false
        Detail(message)
    end
    if not pcall(function() bib:SetCurrentLanguage(code, false) end) then
        Finir("traduction « " .. code .. " » : le jeu refuse de changer de langue")
        return
    end
    local essais = 0
    local function Essayer()
        essais = essais + 1
        local changes, ecrits = 0, 0
        Proteger("traduction", function() changes = TemoinsChanges(temoins) end)
        if changes == 0 and essais < CONFIG.Traduction_Essais then
            PlusTard(CONFIG.Traduction_Attente, Essayer)
            return
        end
        if changes > 0 then
            Proteger("traduction", function() ecrits = EcrireTraduction(code) end)
        end
        Finir(string.format("traduction « %s » : %d noms témoins changés après %d essai(s), %d objets écrits ; "
                            .. "langue du jeu remise à « %s »", code, changes, essais, ecrits, origine))
    end
    PlusTard(CONFIG.Traduction_Attente, Essayer)
end

-- Vrai si l'on est sur la carte du menu principal. On ne se fie pas seulement
-- à FrontEndGameMode : après un passage au menu, il peut traîner en mémoire
-- pendant la course (cause du crash du 10/10 après un Ctrl+R en course).
local function AuMenuPrincipal()
    return NomCarte() == CONFIG.CarteMenu and EstValide(FindFirstOf(CONFIG.ClasseModeMenu))
end

-- Boucle principale (fil du jeu, toutes les 0,5 s) : langue et commande de
-- la fenêtre, catalogue dès que le menu principal est atteint, chrono…
local function BouclePrincipale()
    Proteger("langue", LireLangue)
    local choix = nil
    Proteger("commande", function() choix = LireCommande() end)
    if not SessionProtegee() then
        if choix then
            Autorise()
        end
        return
    end
    if not catalogueExporte and os.clock() >= prochainEssaiCatalogue and AuMenuPrincipal() then
        Proteger("catalogue", ExporterCatalogue)
    end
    -- Exploration (lecture seule), une seule fois, une fois le catalogue fait
    if CONFIG.Exploration and catalogueExporte and not epreuvesExplorees and AuMenuPrincipal() then
        epreuvesExplorees = true   -- même si elle échoue : pas de nouvel essai toutes les 0,5 s
        Proteger("exploration", ExplorerEpreuves)
    end
    if CONFIG.Exploration then
        Proteger("style du joueur", NoterStyleDuJoueur)
    end
    -- Styles des pilotes (builds, buffs), une fois par session, au menu
    if catalogueExporte and not stylesExportes and AuMenuPrincipal() then
        Proteger("styles", ExporterStyles)
    end
    -- Difficultés du mode histoire (lecture seule), une fois par session, au menu
    if catalogueExporte and stylesExportes and not difficultesExportees and AuMenuPrincipal() then
        Proteger("difficultes", ExporterDifficultes)
    end
    -- Difficulté des IA : bases notées en course, remise au retour au menu
    Proteger("difficulte", SuivreDifficulte)
    -- Adversaires des courses de modules : liste du jeu remise au retour au menu
    Proteger("adversaires", SuivreAdversaires)
    -- Buffs du pilote choisi, une fois par course chargée
    Proteger("buffs", AppliquerBuffs)
    -- Apparence du véhicule du pilote choisi, une fois par course, après les buffs
    Proteger("apparence", AppliquerApparence)
    -- Noms du jeu dans la langue de la fenêtre, si elle n'est pas celle du jeu
    if CONFIG.Traduction and catalogueExporte and (epreuvesExplorees or not CONFIG.Exploration)
       and stylesExportes and not traduction.enCours and not traduction.faites[langue] and AuMenuPrincipal() then
        local jeu = CodeLangue(Lire(function()
            return ChaineLua(Bibliotheque(CONFIG.BibliothequeLangues):GetCurrentLanguage())
        end))
        if jeu ~= "" and langue ~= jeu and not Interdites()["traduction"] then
            Proteger("traduction", TraduireCatalogue, langue)
        elseif jeu == langue then
            -- Rien à traduire pour cette langue : on ne revérifie plus
            -- (sinon, FindFirstOf toutes les 0,5 s au menu)
            traduction.faites[langue] = true
        end
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
end

Boucler(CONFIG.DelaiScrutation, function() Proteger("boucle", BouclePrincipale) end)

-- ─────────────────────────────────────────────────────────────────────────
--  TOUCHES
--  UE4SS les détecte sur son propre fil : LierTouche ne fait que lever un
--  drapeau, la boucle des touches agit dans le fil du jeu (voir LierTouche).
-- ─────────────────────────────────────────────────────────────────────────
LierTouche(CONFIG.ToucheRelancer, {}, function()
    if not Autorise() then
        return
    end
    if dernierChoix then
        Lancer(dernierChoix)
    else
        Journal(Traduire("f5_rien"))
    end
end, "F5")

LierTouche(CONFIG.ToucheRecommencer, {}, Recommencer, "F6")

-- Save states : F7/F8, Maj+F7/Maj+F8, Ctrl+F7/Ctrl+F8 pour les emplacements 1, 2, 3
for n, t in ipairs(CONFIG.SaveState_Touches) do
    LierTouche(t.touche, t.modificateurs, function() Sauver(n) end)
    LierTouche(t.charger, t.modificateurs, function() Charger(n) end)
end

Boucler(CONFIG.Touches_Delai, TraiterTouches)

-- Save states à la manette (croix bas / droite), lus 30 fois par seconde.
-- Une erreur ici ne doit jamais arrêter la boucle ; elle n'est notée qu'une fois.
Boucler(CONFIG.Manette_Delai, function() Proteger("manette", LireManette) end)

LireLangue()
Journal(Traduire("charge", "2.0.0"))
