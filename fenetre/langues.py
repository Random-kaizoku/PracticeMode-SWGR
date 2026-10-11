"""Textes de la fenêtre et du launcher, en français et en anglais.

Chaque texte a une clé et ses deux versions : (français, anglais).
    t("lancer")                → « ▶  Lancer la course » ou « ▶  Start the race »
    t("emplacement_n", n=2)    → « Emplacement 2 » ou « Slot 2 »

La langue se choisit avec le bouton FR / EN de la fenêtre ; elle est gardée
dans PracticeMode.ini et transmise au mod par echange/langue.txt.
Pour ajouter une langue : son code dans LANGUES, puis une version de plus
à chaque texte (dans le même ordre).

Les noms qui viennent du jeu (circuits, pilotes, affixes, stats…) ne passent
pas par ici : ils sont dans la langue réglée DANS le jeu.
"""
import ctypes

LANGUES = ("fr", "en")
NOMS = {"fr": "FR", "en": "EN"}
_actuelle = "fr"


def langue_par_defaut():
    """Langue de Windows : français si Windows est en français, sinon anglais."""
    try:
        return "fr" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x0C else "en"
    except (AttributeError, OSError):
        return "en"


def choisir(code):
    global _actuelle
    _actuelle = code if code in LANGUES else "fr"


def actuelle():
    return _actuelle


def t(cle, **valeurs):
    """Le texte `cle` dans la langue choisie ; {nom} est remplacé par valeurs[nom]."""
    texte = TEXTES[cle][LANGUES.index(_actuelle)]
    return texte.format(**valeurs) if valeurs else texte


TEXTES = {
    # ── Fenêtre : cadre général ──
    "titre": ("PracticeMode — Star Wars: Galactic Racer", "PracticeMode — Star Wars: Galactic Racer"),
    "langue": ("Langue / Language", "Langue / Language"),
    "bandeau_session": ("Session d'entraînement", "Practice session"),
    "btn_demarrer": ("▶ Démarrer l'entraînement", "▶ Start practice"),
    "btn_relancer": ("Relancer le jeu", "Restart the game"),
    "btn_terminer": ("■ Terminer et remettre le jeu d'origine", "■ End and restore the original game"),
    "btn_pare_feu": ("Lever le blocage pare-feu", "Lift the firewall block"),
    "vehicule": ("Véhicule :", "Vehicle:"),
    "onglet_course": ("  Course  ", "  Race  "),
    "onglet_build": ("  Build  ", "  Build  "),
    "onglet_temps": ("  Mes temps  ", "  My times  "),
    "tours": ("Tours :", "Laps:"),
    "speciaux": ("Variantes spéciales de circuits (multi, tests, campagne…)",
                 "Special track variants (multiplayer, tests, campaign…)"),
    "premier_plan": ("Toujours au premier plan", "Always on top"),
    "recharger_catalogue": ("Recharger le catalogue", "Reload catalogue"),
    "lancer": ("▶  Lancer la course", "▶  Start the race"),
    "aide": ("En jeu : F6 = recommencer · F5 = relancer le dernier choix · "
             "F7/F8 = sauver/revenir (emplacement 1), Maj+F7/F8 (2), Ctrl+F7/F8 (3) · "
             "manette : croix bas = sauver, croix droite = revenir (1). Double-clic sur un circuit = lancer.",
             "In game: F6 = restart · F5 = relaunch the last choice · "
             "F7/F8 = save/load (slot 1), Shift+F7/F8 (2), Ctrl+F7/F8 (3) · "
             "gamepad: D-pad down = save, D-pad right = load (1). Double-click a track = start."),

    # ── Onglet Course ──
    "col_planete": ("Planète", "Planet"),
    "col_circuit": ("Circuit", "Track"),
    "col_pilote": ("Pilote", "Racer"),
    "pilote_defaut": ("(pilote par défaut)", "(default racer)"),
    "pilotes_module": ("Pilotes de module", "Podracer pilots"),
    "pilotes_speeder": ("Pilotes de speeder", "Speeder racers"),
    "pilote_age": ("version âgée", "older version"),
    "pilote_boss": ("course de boss", "boss race"),
    "point_a_point": ("point à point", "point to point"),
    "boucle": ("boucle", "loop"),
    "sens_inverse": ("sens inverse", "reversed"),
    "court": ("court", "short"),
    "mines": ("mines", "mines"),
    "extreme": ("conditions extrêmes", "extreme conditions"),

    # ── Onglet Build ──
    "stats_titre": ("Améliorations de stat (0 à 10)", "Stat upgrades (0 to 10)"),
    "stats_secours": (["Virage", "Accélération", "Résistance", "Boost", "Batterie", "Avancé"],
                      ["Handling", "Acceleration", "Resilience", "Boost", "Battery", "Advanced"]),
    "capacites": ("Capacités", "Abilities"),
    "emplacement_n": ("Emplacement {n}", "Slot {n}"),
    "capacite_crash": ("Capacité de crash", "Crash ability"),
    "options": ("Options", "Options"),
    "opt_boost": ("Boost Afterburner", "Afterburner boost"),
    "opt_ramjet": ("Ramjet installé", "Ramjet installed"),
    "opt_pannes": ("Pannes critiques", "Critical malfunctions"),
    "opt_illimites": ("Crashs illimités", "Unlimited crashes"),
    "build_zero": ("Remettre le build à zéro", "Reset the build"),
    "affixes_titre": ("Affixes — clic sur une ligne pour cocher / décocher",
                      "Affixes — click a row to tick / untick"),
    "rechercher": ("Rechercher :", "Search:"),
    "caches": ("Afficher les affixes cachés / internes", "Show hidden / internal affixes"),
    "col_affixe": ("Affixe", "Affix"),
    "col_rarete": ("Rareté", "Rarity"),
    "tout_decocher": ("Tout décocher", "Untick all"),
    "description_titre": ("Description (survol ou choix)", "Description (hover or selection)"),
    "recap_titre": ("Ton build actuel (ce qui sera envoyé au jeu)", "Your current build (what will be sent to the game)"),
    "aucune": ("(aucune)", "(none)"),
    "aucune_sans": ("aucune", "none"),
    "aucun_sans": ("aucun", "none"),
    "nb_affixes": ("{n} affixe(s) coché(s)", "{n} affix(es) ticked"),
    "defaut": ("Défaut : ", "Drawback: "),
    "recap_stats": ("Stats : ", "Stats: "),
    "recap_capacites": ("Capacités : ", "Abilities: "),
    "recap_crash": ("Crash : ", "Crash: "),
    "recap_affixes": ("Affixes ({n}) : ", "Affixes ({n}): "),
    "recap_options": ("Options activées : ", "Enabled options: "),
    "resume_capacites": ("capacités : ", "abilities: "),
    "resume_crash": ("crash : ", "crash: "),
    "resume_affixes": ("affixes ({n}) : ", "affixes ({n}): "),
    "resume_illimites": ("crashs illimités", "unlimited crashes"),
    "raretes_secours": ({0: "commun", 1: "inhabituel", 2: "rare", 3: "épique", 4: "défectueux",
                         5: "expérimental", 6: ""},
                        {0: "common", 1: "uncommon", 2: "rare", 3: "epic", 4: "faulty",
                         5: "experimental", 6: ""}),
    "categories": ({"Faulty": "Défectueux (malus)", "Conditions": "Conditions de piste", "MYST": "Mystère",
                    "SAFX": "Sous-affixes (internes)", "AI": "Réservés à l'IA", "Custom": "Spéciaux",
                    "Energy": "Énergie", "Ignition": "Allumage", "CritMalf": "Pannes critiques",
                    "Autres": "Autres"},
                   {"Faulty": "Faulty (drawbacks)", "Conditions": "Track conditions", "MYST": "Mystery",
                    "SAFX": "Sub-affixes (internal)", "AI": "AI only", "Custom": "Special",
                    "Energy": "Energy", "Ignition": "Ignition", "CritMalf": "Critical malfunctions",
                    "Autres": "Other"}),

    # ── Onglet Mes temps ──
    "filtre_temps": ("Seulement le circuit et le véhicule choisis", "Only the selected track and vehicle"),
    "ouvrir_temps": ("Ouvrir le dossier des temps", "Open the times folder"),
    "legende_record": ("★ = ton record (même circuit, véhicule et tours ; courses avec save state exclues)",
                       "★ = your record (same track, vehicle and laps; races with save states excluded)"),
    "colonnes_temps": (("Date", "Planète", "Circuit", "Tours", "Véhicule", "Pilote", "Temps", "Meilleur tour",
                        "Tours"),
                       ("Date", "Planet", "Track", "Laps", "Vehicle", "Racer", "Time", "Best lap", "Laps")),

    # ── Ligne d'état ──
    "attente_catalogue": ("En attente du catalogue : lance le jeu (session ouverte) et va au menu principal…",
                          "Waiting for the catalogue: start the game (session open) and go to the main menu…"),
    "aucune_capacite": ("Le catalogue ne contient aucune capacité : va au menu principal du jeu, "
                        "Ctrl+R, puis « Recharger le catalogue ».",
                        "The catalogue has no abilities: go to the game's main menu, press Ctrl+R, "
                        "then “Reload catalogue”."),
    "choisis_circuit": ("Choisis d'abord un circuit (onglet Course).", "Pick a track first (Race tab)."),
    "commande_envoyee": ("Commande envoyée au jeu…", "Command sent to the game…"),
    "catalogue_demande": ("Demande de catalogue envoyée…", "Catalogue request sent…"),
    "jeu_prefixe": ("Jeu : ", "Game: "),

    # ── Bandeau de session ──
    "session_en_cours": ("● ENTRAÎNEMENT EN COURS — jeu moddé, PAS DE MULTI",
                         "● PRACTICE RUNNING — modded game, NO MULTIPLAYER"),
    "session_ouverte": ("● Session ouverte (jeu moddé) — le jeu n'est pas lancé",
                        "● Session open (modded game) — the game is not running"),
    "session_origine_lance": ("● Jeu d'origine en cours (aucun mod)", "● Original game running (no mods)"),
    "session_vanilla": ("● Jeu d'origine (vanilla) — prêt pour le multi",
                        "● Original game (vanilla) — ready for multiplayer"),

    # ── Messages du launcher (fenêtre) ──
    "patiente": ("patiente : une opération est déjà en cours", "please wait: an operation is already running"),
    "erreur_inattendue": ("✖ erreur inattendue : {e}", "✖ unexpected error: {e}"),
    "pare_feu_desactive": ("Le pare-feu Windows est désactivé : le blocage ne servirait à rien. "
                           "Réactive-le (Sécurité Windows → Pare-feu) puis réessaie.",
                           "Windows Firewall is turned off: blocking would be useless. "
                           "Turn it back on (Windows Security → Firewall) and try again."),
    "debut_sauvegarde": ("début de session : sauvegarde de tes données de jeu…",
                         "session start: backing up your game data…"),
    "pare_feu_uac": ("pare-feu : valide la fenêtre « administrateur » de Windows qui s'ouvre…",
                     "firewall: accept the Windows “administrator” prompt that opens…"),
    "pare_feu_refuse": ("pare-feu refusé : entraînement annulé, remise d'origine du jeu…",
                        "firewall refused: practice cancelled, restoring the original game…"),
    "pare_feu_echec": ("le pare-feu n'a pas pu être activé ({etat}) : annulation…",
                       "the firewall could not be enabled ({etat}): cancelling…"),
    "pas_de_reponse": ("pas de réponse", "no response"),
    "pare_feu_probleme": ("problème avec le pare-feu : annulation, remise d'origine du jeu…",
                          "firewall problem: cancelling, restoring the original game…"),
    "pare_feu_actif": ("pare-feu actif : le jeu ne peut plus rien envoyer sur Internet",
                       "firewall active: the game can no longer send anything to the Internet"),
    "lancement_jeu": ("lancement du jeu par Steam… Quand tu fermeras le jeu, tout sera remis d'origine tout seul.",
                      "starting the game through Steam… When you close the game, everything is restored automatically."),
    "fin_remise": ("fin de session : remise d'origine du jeu…", "session end: restoring the original game…"),
    "fin_ok": ("✔ Jeu remis 100 % d'origine. Repasse Steam EN LIGNE avant de jouer en multi.",
               "✔ Game restored to 100% original. Put Steam back ONLINE before playing multiplayer."),
    "session_oubliee": ("⚠ une session d'entraînement est restée ouverte : clique sur "
                        "« Terminer et remettre le jeu d'origine » (ou « Relancer le jeu » pour continuer)",
                        "⚠ a practice session was left open: click "
                        "“End and restore the original game” (or “Restart the game” to continue)"),
    "blocage_oublie": ("⚠ le pare-feu bloque encore le jeu (session précédente interrompue) : "
                       "clique sur « Lever le blocage pare-feu » avant de jouer en multi",
                       "⚠ the firewall still blocks the game (previous session interrupted): "
                       "click “Lift the firewall block” before playing multiplayer"),
    "jeu_ferme": ("jeu fermé : remise d'origine dans quelques secondes…",
                  "game closed: restoring in a few seconds…"),
    "fenetre_fermee": ("fenêtre fermée pendant une session : rouvre-la après le jeu et clique sur "
                       "« Terminer et remettre le jeu d'origine »",
                       "window closed during a session: reopen it after the game and click "
                       "“End and restore the original game”"),

    # ── Messages du launcher (session.py) ──
    "crashpad_arrete": ("crashpad_handler arrêté (PID {pid})", "crashpad_handler stopped (PID {pid})"),
    "destination_existe": ("La destination existe déjà : {chemin}", "The destination already exists: {chemin}"),
    "copie_differente": ("Copie différente de l'original : {chemin}", "Copy differs from the original: {chemin}"),
    "deja_ouverte": ("Une session est déjà ouverte. Termine-la d'abord.", "A session is already open. End it first."),
    "jeu_tourne": ("Le jeu tourne : ferme-le complètement d'abord.",
                   "The game is running: close it completely first."),
    "ue4ss_sans_session": ("UE4SS est déjà dans le dossier du jeu alors qu'aucune session n'est ouverte "
                           "(autre mod ?). Retire dwmapi.dll et le dossier ue4ss de Griffin\\Binaries\\Win64 "
                           "avant de continuer.",
                           "UE4SS is already in the game folder although no session is open (another mod?). "
                           "Remove dwmapi.dll and the ue4ss folder from Griffin\\Binaries\\Win64 before going on."),
    "jeu_introuvable": ("Jeu introuvable : clique sur « Démarrer » pour choisir son dossier "
                        "(celui qui contient le dossier Griffin).",
                        "Game not found: click “Start” to pick its folder (the one that contains the Griffin folder)."),
    "choisir_jeu": ("Choisis le dossier de STAR WARS Galactic Racer (celui qui contient le dossier Griffin)",
                    "Pick the STAR WARS Galactic Racer folder (the one that contains the Griffin folder)"),
    "dossier_jeu_invalide": ("Ce dossier ne contient pas le jeu (Griffin\\Binaries\\Win64\\SWGR-Win64-Shipping.exe "
                             "introuvable).",
                             "This folder does not contain the game (Griffin\\Binaries\\Win64\\SWGR-Win64-Shipping.exe "
                             "not found)."),
    "dossier_jeu_ok": ("dossier du jeu : {chemin}", "game folder: {chemin}"),
    "version_inconnue": ("Version du jeu inconnue (empreinte {empreinte}…) : le jeu a sans doute été mis à jour, "
                         "et les correctifs d'UE4SS de PracticeMode ne sont faits que pour la version d'origine. "
                         "Attends une mise à jour de PracticeMode : le lancer quand même pourrait faire planter le jeu.",
                         "Unknown game version (fingerprint {empreinte}…): the game was probably updated, and "
                         "PracticeMode's UE4SS fixes only target the supported version. Wait for a PracticeMode "
                         "update: starting anyway could crash the game."),
    "chemin_accents": ("Le dossier de PracticeMode contient des accents ou caractères spéciaux que le mod ne sait "
                       "pas lire ({chemin}). Déplace le dossier PracticeMode ailleurs, par exemple C:\\PracticeMode.",
                       "The PracticeMode folder path contains accents or special characters the mod cannot read "
                       "({chemin}). Move the PracticeMode folder elsewhere, e.g. C:\\PracticeMode."),
    "vcpp_titre": ("Microsoft Visual C++ manquant", "Microsoft Visual C++ missing"),
    "vcpp_question": ("UE4SS a besoin de Microsoft Visual C++ 2015-2022 (x64), absent de ce PC "
                      "({dll}).\n\nLancer l'installateur fourni avec le jeu ?\n{chemin}",
                      "UE4SS needs Microsoft Visual C++ 2015-2022 (x64), which is missing on this PC "
                      "({dll}).\n\nRun the installer that ships with the game?\n{chemin}"),
    "vcpp_lance": ("installation de Visual C++ lancée : termine-la, puis clique de nouveau sur « Démarrer »",
                   "Visual C++ installer started: finish it, then click “Start” again"),
    "vcpp_absent": ("Microsoft Visual C++ 2015-2022 (x64) manque ({dll}) : installe-le depuis le site de "
                    "Microsoft (vc_redist.x64.exe), puis réessaie.",
                    "Microsoft Visual C++ 2015-2022 (x64) is missing ({dll}): install it from Microsoft's "
                    "website (vc_redist.x64.exe), then try again."),
    "dossier_non_inscriptible": ("PracticeMode ne peut pas écrire dans son dossier ({chemin}). Déplace-le hors de "
                                 "« Program Files », par exemple dans C:\\PracticeMode.",
                                 "PracticeMode cannot write to its folder ({chemin}). Move it out of "
                                 "“Program Files”, e.g. to C:\\PracticeMode."),
    "steam_en_ligne": ("Steam est en ligne. Menu Steam → « Passer en mode hors ligne… », puis réessaie.",
                       "Steam is online. Steam menu → “Go Offline…”, then try again."),
    "steam_cloud": ("Steam Cloud est actif pour le jeu. Bibliothèque → clic droit sur le jeu → "
                    "Propriétés → Général → décoche Steam Cloud.",
                    "Steam Cloud is on for the game. Library → right-click the game → "
                    "Properties → General → untick Steam Cloud."),
    "ue4ss_introuvable": ("UE4SS introuvable dans {chemin}", "UE4SS not found in {chemin}"),
    "sauvegarde_verifiee": ("sauvegardé et vérifié : {element}", "backed up and verified: {element}"),
    "installation_echec": ("L'installation d'UE4SS a échoué.", "UE4SS installation failed."),
    "installe": ("UE4SS et le mod installés", "UE4SS and the mod installed"),
    "ue4ss_sans_marqueur": ("UE4SS est installé mais aucune session n'est enregistrée : retire dwmapi.dll et le "
                            "dossier ue4ss de Griffin\\Binaries\\Win64 à la main.",
                            "UE4SS is installed but no session is recorded: remove dwmapi.dll and the ue4ss "
                            "folder from Griffin\\Binaries\\Win64 by hand."),
    "aucune_session": ("aucune session en cours", "no session in progress"),
    "jeu_tourne_encore": ("Le jeu tourne encore : ferme-le complètement.",
                          "The game is still running: close it completely."),
    "sauvegarde_introuvable": ("Sauvegarde de début introuvable : {chemin}.",
                               "Start-of-session backup not found: {chemin}."),
    "retire_du_jeu": ("retiré du jeu (copie gardée) : {nom}", "removed from the game (copy kept): {nom}"),
    "restaure": ("restauré : {element}", "restored: {element}"),
    "ue4ss_encore": ("UE4SS est encore présent dans le jeu !", "UE4SS is still in the game!"),
    "win64_different": ("Le dossier Win64 diffère de l'original : {diff}",
                        "The Win64 folder differs from the original: {diff}"),
    "jeu_origine": ("jeu revenu 100 % d'origine", "game back to 100% original"),
    "pf_leve": ("pare-feu : blocage levé", "firewall: block lifted"),
    "pf_aucun": ("pare-feu : aucun blocage en place", "firewall: no block in place"),
    "pf_encore": ("pare-feu : le blocage est encore là, confirmation administrateur nécessaire pour le lever",
                  "firewall: the block is still there, administrator confirmation needed to lift it"),
    "pf_refuse": ("pare-feu : confirmation refusée, le jeu reste bloqué (sans danger) jusqu'au prochain essai",
                  "firewall: confirmation refused, the game stays blocked (harmless) until the next try"),
    "pf_non_verifie": ("pare-feu : impossible de vérifier le retrait du blocage",
                       "firewall: could not verify that the block was lifted"),
}
