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


class Message:
    """Un message à afficher plus tard (liste des messages de la fenêtre,
    journal du launcher). Il est traduit au moment où on l'affiche : quand on
    change de langue, les messages déjà affichés changent de langue aussi."""

    def __init__(self, cle, prefixe="", **valeurs):
        self.cle, self.prefixe, self.valeurs = cle, prefixe, valeurs

    def __str__(self):
        return self.prefixe + t(self.cle, **self.valeurs)

    def avec_prefixe(self, prefixe):
        return Message(self.cle, prefixe + self.prefixe, **self.valeurs)


def m(cle, prefixe="", **valeurs):
    """Message traduisible : m("pf_leve") ; m("restaure", element="Saved/Config")."""
    return Message(cle, prefixe, **valeurs)


TEXTES = {
    # ── Fenêtre : cadre général ──
    "titre": ("PracticeMode — Star Wars: Galactic Racer", "PracticeMode — Star Wars: Galactic Racer"),
    "entete_sous_titre": ("STAR WARS : GALACTIC RACER   ·   MODE ENTRAÎNEMENT   ·   v{version}",
                          "STAR WARS: GALACTIC RACER   ·   PRACTICE MODE   ·   v{version}"),
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
    "onglet_classement": ("  Classement  ", "  Leaderboard  "),
    "tours": ("Tours :", "Laps:"),
    "adversaires": ("Adversaires IA :", "AI opponents:"),
    "adversaires_aide": ("(0 = seul)", "(0 = alone)"),
    # Difficulté des IA (v0.9.7)
    "difficulte": ("Difficulté des IA :", "AI difficulty:"),
    "difficulte_jeu": ("Celle du jeu (sans changement)", "Game default (unchanged)"),
    "difficulte_jeu_aide": ("Les IA gardent les réglages du jeu.", "The AI keep the game's settings."),
    "difficulte_mod": ("Le mod règle : {reglages}.", "The mod sets: {reglages}."),
    "difficulte_seul": ("(seulement avec des adversaires IA)", "(only with AI opponents)"),
    "niv_cadet": ("Recrue", "Cadet"),
    "niv_pilote": ("Pilote", "Pilot"),
    "niv_as": ("As", "Ace"),
    "niv_champion": ("Antagoniste", "Champion"),
    "reg_avance": ("avance des IA {v}", "AI lead {v}"),
    "reg_avance_max": ("avance max. des IA {v}", "AI max lead {v}"),
    "reg_avance_min": ("avance min. des IA {v}", "AI min lead {v}"),
    "reg_agressivite": ("agressivité {v}", "aggression {v}"),
    "reg_delai": ("délai entre leurs attaques {v}", "delay between their attacks {v}"),
    "reg_capacites": ("capacités {v}", "abilities {v}"),
    "reg_aucun": ("rien (réglages du jeu)", "nothing (game settings)"),
    "speciaux": ("Variantes spéciales de circuits (multi, tests, campagne…)",
                 "Special track variants (multiplayer, tests, campaign…)"),
    "premier_plan": ("Toujours au premier plan", "Always on top"),
    "recharger_catalogue": ("Recharger le catalogue", "Reload catalogue"),
    "lancer": ("▶  Lancer la course", "▶  Start the race"),
    "aide": ("En jeu : F6 = recommencer · F5 = relancer le dernier choix · "
             "F7/F8 = sauver/revenir (emplacement 1), Maj+F7/F8 (2), Ctrl+F7/F8 (3) · "
             "manette : croix bas = sauver, croix droite = revenir (1). Double-clic sur un circuit = lancer. "
             "Avec adversaires IA : lancement depuis le menu principal du jeu, recommencer = menu pause du jeu.",
             "In game: F6 = restart · F5 = relaunch the last choice · "
             "F7/F8 = save/load (slot 1), Shift+F7/F8 (2), Ctrl+F7/F8 (3) · "
             "gamepad: D-pad down = save, D-pad right = load (1). Double-click a track = start. "
             "With AI opponents: start from the game's main menu, restart = the game's pause menu."),

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
    "resume_buffs": ("buffs : ", "buffs: "),
    "recap_buffs": ("Buffs du pilote : ", "Racer buffs: "),
    # Style du pilote (v0.9.6) : son build et ses buffs (traits)
    "style_titre": ("Style du pilote : son build et ses buffs", "Racer style: build and buffs"),
    "style_auto": ("Charger le build du pilote quand je le choisis", "Load the racer's build when I pick them"),
    "style_recharger": ("Recharger le build du pilote", "Reload the racer's build"),
    "style_aucun": ("Aucun : choisis un pilote dans l'onglet Course.", "None: pick a racer in the Race tab."),
    "style_absent": ("{pilote} : pas de style connu pour ce véhicule.", "{pilote}: no known style for this vehicle."),
    "style_attente": ("Styles pas encore lus : ils le seront au menu principal du jeu.",
                      "Styles not read yet: they will be at the game's main menu."),
    "style_nom": ("{style}  ({pilote})", "{style}  ({pilote})"),
    "style_sans_build": ("pas de build imposé : stats et affixes inchangés", "no set build: stats and affixes unchanged"),
    "style_build_absent": ("son build n'était pas chargé par le jeu : stats et affixes inchangés",
                           "its build was not loaded by the game: stats and affixes unchanged"),
    "style_sans_buff": ("aucun buff", "no buffs"),
    "buffs_pilote_charges": ("Buffs de {pilote} (style « {style} ») : {n} buff(s), cochés dans l'onglet Build ; "
                             "ton build est gardé.",
                             "{pilote}'s buffs (style \"{style}\"): {n} buff(s), ticked in the Build tab; "
                             "your build is kept."),
    "style_module_build_garde": ("module : ton build est gardé (celui du jeu pour ce pilote est incomplet) ; "
                                 "seuls ses buffs sont proposés",
                                 "pod: your build is kept (the game's one for this racer is incomplete); "
                                 "only their buffs are offered"),
    "build_pilote_charge": ("Build de {pilote} chargé (style « {style} ») : {n} buff(s), cochés dans l'onglet Build.",
                            "{pilote}'s build loaded (“{style}” style): {n} buff(s), ticked in the Build tab."),
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
    "colonnes_temps": (("Date", "Planète", "Circuit", "Tours", "Véhicule", "Pilote", "Temps", "Place",
                        "Meilleur tour", "Tours", "En ligne"),
                       ("Date", "Planet", "Track", "Laps", "Vehicle", "Racer", "Time", "Position",
                        "Best lap", "Laps", "Online")),
    "detail_titre": ("Build de la course sélectionnée", "Build of the selected race"),
    "detail_vide": ("Clique sur une ligne pour voir le build utilisé pendant cette course.",
                    "Click a row to see the build used in that race."),
    "detail_ancien": ("Temps noté avant la v0.9.6 : seul ce résumé du build a été enregistré.",
                      "Time saved before v0.9.6: only this build summary was recorded."),
    "detail_reprendre": ("Reprendre ce build", "Use this build"),
    "detail_course_ia": ("Course : {n} adversaire(s) IA", "Race: {n} AI opponent(s)"),
    "detail_difficulte": (", difficulté {d}", ", difficulty {d}"),
    "detail_place": (" — place {p} / {total}", " — position {p} / {total}"),
    "detail_seul": ("Course : seul (contre-la-montre)", "Race: alone (time trial)"),
    "detail_style": ("Style du pilote : ", "Racer style: "),
    "detail_illimites": ("crashs illimités", "unlimited crashes"),
    "build_repris": ("Build de la course du {date} repris : regarde l'onglet Build.",
                     "Build from the {date} race loaded: see the Build tab."),
    "build_repris_vehicule": (" Attention : cette course était en {vehicule}, change le type de véhicule dans l'onglet Course.",
                              " Warning: that race was with a {vehicule}, change the vehicle type in the Race tab."),

    # ── Classement en ligne (v0.9.8) ──
    "cl_pseudo": ("Pseudo", "Name"),
    "cl_pseudo_aide": ("3 à 12 caractères : A-Z, 0-9, espace . _ -   (comme sur une borne d'arcade)",
                       "3 to 12 characters: A-Z, 0-9, space . _ -   (like an arcade cabinet)"),
    "cl_serveur": ("Serveur :", "Server:"),
    "cl_tester": ("Tester", "Test"),
    "cl_actualiser": ("↻ Actualiser", "↻ Refresh"),
    "cl_ce_circuit": ("Circuit choisi", "Selected track"),
    "categories_classement": ({"solo-sans": "Solo sans build", "solo-avec": "Solo avec build",
                               "ia-sans": "IA sans build", "ia-avec": "IA avec build"},
                              {"solo-sans": "Solo, no build", "solo-avec": "Solo with build",
                               "ia-sans": "AI, no build", "ia-avec": "AI with build"}),
    "cl_titre_tableaux": ("Classements du véhicule choisi", "Leaderboards for the selected vehicle"),
    "cl_titre_classement": ("Classement", "Leaderboard"),
    "cl_colonnes_tableaux": (("Circuit", "Tours", "Temps", "Record"), ("Track", "Laps", "Times", "Record")),
    "cl_colonnes": (("#", "Pseudo", "Temps", "Écart", "Meilleur tour", "Pilote", "IA", "Difficulté", "Place",
                     "Date"),
                    ("#", "Name", "Time", "Gap", "Best lap", "Racer", "AI", "Difficulty", "Pos.", "Date")),
    "cl_tableau": ("{circuit}  ·  {vehicule}  ·  {tours} tour(s)  ·  {categorie}",
                   "{circuit}  ·  {vehicule}  ·  {tours} lap(s)  ·  {categorie}"),
    "cl_total": ("  —  {n} pilote(s)", "  —  {n} racer(s)"),
    "cl_aucun_tableau": ("Choisis un classement dans la liste, ou clique sur « Circuit choisi ».",
                         "Pick a leaderboard in the list, or click “Selected track”."),
    "cl_vide": ("Aucun temps publié ici pour l'instant : sois le premier !",
                "No time published here yet: be the first!"),
    "cl_place_1": ("1er", "#1"),
    "cl_place_n": ("{n}e", "#{n}"),
    "cl_detail_titre": ("Temps sélectionné", "Selected time"),
    "cl_detail_vide": ("Clique sur un temps pour voir le build utilisé (et le reprendre).",
                       "Click a time to see the build used (and use it)."),
    "cl_detail_tours": ("Tours : ", "Laps: "),
    "cl_detail_infos": ("Course du {date}, Practice Mode v{version}.", "Race of {date}, Practice Mode v{version}."),
    "cl_build_repris": ("Build de {pseudo} repris : regarde l'onglet Build.",
                        "{pseudo}'s build loaded: see the Build tab."),
    "cl_pas_configure": ("Le classement en ligne n'est pas encore configuré : il manque l'adresse du serveur "
                         "(champ « Serveur », voir serveur/classement/LISEZ-MOI.md).",
                         "The online leaderboard is not set up yet: the server address is missing "
                         "(“Server” field, see serveur/classement/LISEZ-MOI.md)."),
    "cl_chargement": ("Chargement…", "Loading…"),
    "cl_tableaux_lus": ("{n} classement(s) avec des temps pour ce véhicule ({vehicule}) dans cette catégorie · "
                        "mis à jour à {heure}",
                        "{n} leaderboard(s) with times for this vehicle ({vehicule}) in this category · "
                        "updated at {heure}"),
    "cl_serveur_ok": ("✔ Serveur du classement joignable.", "✔ Leaderboard server reachable."),
    "cl_publier": ("Publier ce temps", "Publish this time"),
    "cl_publication": ("Publication du temps au classement en ligne…", "Publishing the time to the online leaderboard…"),
    "cl_publie": ("✔ Publié : {place} sur {total} au classement « {categorie} ».",
                  "✔ Published: {place} of {total} in the “{categorie}” leaderboard."),
    "cl_record_battu": (" Record en ligne battu (avant : {ancien}).", " Online record beaten (before: {ancien})."),
    "cl_record_garde": (" Ton record en ligne ({record}) reste meilleur.",
                        " Your online record ({record}) is still better."),
    "cl_detail_publie": ("En ligne : ", "Online: "),
    "cl_detail_publie_texte": ("publié le {quand} sous le pseudo {pseudo} — {place} sur {total} ({categorie})",
                               "published on {quand} as {pseudo} — {place} of {total} ({categorie})"),
    "cl_detail_publie_garde": ("publié le {quand} sous le pseudo {pseudo} ; un meilleur temps à toi est au "
                               "classement ({categorie})",
                               "published on {quand} as {pseudo}; a better time of yours is on the "
                               "leaderboard ({categorie})"),
    "cl_refus": ({"save_state": "Temps fait avec un save state (F8) : il ne peut pas être publié.",
                  "sans_detail": "Temps noté par une ancienne version du mod (sans le détail du build) : "
                                 "il ne peut pas être publié.",
                  "circuit_inconnu": "Circuit introuvable dans le catalogue : ce temps ne peut pas être publié.",
                  "vehicule_inconnu": "Véhicule inconnu : ce temps ne peut pas être publié.",
                  "temps_invalide": "Temps illisible dans temps.csv : il ne peut pas être publié.",
                  "pseudo_invalide": "Choisis d'abord ton pseudo (onglet Classement, en haut).",
                  "catalogue": "Catalogue pas encore chargé : lance le jeu une fois jusqu'au menu principal."},
                 {"save_state": "Time set with a save state (F8): it cannot be published.",
                  "sans_detail": "Time saved by an old version of the mod (no build detail): it cannot be published.",
                  "circuit_inconnu": "Track not found in the catalogue: this time cannot be published.",
                  "vehicule_inconnu": "Unknown vehicle: this time cannot be published.",
                  "temps_invalide": "Unreadable time in temps.csv: it cannot be published.",
                  "pseudo_invalide": "Choose your name first (Leaderboard tab, at the top).",
                  "catalogue": "Catalogue not loaded yet: start the game once, up to the main menu."}),
    "err_classement": ({"adresse": "Pas d'adresse de serveur valable : onglet Classement, champ « Serveur ».",
                        "reseau": "Le serveur du classement ne répond pas (pas d'Internet ? mauvaise adresse ?).",
                        "reponse": "Réponse illisible : cette adresse n'est sans doute pas celle du serveur "
                                   "du classement.",
                        "api": "Le serveur du classement est plus récent que cette fenêtre : "
                               "mets Practice Mode à jour.",
                        "pseudo_pris": "Ce pseudo est déjà pris par un autre joueur : choisis-en un autre.",
                        "pseudo_interdit": "Ce pseudo n'est pas accepté : choisis-en un autre.",
                        "pseudo_invalide": "Pseudo invalide : 3 à 12 caractères (A-Z, 0-9, espace . _ -).",
                        "jeton_invalide": "Jeton de la fenêtre invalide : retire la ligne « jeton » de "
                                          "PracticeMode.ini.",
                        "banni": "Ce pseudo (ou cette connexion) a été banni du classement.",
                        "trop_d_envois": "Trop d'envois en peu de temps : réessaie dans une heure.",
                        "save_state": "Les temps faits avec un save state ne sont pas acceptés.",
                        "temps_invalide": "Temps refusé par le serveur (impossible).",
                        "build_invalide": "Build refusé par le serveur.",
                        "base_absente": "Serveur mal configuré : la base de données n'est pas reliée "
                                        "(liaison « DB »).",
                        "serveur": "Erreur du serveur du classement : réessaie plus tard.",
                        "interne": "Erreur inattendue dans la fenêtre : {detail}"},
                       {"adresse": "No valid server address: Leaderboard tab, “Server” field.",
                        "reseau": "The leaderboard server does not answer (no Internet? wrong address?).",
                        "reponse": "Unreadable answer: this address is probably not the leaderboard server.",
                        "api": "The leaderboard server is newer than this window: update Practice Mode.",
                        "pseudo_pris": "This name is already taken by another player: pick another one.",
                        "pseudo_interdit": "This name is not accepted: pick another one.",
                        "pseudo_invalide": "Invalid name: 3 to 12 characters (A-Z, 0-9, space . _ -).",
                        "jeton_invalide": "Invalid window token: remove the “jeton” line from PracticeMode.ini.",
                        "banni": "This name (or this connection) has been banned from the leaderboard.",
                        "trop_d_envois": "Too many submissions in a short time: try again in an hour.",
                        "save_state": "Times set with a save state are not accepted.",
                        "temps_invalide": "Time refused by the server (impossible).",
                        "build_invalide": "Build refused by the server.",
                        "base_absente": "Server misconfigured: the database is not bound (“DB” binding).",
                        "serveur": "Leaderboard server error: try again later.",
                        "interne": "Unexpected error in the window: {detail}"}),
    "err_classement_autre": ("Classement en ligne : erreur « {code} ».", "Online leaderboard: error “{code}”."),

    # ── Ligne d'état ──
    "attente_catalogue": ("En attente du catalogue : lance le jeu (session ouverte) et va au menu principal…",
                          "Waiting for the catalogue: start the game (session open) and go to the main menu…"),
    "aucune_capacite": ("Le catalogue ne contient aucune capacité : va au menu principal du jeu, "
                        "puis clique sur « Recharger le catalogue ».",
                        "The catalogue has no abilities: go to the game's main menu, "
                        "then click “Reload catalogue”."),
    "choisis_circuit": ("Choisis d'abord un circuit (onglet Course).", "Pick a track first (Race tab)."),
    "commande_envoyee": ("Commande envoyée au jeu…", "Command sent to the game…"),
    "catalogue_demande": ("Demande de catalogue envoyée…", "Catalogue request sent…"),
    "jeu_prefixe": ("Jeu : ", "Game: "),

    # ── Bandeau de session ──
    "session_en_cours": ("ENTRAÎNEMENT EN COURS — jeu moddé, PAS DE MULTI",
                         "PRACTICE RUNNING — modded game, NO MULTIPLAYER"),
    "session_ouverte": ("Session ouverte (jeu moddé) — le jeu n'est pas lancé",
                        "Session open (modded game) — the game is not running"),
    "session_origine_lance": ("Jeu d'origine en cours (aucun mod)", "Original game running (no mods)"),
    "session_vanilla": ("Jeu d'origine (vanilla) — prêt pour le multi",
                        "Original game (vanilla) — ready for multiplayer"),

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
    "steam_en_ligne_session": ("Steam est EN LIGNE alors qu'une session moddée est ouverte : le mod se bloque. "
                               "Ferme le jeu et termine la session avant de jouer en multi.",
                               "Steam is ONLINE while a modded session is open: the mod locks itself. "
                               "Close the game and end the session before playing multiplayer."),
    "relance_sans_pare_feu": ("Le blocage pare-feu n'est plus en place : termine la session, puis redémarre "
                              "l'entraînement.",
                              "The firewall block is no longer in place: end the session, then start practice "
                              "again."),
    "fermer_titre": ("Session d'entraînement en cours", "Practice session in progress"),
    "fermer_jeu_lance": ("Le jeu tourne avec le mod. Si tu fermes cette fenêtre, il ne sera PAS remis d'origine "
                         "automatiquement quand tu le quitteras : il faudra rouvrir PracticeMode et cliquer sur "
                         "« Terminer ». Le pare-feu reste actif d'ici là.\n\nFermer quand même ?",
                         "The game is running with the mod. If you close this window, it will NOT be restored "
                         "automatically when you quit it: you will have to reopen PracticeMode and click "
                         "“End”. The firewall stays active until then.\n\nClose anyway?"),
    "fermer_terminer": ("Une session d'entraînement est encore ouverte : le jeu est moddé.\n\n"
                        "Oui : remettre le jeu d'origine maintenant, puis fermer.\n"
                        "Non : fermer sans rien remettre (à faire plus tard).\n"
                        "Annuler : ne pas fermer.",
                        "A practice session is still open: the game is modded.\n\n"
                        "Yes: restore the original game now, then close.\n"
                        "No: close without restoring (to do later).\n"
                        "Cancel: do not close."),
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
