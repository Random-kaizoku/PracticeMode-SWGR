"""PracticeMode : fenêtre de choix pour le mode entraînement de Star Wars: Galactic Racer.

Cette fenêtre ne touche pas au jeu. Elle échange seulement des fichiers
texte avec le mod UE4SS « PracticeMode », dans le dossier « echange » :

    catalogue.json  ← écrit par le mod : circuits, véhicules, pilotes,
                      capacités, affixes, noms des stats
    commande.txt    → écrit par cette fenêtre : la course et le build demandés
    etat.txt        ← écrit par le mod : ce qui vient de se passer
    langue.txt      → écrit par cette fenêtre : « fr » ou « en » (bouton FR / EN),
                      la langue des messages du mod

Les textes de la fenêtre sont dans langues.py (français et anglais).

Utilisation : double-clic sur Fenetre-PracticeMode.bat (ou sur ce fichier).
Le jeu doit tourner avec la session ouverte (Debut-Session.bat).
"""
import configparser
import csv
import json
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
from collections import Counter
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import langues as L   # textes en français / anglais (fichier langues.py)
import session as S   # le « launcher » : sauvegarde, UE4SS, pare-feu (fichier session.py)
from langues import t

# ─────────────────────────────────────────────────────────────────────────
#  RÉGLAGES
# ─────────────────────────────────────────────────────────────────────────
VERSION = "0.9.4"   # même numéro que le mod (main.lua) ; vérifié par outils/empaqueter.py

DOSSIER_PROJET = S.dossier_application()   # dossier de PracticeMode.exe, ou du dépôt
DOSSIER_ECHANGE = DOSSIER_PROJET / "echange"
FICHIER_CATALOGUE = DOSSIER_ECHANGE / "catalogue.json"
FICHIER_COMMANDE = DOSSIER_ECHANGE / "commande.txt"
FICHIER_ETAT = DOSSIER_ECHANGE / "etat.txt"
FICHIER_LANGUE = DOSSIER_ECHANGE / "langue.txt"   # lu par le mod : langue de ses messages
FICHIER_PREFERENCES = (DOSSIER_PROJET if getattr(sys, "frozen", False)
                       else Path(__file__).resolve().parent) / "PracticeMode.ini"
FICHIER_TEMPS_CSV = DOSSIER_PROJET / "temps" / "temps.csv"   # écrit par le mod à chaque arrivée

# Nos 4 types de véhicule : nom de l'archétype dans le jeu → (clé, tag de secours, n° EVehicleArchetype)
# La clé doit correspondre à CONFIG.Types dans le mod.
TYPES = {
    "VA_Bike":    ("motojet", "Vehicle.Standard.Bike", 2),
    "VA_Car":     ("voiture", "Vehicle.Standard.Car", 0),
    "VA_Skimmer": ("skimmer", "Vehicle.Standard.Skimmer", 3),
    "VA_Plane":   ("avion",   "Vehicle.Special.Plane", 1),
}

# Codes de planète dans les noms de circuits → nom de l'objet planète
PLANETES = {
    "BGL": "PLA_Beagle", "COR": "PLA_Corgi", "DAL": "PLA_Dalmatian",
    "HSK": "PLA_Husky", "HUS": "PLA_Husky", "MAS": "PLA_Mastiff",
    "SPA": "PLA_Spaniel", "WHP": "PLA_Whippet",
}

# Circuits « spéciaux » (multijoueur, tests, campagne, salons…) : masqués par
# défaut, visibles avec la case « variantes spéciales ».
DOSSIERS_SPECIAUX = ("/Plane_MP/", "/Plane_RaceTests/", "/Plane_Insta/", "/Plane_PresentDay/",
                     "/Shakedown/", "/GamesCom/", "/DBC/", "/Scenarios/")
MOTS_SPECIAUX = {"MP", "INSTA", "TT", "SHK", "GC", "PDay", "Pday", "PDAY", "Act1", "Act2", "Act3",
                 "ACT1", "ACT2", "ACT3", "ARC", "BOSS", "SHORTBOSS", "FAIR", "MID", "RollingStart"}

DELAI_ETAT = 1000   # rafraîchissement de la ligne d'état (millisecondes)

# Améliorations de stat : 6 emplacements (EVehiclePartSlot 0 à 5).
# Noms de secours (t("stats_secours")), remplacés par ceux du jeu dès que le
# catalogue les fournit. Même chose pour les raretés (t("raretes_secours")).
NIVEAU_MAX = 10
NB_CAPACITES = 4

# Liste des pilotes : la ligne « pilote par défaut », puis les deux groupes
PILOTE_DEFAUT = "defaut"
GROUPES_PILOTES = ("module", "speeder")


def aucune():
    """« (aucune) » : le choix vide des listes de capacités, dans la langue choisie."""
    return t("aucune")


COULEURS_RARETE = {0: "#6b6b6b", 1: "#2e7d32", 2: "#1565c0", 3: "#7b1fa2", 4: "#c62828", 5: "#ef6c00"}

# Catégories d'affixes : on prend le mot qui suit « AFX_ » dans le nom interne
# (AFX_Ramjet_… → Ramjet). Certains mots sont des variantes du même thème.
ALIAS_CATEGORIES = {
    "Crashes": "Crash", "Surge": "Surging", "Slipstream": "Slipstreaming", "Overcharge": "Overcharged",
    "SysMalf": "SysMalfunction", "Landing": "PerfectLanding", "Concussion": "Concussed",
    "Condition": "Conditions", "AFXCustom": "Custom", "Choke": "Autres", "FirstPlace": "Autres",
    "Corrode": "Autres", "Cooling": "Cooled",
}
# Noms des catégories quand le jeu ne fournit pas lui-même le mot
# (voir noms_des_mots_cles) : t("categories") dans langues.py
CATEGORIES_CACHEES = {"SAFX", "AI"}   # masquées sauf avec « afficher les affixes cachés »


# ─────────────────────────────────────────────────────────────────────────
#  DONNÉES : lecture et organisation du catalogue (sans interface)
# ─────────────────────────────────────────────────────────────────────────
def compatible(tag_vehicule, tag_circuit):
    """Vrai si le véhicule peut rouler sur le circuit.
    « Vehicle.Standard.Bike » roule sur « Vehicle.Standard », pas sur « Vehicle.Special.Plane »."""
    if not tag_circuit:
        return True
    return tag_vehicule == tag_circuit or tag_vehicule.startswith(tag_circuit + ".")


def nom_court(nom):
    """BP_Ability_Shield_Charged_C → Shield_Charged"""
    for prefixe in ("BP_Ability_", "BP_"):
        if nom.startswith(prefixe):
            nom = nom[len(prefixe):]
    return nom[:-2] if nom.endswith("_C") else nom


def code_planete(nom_circuit):
    """Trouve le code de planète (COR, DAL…) dans un nom comme TRAK_MP_COR_Loop_A_FWD_PLANE."""
    for morceau in nom_circuit.split("_"):
        if morceau.upper() in PLANETES:
            return morceau.upper()
    return None


def est_special(circuit):
    if any(d in circuit["chemin"] for d in DOSSIERS_SPECIAUX):
        return True
    return any(m in MOTS_SPECIAUX for m in circuit["nom"].split("_"))


def description_circuit(circuit):
    """Texte affiché pour un circuit : nom + caractéristiques + nom interne."""
    nom = circuit.get("affiche") or circuit.get("interne") or circuit["nom"]
    details = [t("point_a_point") if circuit.get("p2p") else t("boucle")]
    if circuit.get("inverse"):
        details.append(t("sens_inverse"))
    if "SHORT" in circuit["nom"].upper():
        details.append(t("court"))
    if circuit.get("mines"):
        details.append(t("mines"))
    if "HARD" in circuit["nom"].upper() or "SCORCHING" in circuit.get("interne", "").upper():
        details.append(t("extreme"))
    return f"{nom}  —  {', '.join(details)}  [{circuit.get('interne') or circuit['nom']}]"


def segments_texte(texte, perc=None, ints=None):
    """Transforme un texte du jeu en morceaux (texte, surligné ?) prêts à afficher.

    Le jeu écrit ses descriptions ainsi :
        « La recharge des <widget id="Ability"/><H1>capacités</> est {perc} plus rapide. »
    - {perc}, {int}… sont remplacés par les valeurs de l'objet (perc → « 10 % ») ;
    - <widget …/> est une petite icône : on l'enlève ;
    - <H1>…</> est un mot surligné : on le garde, en gras dans la fenêtre.
    """
    perc, ints = perc or {}, ints or {}

    def valeur(m):
        cle = m.group(1)
        if cle in perc:
            return f"{perc[cle]} %"
        if cle in ints:
            return str(ints[cle])
        return m.group(0)

    texte = re.sub(r"\{(\w+)\}", valeur, texte or "")
    texte = re.sub(r"<widget[^>]*/>", "", texte)
    morceaux = []
    pos = 0
    for m in re.finditer(r"<H1>(.*?)</>", texte):
        if m.start() > pos:
            morceaux.append((texte[pos:m.start()], False))
        morceaux.append((m.group(1), True))
        pos = m.end()
    if pos < len(texte):
        morceaux.append((texte[pos:], False))
    return morceaux


def texte_simple(texte, perc=None, ints=None):
    return "".join(t for t, _ in segments_texte(texte, perc, ints))


def noms_des_mots_cles(textes):
    """Le jeu associe une icône à un mot : <widget id="Ramjet"/><H1>statoréacteur</>.
    On en déduit le nom français de chaque mot-clé (le plus fréquent)."""
    votes = {}
    for t in textes:
        for cle, mot in re.findall(r'<widget id="(\w+)"/>\s*<H1>([^<]+)</>', t or ""):
            votes.setdefault(cle, Counter())[mot.strip()] += 1
    return {cle: c.most_common(1)[0][0] for cle, c in votes.items()}


def groupe_pilote(nom):
    """DA_PlaneRacer_Nesodon → « module » (pilote de podracer) ; DA_Racer_Star → « speeder »."""
    return "module" if "PlaneRacer" in nom else "speeder"


def variante_pilote(nom):
    """Ce qui distingue une version d'un pilote d'une autre du même nom :
    DA_PlaneRacer_NesodonAged → « version âgée » ; DA_Racer_MentorBossRace →
    « course de boss » ; la version de base → « » (pas de suffixe)."""
    if nom.endswith("Aged"):
        return t("pilote_age")
    if "BossRace" in nom:
        return t("pilote_boss")
    return ""


def categorie_affixe(nom):
    """AFX_Ramjet_CriticalResetChance_v2 → Ramjet ; SAFX_… → SAFX."""
    morceaux = nom.split("_")
    if morceaux[0] == "AFX" and len(morceaux) > 2:
        mot = morceaux[1]
    else:
        mot = morceaux[0]
    return ALIAS_CATEGORIES.get(mot, mot)


def code_langue(texte):
    """« fr-FR » → « fr »"""
    return (texte or "")[:2].lower()


def textes_dans_la_langue(donnees):
    """Le mod donne chaque texte du jeu deux fois : dans la langue du jeu
    (« affiche ») et dans sa langue d'origine (« affiche_src », en général
    l'anglais). Si la fenêtre est dans la langue d'origine mais pas le jeu
    (fenêtre EN, jeu FR), on prend la version d'origine ; sinon celle du jeu.
    Ex. : affiche « Lantaana », affiche_src « Lantaana » ; affiche « Pilote
    automatique », affiche_src « Autopilot »."""
    ui = donnees.get("interface") or {}
    jeu, source = code_langue(ui.get("langue_jeu")), code_langue(ui.get("langue_source"))
    if not source or L.actuelle() != source or jeu == source:
        return donnees

    def remplacer(d):
        for cle in [k for k in d if k.endswith("_src")]:
            base, valeur = cle[:-4], d[cle]
            if isinstance(valeur, dict):
                d[base] = {**(d.get(base) or {}), **{k: v for k, v in valeur.items() if v}}
            elif valeur:
                d[base] = valeur

    for section in donnees.values():
        if isinstance(section, list):
            for element in section:
                if isinstance(element, dict):
                    remplacer(element)
    remplacer(ui)
    return donnees


def cle_circuit(nom):
    """« Lantaana — … [TRAK_DAL_P2P] » → « TRAK_DAL_P2P » : le nom interne,
    le même quelle que soit la langue (pour regrouper les records)."""
    m = re.search(r"\[([^\]]+)\]\s*$", nom or "")
    return m.group(1) if m else (nom or "")


class Catalogue:
    """Le contenu de catalogue.json, rangé pour l'interface."""

    def __init__(self, donnees):
        # Nom de chaque véhicule dans toutes les langues → sa clé (motojet…),
        # pour reconnaître un même véhicule dans temps.csv quelle que soit la langue
        self.cle_par_nom_vehicule = {}
        for v in donnees.get("vehicules", []):
            if v["nom"] in TYPES:
                for nom in (v.get("affiche"), v.get("affiche_src"), TYPES[v["nom"]][0]):
                    if nom:
                        self.cle_par_nom_vehicule[nom] = TYPES[v["nom"]][0]
        donnees = textes_dans_la_langue(donnees)

        # Véhicules : uniquement nos 4 types connus
        self.vehicules = []   # (clé, nom affiché, tag, n° d'archétype)
        for v in donnees.get("vehicules", []):
            if v["nom"] in TYPES:
                cle, tag_secours, numero = TYPES[v["nom"]]
                self.vehicules.append((cle, v.get("affiche") or cle, v.get("tag") or tag_secours, numero))
        ordre = [t[0] for t in TYPES.values()]
        self.vehicules.sort(key=lambda x: ordre.index(x[0]))

        # Planètes et circuits
        self.nom_planete = {p["nom"]: (p.get("affiche") or p["nom"]) for p in donnees.get("planetes", [])}
        self.circuits = []
        for c in donnees.get("circuits", []):
            code = code_planete(c["nom"])
            c["planete"] = self.nom_planete.get(PLANETES.get(code, ""), code or "?")
            c["special"] = est_special(c)
            c["texte"] = description_circuit(c)
            self.circuits.append(c)

        # Pilotes, rangés en deux groupes (module / speeder). Un même pilote
        # peut exister en plusieurs versions (Sebulba : jeune, âgé, mentor,
        # course de boss) : quand deux versions d'un groupe portent le même
        # nom, on ajoute la variante entre parenthèses.
        self.pilotes = []
        for p in donnees.get("pilotes", []):
            p["groupe"] = groupe_pilote(p["nom"])
            p["texte"] = p.get("affiche") or p["nom"]
            self.pilotes.append(p)
        homonymes = Counter((p["groupe"], p["texte"]) for p in self.pilotes)
        for p in self.pilotes:
            variante = variante_pilote(p["nom"])
            if homonymes[(p["groupe"], p["texte"])] > 1 and variante:
                p["texte"] += f"  ({variante})"
        self.pilotes.sort(key=lambda p: p["texte"].lower())

        # Noms des stats et des raretés fournis par le jeu (VehicleUIConfig)
        self.interface = donnees.get("interface", {}) or {}

        # Capacités : actives d'un côté, de crash de l'autre
        for c in donnees.get("capacites", []):
            c["texte"] = c.get("affiche") or nom_court(c["nom"])
            if c.get("affiche"):
                c["texte"] += f"   ({nom_court(c['nom'])})"
        tri = lambda x: x["texte"].lower()
        self.capacites = sorted([c for c in donnees.get("capacites", []) if not c.get("crash")], key=tri)
        self.crashs = sorted([c for c in donnees.get("capacites", []) if c.get("crash")], key=tri)

        # Affixes, rangés par catégorie
        self.affixes = donnees.get("affixes", [])
        mots = noms_des_mots_cles([a.get("description", "") for a in self.affixes])
        self.categories = {}   # mot-clé → nom affiché
        for a in self.affixes:
            a["categorie"] = categorie_affixe(a["nom"])
            a["texte"] = a.get("affiche") or a["nom"]
            if a["categorie"] not in self.categories:
                nom = t("categories").get(a["categorie"]) or mots.get(a["categorie"]) or a["categorie"]
                self.categories[a["categorie"]] = nom[:1].upper() + nom[1:]
        self.par_chemin = {a["chemin"]: a for a in self.affixes}
        self.capacite_par_chemin = {c["chemin"]: c for c in self.capacites + self.crashs}

    # ── noms affichés par le jeu ──────────────────────────────────────────
    def nom_stat(self, emplacement, numero_archetype):
        """Nom d'une stat tel qu'affiché en jeu ; l'emplacement 5 (« avancé »)
        porte un nom différent selon le type de véhicule."""
        ui = self.interface
        stat = (ui.get("stats") or {}).get(str(emplacement), "")
        piece = (ui.get("emplacements") or {}).get(str(emplacement), "")
        if emplacement == 5:
            stat = (ui.get("avance_stats") or {}).get(str(numero_archetype), "") or stat
            piece = (ui.get("avance_emplacements") or {}).get(str(numero_archetype), "") or piece
        if emplacement == 2 and not stat:
            stat = ui.get("resilience", "")
        nom = stat or t("stats_secours")[emplacement]
        return f"{nom}  ({piece})" if piece and piece != nom else nom

    def nom_rarete(self, rarete):
        nom = (self.interface.get("raretes") or {}).get(str(rarete), "")
        return nom or t("raretes_secours").get(rarete, "")

    # ── circuits ──────────────────────────────────────────────────────────
    def circuits_pour(self, tag_vehicule, planete=None, speciaux=False):
        res = [c for c in self.circuits
               if compatible(tag_vehicule, c.get("tag", ""))
               and (speciaux or not c["special"])
               and (planete is None or c["planete"] == planete)]
        return sorted(res, key=lambda c: c["texte"].lower())

    def planetes_pour(self, tag_vehicule, speciaux=False):
        return sorted({c["planete"] for c in self.circuits_pour(tag_vehicule, None, speciaux)})

    def cle_vehicule(self, nom):
        """Nom de véhicule (dans n'importe quelle langue) → clé motojet / voiture…"""
        return self.cle_par_nom_vehicule.get(nom, nom)


def lire_catalogue():
    """Renvoie un Catalogue, ou None si le fichier n'existe pas encore."""
    try:
        with open(FICHIER_CATALOGUE, encoding="utf-8") as f:
            return Catalogue(json.load(f))
    except (OSError, ValueError):
        return None


def envoyer_commande(lignes):
    """Écrit commande.txt d'un seul coup (fichier temporaire puis renommage),
    pour que le mod ne lise jamais une commande à moitié écrite."""
    DOSSIER_ECHANGE.mkdir(parents=True, exist_ok=True)
    tmp = FICHIER_COMMANDE.with_suffix(".tmp")
    tmp.write_text("\n".join(f"{k}={v}" for k, v in lignes.items()) + "\n", encoding="utf-8")
    os.replace(tmp, FICHIER_COMMANDE)


# ─────────────────────────────────────────────────────────────────────────
#  INTERFACE
# ─────────────────────────────────────────────────────────────────────────
class Fenetre(tk.Tk):
    def __init__(self):
        super().__init__()
        self.prefs = configparser.ConfigParser(interpolation=None)
        self.prefs.read(FICHIER_PREFERENCES, encoding="utf-8")
        for section in ("choix", "build", "fenetre"):
            if section not in self.prefs:
                self.prefs[section] = {}
        self.choix = self.prefs["choix"]
        self.pref_build = self.prefs["build"]

        # Langue : celle choisie la dernière fois, sinon celle de Windows
        L.choisir(self.prefs["fenetre"].get("langue") or L.langue_par_defaut())
        self.var_langue = tk.StringVar(value=L.actuelle())
        self.ecrire_langue_pour_le_mod()
        self.title(f"{t('titre')}  —  v{VERSION}")
        self.geometry("1350x800")
        self.minsize(1100, 650)
        self.catalogue = None

        # Variables de l'onglet Course
        self.var_type = tk.StringVar(value=self.choix.get("type", "motojet"))
        self.var_tours = tk.IntVar(value=int(self.choix.get("tours", "3")))
        self.var_speciaux = tk.BooleanVar(value=self.choix.getboolean("speciaux", False))
        self.var_dessus = tk.BooleanVar(value=self.choix.getboolean("au_premier_plan", True))
        self.var_etat = tk.StringVar(value="")
        self.circuits_affiches = []
        self.pilote = PILOTE_DEFAUT          # ligne choisie dans la liste des pilotes

        # Variables de l'onglet Build (valeurs reprises de la dernière fois)
        niveaux = (self.pref_build.get("niveaux", "") or "").split(",")
        self.var_niveaux = [tk.IntVar(value=int(niveaux[i]) if i < len(niveaux) and niveaux[i].isdigit() else 0)
                            for i in range(6)]
        self.var_capacites = [tk.StringVar(value=aucune()) for _ in range(NB_CAPACITES)]
        self.var_crash = tk.StringVar(value=aucune())
        self.var_boost = tk.BooleanVar(value=self.pref_build.getboolean("boost", True))
        self.var_ramjet = tk.BooleanVar(value=self.pref_build.getboolean("ramjet", True))
        self.var_pannes = tk.BooleanVar(value=self.pref_build.getboolean("pannes", True))
        self.var_illimites = tk.BooleanVar(value=self.pref_build.getboolean("crashs_illimites", True))
        self.var_recherche = tk.StringVar(value="")
        self.var_recherche.trace_add("write", lambda *a: self.remplir_affixes())
        self.var_caches = tk.BooleanVar(value=False)
        self.var_filtre_temps = tk.BooleanVar(value=False)
        self.var_nb_affixes = tk.StringVar(value="")
        self.affixes_choisis = [a for a in (self.pref_build.get("affixes", "") or "").split("|") if a]
        self.chemin_par_texte = {aucune(): ""}

        # Session d'entraînement (launcher). Le dossier du jeu est trouvé tout
        # seul par Steam, sauf si l'utilisateur en a choisi un (préférences).
        dossier_jeu = self.prefs["fenetre"].get("dossier_jeu", "")
        self.cfg = S.Config(racine_jeu=dossier_jeu) if S.est_dossier_du_jeu(dossier_jeu or None) else S.Config()
        self.file_messages = queue.Queue()   # messages envoyés par les tâches de fond
        self.travail_en_cours = False        # une tâche de fond tourne-t-elle ?
        self.jeu_vu = False                  # le jeu a-t-il tourné pendant cette session ?
        self.absent_depuis = None            # depuis quand le jeu est-il fermé ?
        self.var_session = tk.StringVar(value="")
        self.etat_session = None             # (clé du texte, couleur) affichés dans le bandeau
        self.etat_boutons = None             # (session ouverte, jeu lancé) au dernier contrôle

        self._construire()
        self.attributes("-topmost", self.var_dessus.get())
        self.charger_catalogue()
        self.after(DELAI_ETAT, self.rafraichir_etat)
        self.after(300, self.lire_messages)
        self.after(500, self.surveiller_session)
        self.executer(self.verifier_pare_feu_au_demarrage)
        self.protocol("WM_DELETE_WINDOW", self.fermer)

    # ═════════════════════════════════════════════════════════════════════
    #  CONSTRUCTION
    # ═════════════════════════════════════════════════════════════════════
    def _construire(self):
        # ── Bandeau « Session d'entraînement » ──
        bandeau = ttk.LabelFrame(self, text=t("bandeau_session"), padding=8)
        bandeau.pack(fill="x", padx=8, pady=(8, 0))
        self.etiquette_session = tk.Label(bandeau, textvariable=self.var_session, font=("Segoe UI", 11, "bold"),
                                          anchor="w")
        self.etiquette_session.grid(row=0, column=0, sticky="w")
        boutons = ttk.Frame(bandeau)
        boutons.grid(row=0, column=1, sticky="e")
        bandeau.columnconfigure(0, weight=1)
        self.bouton_demarrer = ttk.Button(boutons, text=t("btn_demarrer"), command=self.demarrer)
        self.bouton_relancer = ttk.Button(boutons, text=t("btn_relancer"), command=lambda: S.lancer_jeu(self.cfg))
        self.bouton_terminer = ttk.Button(boutons, text=t("btn_terminer"),
                                          command=lambda: self.executer(self.sequence_fin))
        self.bouton_pare_feu = ttk.Button(boutons, text=t("btn_pare_feu"),
                                          command=lambda: self.executer(self.sequence_lever_pare_feu))
        for b in (self.bouton_demarrer, self.bouton_relancer, self.bouton_terminer, self.bouton_pare_feu):
            b.pack(side="left", padx=4)
        self.liste_messages = tk.Listbox(bandeau, height=3, font=("Consolas", 9), activestyle="none")
        self.liste_messages.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        haut = ttk.Frame(self, padding=8)
        haut.pack(fill="x")
        ttk.Label(haut, text=t("vehicule"), font=("Segoe UI", 10, "bold")).pack(side="left")
        self.cadre_types = ttk.Frame(haut)
        self.cadre_types.pack(side="left", padx=8)

        # Bouton de langue : [FR][EN], le choix actif est enfoncé et en bleu
        langue = ttk.Frame(haut)
        langue.pack(side="right")
        ttk.Label(langue, text=t("langue")).pack(side="left", padx=(0, 6))
        for code in L.LANGUES:
            tk.Radiobutton(langue, text=L.NOMS[code], value=code, variable=self.var_langue,
                           indicatoron=False, width=4, font=("Segoe UI", 9, "bold"),
                           selectcolor="#bbdefb", cursor="hand2",
                           command=self.changer_langue).pack(side="left")

        # Le bas de la fenêtre est placé AVANT les onglets (en partant du bas) :
        # s'il manque de la hauteur, ce sont les onglets qui rétrécissent, et le
        # bouton « Lancer la course » reste toujours visible.
        ttk.Label(self, textvariable=self.var_etat, padding=(8, 2, 8, 6),
                  font=("Consolas", 10)).pack(side="bottom", fill="x")
        ttk.Label(self, text=t("aide"), foreground="#555", padding=(8, 0),
                  wraplength=1300).pack(side="bottom", fill="x")
        bas = ttk.Frame(self, padding=(8, 6))
        bas.pack(side="bottom", fill="x")
        ttk.Label(bas, text=t("tours")).pack(side="left")
        ttk.Spinbox(bas, from_=1, to=20, width=4, textvariable=self.var_tours).pack(side="left", padx=(4, 16))
        ttk.Checkbutton(bas, text=t("speciaux"),
                        variable=self.var_speciaux, command=self.remplir_planetes).pack(side="left")
        ttk.Checkbutton(bas, text=t("premier_plan"), variable=self.var_dessus,
                        command=lambda: self.attributes("-topmost", self.var_dessus.get())).pack(side="left", padx=16)
        ttk.Button(bas, text=t("recharger_catalogue"), command=self.demander_catalogue).pack(side="right")
        ttk.Button(bas, text=t("lancer"), command=self.lancer).pack(side="right", padx=8)

        onglets = self.onglets = ttk.Notebook(self)
        onglets.pack(fill="both", expand=True, padx=8)
        page_course = ttk.Frame(onglets, padding=8)
        page_build = ttk.Frame(onglets, padding=8)
        page_temps = ttk.Frame(onglets, padding=8)
        onglets.add(page_course, text=t("onglet_course"))
        onglets.add(page_build, text=t("onglet_build"))
        onglets.add(page_temps, text=t("onglet_temps"))
        self._construire_course(page_course)
        self._construire_build(page_build)
        self._construire_temps(page_temps)

    def _liste(self, parent, ligne, colonne, largeur):
        cadre = ttk.Frame(parent)
        cadre.grid(row=ligne, column=colonne, sticky="nsew", padx=(0, 8))
        liste = tk.Listbox(cadre, width=largeur, exportselection=False, activestyle="none",
                           font=("Segoe UI", 10))
        defil = ttk.Scrollbar(cadre, orient="vertical", command=liste.yview)
        liste.configure(yscrollcommand=defil.set)
        liste.pack(side="left", fill="both", expand=True)
        defil.pack(side="right", fill="y")
        return liste

    def _construire_course(self, page):
        page.columnconfigure(1, weight=3)
        page.columnconfigure(2, weight=1)
        page.rowconfigure(1, weight=1)
        for col, titre in enumerate((t("col_planete"), t("col_circuit"), t("col_pilote"))):
            ttk.Label(page, text=titre, font=("Segoe UI", 10, "bold")).grid(row=0, column=col, sticky="w")
        self.liste_planetes = self._liste(page, 1, 0, 18)
        self.liste_circuits = self._liste(page, 1, 1, 70)

        # Pilotes : un arbre à deux branches (module / speeder)
        cadre = ttk.Frame(page)
        cadre.grid(row=1, column=2, sticky="nsew")
        self.arbre_pilotes = ttk.Treeview(cadre, show="tree", selectmode="browse")
        self.arbre_pilotes.column("#0", width=250)
        defil = ttk.Scrollbar(cadre, orient="vertical", command=self.arbre_pilotes.yview)
        self.arbre_pilotes.configure(yscrollcommand=defil.set)
        self.arbre_pilotes.pack(side="left", fill="both", expand=True)
        defil.pack(side="right", fill="y")
        self.arbre_pilotes.tag_configure("groupe", font=("Segoe UI", 10, "bold"))
        self.arbre_pilotes.bind("<<TreeviewSelect>>", lambda e: self.pilote_choisi())

        self.liste_planetes.bind("<<ListboxSelect>>", lambda e: self.remplir_circuits())
        self.liste_circuits.bind("<<ListboxSelect>>", lambda e: self.circuit_choisi())
        self.liste_circuits.bind("<Double-Button-1>", lambda e: self.lancer())

    def _construire_build(self, page):
        """Onglet Build :
             [Stats] [Capacités + options] [Affixes par catégorie]
             [Description de l'élément survolé ] [Récapitulatif du build]"""
        page.columnconfigure(2, weight=1)
        page.rowconfigure(0, weight=1)

        # ── Colonne 1 : améliorations de stat ──
        stats = ttk.LabelFrame(page, text=t("stats_titre"), padding=8)
        stats.grid(row=0, column=0, sticky="nsw", padx=(0, 8))
        # Nom de la stat à gauche, curseur à droite : une ligne par stat (prend
        # deux fois moins de hauteur que le nom au-dessus du curseur)
        self.etiquettes_stats = []
        for i in range(6):
            etiquette = ttk.Label(stats, text=t("stats_secours")[i], wraplength=140)
            etiquette.grid(row=i, column=0, sticky="w", padx=(0, 6))
            self.etiquettes_stats.append(etiquette)
            tk.Scale(stats, from_=0, to=NIVEAU_MAX, orient="horizontal", length=170, showvalue=True,
                     variable=self.var_niveaux[i], command=lambda *_: self.rafraichir_recap()
                     ).grid(row=i, column=1, sticky="w")

        # ── Colonne 2 : capacités et options ──
        milieu = ttk.Frame(page)
        milieu.grid(row=0, column=1, sticky="nsw", padx=(0, 8))
        caps = ttk.LabelFrame(milieu, text=t("capacites"), padding=8)
        caps.pack(fill="x")
        # Une ligne par emplacement : son nom à gauche, la liste à droite
        self.combos_capacites = []
        for i in range(NB_CAPACITES):
            ttk.Label(caps, text=t("emplacement_n", n=i + 1)).grid(row=i, column=0, sticky="w", padx=(0, 6))
            c = ttk.Combobox(caps, textvariable=self.var_capacites[i], state="readonly", width=38)
            c.grid(row=i, column=1, sticky="w", pady=2)
            c.bind("<<ComboboxSelected>>", lambda e, v=self.var_capacites[i]: self.capacite_choisie(v))
            self.combos_capacites.append(c)
        ttk.Label(caps, text=t("capacite_crash"), wraplength=90).grid(row=NB_CAPACITES, column=0, sticky="w",
                                                                    padx=(0, 6), pady=(8, 0))
        self.combo_crash = ttk.Combobox(caps, textvariable=self.var_crash, state="readonly", width=38)
        self.combo_crash.grid(row=NB_CAPACITES, column=1, sticky="w", pady=(8, 0))
        self.combo_crash.bind("<<ComboboxSelected>>", lambda e: self.capacite_choisie(self.var_crash))

        opts = ttk.LabelFrame(milieu, text=t("options"), padding=8)
        opts.pack(fill="x", pady=(8, 0))
        for texte, var in ((t("opt_boost"), self.var_boost), (t("opt_ramjet"), self.var_ramjet),
                           (t("opt_pannes"), self.var_pannes), (t("opt_illimites"), self.var_illimites)):
            tk.Checkbutton(opts, text=texte, variable=var, anchor="w",
                           command=self.rafraichir_recap).pack(fill="x")

        # ── Colonne 3 : affixes par catégorie, avec cases à cocher ──
        aff = ttk.LabelFrame(page, text=t("affixes_titre"), padding=8)
        aff.grid(row=0, column=2, sticky="nsew")
        aff.columnconfigure(0, weight=1)
        aff.rowconfigure(1, weight=1)
        haut = ttk.Frame(aff)
        haut.grid(row=0, column=0, sticky="ew")
        ttk.Label(haut, text=t("rechercher")).pack(side="left")
        ttk.Entry(haut, textvariable=self.var_recherche, width=26).pack(side="left", padx=4)
        ttk.Checkbutton(haut, text=t("caches"), variable=self.var_caches,
                        command=self.remplir_affixes).pack(side="left", padx=8)

        cadre = ttk.Frame(aff)
        cadre.grid(row=1, column=0, sticky="nsew")
        self.arbre = ttk.Treeview(cadre, columns=("rarete",), show="tree headings", selectmode="none")
        self.arbre.heading("#0", text=t("col_affixe"))
        self.arbre.heading("rarete", text=t("col_rarete"))
        self.arbre.column("#0", width=380)
        self.arbre.column("rarete", width=110, anchor="center")
        defil = ttk.Scrollbar(cadre, orient="vertical", command=self.arbre.yview)
        self.arbre.configure(yscrollcommand=defil.set)
        self.arbre.pack(side="left", fill="both", expand=True)
        defil.pack(side="right", fill="y")
        self.arbre.tag_configure("choisi", background="#d9f2d0", font=("Segoe UI", 10, "bold"))
        self.arbre.tag_configure("categorie", font=("Segoe UI", 10, "bold"))
        for r, couleur in COULEURS_RARETE.items():
            self.arbre.tag_configure(f"r{r}", foreground=couleur)
        self.arbre.bind("<Button-1>", self.clic_affixe)
        self.arbre.bind("<Motion>", self.survol_affixe)

        bas = ttk.Frame(aff)
        bas.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        ttk.Label(bas, textvariable=self.var_nb_affixes, font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(bas, text=t("tout_decocher"), command=self.retirer_affixes).pack(side="right")
        # (ici et pas sous les options : la colonne du milieu n'a pas la place, il était coupé)
        ttk.Button(bas, text=t("build_zero"), command=self.build_a_zero).pack(side="right", padx=(0, 8))

        # ── Ligne du bas : description + récapitulatif ──
        bas_page = ttk.Frame(page)
        bas_page.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        bas_page.columnconfigure(0, weight=1)
        bas_page.columnconfigure(1, weight=1)
        desc = ttk.LabelFrame(bas_page, text=t("description_titre"), padding=6)
        desc.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.texte_desc = tk.Text(desc, height=6, wrap="word", font=("Segoe UI", 10), relief="flat",
                                  background=self.cget("background"))
        self.texte_desc.pack(fill="both", expand=True)
        self.texte_desc.tag_configure("titre", font=("Segoe UI", 11, "bold"))
        self.texte_desc.tag_configure("h1", font=("Segoe UI", 10, "bold"), foreground="#1565c0")
        self.texte_desc.tag_configure("defaut", foreground="#c62828")
        self.texte_desc.configure(state="disabled")
        recap = ttk.LabelFrame(bas_page, text=t("recap_titre"), padding=6)
        recap.grid(row=0, column=1, sticky="nsew")
        self.texte_recap = tk.Text(recap, height=6, wrap="word", font=("Segoe UI", 10), relief="flat",
                                   background=self.cget("background"))
        self.texte_recap.pack(fill="both", expand=True)
        self.texte_recap.tag_configure("cle", font=("Segoe UI", 10, "bold"))
        self.texte_recap.configure(state="disabled")

    def _construire_temps(self, page):
        """Onglet Mes temps : l'historique de temps.csv, record surligné."""
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)
        haut = ttk.Frame(page)
        haut.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Checkbutton(haut, text=t("filtre_temps"), variable=self.var_filtre_temps,
                        command=self.remplir_temps).pack(side="left")
        ttk.Button(haut, text=t("ouvrir_temps"),
                   command=lambda: os.startfile(FICHIER_TEMPS_CSV.parent) if FICHIER_TEMPS_CSV.parent.exists()
                   else None).pack(side="right")
        ttk.Label(haut, text=t("legende_record"),
                  foreground="#555").pack(side="right", padx=12)
        colonnes = ("date", "planete", "circuit", "tours", "vehicule", "pilote", "temps", "meilleur", "detail")
        titres = t("colonnes_temps")
        largeurs = (135, 95, 360, 45, 95, 105, 105, 90, 200)
        cadre = ttk.Frame(page)
        cadre.grid(row=1, column=0, sticky="nsew")
        self.table_temps = ttk.Treeview(cadre, columns=colonnes, show="headings")
        for col, titre, larg in zip(colonnes, titres, largeurs):
            self.table_temps.heading(col, text=titre)
            self.table_temps.column(col, width=larg, anchor="w")
        defil = ttk.Scrollbar(cadre, orient="vertical", command=self.table_temps.yview)
        self.table_temps.configure(yscrollcommand=defil.set)
        self.table_temps.pack(side="left", fill="both", expand=True)
        defil.pack(side="right", fill="y")
        self.table_temps.tag_configure("record", background="#fff3c4", font=("Segoe UI", 10, "bold"))
        self._date_temps = None

    def remplir_temps(self):
        """Relit temps.csv (le plus récent en haut) et marque les records."""
        try:
            with open(FICHIER_TEMPS_CSV, encoding="utf-8", newline="") as f:
                lignes = list(csv.DictReader(f, delimiter=";"))
        except OSError:
            lignes = []
        # Record = plus petit temps (en secondes) par circuit + véhicule + tours,
        # sans compter les courses où un save state a été utilisé (F8).
        # Circuit et véhicule sont reconnus par leur nom interne / leur clé :
        # un temps noté en français et un autre en anglais comptent ensemble.
        vehicule_de = self.catalogue.cle_vehicule if self.catalogue else (lambda nom: nom)

        def cle_ligne(l):
            return cle_circuit(l.get("Circuit")), vehicule_de(l.get("Véhicule")), l.get("Nb tours")

        records = {}
        for l in lignes:
            if l.get("Save state") == "oui":
                continue
            try:
                s = float(l.get("Secondes", "0").replace(",", "."))
            except ValueError:
                continue
            if s > 0:
                cle = cle_ligne(l)
                records[cle] = min(s, records.get(cle, s))
        circuit, vehicule = self.circuit_et_vehicule_choisis()
        self.table_temps.delete(*self.table_temps.get_children())
        for l in reversed(lignes):
            cle = cle_ligne(l)
            if self.var_filtre_temps.get() and (cle[0] != cle_circuit(circuit) or cle[1] != vehicule_de(vehicule)):
                continue
            save_state = l.get("Save state") == "oui"
            try:
                est_record = not save_state and float(l.get("Secondes", "0").replace(",", ".")) == records.get(cle)
            except ValueError:
                est_record = False
            temps = ("★ " if est_record else "") + l.get("Temps", "") + ("  (save state)" if save_state else "")
            valeurs = (l.get("Date", ""), l.get("Planète", ""), l.get("Circuit", ""), l.get("Nb tours", ""),
                       l.get("Véhicule", ""), l.get("Pilote", ""), temps, l.get("Meilleur tour", ""),
                       l.get("Détail des tours", ""))
            self.table_temps.insert("", "end", values=valeurs, tags=("record",) if est_record else ())

    def circuit_et_vehicule_choisis(self):
        """Noms (tels qu'écrits dans temps.csv) du circuit et du véhicule sélectionnés."""
        sel = self.liste_circuits.curselection() if hasattr(self, "liste_circuits") else ()
        circuit = self.nom_circuit(self.circuits_affiches[sel[0]]) if sel else ""
        vehicule = ""
        for cle, affiche, _t, _n in (self.catalogue.vehicules if self.catalogue else []):
            if cle == self.var_type.get():
                vehicule = affiche
        return circuit, vehicule

    @staticmethod
    def nom_circuit(c):
        return f"{c.get('affiche') or c['nom']} [{c.get('interne') or c['nom']}]"

    # ═════════════════════════════════════════════════════════════════════
    #  REMPLISSAGE
    # ═════════════════════════════════════════════════════════════════════
    def charger_catalogue(self):
        self.catalogue = lire_catalogue()
        if not self.catalogue:
            self.var_etat.set(t("attente_catalogue"))
            self.after(2000, self.charger_catalogue)
            return
        for enfant in self.cadre_types.winfo_children():
            enfant.destroy()
        for cle, affiche, _tag, _num in self.catalogue.vehicules:
            ttk.Radiobutton(self.cadre_types, text=affiche, value=cle, variable=self.var_type,
                            command=self.type_change).pack(side="left", padx=6)
        self.remplir_pilotes()
        self.remplir_planetes()
        self.remplir_build()

    def type_change(self):
        self.remplir_planetes()
        self.renommer_stats()
        self.rafraichir_recap()

    def info_vehicule(self):
        for cle, _a, tag, num in (self.catalogue.vehicules if self.catalogue else []):
            if cle == self.var_type.get():
                return tag, num
        return "", 2

    def tag_vehicule(self):
        return self.info_vehicule()[0]

    # ── onglet Course ─────────────────────────────────────────────────────
    def remplir_planetes(self):
        if not self.catalogue:
            return
        planetes = self.catalogue.planetes_pour(self.tag_vehicule(), self.var_speciaux.get())
        self.liste_planetes.delete(0, "end")
        for p in planetes:
            self.liste_planetes.insert("end", p)
        # La planète du circuit choisi (retrouvé par son chemin, le même dans
        # toutes les langues), sinon celle notée la dernière fois
        voulue = self.choix.get("planete", "")
        for c in self.catalogue.circuits:
            if c["chemin"] == self.choix.get("piste", ""):
                voulue = c["planete"]
        index = planetes.index(voulue) if voulue in planetes else 0
        if planetes:
            self.liste_planetes.selection_set(index)
            self.liste_planetes.see(index)
        self.remplir_circuits()

    def remplir_circuits(self):
        sel = self.liste_planetes.curselection()
        planete = self.liste_planetes.get(sel[0]) if sel else None
        self.circuits_affiches = self.catalogue.circuits_pour(self.tag_vehicule(), planete, self.var_speciaux.get())
        self.liste_circuits.delete(0, "end")
        for c in self.circuits_affiches:
            self.liste_circuits.insert("end", c["texte"])
        chemins = [c["chemin"] for c in self.circuits_affiches]
        voulu = self.choix.get("piste", "")
        if voulu in chemins:
            i = chemins.index(voulu)
            self.liste_circuits.selection_set(i)
            self.liste_circuits.see(i)

    def remplir_pilotes(self):
        """Arbre des pilotes : « pilote par défaut », puis pilotes de module et de speeder."""
        arbre = self.arbre_pilotes
        arbre.delete(*arbre.get_children())
        arbre.insert("", "end", iid=PILOTE_DEFAUT, text=t("pilote_defaut"))
        for groupe in GROUPES_PILOTES:
            pilotes = [p for p in self.catalogue.pilotes if p["groupe"] == groupe]
            if pilotes:
                parent = arbre.insert("", "end", iid="grp:" + groupe, text=t("pilotes_" + groupe),
                                      open=True, tags=("groupe",))
                for p in pilotes:
                    arbre.insert(parent, "end", iid=p["chemin"], text=p["texte"])
        voulu = self.choix.get("pilote", "")
        self.pilote = voulu if voulu and arbre.exists(voulu) else PILOTE_DEFAUT
        arbre.selection_set(self.pilote)
        arbre.see(self.pilote)

    def pilote_choisi(self):
        """Clic dans l'arbre des pilotes. Un titre de groupe n'est pas un
        pilote : il s'ouvre ou se ferme, et le pilote choisi reste le même."""
        arbre = self.arbre_pilotes
        sel = arbre.selection()
        if not sel:
            return
        if sel[0].startswith("grp:"):
            arbre.item(sel[0], open=not arbre.item(sel[0], "open"))
            if arbre.exists(self.pilote):
                arbre.selection_set(self.pilote)
            return
        self.pilote = sel[0]

    def pilote_selectionne(self):
        """(chemin du pilote, nom affiché) ; chemin vide = pilote par défaut."""
        if self.pilote == PILOTE_DEFAUT or not self.arbre_pilotes.exists(self.pilote):
            return "", t("pilote_defaut")
        return self.pilote, self.arbre_pilotes.item(self.pilote, "text")

    def circuit_choisi(self):
        """À la sélection d'un circuit, propose son nombre de tours habituel."""
        sel = self.liste_circuits.curselection()
        if sel:
            tours = self.circuits_affiches[sel[0]].get("tours")
            if isinstance(tours, int) and tours > 0:
                self.var_tours.set(tours)

    # ── onglet Build ──────────────────────────────────────────────────────
    def remplir_build(self):
        cat = self.catalogue
        self.chemin_par_texte = {aucune(): ""}
        for c in cat.capacites + cat.crashs:
            self.chemin_par_texte[c["texte"]] = c["chemin"]
        texte_par_chemin = {v: k for k, v in self.chemin_par_texte.items()}

        valeurs = [aucune()] + [c["texte"] for c in cat.capacites]
        anciennes = (self.pref_build.get("capacites", "") or "").split("|")
        for i, combo in enumerate(self.combos_capacites):
            combo["values"] = valeurs
            chemin = anciennes[i] if i < len(anciennes) else ""
            self.var_capacites[i].set(texte_par_chemin.get(chemin, aucune()))
        self.combo_crash["values"] = [aucune()] + [c["texte"] for c in cat.crashs]
        self.var_crash.set(texte_par_chemin.get(self.pref_build.get("crash", ""), aucune()))
        if not cat.capacites:
            self.var_etat.set(t("aucune_capacite"))
        # On oublie les affixes choisis qui n'existent plus dans le catalogue
        self.affixes_choisis = [a for a in self.affixes_choisis if a in cat.par_chemin]
        self.renommer_stats()
        self.remplir_affixes()

    def renommer_stats(self):
        """Met les noms des stats du jeu sur les curseurs (le 6e dépend du véhicule)."""
        if not self.catalogue:
            return
        _tag, numero = self.info_vehicule()
        for i, etiquette in enumerate(self.etiquettes_stats):
            etiquette.configure(text=self.catalogue.nom_stat(i, numero))

    def remplir_affixes(self):
        """Arbre des affixes : une branche par catégorie, ☑ devant les affixes choisis."""
        if not self.catalogue:
            return
        recherche = self.var_recherche.get().strip().lower()
        caches = self.var_caches.get()
        self.arbre.delete(*self.arbre.get_children())
        groupes = {}
        for a in self.catalogue.affixes:
            choisi = a["chemin"] in self.affixes_choisis
            visible = a.get("visible", True) and a["categorie"] not in CATEGORIES_CACHEES
            if not (caches or visible or choisi):
                continue
            if recherche and not (recherche in a["texte"].lower()
                                  or recherche in texte_simple(a.get("description", "")).lower()
                                  or recherche in self.catalogue.categories[a["categorie"]].lower()):
                continue
            groupes.setdefault(a["categorie"], []).append(a)
        noms = self.catalogue.categories
        for cat in sorted(groupes, key=lambda c: noms[c].lower()):
            liste = sorted(groupes[cat], key=lambda a: a["texte"].lower())
            nb = sum(1 for a in liste if a["chemin"] in self.affixes_choisis)
            texte = f"{noms[cat]}   ({nb} / {len(liste)})" if nb else f"{noms[cat]}   ({len(liste)})"
            parent = self.arbre.insert("", "end", iid="cat:" + cat, text=texte, open=bool(recherche or nb),
                                       tags=("categorie",))
            for a in liste:
                choisi = a["chemin"] in self.affixes_choisis
                tags = [f"r{a.get('rarete', 0)}"] + (["choisi"] if choisi else [])
                self.arbre.insert(parent, "end", iid=a["chemin"], text=("☑  " if choisi else "☐  ") + a["texte"],
                                  values=(self.catalogue.nom_rarete(a.get("rarete", 6)),), tags=tags)
        self.var_nb_affixes.set(t("nb_affixes", n=len(self.affixes_choisis)))
        self.rafraichir_recap()

    def clic_affixe(self, evenement):
        """Clic sur une ligne d'affixe : coche ou décoche ; sur une catégorie : ouvre/ferme."""
        ligne = self.arbre.identify_row(evenement.y)
        if not ligne:
            return
        if ligne.startswith("cat:"):
            self.arbre.item(ligne, open=not self.arbre.item(ligne, "open"))
            return "break"
        if ligne in self.affixes_choisis:
            self.affixes_choisis.remove(ligne)
        else:
            self.affixes_choisis.append(ligne)
        ouvertes = [c for c in self.arbre.get_children() if self.arbre.item(c, "open")]
        haut = self.arbre.yview()[0]
        self.remplir_affixes()
        for c in ouvertes:
            if self.arbre.exists(c):
                self.arbre.item(c, open=True)
        self.arbre.yview_moveto(haut)
        self.decrire_affixe(ligne)
        return "break"

    def survol_affixe(self, evenement):
        ligne = self.arbre.identify_row(evenement.y)
        if ligne and not ligne.startswith("cat:") and ligne != getattr(self, "_dernier_survol", None):
            self._dernier_survol = ligne
            self.decrire_affixe(ligne)

    def capacite_choisie(self, variable):
        chemin = self.chemin_par_texte.get(variable.get(), "")
        c = self.catalogue.capacite_par_chemin.get(chemin) if self.catalogue else None
        if c:
            self.ecrire_description(c["texte"], [(c.get("description", ""), {}, {}, False)])
        self.rafraichir_recap()

    def decrire_affixe(self, chemin):
        a = self.catalogue.par_chemin.get(chemin)
        if not a:
            return
        parties = [(a.get("description", ""), a.get("perc"), a.get("int"), False)]
        if a.get("description_def"):
            parties.append((t("defaut") + a["description_def"], a.get("perc_def"), a.get("int_def"), True))
        titre = f"{a['texte']}  —  {self.catalogue.nom_rarete(a.get('rarete', 6))}"
        self.ecrire_description(titre, parties)

    def ecrire_description(self, titre, parties):
        """Affiche un titre puis des descriptions du jeu, mots surlignés en bleu gras."""
        zone = self.texte_desc
        zone.configure(state="normal")
        zone.delete("1.0", "end")
        zone.insert("end", titre + "\n", "titre")
        for texte, perc, ints, est_defaut in parties:
            if not texte:
                continue
            for morceau, surligne in segments_texte(texte, perc, ints):
                tags = ["h1"] if surligne else []
                if est_defaut:
                    tags.append("defaut")
                zone.insert("end", morceau, tuple(tags))
            zone.insert("end", "\n")
        zone.configure(state="disabled")

    def rafraichir_recap(self):
        """Récapitulatif lisible de tout ce qui sera envoyé au jeu."""
        if not hasattr(self, "texte_recap"):
            return
        cat = self.catalogue
        zone = self.texte_recap
        zone.configure(state="normal")
        zone.delete("1.0", "end")
        _tag, numero = self.info_vehicule()
        stats = []
        for i, v in enumerate(self.var_niveaux):
            nom = cat.nom_stat(i, numero).split("  (")[0] if cat else t("stats_secours")[i]
            stats.append(f"{nom} {v.get()}")
        zone.insert("end", t("recap_stats"), "cle")
        zone.insert("end", " · ".join(stats) + "\n")
        caps = [v.get().split("   (")[0] for v in self.var_capacites if v.get() != aucune()]
        zone.insert("end", t("recap_capacites"), "cle")
        zone.insert("end", (", ".join(caps) or aucune()) + "\n")
        zone.insert("end", t("recap_crash"), "cle")
        zone.insert("end", self.var_crash.get().split("   (")[0] + "\n")
        noms_aff = [cat.par_chemin[c]["texte"] for c in self.affixes_choisis if cat and c in cat.par_chemin]
        zone.insert("end", t("recap_affixes", n=len(noms_aff)), "cle")
        zone.insert("end", (", ".join(noms_aff) or t("aucun_sans")) + "\n")
        options = [nom for nom, var in (("Afterburner", self.var_boost), ("Ramjet", self.var_ramjet),
                                        (t("opt_pannes"), self.var_pannes),
                                        (t("opt_illimites"), self.var_illimites)) if var.get()]
        zone.insert("end", t("recap_options"), "cle")
        zone.insert("end", ", ".join(options) or t("aucune_sans"))
        zone.configure(state="disabled")

    def resume_build(self):
        """Résumé du build sur une ligne, pour le fichier des temps (sans « | »)."""
        cat = self.catalogue
        caps = [v.get().split("   (")[0] for v in self.var_capacites if v.get() != aucune()]
        crash = self.var_crash.get().split("   (")[0]
        noms_aff = [cat.par_chemin[c]["texte"] for c in self.affixes_choisis if cat and c in cat.par_chemin]
        morceaux = ["stats " + "/".join(str(v.get()) for v in self.var_niveaux),
                    t("resume_capacites") + (", ".join(caps) or t("aucune_sans")),
                    t("resume_crash") + crash,
                    t("resume_affixes", n=len(noms_aff)) + (", ".join(noms_aff) or t("aucun_sans"))]
        if self.var_illimites.get():
            morceaux.append(t("resume_illimites"))
        return " · ".join(morceaux).replace("|", "/")

    def retirer_affixes(self):
        self.affixes_choisis = []
        self.remplir_affixes()

    def build_a_zero(self):
        for v in self.var_niveaux:
            v.set(0)
        for v in self.var_capacites:
            v.set(aucune())
        self.var_crash.set(aucune())
        self.retirer_affixes()

    def commande_build(self):
        """Les clés du build à ajouter à la commande envoyée au jeu,
        et la liste des capacités emplacement par emplacement (pour les préférences)."""
        capacites = [self.chemin_par_texte.get(v.get(), "") for v in self.var_capacites]
        return {
            "niveaux": ",".join(str(int(v.get())) for v in self.var_niveaux),
            "capacites": "|".join(c for c in capacites if c),
            "crash": self.chemin_par_texte.get(self.var_crash.get(), ""),
            "affixes": "|".join(self.affixes_choisis),
            "boost": "1" if self.var_boost.get() else "0",
            "ramjet": "1" if self.var_ramjet.get() else "0",
            "pannes": "1" if self.var_pannes.get() else "0",
            "crashs_illimites": "1" if self.var_illimites.get() else "0",
        }, capacites

    # ═════════════════════════════════════════════════════════════════════
    #  SESSION D'ENTRAÎNEMENT (LAUNCHER)
    #  Les étapes longues (copies, attente du pare-feu) tournent en tâche de
    #  fond pour que la fenêtre ne se fige pas. Elles envoient leurs messages
    #  dans une file, que la fenêtre affiche toutes les 0,3 s.
    # ═════════════════════════════════════════════════════════════════════
    def message(self, texte):
        """Utilisable depuis une tâche de fond : met le message dans la file
        et le garde dans sessions/journal-fenetre.txt."""
        ligne = f"{datetime.now():%H:%M:%S}  {texte}"
        self.file_messages.put(ligne)
        try:
            self.cfg.sessions.mkdir(parents=True, exist_ok=True)
            with open(self.cfg.sessions / "journal-fenetre.txt", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now():%Y-%m-%d} {ligne}\n")
        except OSError:
            pass

    def lire_messages(self):
        while not self.file_messages.empty():
            self.liste_messages.insert("end", self.file_messages.get())
            self.liste_messages.see("end")
        self.after(300, self.lire_messages)

    def executer(self, travail):
        """Lance une tâche de fond, une seule à la fois."""
        if self.travail_en_cours:
            self.message(t("patiente"))
            return
        self.travail_en_cours = True

        def enveloppe():
            try:
                travail()
            except S.ErreurSession as e:
                self.message("✖ " + str(e))
            except Exception as e:   # filet de sécurité : jamais de fenêtre figée
                self.message(t("erreur_inattendue", e=repr(e)))
            finally:
                self.travail_en_cours = False
        threading.Thread(target=enveloppe, daemon=True).start()

    def demarrer(self):
        """▶ Démarrer : d'abord les questions à poser à l'utilisateur (fenêtres
        de dialogue, donc ici et pas en tâche de fond), puis sequence_debut."""
        # 1. Le jeu n'a pas été trouvé par Steam : on demande son dossier
        if not S.jeu_trouve(self.cfg):
            dossier = filedialog.askdirectory(title=t("choisir_jeu"), mustexist=True)
            if not dossier:
                return
            if not S.est_dossier_du_jeu(dossier):
                messagebox.showerror("PracticeMode", t("dossier_jeu_invalide"))
                return
            self.prefs["fenetre"]["dossier_jeu"] = str(Path(dossier))
            self.enregistrer_preferences()
            self.cfg = S.Config(racine_jeu=dossier)
            self.message(t("dossier_jeu_ok", chemin=Path(dossier)))
        # 2. UE4SS a besoin de Visual C++ : s'il manque, on propose l'installateur du jeu
        manquant = S.visual_cpp_manquant()
        if manquant:
            installateur = S.installateur_visual_cpp(self.cfg)
            if not installateur:
                self.message("✖ " + t("vcpp_absent", dll=", ".join(manquant)))
                return
            if messagebox.askyesno(t("vcpp_titre"), t("vcpp_question", dll=", ".join(manquant),
                                                     chemin=installateur)):
                os.startfile(installateur)   # l'installateur de Microsoft demande lui-même l'administrateur
                self.message(t("vcpp_lance"))
            return
        self.executer(self.sequence_debut)

    def sequence_debut(self):
        """▶ Démarrer : sauvegarde + UE4SS + pare-feu + lancement du jeu."""
        if S.pare_feu_windows_actif() is False:
            raise S.ErreurSession(t("pare_feu_desactive"))
        self.message(t("debut_sauvegarde"))
        S.debut(self.cfg, self.message)
        try:
            self.message(t("pare_feu_uac"))
            if not S.lancer_script_pare_feu(self.cfg, "Session"):
                self.message(t("pare_feu_refuse"))
                S.fin(self.cfg, self.message)
                return
            etat = S.attendre_etat_pare_feu(self.cfg, "actif", 120)
            if etat != "actif":
                self.message(t("pare_feu_echec", etat=etat or t("pas_de_reponse")))
                S.fin(self.cfg, self.message)
                S.liberer_pare_feu(self.cfg, self.message)
                return
        except Exception:
            # Quoi qu'il arrive, pas de jeu moddé sans pare-feu : on défait tout.
            self.message(t("pare_feu_probleme"))
            S.fin(self.cfg, self.message)
            raise
        self.message(t("pare_feu_actif"))
        self.jeu_vu, self.absent_depuis = False, None
        S.lancer_jeu(self.cfg)
        self.message(t("lancement_jeu"))

    def sequence_fin(self):
        """Fin : retrait d'UE4SS, sauvegarde remise, pare-feu levé."""
        self.message(t("fin_remise"))
        S.fin(self.cfg, self.message)
        S.liberer_pare_feu(self.cfg, self.message)
        self.jeu_vu, self.absent_depuis = False, None
        self.message(t("fin_ok"))

    def sequence_lever_pare_feu(self):
        S.liberer_pare_feu(self.cfg, self.message)

    def verifier_pare_feu_au_demarrage(self):
        """À l'ouverture : dossier utilisable, jeu trouvé, et une session ou un
        blocage oubliés par une session interrompue ?"""
        try:
            DOSSIER_ECHANGE.mkdir(parents=True, exist_ok=True)
            essai = DOSSIER_ECHANGE / "essai-ecriture.tmp"
            essai.write_text("ok", encoding="utf-8")
            essai.unlink()
        except OSError:
            self.message("✖ " + t("dossier_non_inscriptible", chemin=DOSSIER_PROJET))
        if S.jeu_trouve(self.cfg):
            self.message(t("dossier_jeu_ok", chemin=self.cfg.racine_jeu))
        else:
            self.message("⚠ " + t("jeu_introuvable"))
        if S.session_en_cours(self.cfg) and not S.jeu_lance(self.cfg):
            self.message(t("session_oubliee"))
        elif not S.session_en_cours(self.cfg) and S.regles_pare_feu_presentes(self.cfg):
            self.message(t("blocage_oublie"))

    def surveiller_session(self):
        """Toutes les 2 s : état affiché, boutons, et fin automatique quand le jeu se ferme."""
        try:
            session = S.session_en_cours(self.cfg)
            lance = S.jeu_lance(self.cfg)
        except Exception:
            session, lance = None, False
        if session and lance:
            self.jeu_vu, self.absent_depuis = True, None
            self.afficher_session("session_en_cours", "#c62828")
        elif session:
            if self.jeu_vu and not self.travail_en_cours:
                # Le jeu vient de se fermer : on attend quelques secondes (il
                # peut encore écrire sa sauvegarde) puis on remet tout d'origine.
                if self.absent_depuis is None:
                    self.absent_depuis = time.time()
                    self.message(t("jeu_ferme"))
                elif time.time() - self.absent_depuis > 8:
                    self.jeu_vu = False
                    self.executer(self.sequence_fin)
            self.afficher_session("session_ouverte", "#ef6c00")
        elif lance:
            self.afficher_session("session_origine_lance", "#555555")
        else:
            self.afficher_session("session_vanilla", "#2e7d32")
        self.etat_boutons = (session, lance)
        self.activer_boutons()
        self.after(2000, self.surveiller_session)

    def activer_boutons(self):
        """N'autorise que les boutons qui ont un sens dans l'état actuel."""
        if self.etat_boutons is None:
            return
        session, lance = self.etat_boutons
        occupe = self.travail_en_cours
        self.bouton_demarrer.state(["!disabled"] if not (session or lance or occupe) else ["disabled"])
        self.bouton_relancer.state(["!disabled"] if session and not lance and not occupe else ["disabled"])
        self.bouton_terminer.state(["!disabled"] if session and not lance and not occupe else ["disabled"])
        self.bouton_pare_feu.state(["!disabled"] if not session and not occupe else ["disabled"])

    def afficher_session(self, cle, couleur):
        """Bandeau : `cle` est la clé du texte (voir langues.py)."""
        self.etat_session = (cle, couleur)
        if self.var_session.get() != t(cle):
            self.var_session.set(t(cle))
        self.etiquette_session.configure(foreground=couleur)

    # ═════════════════════════════════════════════════════════════════════
    #  LANGUE
    #  Changer de langue reconstruit toute la fenêtre : les choix en cours
    #  (circuit, pilote, build…) sont d'abord mis de côté puis remis.
    # ═════════════════════════════════════════════════════════════════════
    def ecrire_langue_pour_le_mod(self):
        """echange/langue.txt : le mod y lit la langue de ses messages."""
        try:
            DOSSIER_ECHANGE.mkdir(parents=True, exist_ok=True)
            FICHIER_LANGUE.write_text(L.actuelle(), encoding="utf-8")
        except OSError:
            pass

    def memoriser_selection(self):
        """Garde planète, circuit et pilote sélectionnés (même sans avoir lancé)."""
        sel_pl = self.liste_planetes.curselection()
        if sel_pl:
            self.choix["planete"] = self.liste_planetes.get(sel_pl[0])
        sel_c = self.liste_circuits.curselection()
        if sel_c:
            self.choix["piste"] = self.circuits_affiches[sel_c[0]]["chemin"]
        self.choix["pilote"] = self.pilote_selectionne()[0]

    def changer_langue(self):
        code = self.var_langue.get()
        if code == L.actuelle():
            return
        if self.catalogue:
            self.memoriser_selection()
        self.enregistrer_preferences()          # le build part dans les préférences…
        L.choisir(code)
        self.prefs["fenetre"]["langue"] = code
        self.enregistrer_preferences()
        self.ecrire_langue_pour_le_mod()
        messages = self.liste_messages.get(0, "end")
        onglet = self.onglets.index("current")
        for enfant in self.winfo_children():
            enfant.destroy()
        self.title(f"{t('titre')}  —  v{VERSION}")
        self._construire()                     # …et revient dans la nouvelle langue
        for m in messages:
            self.liste_messages.insert("end", m)
        self.liste_messages.see("end")
        self.onglets.select(onglet)
        if self.etat_session:
            self.afficher_session(*self.etat_session)
        self.activer_boutons()
        self.var_etat.set("")
        self._date_temps = None                # l'onglet Mes temps se remplira tout seul
        if self.catalogue:
            self.charger_catalogue()

    # ═════════════════════════════════════════════════════════════════════
    #  ACTIONS
    # ═════════════════════════════════════════════════════════════════════
    def lancer(self):
        sel_c = self.liste_circuits.curselection()
        if not sel_c:
            self.var_etat.set(t("choisis_circuit"))
            return
        circuit = self.circuits_affiches[sel_c[0]]
        pilote, nom_pilote = self.pilote_selectionne()
        try:
            tours = max(1, min(20, int(self.var_tours.get())))
        except (tk.TclError, ValueError):
            tours = circuit.get("tours") or 3
        commande = {"type": self.var_type.get(), "piste": circuit["chemin"], "tours": tours, "pilote": pilote}
        build, _capacites = self.commande_build()
        commande.update(build)
        # Noms lisibles, recopiés tels quels par le mod dans le fichier des temps
        sel_pl = self.liste_planetes.curselection()
        _circuit, nom_vehicule = self.circuit_et_vehicule_choisis()
        commande.update({
            "nom_planete": self.liste_planetes.get(sel_pl[0]) if sel_pl else "",
            "nom_circuit": self.nom_circuit(circuit),
            "nom_vehicule": nom_vehicule,
            "nom_pilote": nom_pilote,
            "resume_build": self.resume_build(),
        })
        envoyer_commande(commande)
        sel_pl = self.liste_planetes.curselection()
        self.choix.update({"type": commande["type"], "piste": circuit["chemin"], "tours": str(tours),
                           "pilote": pilote, "planete": self.liste_planetes.get(sel_pl[0]) if sel_pl else ""})
        self.enregistrer_preferences()
        self.var_etat.set(t("commande_envoyee"))

    def demander_catalogue(self):
        envoyer_commande({"action": "catalogue"})
        self.var_etat.set(t("catalogue_demande"))
        self.after(1500, self.charger_catalogue)

    def rafraichir_etat(self):
        try:
            texte = FICHIER_ETAT.read_text(encoding="utf-8").strip()
            if texte:
                self.var_etat.set(t("jeu_prefixe") + texte)
        except OSError:
            pass
        # Nouveau temps enregistré par le mod ? On recharge l'onglet Mes temps.
        try:
            date = FICHIER_TEMPS_CSV.stat().st_mtime
        except OSError:
            date = None
        if date != self._date_temps:
            self._date_temps = date
            self.remplir_temps()
        self.after(DELAI_ETAT, self.rafraichir_etat)

    def enregistrer_preferences(self):
        if self.catalogue:
            build, capacites = self.commande_build()
            self.pref_build.update(build)
            self.pref_build["capacites"] = "|".join(capacites)   # garde la place de chaque emplacement
        self.choix["speciaux"] = str(self.var_speciaux.get())
        self.choix["au_premier_plan"] = str(self.var_dessus.get())
        with open(FICHIER_PREFERENCES, "w", encoding="utf-8") as f:
            self.prefs.write(f)

    def fermer(self):
        self.enregistrer_preferences()
        if S.session_en_cours(self.cfg):
            # On ferme quand même : la session sera terminée à la prochaine
            # ouverture (le pare-feu reste actif d'ici là, ce qui est sans danger).
            self.message(t("fenetre_fermee"))
        self.destroy()


def auto_test(fichier_resultat):
    """Contrôle de démarrage de la version .exe (lancé par outils/empaqueter.py) :
    ouvre la fenêtre CACHÉE, relève l'essentiel, écrit le résultat et se ferme."""
    try:
        f = Fenetre()
        f.withdraw()
        f.update()
        resultat = {"ok": True, "titre": f.title(), "langue": L.actuelle(), "dossier": str(DOSSIER_PROJET),
                    "exe": bool(getattr(sys, "frozen", False)), "jeu_trouve": S.jeu_trouve(f.cfg),
                    "versions_compatibles": len(S.versions_compatibles(f.cfg)),
                    "pare_feu_script": f.cfg.script_pare_feu.exists(),
                    "ue4ss": (f.cfg.installation / "ue4ss" / "UE4SS.dll").exists()}
        f.destroy()
    except Exception as e:   # le résultat doit être écrit quoi qu'il arrive
        resultat = {"ok": False, "erreur": repr(e)}
    Path(fichier_resultat).write_text(json.dumps(resultat, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--auto-test":
        auto_test(sys.argv[2])
    else:
        Fenetre().mainloop()
