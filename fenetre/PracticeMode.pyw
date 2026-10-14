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

Classement en ligne (v0.9.8, classement.py) : c'est la fenêtre, et jamais le
jeu, qui publie un temps quand on clique sur « Publier ce temps », sur un
serveur à part (Cloudflare), totalement séparé des classements officiels.

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

import classement as C   # classement en ligne : pseudo, envoi, lecture (fichier classement.py)
import langues as L   # textes en français / anglais (fichier langues.py)
import session as S   # le « launcher » : sauvegarde, UE4SS, pare-feu (fichier session.py)
import theme as T     # couleurs, polices et éléments dessinés de la fenêtre (fichier theme.py)
from langues import t

# ─────────────────────────────────────────────────────────────────────────
#  RÉGLAGES
# ─────────────────────────────────────────────────────────────────────────
VERSION = "2.0.1"   # même numéro que le mod (main.lua) ; vérifié par outils/empaqueter.py

DOSSIER_PROJET = S.dossier_application()   # dossier de PracticeMode.exe, ou du dépôt
DOSSIER_ECHANGE = DOSSIER_PROJET / "echange"
FICHIER_CATALOGUE = DOSSIER_ECHANGE / "catalogue.json"
FICHIER_COMMANDE = DOSSIER_ECHANGE / "commande.txt"
FICHIER_ETAT = DOSSIER_ECHANGE / "etat.txt"
FICHIER_LANGUE = DOSSIER_ECHANGE / "langue.txt"   # lu par le mod : langue de ses messages
FICHIER_PREFERENCES = (DOSSIER_PROJET if getattr(sys, "frozen", False)
                       else Path(__file__).resolve().parent) / "PracticeMode.ini"
FICHIER_TEMPS_CSV = DOSSIER_PROJET / "temps" / "temps.csv"   # écrit par le mod à chaque arrivée
FICHIER_STYLES = DOSSIER_ECHANGE / "styles.json"   # écrit par le mod : styles des pilotes (build, buffs)
FICHIER_DIFFICULTES = DOSSIER_ECHANGE / "difficultes.json"   # écrit par le mod : difficultés du mode histoire
FICHIER_PUBLIES = DOSSIER_PROJET / "temps" / "classement-publies.json"   # temps publiés en ligne (v0.9.8)
LIGNES_CLASSEMENT = 100   # temps lus pour un classement en ligne (les premiers, plus le sien)
# Classement en ligne visible ? Non dans la version publique 2.0.0 : son
# serveur n'est pas encore en ligne. L'onglet est construit mais pas affiché,
# le bouton « Publier ce temps » et la colonne « En ligne » sont cachés : la
# fenêtre ne peut alors rien envoyer ni lire sur Internet. True pour le rallumer.
CLASSEMENT_ACTIF = False
# Difficulté des IA (v0.9.7) : les 4 niveaux du mode histoire, du plus facile au plus dur
NIVEAUX_DIFFICULTE = ("cadet", "pilote", "as", "champion")
# Réglages du jeu que le mod change pour chaque niveau, et leur texte (« avance des IA +2 s »)
REGLAGES_IA = [("AiMaxTimeAheadModifier", "reg_avance_max"), ("AiMaxTimeAheadMultiplier", "reg_avance_max"),
               ("AiMinTimeAheadModifier", "reg_avance_min"),
               ("AiAggressionVPlayerChanceMultiplier", "reg_agressivite"),
               ("AiAggressionVPlayerCooldownMultiplier", "reg_delai"), ("AiAbilityChanceMultiplier", "reg_capacites")]
# Difficultés du jeu → niveau, quand difficultes.json n'en donne pas (mod
# v0.9.7 : Recrue et Antagoniste n'y étaient pas reconnues)
NIVEAU_PAR_NOM = (("easy", "cadet"), ("nightmare", "champion"), ("normal", "pilote"), ("hard", "as"))

# Style d'un pilote : lequel prendre selon le véhicule. Clés de styles.json :
# modes multijoueur du jeu (EMPGameMode : 2 tournoi solo, 3 tournoi de modules,
# 5 action instantanée, 6 action instantanée en module), puis le style de campagne.
# Le style « action instantanée » impose le build du pilote (ses vraies stats).
ORDRE_STYLES = {"avion": ("6", "3", "campagne"), "autre": ("5", "2", "campagne")}
NB_ADVERSAIRES_MAX = 11   # comme CONFIG.AdversairesMax dans le mod

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
    return "".join(morceau for morceau, _ in segments_texte(texte, perc, ints))


def noms_des_mots_cles(textes):
    """Le jeu associe une icône à un mot : <widget id="Ramjet"/><H1>statoréacteur</>.
    On en déduit le nom français de chaque mot-clé (le plus fréquent)."""
    votes = {}
    for txt in textes:   # (pas « t » : c'est la fonction de traduction)
        for cle, mot in re.findall(r'<widget id="(\w+)"/>\s*<H1>([^<]+)</>', txt or ""):
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


def fichier_traduction(code):
    """echange/catalogue-<langue>.json : les noms du jeu dans une autre langue
    que la sienne, écrits par le mod (il passe le jeu dans cette langue le
    temps de les lire, au menu principal)."""
    return DOSSIER_ECHANGE / f"catalogue-{code}.json"


def lire_traduction(code):
    try:
        with open(fichier_traduction(code), encoding="utf-8") as f:
            traduction = json.load(f)
        return traduction if traduction.get("langue") == code else None
    except (OSError, ValueError):
        return None


def appliquer_traduction(donnees, traduction):
    """Remplace, objet par objet (repéré par son chemin), les noms et
    descriptions du catalogue par ceux de la traduction, s'il y en a une pour
    la langue de la fenêtre et que le jeu est dans une autre langue.
    Ex. : « Champs de guerre » → « Battlefield »."""
    if not traduction:
        return donnees
    objets = traduction.get("objets") or {}
    for section in donnees.values():
        if isinstance(section, list):
            for element in section:
                if isinstance(element, dict) and element.get("chemin") in objets:
                    for cle, valeur in objets[element["chemin"]].items():
                        if valeur:
                            element[cle] = valeur
    ui = donnees.setdefault("interface", {})
    for cle, valeur in (traduction.get("interface") or {}).items():
        if isinstance(valeur, dict):
            ui[cle] = {**(ui.get(cle) or {}), **{k: v for k, v in valeur.items() if v}}
        elif valeur:
            ui[cle] = valeur
    return donnees


def texte_reglages(reglages):
    """{"AiMaxTimeAheadModifier": 2.0, …} → « avance des IA +2 s, agressivité ×1.5, … »"""
    def valeur(champ):
        v = reglages.get(champ)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return f"×{v:g}" if champ.endswith("Multiplier") else f"{v:+g} s"
        return None
    # Même écart pour l'avance max. et min. (sans multiplicateur) : une seule mention
    fusion = (valeur("AiMaxTimeAheadModifier") is not None
              and valeur("AiMaxTimeAheadModifier") == valeur("AiMinTimeAheadModifier")
              and valeur("AiMaxTimeAheadMultiplier") is None)
    morceaux = []
    for champ, cle in REGLAGES_IA:
        v = valeur(champ)
        if v is None or (fusion and champ == "AiMinTimeAheadModifier"):
            continue
        morceaux.append(t("reg_avance" if fusion and champ == "AiMaxTimeAheadModifier" else cle, v=v))
    return ", ".join(morceaux) or t("reg_aucun")


def niveau_difficulte(d):
    """Niveau (cadet, pilote, as, champion) d'une difficulté de difficultes.json."""
    if d.get("niveau") in NIVEAUX_DIFFICULTE:
        return d["niveau"]
    nom = (d.get("nom") or "").lower()
    return next((niveau for mot, niveau in NIVEAU_PAR_NOM if mot in nom), None)


def cle_circuit(nom):
    """« Lantaana — … [TRAK_DAL_P2P] » → « TRAK_DAL_P2P » : le nom interne,
    le même quelle que soit la langue (pour regrouper les records)."""
    m = re.search(r"\[([^\]]+)\]\s*$", nom or "")
    return m.group(1) if m else (nom or "")


def detail_build(texte):
    """Colonne « Détail du build » de temps.csv (v0.9.6) → dictionnaire.
    « niveaux=0,3,…;capacites=<chemin>|<chemin>;adversaires=5;position=2 »"""
    res = {}
    for morceau in (texte or "").split(";"):
        cle, egal, valeur = morceau.partition("=")
        if egal and cle.strip():
            res[cle.strip()] = valeur.strip()
    return res


class Catalogue:
    """Le contenu de catalogue.json, rangé pour l'interface."""

    def __init__(self, donnees, traduction=None, toutes_traductions=(), styles=None, difficultes=None):
        # Nom de chaque véhicule dans toutes les langues → sa clé (motojet…),
        # pour reconnaître un même véhicule dans temps.csv quelle que soit la
        # langue dans laquelle le temps a été noté
        self.cle_par_nom_vehicule = {}
        for v in donnees.get("vehicules", []):
            if v["nom"] in TYPES:
                noms = [v.get("affiche"), TYPES[v["nom"]][0]]
                noms += [((tr.get("objets") or {}).get(v.get("chemin")) or {}).get("affiche")
                         for tr in toutes_traductions if tr]
                for nom in noms:
                    if nom:
                        self.cle_par_nom_vehicule[nom] = TYPES[v["nom"]][0]
        # Même chose pour les pilotes (nom affiché → nom interne DA_…), pour
        # publier un temps au classement en ligne quelle que soit la langue
        self.pilote_par_nom = {}
        for p in donnees.get("pilotes", []):
            noms = [p.get("affiche")] + [((tr.get("objets") or {}).get(p.get("chemin")) or {}).get("affiche")
                                         for tr in toutes_traductions if tr]
            for nom in noms:
                if nom:
                    self.pilote_par_nom.setdefault(nom, p["nom"])
        donnees = appliquer_traduction(donnees, traduction)

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
            self.pilote_par_nom[p["texte"]] = p["nom"]   # (nom exact, variante comprise)
        self.pilotes.sort(key=lambda p: p["texte"].lower())
        self.texte_pilote = {p["nom"]: p["texte"] for p in self.pilotes}   # nom interne → nom affiché

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

        # Styles des pilotes (styles.json, v0.9.6) : build et buffs (traits) de
        # chaque pilote. Absent tant que le mod ne l'a pas écrit (au menu principal).
        styles = appliquer_traduction(styles, traduction) if styles else {}
        self.styles_lus = bool(styles)
        self.style_par_chemin = {s["chemin"]: s for s in styles.get("styles", [])}
        self.trait_par_chemin = {tr["chemin"]: tr for tr in styles.get("traits", [])}
        self.styles_par_pilote = {p["chemin"]: p.get("styles") or {} for p in styles.get("pilotes", [])}
        for s in self.style_par_chemin.values():
            s["texte"] = s.get("affiche") or s.get("nom", "")
        for tr in self.trait_par_chemin.values():
            tr["texte"] = tr.get("affiche") or tr.get("nom", "")

        # Difficultés du mode histoire (difficultes.json, v0.9.7) : noms et
        # descriptions du jeu, et ce que le mod change pour chaque niveau
        difficultes = appliquer_traduction(difficultes, traduction) if difficultes else {}
        self.difficultes = {niveau_difficulte(d): d for d in difficultes.get("difficultes", [])
                            if niveau_difficulte(d)}
        self.reglages_difficulte = difficultes.get("reglages_mod") or {}

    # ── styles des pilotes ────────────────────────────────────────────────
    def style_pour(self, pilote, cle_vehicule):
        """Le style d'un pilote pour ce véhicule (dictionnaire), ou None.
        Podracer : styles « module » d'abord ; autres véhicules : « action
        instantanée » d'abord (celui qui a le build du pilote), puis campagne."""
        styles = self.styles_par_pilote.get(pilote) or {}
        if cle_vehicule == "avion":
            # Module (v2.0.0) : les styles « action instantanée » des pilotes de
            # pod n'ont ni capacité ni statoréacteur ; celui du tournoi de
            # modules en a parfois un vrai (Sebulba : le lance-flammes). On le
            # prend en premier quand il a une capacité.
            s = self.style_par_chemin.get(styles.get("3"))
            if s and s.get("capacites"):
                return s
        for mode in ORDRE_STYLES["avion" if cle_vehicule == "avion" else "autre"]:
            s = self.style_par_chemin.get(styles.get(mode))
            if s and (s.get("build") or s.get("traits") or s.get("capacites")):
                return s
        return None

    def nom_trait(self, chemin):
        tr = self.trait_par_chemin.get(chemin)
        return tr["texte"] if tr else nom_court(chemin.rsplit(".", 1)[-1])

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

    def nom_vehicule(self, cle):
        """Clé motojet / voiture… → nom affiché par le jeu."""
        for c, affiche, _tag, _num in self.vehicules:
            if c == cle:
                return affiche
        return cle

    def circuit_par_nom(self, nom):
        """Circuit (dictionnaire) d'après son nom d'objet (TRAK_…), ou None."""
        for c in self.circuits:
            if c["nom"] == nom:
                return c
        return None

    def circuit_interne(self, cle):
        """Circuit noté dans temps.csv (« … [nom interne] ») → nom d'objet TRAK_…
        (le même pour tout le monde, et qui ne contient que A-Z, 0-9 et _)."""
        for c in self.circuits:
            if cle in (c.get("interne"), c["nom"]):
                return c["nom"]
        return ""


def lire_json(fichier):
    try:
        with open(fichier, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def lire_catalogue():
    """Renvoie un Catalogue, ou None si le fichier n'existe pas encore."""
    donnees = lire_json(FICHIER_CATALOGUE)
    if donnees is None:
        return None
    return Catalogue(donnees, lire_traduction(L.actuelle()), [lire_traduction(code) for code in L.LANGUES],
                     lire_json(FICHIER_STYLES), lire_json(FICHIER_DIFFICULTES))


def envoyer_commande(lignes):
    """Écrit commande.txt d'un seul coup (fichier temporaire puis renommage),
    pour que le mod ne lise jamais une commande à moitié écrite."""
    DOSSIER_ECHANGE.mkdir(parents=True, exist_ok=True)
    tmp = FICHIER_COMMANDE.with_suffix(".tmp")
    tmp.write_text("\n".join(f"{k}={v}" for k, v in lignes.items()) + "\n", encoding="utf-8")
    os.replace(tmp, FICHIER_COMMANDE)


def lire_publies():
    """Temps déjà publiés au classement en ligne (v0.9.8) : course → place obtenue."""
    donnees = lire_json(FICHIER_PUBLIES)
    return donnees if isinstance(donnees, dict) else {}


def ecrire_publies(publies):
    try:
        FICHIER_PUBLIES.parent.mkdir(parents=True, exist_ok=True)
        tmp = FICHIER_PUBLIES.with_suffix(".tmp")
        tmp.write_text(json.dumps(publies, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, FICHIER_PUBLIES)
    except OSError:
        pass


# ─────────────────────────────────────────────────────────────────────────
#  INTERFACE
# ─────────────────────────────────────────────────────────────────────────
class Fenetre(tk.Tk):
    def __init__(self):
        super().__init__()
        self.prefs = configparser.ConfigParser(interpolation=None)
        self.prefs.read(FICHIER_PREFERENCES, encoding="utf-8")
        for section in ("choix", "build", "fenetre", "classement"):
            if section not in self.prefs:
                self.prefs[section] = {}
        self.choix = self.prefs["choix"]
        self.pref_build = self.prefs["build"]
        self.pref_classement = self.prefs["classement"]

        # Langue : celle choisie la dernière fois, sinon celle de Windows
        L.choisir(self.prefs["fenetre"].get("langue") or L.langue_par_defaut())
        self.var_langue = tk.StringVar(value=L.actuelle())
        self.ecrire_langue_pour_le_mod()
        self.title(f"{t('titre')}  —  v{VERSION}")
        self.polices = T.appliquer(self)   # thème sombre, néon (avant de construire quoi que ce soit)
        T.icone(self)
        self.geometry(T.taille_initiale(self, 1400, 940))
        self.minsize(1100, 650)
        self.catalogue = None

        # Variables de l'onglet Course
        self.var_type = tk.StringVar(value=self.choix.get("type", "motojet"))
        self.var_tours = tk.IntVar(value=int(self.choix.get("tours", "3")))
        adversaires = self.choix.get("adversaires", "0")
        self.var_adversaires = tk.IntVar(value=int(adversaires) if adversaires.isdigit() else 0)
        # Difficulté des IA (v0.9.7) : niveau choisi (« » = celle du jeu, sans changement)
        difficulte = self.choix.get("difficulte", "")
        self.difficulte = difficulte if difficulte in NIVEAUX_DIFFICULTE else ""
        self.var_difficulte = tk.StringVar(value="")
        self.var_difficulte_texte = tk.StringVar(value="")
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
        # Style du pilote (v0.9.6) : chargé à la sélection d'un pilote ; ses
        # traits (buffs) cochés sont envoyés au jeu avec la course.
        self.var_build_pilote = tk.BooleanVar(value=self.pref_build.getboolean("build_pilote", True))
        self.style_choisi = self.pref_build.get("style", "") or ""
        self.traits_choisis = [x for x in (self.pref_build.get("traits", "") or "").split("|") if x]
        self.lignes_temps = {}   # ligne du tableau Mes temps → ligne de temps.csv

        # Classement en ligne (v0.9.8) : pseudo « arcade », adresse du serveur,
        # catégorie affichée. Rien n'est envoyé ni lu sans un clic de l'utilisateur.
        self.var_pseudo = tk.StringVar(value=C.nettoyer_saisie(self.pref_classement.get("pseudo", "")))
        self.var_pseudo.trace_add("write", lambda *a: self.pseudo_tape())
        self.var_adresse = tk.StringVar(value=self.pref_classement.get("adresse", "") or C.URL_PAR_DEFAUT)
        categorie = self.pref_classement.get("categorie", "")
        self.var_categorie = tk.StringVar(value=categorie if categorie in C.CATEGORIES else C.CATEGORIES[0])
        self.var_classement_titre = tk.StringVar(value="")
        self.var_classement_etat = tk.StringVar(value="")
        self.publies = lire_publies()          # temps déjà publiés (pour la colonne « En ligne »)
        self.file_reseau = queue.Queue()       # résultats des appels au serveur (tâches de fond)
        self.numero_demande = {"tableaux": 0, "classement": 0}   # (seule la dernière réponse compte)
        self.publication_en_cours = False
        self.tableau_affiche = None            # classement affiché : circuit, vehicule, tours, categorie
        self.cache_tableaux = None             # (catégorie, liste) : dernière liste des classements lue
        self.cache_classement = None           # (tableau, réponse) : dernier classement lu
        self.entrees_classement = {}           # ligne du tableau → temps lu au classement
        self.classement_ouvert = False         # onglet déjà ouvert (premier chargement fait) ?

        # Session d'entraînement (launcher). Le dossier du jeu est trouvé tout
        # seul par Steam, sauf si l'utilisateur en a choisi un (préférences).
        dossier_jeu = self.prefs["fenetre"].get("dossier_jeu", "")
        self.cfg = S.Config(racine_jeu=dossier_jeu) if S.est_dossier_du_jeu(dossier_jeu or None) else S.Config()
        self.file_messages = queue.Queue()   # messages envoyés par les tâches de fond
        self.historique_messages = []        # (heure, message) : réaffichés après un changement de langue
        self.travail_en_cours = False        # une tâche de fond tourne-t-elle ?
        self.jeu_vu = False                  # le jeu a-t-il tourné pendant cette session ?
        self.absent_depuis = None            # depuis quand le jeu est-il fermé ?
        self.var_session = tk.StringVar(value="")
        self.etat_session = None             # (clé du texte, couleur) affichés dans le bandeau
        self.etat_boutons = None             # (session ouverte, jeu lancé) au dernier contrôle
        self.alerte_steam = False            # alerte « Steam en ligne pendant une session » déjà donnée ?
        self.fermeture_demandee = False      # fermer la fenêtre dès que la fin de session est faite

        self._construire()
        T.barre_titre_sombre(self)
        self.attributes("-topmost", self.var_dessus.get())
        self._date_traduction = self.date_traduction()   # (le catalogue chargé ici l'inclut déjà)
        self.charger_catalogue()
        self.after(DELAI_ETAT, self.rafraichir_etat)
        self.after(300, self.lire_messages)
        self.after(500, self.surveiller_session)
        self.after(100, self.lire_reseau)
        self.executer(self.verifier_pare_feu_au_demarrage)
        self.protocol("WM_DELETE_WINDOW", self.fermer)

    # ═════════════════════════════════════════════════════════════════════
    #  CONSTRUCTION
    # ═════════════════════════════════════════════════════════════════════
    def _construire(self):
        P = self.polices
        # ── Bandeau du haut : titre néon, véhicule et langue en boutons segmentés ──
        entete = T.Entete(self, P, "PRACTICE MODE", t("entete_sous_titre", version=VERSION))
        entete.pack(fill="x")
        ttk.Label(entete.droite, text=t("vehicule").rstrip(" :").upper(),
                  style="Entete.TLabel").pack(side="left", padx=(0, 8))
        self.cadre_types = ttk.Frame(entete.droite, style="Entete.TFrame")   # (rempli par charger_catalogue)
        self.cadre_types.pack(side="left")
        ttk.Label(entete.droite, text=t("langue").upper(), style="Entete.TLabel").pack(side="left", padx=(28, 8))
        for code in L.LANGUES:
            ttk.Radiobutton(entete.droite, text=L.NOMS[code], value=code, variable=self.var_langue, width=4,
                            style="Segment.Toolbutton", command=self.changer_langue).pack(side="left")

        # ── Session d'entraînement : voyant, état, boutons, messages ──
        bandeau = ttk.LabelFrame(self, text=t("bandeau_session").upper(), padding=(10, 4, 10, 8))
        bandeau.pack(fill="x", padx=12, pady=(10, 0))
        bandeau.columnconfigure(1, weight=1)
        self.voyant = T.Voyant(bandeau)
        self.voyant.grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.etiquette_session = tk.Label(bandeau, textvariable=self.var_session, font=P.etat, anchor="w",
                                          background=T.FOND)
        self.etiquette_session.grid(row=0, column=1, sticky="w")
        boutons = ttk.Frame(bandeau)
        boutons.grid(row=0, column=2, sticky="e")
        self.bouton_demarrer = ttk.Button(boutons, text=t("btn_demarrer"), command=self.demarrer)
        self.bouton_relancer = ttk.Button(boutons, text=t("btn_relancer"), command=self.relancer_jeu)
        self.bouton_terminer = ttk.Button(boutons, text=t("btn_terminer"),
                                          command=lambda: self.executer(self.sequence_fin))
        self.bouton_pare_feu = ttk.Button(boutons, text=t("btn_pare_feu"),
                                          command=lambda: self.executer(self.sequence_lever_pare_feu))
        for b in (self.bouton_demarrer, self.bouton_relancer, self.bouton_terminer, self.bouton_pare_feu):
            b.pack(side="left", padx=(8, 0))
        self.liste_messages = tk.Listbox(bandeau, height=2, font=P.mono_petit, activestyle="none")
        self.liste_messages.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        if self.etat_session:
            self.voyant.allumer(self.etat_session[1])

        # Le bas de la fenêtre est placé AVANT les onglets (en partant du bas) :
        # s'il manque de la hauteur, ce sont les onglets qui rétrécissent, et le
        # bouton « Lancer la course » reste toujours visible.
        ttk.Label(self, textvariable=self.var_etat, style="Statut.TLabel",
                  padding=(14, 5)).pack(side="bottom", fill="x")
        ttk.Label(self, text=t("aide"), style="Aide.TLabel", padding=(14, 2, 14, 6),
                  wraplength=1300).pack(side="bottom", fill="x")
        bas = ttk.Frame(self, padding=(12, 8, 12, 6))
        bas.pack(side="bottom", fill="x")
        ttk.Separator(self).pack(side="bottom", fill="x", padx=12)
        ttk.Label(bas, text=t("tours")).pack(side="left")
        ttk.Spinbox(bas, from_=1, to=20, width=4, textvariable=self.var_tours).pack(side="left", padx=(6, 18))
        ttk.Label(bas, text=t("adversaires")).pack(side="left")
        ttk.Spinbox(bas, from_=0, to=NB_ADVERSAIRES_MAX, width=4,
                    textvariable=self.var_adversaires).pack(side="left", padx=(6, 4))
        ttk.Label(bas, text=t("adversaires_aide"), style="Doux.TLabel").pack(side="left", padx=(0, 18))
        ttk.Checkbutton(bas, text=t("premier_plan"), variable=self.var_dessus,
                        command=lambda: self.attributes("-topmost", self.var_dessus.get())).pack(side="left")
        ttk.Button(bas, text=t("lancer"), style="Accent.TButton", command=self.lancer).pack(side="right")
        ttk.Button(bas, text=t("recharger_catalogue"), command=self.demander_catalogue).pack(side="right", padx=10)

        onglets = self.onglets = ttk.Notebook(self)
        onglets.pack(fill="both", expand=True, padx=12, pady=(8, 6))
        page_course = ttk.Frame(onglets, padding=10)
        page_build = ttk.Frame(onglets, padding=10)
        page_temps = ttk.Frame(onglets, padding=10)
        page_classement = self.page_classement = ttk.Frame(onglets, padding=10)
        onglets.add(page_course, text=t("onglet_course").strip().upper())
        onglets.add(page_build, text=t("onglet_build").strip().upper())
        onglets.add(page_temps, text=t("onglet_temps").strip().upper())
        if CLASSEMENT_ACTIF:
            onglets.add(page_classement, text=t("onglet_classement").strip().upper())
        self._construire_course(page_course)
        self._construire_build(page_build)
        self._construire_temps(page_temps)
        self._construire_classement(page_classement)
        onglets.bind("<<NotebookTabChanged>>", lambda e: self.onglet_change())

    def _liste(self, parent, ligne, colonne, largeur):
        cadre = ttk.Frame(parent)
        cadre.grid(row=ligne, column=colonne, sticky="nsew", padx=(0, 8))
        liste = tk.Listbox(cadre, width=largeur, exportselection=False, activestyle="none",
                           font=self.polices.texte)
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
            ttk.Label(page, text=titre.upper(), style="Titre.TLabel").grid(row=0, column=col, sticky="w",
                                                                           pady=(0, 6))
        # (au-dessus de la liste des circuits, qu'elle change)
        ttk.Checkbutton(page, text=t("speciaux"), variable=self.var_speciaux,
                        command=self.remplir_planetes).grid(row=0, column=1, sticky="e", padx=(0, 8), pady=(0, 6))
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
        self.arbre_pilotes.tag_configure("groupe", font=self.polices.hud_petit, foreground=T.AMBRE)
        self.arbre_pilotes.bind("<<TreeviewSelect>>", lambda e: self.pilote_choisi())

        self.liste_planetes.bind("<<ListboxSelect>>", lambda e: self.remplir_circuits())
        self.liste_circuits.bind("<<ListboxSelect>>", lambda e: self.circuit_choisi())
        self.liste_circuits.bind("<Double-Button-1>", lambda e: self.lancer())

        # Difficulté des IA (v0.9.7) : celle du mode histoire, pour les courses avec adversaires
        ligne = ttk.Frame(page)
        ligne.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Label(ligne, text=t("difficulte").rstrip(" :").upper(), style="Titre.TLabel").pack(side="left")
        self.combo_difficulte = ttk.Combobox(ligne, state="readonly", width=24, textvariable=self.var_difficulte)
        self.combo_difficulte.pack(side="left", padx=(6, 12))
        self.combo_difficulte.bind("<<ComboboxSelected>>", lambda e: self.difficulte_choisie())
        description = ttk.Label(ligne, textvariable=self.var_difficulte_texte, style="Doux.TLabel", wraplength=900,
                                justify="left")
        description.pack(side="left", fill="x", expand=True)
        # (le texte revient à la ligne selon la place vraiment disponible)
        description.bind("<Configure>", lambda e: e.widget.configure(wraplength=max(200, e.width - 4)))
        if not getattr(self, "_suivi_adversaires", False):   # (une seule fois : les onglets sont reconstruits)
            self._suivi_adversaires = True
            self.var_adversaires.trace_add("write", lambda *a: self.decrire_difficulte())
        self.remplir_difficultes()

    def _construire_build(self, page):
        """Onglet Build :
             [Stats] [Capacités + options] [Affixes par catégorie]
             [Description de l'élément survolé ] [Récapitulatif du build]"""
        page.columnconfigure(2, weight=1)
        page.rowconfigure(0, weight=1)

        # ── Colonne 1 : améliorations de stat, puis style du pilote ──
        gauche = ttk.Frame(page)
        gauche.grid(row=0, column=0, sticky="nsw", padx=(0, 8))
        stats = ttk.LabelFrame(gauche, text=t("stats_titre").upper(), padding=(10, 4))
        stats.pack(fill="x")
        # Nom de la stat à gauche, curseur à droite : une ligne par stat (prend
        # deux fois moins de hauteur que le nom au-dessus du curseur)
        self.etiquettes_stats = []
        for i in range(6):
            etiquette = ttk.Label(stats, text=t("stats_secours")[i], wraplength=140)
            etiquette.grid(row=i, column=0, sticky="w", padx=(0, 8), pady=2)
            self.etiquettes_stats.append(etiquette)
            ttk.Scale(stats, from_=0, to=NIVEAU_MAX, orient="horizontal", length=150, variable=self.var_niveaux[i],
                      command=lambda valeur, var=self.var_niveaux[i]: self.niveau_change(var, valeur)
                      ).grid(row=i, column=1, sticky="w")
            ttk.Label(stats, textvariable=self.var_niveaux[i], style="Valeur.TLabel", width=3,
                      anchor="e").grid(row=i, column=2, sticky="e", padx=(6, 0))

        # Style du pilote choisi : son nom, ses buffs (cochés = envoyés au jeu)
        cadre_style = ttk.LabelFrame(gauche, text=t("style_titre").upper(), padding=(10, 4))
        cadre_style.pack(fill="both", expand=True, pady=(10, 0))
        self.var_style_texte = tk.StringVar(value="")
        etiquette = ttk.Label(cadre_style, textvariable=self.var_style_texte, font=self.polices.gras,
                              foreground=T.AMBRE, wraplength=320)
        etiquette.pack(anchor="w")
        etiquette.bind("<Enter>", lambda e: self.decrire_style())
        self.cadre_traits = ttk.Frame(cadre_style)
        self.cadre_traits.pack(fill="x", pady=(2, 6))
        ttk.Checkbutton(cadre_style, text=t("style_auto"), variable=self.var_build_pilote).pack(anchor="w")
        ttk.Button(cadre_style, text=t("style_recharger"),
                   command=self.charger_build_pilote).pack(anchor="w", pady=(4, 0))

        # ── Colonne 2 : capacités et options ──
        milieu = ttk.Frame(page)
        milieu.grid(row=0, column=1, sticky="nsw", padx=(0, 8))
        caps = ttk.LabelFrame(milieu, text=t("capacites").upper(), padding=(10, 4))
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

        opts = ttk.LabelFrame(milieu, text=t("options").upper(), padding=(10, 4))
        opts.pack(fill="x", pady=(10, 0))
        for texte, var in ((t("opt_boost"), self.var_boost), (t("opt_ramjet"), self.var_ramjet),
                           (t("opt_pannes"), self.var_pannes), (t("opt_illimites"), self.var_illimites)):
            ttk.Checkbutton(opts, text=texte, variable=var, command=self.rafraichir_recap).pack(fill="x")

        # ── Colonne 3 : affixes par catégorie, avec cases à cocher ──
        aff = ttk.LabelFrame(page, text=t("affixes_titre").upper(), padding=(10, 4))
        aff.grid(row=0, column=2, sticky="nsew")
        aff.columnconfigure(0, weight=1)
        aff.rowconfigure(1, weight=1)
        haut = ttk.Frame(aff)
        haut.grid(row=0, column=0, sticky="ew")
        haut.columnconfigure(1, weight=1)
        ttk.Label(haut, text=t("rechercher")).grid(row=0, column=0, sticky="w")
        ttk.Entry(haut, textvariable=self.var_recherche).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        # (sur sa propre ligne : son texte est long)
        ttk.Checkbutton(haut, text=t("caches"), variable=self.var_caches,
                        command=self.remplir_affixes).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 4))

        cadre = ttk.Frame(aff)
        cadre.grid(row=1, column=0, sticky="nsew")
        self.arbre = ttk.Treeview(cadre, columns=("rarete",), show="tree headings", selectmode="none")
        self.arbre.heading("#0", text=t("col_affixe"))
        self.arbre.heading("rarete", text=t("col_rarete"))
        self.arbre.column("#0", width=270)
        self.arbre.column("rarete", width=95, anchor="center", stretch=False)
        defil = ttk.Scrollbar(cadre, orient="vertical", command=self.arbre.yview)
        self.arbre.configure(yscrollcommand=defil.set)
        self.arbre.pack(side="left", fill="both", expand=True)
        defil.pack(side="right", fill="y")
        self.arbre.tag_configure("choisi", background=T.NEON_SOMBRE, font=self.polices.gras)
        self.arbre.tag_configure("categorie", font=self.polices.hud_petit, foreground=T.AMBRE)
        for r, couleur in T.RARETES.items():
            self.arbre.tag_configure(f"r{r}", foreground=couleur)
        self.arbre.bind("<Button-1>", self.clic_affixe)
        self.arbre.bind("<Motion>", self.survol_affixe)

        bas = ttk.Frame(aff)
        bas.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        ttk.Label(bas, textvariable=self.var_nb_affixes, style="Titre.TLabel").pack(side="left")
        ttk.Button(bas, text=t("tout_decocher"), command=self.retirer_affixes).pack(side="right")
        # (ici et pas sous les options : la colonne du milieu n'a pas la place, il était coupé)
        ttk.Button(bas, text=t("build_zero"), command=self.build_a_zero).pack(side="right", padx=(0, 8))

        # ── Ligne du bas : description + récapitulatif ──
        bas_page = ttk.Frame(page)
        bas_page.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        bas_page.columnconfigure(0, weight=1)
        bas_page.columnconfigure(1, weight=1)
        desc = ttk.LabelFrame(bas_page, text=t("description_titre").upper(), padding=6)
        desc.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.texte_desc = tk.Text(desc, height=4, wrap="word", font=self.polices.texte)
        self.texte_desc.pack(fill="both", expand=True)
        self.texte_desc.tag_configure("titre", font=self.polices.titre_texte, foreground=T.TEXTE_TITRE)
        self.texte_desc.tag_configure("h1", font=self.polices.gras, foreground=T.NEON)
        self.texte_desc.tag_configure("defaut", foreground=T.ROUGE)
        self.texte_desc.configure(state="disabled")
        recap = ttk.LabelFrame(bas_page, text=t("recap_titre").upper(), padding=6)
        recap.grid(row=0, column=1, sticky="nsew")
        self.texte_recap = tk.Text(recap, height=5, wrap="word", font=self.polices.texte)
        self.texte_recap.pack(fill="both", expand=True)
        self.texte_recap.tag_configure("cle", font=self.polices.gras, foreground=T.NEON)
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
        ttk.Label(haut, text=t("legende_record"), style="Doux.TLabel").pack(side="right", padx=12)
        colonnes = ("date", "planete", "circuit", "tours", "vehicule", "pilote", "temps", "place", "meilleur", "detail",
                    "en_ligne")
        titres = t("colonnes_temps")
        largeurs = (135, 95, 300, 45, 95, 105, 105, 60, 90, 170, 75)
        cadre = ttk.Frame(page)
        cadre.grid(row=1, column=0, sticky="nsew")
        self.table_temps = ttk.Treeview(cadre, columns=colonnes, show="headings", selectmode="browse")
        for col, titre, larg in zip(colonnes, titres, largeurs):
            self.table_temps.heading(col, text=titre)
            self.table_temps.column(col, width=larg, anchor="w")
        defil = ttk.Scrollbar(cadre, orient="vertical", command=self.table_temps.yview)
        self.table_temps.configure(yscrollcommand=defil.set)
        self.table_temps.pack(side="left", fill="both", expand=True)
        defil.pack(side="right", fill="y")
        self.table_temps.tag_configure("record", background=T.RECORD_FOND, foreground=T.AMBRE,
                                       font=self.polices.gras)
        if not CLASSEMENT_ACTIF:
            self.table_temps.configure(displaycolumns=colonnes[:-1])   # (sans « En ligne »)
        self.table_temps.bind("<<TreeviewSelect>>", lambda e: self.afficher_detail_temps())
        self._date_temps = None

        # Build de la course sélectionnée (clic sur une ligne)
        detail = ttk.LabelFrame(page, text=t("detail_titre").upper(), padding=6)
        detail.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        detail.columnconfigure(0, weight=1)
        self.texte_detail = tk.Text(detail, height=8, wrap="word", font=self.polices.texte)
        self.texte_detail.grid(row=0, column=0, sticky="ew")
        self.texte_detail.tag_configure("cle", font=self.polices.gras, foreground=T.NEON)
        self.texte_detail.tag_configure("note", foreground=T.TEXTE_DOUX)
        self.texte_detail.tag_configure("en_ligne", font=self.polices.gras, foreground=T.AMBRE)
        boutons = ttk.Frame(detail)
        boutons.grid(row=0, column=1, sticky="ne", padx=(8, 0))
        self.bouton_reprendre = ttk.Button(boutons, text=t("detail_reprendre"), state="disabled",
                                           command=self.reprendre_build_temps)
        self.bouton_reprendre.pack(fill="x")
        # Classement en ligne (v0.9.8) : publié seulement sur ce clic
        self.bouton_publier = ttk.Button(boutons, text=t("cl_publier"), state="disabled", command=self.publier_temps)
        if CLASSEMENT_ACTIF:
            self.bouton_publier.pack(fill="x", pady=(8, 0))
        self.afficher_detail_temps()

    def remplir_temps(self):
        """Relit temps.csv (le plus récent en haut) et marque les records."""
        try:
            with open(FICHIER_TEMPS_CSV, encoding="utf-8", newline="") as f:
                # (restkey : la colonne « Détail du build » de la v0.9.6 n'a pas
                # d'en-tête dans un fichier commencé avec une version plus ancienne)
                lignes = list(csv.DictReader(f, delimiter=";", restkey="_suite"))
        except OSError:
            lignes = []
        for l in lignes:
            texte = l.get("Détail du build") or (l.get("_suite") or [""])[0]
            l["_detail"] = detail_build(texte)
        # Record = plus petit temps (en secondes) par circuit + véhicule + tours
        # + nombre d'adversaires, sans compter les courses où un save state a été
        # utilisé (F8). Circuit et véhicule sont reconnus par leur nom interne /
        # leur clé : un temps noté en français et un autre en anglais comptent ensemble.
        vehicule_de = self.catalogue.cle_vehicule if self.catalogue else (lambda nom: nom)

        def cle_ligne(l):
            return (cle_circuit(l.get("Circuit")), vehicule_de(l.get("Véhicule")), l.get("Nb tours"),
                    l["_detail"].get("adversaires", "0"), l["_detail"].get("difficulte", ""))

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
        selection = self.table_temps.selection()
        ancienne = self.lignes_temps.get(selection[0]) if selection else None
        self.table_temps.delete(*self.table_temps.get_children())
        self.lignes_temps = {}
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
            d = l["_detail"]
            adversaires = int(d.get("adversaires", "0") or 0) if d.get("adversaires", "0").isdigit() else 0
            place = f"{d['position']} / {adversaires + 1}" if adversaires and d.get("position") else ""
            # Colonne « En ligne » : place au moment de la publication, ou ✔ si un
            # meilleur temps du même pseudo est celui du classement
            publie = self.publies.get(C.cle_publication(l))
            en_ligne = ""
            if isinstance(publie, dict):
                en_ligne = f"#{publie.get('rang')} / {publie.get('total')}" if publie.get("record", True) else "✔"
            valeurs = (l.get("Date", ""), l.get("Planète", ""), l.get("Circuit", ""), l.get("Nb tours", ""),
                       l.get("Véhicule", ""), l.get("Pilote", ""), temps, place, l.get("Meilleur tour", ""),
                       l.get("Détail des tours", ""), en_ligne)
            iid = self.table_temps.insert("", "end", values=valeurs, tags=("record",) if est_record else ())
            self.lignes_temps[iid] = l
            if ancienne is not None and l.get("Date") == ancienne.get("Date") and l.get("Temps") == ancienne.get("Temps"):
                self.table_temps.selection_set(iid)
        self.afficher_detail_temps()

    # ── détail du build d'un temps ────────────────────────────────────────
    def ligne_temps_choisie(self):
        sel = self.table_temps.selection() if hasattr(self, "table_temps") else ()
        return self.lignes_temps.get(sel[0]) if sel else None

    def afficher_detail_temps(self):
        """Panneau sous le tableau : le build complet de la course sélectionnée,
        avec les noms du jeu dans la langue de la fenêtre."""
        if not hasattr(self, "texte_detail"):
            return
        zone = self.texte_detail
        zone.configure(state="normal")
        zone.delete("1.0", "end")
        l = self.ligne_temps_choisie()
        d = l["_detail"] if l else {}
        self.bouton_reprendre.configure(state="normal" if d.get("niveaux") and self.catalogue else "disabled")
        publiable = bool(d.get("niveaux")) and (l or {}).get("Save state") != "oui"
        self.bouton_publier.configure(state="normal" if publiable and not self.publication_en_cours else "disabled")
        if not l:
            zone.insert("end", t("detail_vide"), "note")
        elif not d.get("niveaux"):
            zone.insert("end", l.get("Build", "") + "\n")
            zone.insert("end", t("detail_ancien"), "note")
        else:
            self.ecrire_build(zone, d, self.catalogue.cle_vehicule(l.get("Véhicule", "")) if self.catalogue else "")
            publie = self.publies.get(C.cle_publication(l))
            if isinstance(publie, dict):
                self.a_la_ligne(zone)
                zone.insert("end", t("cl_detail_publie"), "en_ligne")
                if publie.get("record", True):
                    zone.insert("end", t("cl_detail_publie_texte", quand=publie.get("quand", ""),
                                         pseudo=publie.get("pseudo", ""), place=self.place(publie.get("rang")),
                                         total=publie.get("total", "?"),
                                         categorie=self.nom_categorie(publie.get("categorie", ""))))
                else:
                    zone.insert("end", t("cl_detail_publie_garde", quand=publie.get("quand", ""),
                                         pseudo=publie.get("pseudo", ""),
                                         categorie=self.nom_categorie(publie.get("categorie", ""))))
        zone.configure(state="disabled")

    def ecrire_build(self, zone, d, cle_veh):
        """Écrit le build d'une course dans une zone de texte, avec les noms du
        jeu dans la langue de la fenêtre. `d` : les clés de la colonne « Détail
        du build » de temps.csv (« niveaux », « capacites »…), en texte ;
        `cle_veh` : motojet / voiture… (le nom de la 6e stat en dépend)."""
        cat = self.catalogue
        numero = 2
        for nom_arch, (cle, _tag, num) in TYPES.items():
            if cle == cle_veh:
                numero = num
        niveaux = [n for n in d.get("niveaux", "").split(",") if n != ""]
        stats = []
        for i, n in enumerate(niveaux[:6]):
            nom = cat.nom_stat(i, numero).split("  (")[0] if cat else t("stats_secours")[i]
            stats.append(f"{nom} {n}")

        def nom_capacite(chemin):
            c = cat.capacite_par_chemin.get(chemin) if cat else None
            return c["texte"].split("   (")[0] if c else nom_court(chemin.rsplit(".", 1)[-1])

        def nom_affixe(chemin):
            a = cat.par_chemin.get(chemin) if cat else None
            return a["texte"] if a else chemin.rsplit(".", 1)[-1]

        caps = [nom_capacite(c) for c in d.get("capacites", "").split("|") if c]
        affixes = [nom_affixe(a) for a in d.get("affixes", "").split("|") if a]
        traits = [cat.nom_trait(x) if cat else x for x in d.get("traits", "").split("|") if x]
        options = [nom for nom, cle in (("Afterburner", "boost"), ("Ramjet", "ramjet"),
                                        (t("opt_pannes"), "pannes"), (t("detail_illimites"), "crashs_illimites"))
                   if d.get(cle) == "1"]
        adversaires = int(d["adversaires"]) if d.get("adversaires", "").isdigit() else 0
        if adversaires:
            course = t("detail_course_ia", n=adversaires)
            if d.get("difficulte"):
                course += t("detail_difficulte", d=self.nom_difficulte(d["difficulte"]))
            if d.get("position"):
                course += t("detail_place", p=d["position"], total=adversaires + 1)
        else:
            course = t("detail_seul")
        zone.insert("end", course + "\n", "cle")
        zone.insert("end", t("recap_stats"), "cle")
        zone.insert("end", " · ".join(stats) + "\n")
        zone.insert("end", t("recap_capacites"), "cle")
        zone.insert("end", (", ".join(caps) or t("aucune_sans")) + "\n")
        zone.insert("end", t("recap_crash"), "cle")
        zone.insert("end", (nom_capacite(d["crash"]) if d.get("crash") else t("aucune_sans")) + "\n")
        zone.insert("end", t("recap_affixes", n=len(affixes)), "cle")
        zone.insert("end", (", ".join(affixes) or t("aucun_sans")) + "\n")
        zone.insert("end", t("recap_options"), "cle")
        zone.insert("end", (", ".join(options) or t("aucune_sans")) + "\n")
        style = cat.style_par_chemin.get(d.get("style", "")) if cat else None
        if style or traits:
            zone.insert("end", t("detail_style"), "cle")
            zone.insert("end", ((style["texte"] + " — ") if style else "") + (", ".join(traits) or t("style_sans_buff")))

    def reprendre_build_temps(self):
        """Remet dans l'onglet Build le build de la course sélectionnée."""
        l = self.ligne_temps_choisie()
        if not l or not l["_detail"].get("niveaux") or not self.catalogue:
            return
        self.reprendre_build(l["_detail"], t("build_repris", date=l.get("Date", "")),
                             self.catalogue.cle_vehicule(l.get("Véhicule", "")), l.get("Véhicule", ""))

    def reprendre_build(self, d, etat, cle_course, nom_vehicule):
        """Remet un build dans l'onglet Build. `d` : clés de la colonne « Détail
        du build » (une course de Mes temps, ou un temps du classement en ligne) ;
        `etat` : message de la ligne d'état ; `cle_course` / `nom_vehicule` : le
        véhicule de la course (pour prévenir s'il n'est pas celui choisi)."""
        self.appliquer_build({
            "niveaux": [int(n) if n.isdigit() else 0 for n in d.get("niveaux", "").split(",")],
            "capacites": [c for c in d.get("capacites", "").split("|") if c],
            "crash": d.get("crash", ""),
            "affixes": [a for a in d.get("affixes", "").split("|") if a],
            "boost": d.get("boost") == "1", "ramjet": d.get("ramjet") == "1", "pannes": d.get("pannes") == "1",
        })
        if d.get("crashs_illimites") in ("0", "1"):
            self.var_illimites.set(d["crashs_illimites"] == "1")
        self.style_choisi = d.get("style", "")
        self.traits_choisis = [x for x in d.get("traits", "").split("|") if x]
        self.afficher_style()
        self.rafraichir_recap()
        # Le build dépend du véhicule (6e stat, capacités) : on prévient si la
        # course était sur un autre véhicule que celui choisi. On ne change pas
        # le véhicule nous-mêmes, sinon le build du pilote serait rechargé par-dessus.
        connues = {cle for cle, _a, _t, _n in self.catalogue.vehicules}
        if cle_course in connues and cle_course != self.var_type.get():
            etat += t("build_repris_vehicule", vehicule=nom_vehicule)
        self.var_etat.set(etat)
        self.onglets.select(1)

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
            ttk.Radiobutton(self.cadre_types, text=affiche.upper(), value=cle, variable=self.var_type,
                            style="Segment.Toolbutton", command=self.type_change).pack(side="left")
        self.remplir_pilotes()
        self.remplir_planetes()
        self.remplir_build()
        self.remplir_difficultes()
        self.afficher_tableaux()     # (noms des circuits du classement en ligne)
        self.afficher_classement()

    def type_change(self):
        self.remplir_planetes()
        self.renommer_stats()
        self.afficher_tableaux()   # (classements en ligne du véhicule choisi, déjà lus)
        # Le pilote n'a pas le même style en module et sur les autres véhicules
        pilote = self.pilote_selectionne()[0]
        if pilote and self.var_build_pilote.get() and self.catalogue and self.catalogue.styles_lus:
            style = self.catalogue.style_pour(pilote, self.var_type.get())
            if (style["chemin"] if style else "") != self.style_choisi:
                self.charger_build_pilote()
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
        change = sel[0] != self.pilote   # (la sélection remise par le programme ne compte pas)
        self.pilote = sel[0]
        if change and self.var_build_pilote.get():
            self.charger_build_pilote()

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

    # ── difficulté des IA (v0.9.7) ────────────────────────────────────────
    def nom_difficulte(self, niveau):
        """Nom du niveau dans la langue de la fenêtre : celui du jeu s'il est
        connu (difficultes.json, traduit), sinon Recrue / Pilote / As / Antagoniste
        (Cadet / Pilot / Ace / Champion en anglais)."""
        if niveau not in NIVEAUX_DIFFICULTE:
            return niveau
        d = self.catalogue.difficultes.get(niveau) if self.catalogue else None
        return (d or {}).get("affiche") or t("niv_" + niveau)

    def remplir_difficultes(self):
        if not hasattr(self, "combo_difficulte"):
            return
        noms = [t("difficulte_jeu")] + [self.nom_difficulte(n) for n in NIVEAUX_DIFFICULTE]
        self.combo_difficulte["values"] = noms
        self.var_difficulte.set(self.nom_difficulte(self.difficulte) if self.difficulte else noms[0])
        self.decrire_difficulte()

    def difficulte_choisie(self):
        i = self.combo_difficulte.current()
        self.difficulte = NIVEAUX_DIFFICULTE[i - 1] if i > 0 else ""
        self.decrire_difficulte()

    def nombre_adversaires(self):
        try:
            return max(0, min(NB_ADVERSAIRES_MAX, int(self.var_adversaires.get())))
        except (tk.TclError, ValueError):
            return 0

    def decrire_difficulte(self):
        """À côté du choix : la description du jeu et ce que le mod change."""
        if not self.difficulte:
            texte = t("difficulte_jeu_aide")
        else:
            morceaux = []
            d = self.catalogue.difficultes.get(self.difficulte) if self.catalogue else None
            if d and d.get("description"):
                morceaux.append(d["description"].strip())
            reglages = (self.catalogue.reglages_difficulte if self.catalogue else {}).get(self.difficulte)
            if reglages is not None:
                morceaux.append(t("difficulte_mod", reglages=texte_reglages(reglages)))
            texte = "  ".join(morceaux)
        if self.nombre_adversaires() == 0:
            texte = (texte + "  " if texte else "") + t("difficulte_seul")
        self.var_difficulte_texte.set(texte)

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
        self.afficher_style()

    def niveau_change(self, var, valeur):
        """Curseur d'une stat : niveaux entiers seulement, puis récapitulatif."""
        entier = int(round(float(valeur)))
        if var.get() != entier:
            var.set(entier)
        self.rafraichir_recap()

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
        zone.insert("end", (", ".join(options) or t("aucune_sans")) + "\n")
        zone.insert("end", t("recap_buffs"), "cle")
        zone.insert("end", ", ".join(cat.nom_trait(x) for x in self.traits_choisis) if cat and self.traits_choisis
                    else t("style_sans_buff"))
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
        if self.traits_choisis and cat:
            morceaux.append(t("resume_buffs") + ", ".join(cat.nom_trait(x) for x in self.traits_choisis))
        return " · ".join(morceaux).replace("|", "/")

    def retirer_affixes(self):
        self.affixes_choisis = []
        self.remplir_affixes()

    # ── style du pilote : build et buffs (v0.9.6) ─────────────────────────
    def appliquer_build(self, b):
        """Met un build dans l'onglet Build. `b` : niveaux (liste de 6),
        capacites (chemins), crash, affixes (chemins), boost, ramjet, pannes.
        Les clés absentes ne changent rien."""
        cat = self.catalogue
        texte_par_chemin = {v: k for k, v in self.chemin_par_texte.items()}
        if "niveaux" in b:
            for i, v in enumerate(self.var_niveaux):
                v.set(max(0, min(NIVEAU_MAX, b["niveaux"][i] if i < len(b["niveaux"]) else 0)))
        if "capacites" in b:
            caps = [c for c in b["capacites"] if c in texte_par_chemin][:NB_CAPACITES]
            for i, v in enumerate(self.var_capacites):
                v.set(texte_par_chemin[caps[i]] if i < len(caps) else aucune())
        if "crash" in b:
            self.var_crash.set(texte_par_chemin.get(b["crash"] or "", aucune()))
        if "affixes" in b:
            self.affixes_choisis = [a for a in b["affixes"] if cat and a in cat.par_chemin]
        for cle, var in (("boost", self.var_boost), ("ramjet", self.var_ramjet), ("pannes", self.var_pannes)):
            if cle in b and b[cle] is not None:
                var.set(bool(b[cle]))
        self.remplir_affixes()

    def charger_build_pilote(self):
        """Le build et les buffs du pilote choisi, pour le véhicule choisi :
        stats, capacités, crash, affixes et options de son build (s'il en a un),
        ses capacités de départ, et ses traits (buffs), tous cochés."""
        cat = self.catalogue
        if not cat:
            return
        pilote, nom_pilote = self.pilote_selectionne()
        if not pilote:
            self.style_choisi, self.traits_choisis = "", []
            self.afficher_style()
            self.rafraichir_recap()
            return
        if not cat.styles_lus:
            self.var_etat.set(t("style_attente"))
            return
        style = cat.style_pour(pilote, self.var_type.get())
        if not style:
            self.style_choisi, self.traits_choisis = "", []
            self.afficher_style()
            self.rafraichir_recap()
            self.var_etat.set(t("style_absent", pilote=nom_pilote))
            return
        # Module (v2.0.0) : les builds des styles de pods relevés dans le jeu
        # (VBD_MP_*) n'ont ni capacité ni statoréacteur, et des niveaux très bas
        # (vu le 12/10/2026 avec Sebulba) : le jeu donne ces éléments ailleurs.
        # Le build de la fenêtre est donc gardé ; seuls les buffs sont proposés.
        if not self.build_style_garde(style):
            b = style.get("build") or {}
            capacites = list(style.get("capacites") or [])
            capacites += [c for c in (b.get("capacites") or []) if c and c not in capacites]
            nouveau = {"capacites": capacites} if capacites else {}
            if b:
                niveaux = b.get("niveaux") or {}
                nouveau.update({
                    "niveaux": [int(niveaux.get(str(i), 0) or 0) for i in range(6)],
                    "crash": b.get("crash") or "",
                    "affixes": [a for a in (b.get("affixes") or []) if a],
                    "boost": b.get("boost") == 1 if b.get("boost") is not None else None,
                    "ramjet": b.get("ramjet"),
                    "pannes": b.get("pannes"),
                })
            self.appliquer_build(nouveau)
        self.style_choisi = style["chemin"]
        self.traits_choisis = list(style.get("traits") or [])
        self.afficher_style()
        self.rafraichir_recap()
        self.var_etat.set(t("buffs_pilote_charges" if self.build_style_garde(style) else "build_pilote_charge",
                            pilote=nom_pilote, style=style["texte"], n=len(self.traits_choisis)))

    def build_style_garde(self, style):
        """Vrai si le build de la fenêtre est gardé au chargement de ce style :
        module dont le style n'a pas de capacité (builds VBD_MP_* du jeu, sans
        capacité ni statoréacteur ; seuls ses buffs sont proposés)."""
        return self.var_type.get() == "avion" and not (style or {}).get("capacites")

    def afficher_style(self):
        """Nom du style choisi et ses buffs (une case par trait)."""
        if not hasattr(self, "cadre_traits"):
            return
        for enfant in self.cadre_traits.winfo_children():
            enfant.destroy()
        cat = self.catalogue
        style = cat.style_par_chemin.get(self.style_choisi) if cat else None
        if not self.style_choisi and not self.traits_choisis:
            self.var_style_texte.set(t("style_aucun"))
            return
        _chemin, nom_pilote = self.pilote_selectionne()
        nom_style = style["texte"] if style else nom_court(self.style_choisi.rsplit(".", 1)[-1])
        self.var_style_texte.set(t("style_nom", style=nom_style, pilote=nom_pilote))
        if style and self.build_style_garde(style):
            ttk.Label(self.cadre_traits, text=t("style_module_build_garde"), style="Doux.TLabel", wraplength=300,
                      justify="left").pack(anchor="w")
        elif style and not style.get("build"):
            # Le style a un build, mais le jeu ne l'avait pas en mémoire au menu
            # (le mod ne charge plus rien depuis le disque) : on le dit
            cle = "style_build_absent" if style.get("build_chemin") else "style_sans_build"
            ttk.Label(self.cadre_traits, text=t(cle), style="Doux.TLabel", wraplength=300,
                      justify="left").pack(anchor="w")
        traits = list(style.get("traits") or []) if style else []
        traits += [x for x in self.traits_choisis if x not in traits]
        if not traits:
            ttk.Label(self.cadre_traits, text=t("style_sans_buff"), style="Doux.TLabel").pack(anchor="w")
        for chemin in traits:
            var = tk.BooleanVar(value=chemin in self.traits_choisis)
            case = ttk.Checkbutton(self.cadre_traits, text=cat.nom_trait(chemin) if cat else chemin, variable=var,
                                   command=lambda c=chemin, v=var: self.cocher_trait(c, v.get()))
            case.var = var   # (garde la variable en vie)
            case.pack(fill="x", pady=1)
            case.bind("<Enter>", lambda e, c=chemin: self.decrire_trait(c))

    def cocher_trait(self, chemin, coche):
        if coche and chemin not in self.traits_choisis:
            self.traits_choisis.append(chemin)
        elif not coche and chemin in self.traits_choisis:
            self.traits_choisis.remove(chemin)
        self.decrire_trait(chemin)
        self.rafraichir_recap()

    def decrire_trait(self, chemin):
        tr = self.catalogue.trait_par_chemin.get(chemin) if self.catalogue else None
        if tr:
            self.ecrire_description(tr["texte"], [(tr.get("description", ""), tr.get("perc"), tr.get("int"), False)])

    def decrire_style(self):
        s = self.catalogue.style_par_chemin.get(self.style_choisi) if self.catalogue else None
        if s:
            self.ecrire_description(s["texte"], [(s.get("description", ""), {}, {}, False)])

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
            "style": self.style_choisi,
            "traits": "|".join(self.traits_choisis),
        }, capacites

    # ═════════════════════════════════════════════════════════════════════
    #  CLASSEMENT EN LIGNE (v0.9.8)
    #  Seule la fenêtre parle au serveur (classement.py), et seulement après
    #  un clic : « Publier ce temps », ouverture de l'onglet, « Actualiser »…
    #  Les appels tournent en tâche de fond ; leurs réponses reviennent ici
    #  par une file lue toutes les 0,1 s (Tk ne se manipule que d'ici).
    # ═════════════════════════════════════════════════════════════════════
    def _construire_classement(self, page):
        """Onglet Classement :
             [Pseudo] [aide]                              [Serveur : adresse] [Tester]
             [SOLO SANS BUILD|SOLO AVEC BUILD|IA SANS BUILD|IA AVEC BUILD]  [Circuit choisi] [Actualiser]
             [Classements de la catégorie] [Le classement choisi                ]
             [Temps sélectionné : son build                       ] [Reprendre ce build]
             état du classement"""
        P = self.polices
        page.columnconfigure(1, weight=1)
        page.rowconfigure(2, weight=1)

        haut = ttk.Frame(page)
        haut.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(haut, text=t("cl_pseudo").upper(), style="Titre.TLabel").pack(side="left")
        self.entree_pseudo = ttk.Entry(haut, textvariable=self.var_pseudo, width=14, font=P.valeur,
                                       style="Arcade.TEntry")
        self.entree_pseudo.pack(side="left", padx=(8, 10))
        ttk.Label(haut, text=t("cl_pseudo_aide"), style="Doux.TLabel").pack(side="left")
        ttk.Button(haut, text=t("cl_tester"), command=self.tester_serveur).pack(side="right")
        ttk.Entry(haut, textvariable=self.var_adresse, width=38).pack(side="right", padx=(6, 6))
        ttk.Label(haut, text=t("cl_serveur")).pack(side="right")

        ligne = ttk.Frame(page)
        ligne.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        for code in C.CATEGORIES:
            ttk.Radiobutton(ligne, text=self.nom_categorie(code).upper(), value=code, variable=self.var_categorie,
                            style="Segment.Toolbutton", command=self.categorie_changee).pack(side="left")
        ttk.Button(ligne, text=t("cl_actualiser"), command=self.actualiser_classement).pack(side="right")
        ttk.Button(ligne, text=t("cl_ce_circuit"),
                   command=self.classement_du_circuit_choisi).pack(side="right", padx=(0, 8))

        # Liste des classements à gauche, le classement choisi à droite ; la
        # séparation se déplace à la souris
        panneaux = ttk.Panedwindow(page, orient="horizontal")
        panneaux.grid(row=2, column=0, columnspan=2, sticky="nsew")

        # À gauche : les classements de la catégorie qui ont déjà des temps,
        # pour le véhicule choisi en haut de la fenêtre (comme l'onglet Course)
        gauche = ttk.LabelFrame(panneaux, text=t("cl_titre_tableaux").upper(), padding=6)
        panneaux.add(gauche, weight=2)
        gauche.rowconfigure(0, weight=1)
        gauche.columnconfigure(0, weight=1)
        titres = t("cl_colonnes_tableaux")
        colonnes = ("tours", "nb", "record")
        self.liste_tableaux = ttk.Treeview(gauche, columns=colonnes, show="tree headings", selectmode="browse",
                                           height=6)
        self.liste_tableaux.heading("#0", text=titres[0])
        self.liste_tableaux.column("#0", width=235, minwidth=140)
        for col, titre, largeur in zip(colonnes, titres[1:], (60, 62, 160)):
            self.liste_tableaux.heading(col, text=titre)
            self.liste_tableaux.column(col, width=largeur, minwidth=largeur, anchor="w", stretch=False)
        defil = ttk.Scrollbar(gauche, orient="vertical", command=self.liste_tableaux.yview)
        self.liste_tableaux.configure(yscrollcommand=defil.set)
        self.liste_tableaux.grid(row=0, column=0, sticky="nsew")
        defil.grid(row=0, column=1, sticky="ns")
        self.liste_tableaux.bind("<<TreeviewSelect>>", lambda e: self.tableau_choisi())

        # À droite : le classement choisi
        droite = ttk.LabelFrame(panneaux, text=t("cl_titre_classement").upper(), padding=6)
        panneaux.add(droite, weight=3)
        droite.rowconfigure(1, weight=1)
        droite.columnconfigure(0, weight=1)
        ttk.Label(droite, textvariable=self.var_classement_titre, style="Titre.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        colonnes = ("rang", "pseudo", "temps", "ecart", "meilleur", "pilote", "ia", "difficulte", "place", "date")
        self.table_classement = ttk.Treeview(droite, columns=colonnes, show="headings", selectmode="browse",
                                             height=6, displaycolumns=colonnes[:6] + ("date",))
        for col, titre, largeur in zip(colonnes, t("cl_colonnes"), (40, 108, 80, 62, 104, 120, 36, 86, 56, 90)):
            self.table_classement.heading(col, text=titre)
            self.table_classement.column(col, width=largeur, minwidth=min(largeur, 60),
                                         anchor="e" if col == "rang" else "w", stretch=col == "pilote")
        defil = ttk.Scrollbar(droite, orient="vertical", command=self.table_classement.yview)
        self.table_classement.configure(yscrollcommand=defil.set)
        self.table_classement.grid(row=1, column=0, sticky="nsew")
        defil.grid(row=1, column=1, sticky="ns")
        self.table_classement.tag_configure("or", foreground=T.AMBRE, font=P.gras)
        self.table_classement.tag_configure("moi", background=T.CHAMP_SURVOL, foreground=T.NEON, font=P.gras)
        self.table_classement.tag_configure("separation", foreground=T.TEXTE_DOUX)
        self.table_classement.bind("<<TreeviewSelect>>", lambda e: self.afficher_detail_classement())
        self.table_classement.bind("<Configure>", lambda e: self.ajuster_colonnes())

        # En bas : le build du temps sélectionné, à reprendre si l'on veut
        detail = ttk.LabelFrame(page, text=t("cl_detail_titre").upper(), padding=6)
        detail.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        detail.columnconfigure(0, weight=1)
        self.texte_detail_classement = tk.Text(detail, height=8, wrap="word", font=P.texte)
        self.texte_detail_classement.grid(row=0, column=0, sticky="ew")
        self.texte_detail_classement.tag_configure("cle", font=P.gras, foreground=T.NEON)
        self.texte_detail_classement.tag_configure("note", foreground=T.TEXTE_DOUX)
        self.bouton_reprendre_classement = ttk.Button(detail, text=t("detail_reprendre"), state="disabled",
                                                      command=self.reprendre_build_classement)
        self.bouton_reprendre_classement.grid(row=0, column=1, sticky="ne", padx=(8, 0))
        ttk.Label(page, textvariable=self.var_classement_etat, style="Doux.TLabel").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
        # (après un changement de langue : les dernières lectures, sans rien redemander)
        self.afficher_tableaux()
        self.afficher_classement()

    # ── noms affichés ─────────────────────────────────────────────────────
    def nom_categorie(self, code):
        return t("categories_classement").get(code, code)

    @staticmethod
    def place(rang):
        """1 → « 1er » ; 3 → « 3e » (en anglais : « #1 », « #3 »)."""
        if not isinstance(rang, int):
            return "?"
        return t("cl_place_1") if rang == 1 else t("cl_place_n", n=rang)

    def nom_circuit_en_ligne(self, nom):
        """TRAK_… → nom du circuit dans le jeu, avec ses caractéristiques."""
        c = self.catalogue.circuit_par_nom(nom) if self.catalogue else None
        return c["texte"].rsplit("  [", 1)[0] if c else nom

    def nom_vehicule_en_ligne(self, cle):
        return self.catalogue.nom_vehicule(cle) if self.catalogue else cle

    def nom_pilote_en_ligne(self, nom):
        """DA_Racer_Star → nom du pilote dans le jeu (sinon le nom interne raccourci)."""
        texte = self.catalogue.texte_pilote.get(nom) if self.catalogue and nom else None
        return texte or (nom or "").replace("DA_PlaneRacer_", "").replace("DA_Racer_", "")

    def titre_tableau(self, tableau):
        return t("cl_tableau", circuit=self.nom_circuit_en_ligne(tableau["circuit"]),
                 vehicule=self.nom_vehicule_en_ligne(tableau["vehicule"]), tours=tableau["tours"],
                 categorie=self.nom_categorie(tableau["categorie"]))

    @staticmethod
    def a_la_ligne(zone):
        """Passe à la ligne, sauf si le texte est vide ou se termine déjà par un retour."""
        if zone.get("1.0", "end-1c") and zone.get("end-2c", "end-1c") != "\n":
            zone.insert("end", "\n")

    # ── appels au serveur, en tâche de fond ───────────────────────────────
    def en_fond(self, travail, puis):
        """`travail()` tourne dans une tâche de fond (la fenêtre ne se fige
        jamais, même sans Internet), puis `puis(resultat, erreur)` ici."""
        def tache():
            try:
                resultat, erreur = travail(), None
            except C.ErreurClassement as e:
                resultat, erreur = None, e
            except Exception as e:   # filet de sécurité : la réponse revient toujours
                resultat, erreur = None, C.ErreurClassement("interne", repr(e))
            self.file_reseau.put((puis, resultat, erreur))
        threading.Thread(target=tache, daemon=True).start()

    def lire_reseau(self):
        try:
            while not self.file_reseau.empty():
                puis, resultat, erreur = self.file_reseau.get()
                try:
                    puis(resultat, erreur)
                except tk.TclError:   # (fenêtre reconstruite entre-temps : changement de langue)
                    pass
                except Exception as e:
                    self.var_etat.set(self.texte_erreur(C.ErreurClassement("interne", repr(e))))
        finally:
            self.after(100, self.lire_reseau)

    def texte_erreur(self, e):
        textes = t("err_classement")
        if e.code in textes:
            return "✖ " + textes[e.code].format(detail=e.detail)
        return "✖ " + t("err_classement_autre", code=e.code)

    # ── pseudo, jeton, adresse ────────────────────────────────────────────
    def pseudo_tape(self):
        """Pendant la frappe : majuscules sans accents, caractères permis, 12 au plus."""
        texte = self.var_pseudo.get()
        propre = C.nettoyer_saisie(texte)
        if propre != texte:
            self.var_pseudo.set(propre)

    def jeton(self):
        """Le jeton de cette fenêtre : tiré au hasard la première fois, puis
        gardé dans les préférences. Il réserve le pseudo à cette fenêtre."""
        jeton = self.pref_classement.get("jeton", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", jeton):
            jeton = C.nouveau_jeton()
            self.pref_classement["jeton"] = jeton
            self.enregistrer_preferences()
        return jeton

    def adresse(self):
        return self.var_adresse.get().strip()

    def tester_serveur(self):
        adresse = self.adresse()
        if not C.adresse_valable(adresse):
            self.var_classement_etat.set(self.texte_erreur(C.ErreurClassement("adresse")))
            return
        self.enregistrer_preferences()
        self.var_classement_etat.set(t("cl_chargement"))
        self.en_fond(lambda: C.verifier(adresse, VERSION), self.serveur_teste)

    def serveur_teste(self, _api, e):
        if e:
            self.var_classement_etat.set(self.texte_erreur(e))
            return
        self.var_classement_etat.set(t("cl_serveur_ok"))
        self.actualiser_classement(etat=False)

    # ── publier un temps (onglet Mes temps) ───────────────────────────────
    def publier_temps(self):
        l = self.ligne_temps_choisie()
        if not CLASSEMENT_ACTIF or not l or self.publication_en_cours:
            return
        pseudo = C.normaliser_pseudo(self.var_pseudo.get())
        if not C.pseudo_valide(pseudo):
            self.var_etat.set(t("cl_refus")["pseudo_invalide"])
            self.onglets.select(self.page_classement)
            self.entree_pseudo.focus_set()
            return
        if not C.adresse_valable(self.adresse()):
            self.var_etat.set(self.texte_erreur(C.ErreurClassement("adresse")))
            self.onglets.select(self.page_classement)
            return
        cat = self.catalogue
        if not cat:
            self.var_etat.set(t("cl_refus")["catalogue"])
            return
        envoi, raison = C.preparer_envoi(l, cat.circuit_interne(cle_circuit(l.get("Circuit"))),
                                         cat.cle_vehicule(l.get("Véhicule", "")),
                                         cat.pilote_par_nom.get(l.get("Pilote", ""), ""), pseudo, self.jeton(),
                                         VERSION)
        if raison:
            self.var_etat.set(t("cl_refus")[raison])
            return
        self.enregistrer_preferences()   # (pseudo et adresse gardés pour la prochaine fois)
        self.publication_en_cours = True
        self.afficher_detail_temps()      # (bouton grisé pendant l'envoi)
        self.var_etat.set(t("cl_publication"))
        adresse, cle = self.adresse(), C.cle_publication(l)
        self.en_fond(lambda: C.publier(adresse, envoi, VERSION), lambda r, e: self.temps_publie(cle, envoi, r, e))

    def temps_publie(self, cle, envoi, r, e):
        self.publication_en_cours = False
        if e:
            self.afficher_detail_temps()
            self.var_etat.set(self.texte_erreur(e))
            return
        record = r.get("record_ms") == envoi["temps_ms"]   # ce temps est-il celui du classement ?
        tableau = r.get("tableau") if isinstance(r.get("tableau"), dict) else {}
        if record:   # (un temps publié avant, du même pseudo, n'est plus celui du classement)
            for autre in self.publies.values():
                if isinstance(autre, dict) and autre.get("pseudo") == r.get("pseudo") and all(
                        autre.get(k) == tableau.get(k) for k in ("circuit", "vehicule", "tours", "categorie")):
                    autre["record"] = False
        self.publies[cle] = {"pseudo": r.get("pseudo"), "rang": r.get("rang"), "total": r.get("total"),
                             "record": record, "record_ms": r.get("record_ms"),
                             "quand": f"{datetime.now():%Y-%m-%d %H:%M}", **tableau}
        ecrire_publies(self.publies)
        message = t("cl_publie", place=self.place(r.get("rang")), total=r.get("total"),
                    categorie=self.nom_categorie(r.get("categorie", "")))
        if r.get("ameliore") and isinstance(r.get("ancien_ms"), int):
            message += t("cl_record_battu", ancien=C.ms_vers_texte(r["ancien_ms"]))
        elif not record and isinstance(r.get("record_ms"), int):
            message += t("cl_record_garde", record=C.ms_vers_texte(r["record_ms"]))
        self.remplir_temps()
        self.var_etat.set(message)
        # L'onglet Classement montrera ce classement-là (relu en tâche de fond)
        if all(k in tableau for k in ("circuit", "vehicule", "tours", "categorie")):
            self.var_categorie.set(tableau["categorie"])
            self.tableau_affiche = {k: tableau[k] for k in ("circuit", "vehicule", "tours", "categorie")}
            self.classement_ouvert = True
            self.actualiser_classement()

    # ── onglet Classement : lectures ──────────────────────────────────────
    def onglet_change(self):
        """Premier passage sur l'onglet Classement : on lit la liste des
        classements (pas avant : rien ne part sur Internet sans qu'on regarde)."""
        try:
            courant = self.onglets.select()
        except tk.TclError:
            return
        if not CLASSEMENT_ACTIF or courant != str(self.page_classement) or self.classement_ouvert:
            return
        if not C.adresse_valable(self.adresse()):   # (lu à la prochaine ouverture, une fois l'adresse mise)
            self.var_classement_etat.set(t("cl_pas_configure"))
            return
        self.classement_ouvert = True
        if self.tableau_affiche is None:
            self.classement_du_circuit_choisi(seul=True)
        self.actualiser_classement()

    def actualiser_classement(self, etat=True):
        self.classement_ouvert = True
        self.charger_tableaux(etat)
        if self.tableau_affiche:
            self.charger_classement()

    def categorie_changee(self):
        """Autre catégorie : sa liste de classements, et le même circuit dans celle-ci."""
        if self.tableau_affiche:
            self.tableau_affiche = {**self.tableau_affiche, "categorie": self.var_categorie.get()}
        self.afficher_tableaux()
        self.afficher_classement()
        self.actualiser_classement()

    def classement_du_circuit_choisi(self, seul=False):
        """Le classement du circuit, du véhicule et du nombre de tours choisis
        dans l'onglet Course (même s'il n'a encore aucun temps). `seul` : sans
        le lire (l'appelant s'en charge)."""
        sel = self.liste_circuits.curselection() if hasattr(self, "liste_circuits") else ()
        if not sel:
            if not seul:
                self.var_classement_etat.set(t("choisis_circuit"))
            return
        circuit = self.circuits_affiches[sel[0]]
        try:
            tours = max(1, min(20, int(self.var_tours.get())))
        except (tk.TclError, ValueError):
            tours = circuit.get("tours") or 3
        self.tableau_affiche = {"circuit": circuit["nom"], "vehicule": self.var_type.get(), "tours": tours,
                                "categorie": self.var_categorie.get()}
        self.afficher_classement()
        self.selectionner_tableau()
        if not seul:
            self.classement_ouvert = True
            self.charger_classement()

    def charger_tableaux(self, etat=True):
        adresse, categorie = self.adresse(), self.var_categorie.get()
        if not C.adresse_valable(adresse):
            self.var_classement_etat.set(t("cl_pas_configure"))
            return
        self.numero_demande["tableaux"] += 1
        numero = self.numero_demande["tableaux"]
        if etat:
            self.var_classement_etat.set(t("cl_chargement"))
        self.en_fond(lambda: C.lire_tableaux(adresse, categorie, version=VERSION),
                     lambda r, e: self.tableaux_lus(numero, categorie, r, e))

    def tableaux_lus(self, numero, categorie, tableaux, e):
        if numero != self.numero_demande["tableaux"]:
            return   # (une demande plus récente est partie entre-temps)
        if e:
            self.var_classement_etat.set(self.texte_erreur(e))
            return
        self.cache_tableaux = (categorie, tableaux, f"{datetime.now():%H:%M}")
        self.afficher_tableaux()

    def afficher_tableaux(self):
        """Liste des classements de la catégorie (dernière lecture), avec les noms du jeu."""
        if not hasattr(self, "liste_tableaux"):
            return
        arbre = self.liste_tableaux
        arbre.delete(*arbre.get_children())
        if not self.cache_tableaux or self.cache_tableaux[0] != self.var_categorie.get():
            return
        _categorie, tableaux, heure = self.cache_tableaux
        vehicule = self.var_type.get()
        lignes = []
        for tb in tableaux if isinstance(tableaux, list) else []:
            try:
                if tb["vehicule"] == vehicule:
                    iid = f"{tb['circuit']}|{tb['vehicule']}|{int(tb['tours'])}"
                    lignes.append((self.nom_circuit_en_ligne(tb["circuit"]).lower(), int(tb["tours"]), iid, tb))
            except (KeyError, TypeError, ValueError):
                continue
        for _nom, tours, iid, tb in sorted(lignes, key=lambda x: x[:2]):
            if arbre.exists(iid):
                continue
            record = f"{C.ms_vers_texte(tb.get('meilleur_ms'))}   {tb.get('meilleur_pseudo') or ''}"
            arbre.insert("", "end", iid=iid, text=self.nom_circuit_en_ligne(tb["circuit"]),
                         values=(tours, tb.get("nb", ""), record))
        self.selectionner_tableau()
        self.var_classement_etat.set(t("cl_tableaux_lus", n=len(lignes), heure=heure,
                                       vehicule=self.nom_vehicule_en_ligne(vehicule)))

    def selectionner_tableau(self):
        """Dans la liste, met en surbrillance le classement affiché à droite."""
        tb = self.tableau_affiche
        if not tb or not hasattr(self, "liste_tableaux"):
            return
        iid = f"{tb['circuit']}|{tb['vehicule']}|{tb['tours']}"
        if self.liste_tableaux.exists(iid):
            self.liste_tableaux.selection_set(iid)
            self.liste_tableaux.see(iid)
        else:
            self.liste_tableaux.selection_set(())

    def tableau_choisi(self):
        sel = self.liste_tableaux.selection()
        if not sel:
            return
        circuit, vehicule, tours = sel[0].split("|")
        tableau = {"circuit": circuit, "vehicule": vehicule, "tours": int(tours), "categorie": self.var_categorie.get()}
        if tableau != self.tableau_affiche:   # (pas une sélection remise par le programme)
            self.tableau_affiche = tableau
            self.afficher_classement()
            self.charger_classement()

    def charger_classement(self):
        tableau, adresse = self.tableau_affiche, self.adresse()
        if not tableau:
            return
        if not C.adresse_valable(adresse):
            self.var_classement_etat.set(t("cl_pas_configure"))
            return
        self.numero_demande["classement"] += 1
        numero = self.numero_demande["classement"]
        pseudo = C.normaliser_pseudo(self.var_pseudo.get())
        pseudo = pseudo if C.pseudo_valide(pseudo) else ""
        self.var_classement_titre.set(self.titre_tableau(tableau) + "  —  " + t("cl_chargement"))
        self.en_fond(lambda: C.lire_classement(adresse, tableau["circuit"], tableau["vehicule"], tableau["tours"],
                                               tableau["categorie"], pseudo, LIGNES_CLASSEMENT, VERSION),
                     lambda r, e: self.classement_lu(numero, tableau, r, e))

    def classement_lu(self, numero, tableau, r, e):
        if numero != self.numero_demande["classement"]:
            return
        if e:
            self.var_classement_titre.set(self.titre_tableau(tableau))
            self.var_classement_etat.set(self.texte_erreur(e))
            return
        self.cache_classement = (tableau, r)
        self.afficher_classement()

    def afficher_classement(self):
        """Le classement affiché (dernière lecture) : le 1er en ambre, son
        propre pseudo en surbrillance (ajouté à la fin s'il est plus loin)."""
        if not hasattr(self, "table_classement"):
            return
        table = self.table_classement
        table.delete(*table.get_children())
        self.entrees_classement = {}
        tableau = self.tableau_affiche
        if not self.cache_classement or self.cache_classement[0] != tableau:
            self.var_classement_titre.set(self.titre_tableau(tableau) if tableau else t("cl_aucun_tableau"))
            self.afficher_detail_classement()
            return
        r = self.cache_classement[1]
        # Colonnes des courses avec IA (nombre, difficulté, place) : seulement pour les classements IA
        table["displaycolumns"] = (("rang", "pseudo", "temps", "ecart", "meilleur", "pilote")
                                   + (("ia", "difficulte", "place") if tableau["categorie"].startswith("ia") else ())
                                   + ("date",))
        self.ajuster_colonnes()
        temps = [x for x in (r.get("temps") or []) if isinstance(x, dict)]
        titre = self.titre_tableau(tableau)
        self.var_classement_titre.set(titre + (t("cl_total", n=r.get("total", len(temps))) if temps
                                               else "  —  " + t("cl_vide")))
        moi = C.normaliser_pseudo(self.var_pseudo.get())
        premier = temps[0].get("temps_ms") if temps else None

        def inserer(x):
            ms = x.get("temps_ms")
            ecart = C.ecart_texte(ms - premier) if isinstance(ms, int) and isinstance(premier, int) else ""
            adversaires = x.get("adversaires") if isinstance(x.get("adversaires"), int) else 0
            place = f"{x['position']} / {adversaires + 1}" if x.get("position") and adversaires else ""
            date = str(x.get("date_course") or x.get("date_envoi") or "")[:10]   # (le jour suffit)
            valeurs = (x.get("rang", ""), x.get("pseudo", ""), C.ms_vers_texte(ms), ecart,
                       C.ms_vers_texte(x.get("meilleur_tour_ms")), self.nom_pilote_en_ligne(x.get("pilote")),
                       adversaires or "", self.nom_difficulte(x["difficulte"]) if x.get("difficulte") else "",
                       place, date)
            tags = (("or",) if x.get("rang") == 1 else ()) + (("moi",) if x.get("pseudo") == moi else ())
            self.entrees_classement[table.insert("", "end", values=valeurs, tags=tags)] = x

        for x in temps:
            inserer(x)
        lui = r.get("moi")
        if isinstance(lui, dict) and all(x.get("pseudo") != lui.get("pseudo") for x in temps):
            table.insert("", "end", values=("…",), tags=("separation",))
            inserer(lui)
        self.afficher_detail_classement()

    def ajuster_colonnes(self):
        """Colonne « Pilote » du classement : la place qui reste (les colonnes des
        courses avec IA apparaissent ou disparaissent selon la catégorie)."""
        table = self.table_classement
        largeur = table.winfo_width()
        visibles = table["displaycolumns"]
        if tuple(visibles) == ("#all",):
            visibles = table["columns"]
        if largeur > 1:
            autres = sum(table.column(c, "width") for c in visibles if c != "pilote")
            table.column("pilote", width=max(80, largeur - autres - 4))

    def afficher_detail_classement(self):
        """Sous le classement : le build du temps sélectionné (comme dans Mes temps)."""
        if not hasattr(self, "texte_detail_classement"):
            return
        zone = self.texte_detail_classement
        zone.configure(state="normal")
        zone.delete("1.0", "end")
        sel = self.table_classement.selection()
        x = self.entrees_classement.get(sel[0]) if sel else None
        d = C.detail_de_entree(x) if x else {}
        self.bouton_reprendre_classement.configure(
            state="normal" if d.get("niveaux") and self.catalogue else "disabled")
        if not x:
            zone.insert("end", t("cl_detail_vide"), "note")
        else:
            if d.get("niveaux"):
                self.ecrire_build(zone, d, self.cache_classement[0]["vehicule"])
            tours = [C.ms_vers_texte(v) for v in (x.get("tours_ms") or []) if isinstance(v, int)]
            if tours:
                self.a_la_ligne(zone)
                zone.insert("end", t("cl_detail_tours"), "cle")
                zone.insert("end", "  ·  ".join(tours))
            self.a_la_ligne(zone)
            zone.insert("end", t("cl_detail_infos", date=x.get("date_course") or str(x.get("date_envoi", ""))[:10],
                                 version=x.get("version") or "?"), "note")
        zone.configure(state="disabled")

    def reprendre_build_classement(self):
        """« Reprendre ce build » sous le classement : le build d'un autre pilote dans l'onglet Build."""
        sel = self.table_classement.selection()
        x = self.entrees_classement.get(sel[0]) if sel else None
        if not x or not self.catalogue or not self.cache_classement:
            return
        d = C.detail_de_entree(x)
        if d.get("niveaux"):
            cle = self.cache_classement[0]["vehicule"]
            self.reprendre_build(d, t("cl_build_repris", pseudo=x.get("pseudo", "")), cle,
                                 self.nom_vehicule_en_ligne(cle))

    # ═════════════════════════════════════════════════════════════════════
    #  SESSION D'ENTRAÎNEMENT (LAUNCHER)
    #  Les étapes longues (copies, attente du pare-feu) tournent en tâche de
    #  fond pour que la fenêtre ne se fige pas. Elles envoient leurs messages
    #  dans une file, que la fenêtre affiche toutes les 0,3 s.
    # ═════════════════════════════════════════════════════════════════════
    def message(self, texte):
        """Utilisable depuis une tâche de fond : met le message dans la file
        et le garde dans sessions/journal-fenetre.txt. `texte` est un texte
        ou, mieux, un message traduisible (L.m(...)) : il changera de langue
        avec la fenêtre."""
        heure = f"{datetime.now():%H:%M:%S}"
        ligne = f"{heure}  {texte}"
        self.file_messages.put((heure, texte))
        try:
            self.cfg.sessions.mkdir(parents=True, exist_ok=True)
            with open(self.cfg.sessions / "journal-fenetre.txt", "a", encoding="utf-8") as f:
                f.write(f"{datetime.now():%Y-%m-%d} {ligne}\n")
        except OSError:
            pass

    def lire_messages(self):
        while not self.file_messages.empty():
            heure, texte = self.file_messages.get()
            self.historique_messages.append((heure, texte))
            self.liste_messages.insert("end", f"{heure}  {texte}")
            self.liste_messages.see("end")
        self.after(300, self.lire_messages)

    def executer(self, travail):
        """Lance une tâche de fond, une seule à la fois."""
        if self.travail_en_cours:
            self.message(L.m("patiente"))
            return
        self.travail_en_cours = True

        def enveloppe():
            try:
                travail()
            except S.ErreurSession as e:
                texte = e.args[0] if e.args else ""
                self.message(texte.avec_prefixe("✖ ") if isinstance(texte, L.Message) else "✖ " + str(e))
            except Exception as e:   # filet de sécurité : jamais de fenêtre figée
                self.message(L.m("erreur_inattendue", e=repr(e)))
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
            self.message(L.m("dossier_jeu_ok", chemin=Path(dossier)))
        # 2. UE4SS a besoin de Visual C++ : s'il manque, on propose l'installateur du jeu
        manquant = S.visual_cpp_manquant()
        if manquant:
            installateur = S.installateur_visual_cpp(self.cfg)
            if not installateur:
                self.message(L.m("vcpp_absent", "✖ ", dll=", ".join(manquant)))
                return
            if messagebox.askyesno(t("vcpp_titre"), t("vcpp_question", dll=", ".join(manquant),
                                                     chemin=installateur)):
                os.startfile(installateur)   # l'installateur de Microsoft demande lui-même l'administrateur
                self.message(L.m("vcpp_lance"))
            return
        self.executer(self.sequence_debut)

    def sequence_debut(self):
        """▶ Démarrer : sauvegarde + UE4SS + pare-feu + lancement du jeu."""
        if S.pare_feu_windows_actif() is False:
            raise S.ErreurSession(t("pare_feu_desactive"))
        self.message(L.m("debut_sauvegarde"))
        S.debut(self.cfg, self.message)
        try:
            self.message(L.m("pare_feu_uac"))
            if not S.lancer_script_pare_feu(self.cfg, "Session"):
                self.message(L.m("pare_feu_refuse"))
                S.fin(self.cfg, self.message)
                return
            etat = S.attendre_etat_pare_feu(self.cfg, "actif", 120)
            if etat != "actif":
                self.message(L.m("pare_feu_echec", etat=etat or t("pas_de_reponse")))
                S.fin(self.cfg, self.message)
                S.liberer_pare_feu(self.cfg, self.message)
                return
        except Exception:
            # Quoi qu'il arrive, pas de jeu moddé sans pare-feu : on défait tout.
            self.message(L.m("pare_feu_probleme"))
            S.fin(self.cfg, self.message)
            raise
        self.message(L.m("pare_feu_actif"))
        self.jeu_vu, self.absent_depuis = False, None
        S.lancer_jeu(self.cfg)
        self.message(L.m("lancement_jeu"))

    def sequence_fin(self):
        """Fin : retrait d'UE4SS, sauvegarde remise, pare-feu levé."""
        self.message(L.m("fin_remise"))
        S.fin(self.cfg, self.message)
        S.liberer_pare_feu(self.cfg, self.message)
        self.jeu_vu, self.absent_depuis = False, None
        self.message(L.m("fin_ok"))

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
            self.message(L.m("dossier_non_inscriptible", "✖ ", chemin=DOSSIER_PROJET))
        if S.jeu_trouve(self.cfg):
            self.message(L.m("dossier_jeu_ok", chemin=self.cfg.racine_jeu))
        else:
            self.message(L.m("jeu_introuvable", "⚠ "))
        if S.session_en_cours(self.cfg) and not S.jeu_lance(self.cfg):
            self.message(L.m("session_oubliee"))
        elif not S.session_en_cours(self.cfg) and S.regles_pare_feu_presentes(self.cfg):
            self.message(L.m("blocage_oublie"))

    def surveiller_session(self):
        """Toutes les 2 s : état affiché, boutons, et fin automatique quand le jeu se ferme."""
        try:
            session = S.session_en_cours(self.cfg)
            lance = S.jeu_lance(self.cfg)
        except Exception:
            session, lance = None, False
        # Steam repassé EN LIGNE pendant une session moddée : on prévient (une
        # fois par passage en ligne). Le mod, lui, se bloque tout seul.
        steam_en_ligne = bool(session) and not S.steam_hors_ligne(self.cfg)
        if steam_en_ligne and not self.alerte_steam:
            self.message(L.m("steam_en_ligne_session", "⚠ "))
        self.alerte_steam = steam_en_ligne
        if session and lance:
            self.jeu_vu, self.absent_depuis = True, None
            self.afficher_session("session_en_cours", T.ROUGE)
        elif session:
            if self.jeu_vu and not self.travail_en_cours:
                # Le jeu vient de se fermer : on attend quelques secondes (il
                # peut encore écrire sa sauvegarde) puis on remet tout d'origine.
                if self.absent_depuis is None:
                    self.absent_depuis = time.time()
                    self.message(L.m("jeu_ferme"))
                elif time.time() - self.absent_depuis > 8:
                    self.jeu_vu = False
                    self.executer(self.sequence_fin)
            self.afficher_session("session_ouverte", T.ORANGE)
        elif lance:
            self.afficher_session("session_origine_lance", T.TEXTE_DOUX)
        else:
            self.afficher_session("session_vanilla", T.VERT)
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
        self.voyant.allumer(couleur)

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
        onglet = self.onglets.index("current")
        for enfant in self.winfo_children():
            enfant.destroy()
        self.title(f"{t('titre')}  —  v{VERSION}")
        self._construire()                     # …et revient dans la nouvelle langue
        for heure, texte in self.historique_messages:   # traduits de nouveau (L.Message)
            self.liste_messages.insert("end", f"{heure}  {texte}")
        self.liste_messages.see("end")
        self.onglets.select(onglet)
        if self.etat_session:
            self.afficher_session(*self.etat_session)
        self.activer_boutons()
        self.var_etat.set("")
        self._date_temps = None                # l'onglet Mes temps se remplira tout seul
        self._date_traduction = self.date_traduction()   # (le catalogue rechargé ci-dessous l'inclut déjà)
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
        try:
            adversaires = max(0, min(NB_ADVERSAIRES_MAX, int(self.var_adversaires.get())))
        except (tk.TclError, ValueError):
            adversaires = 0
        commande = {"type": self.var_type.get(), "piste": circuit["chemin"], "tours": tours, "pilote": pilote,
                    "adversaires": adversaires}
        if adversaires > 0 and self.difficulte:   # (la difficulté ne sert qu'avec des adversaires)
            commande.update({"difficulte": self.difficulte, "nom_difficulte": self.nom_difficulte(self.difficulte)})
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
        # Le mod vient d'écrire les noms du jeu dans la langue de la fenêtre ?
        # On recharge le catalogue (en gardant circuit, pilote et build choisis).
        date_trad = self.date_traduction()
        if date_trad != self._date_traduction:
            self._date_traduction = date_trad
            if self.catalogue and any(d is not None for d in date_trad):
                self.memoriser_selection()
                self.enregistrer_preferences()
                self.charger_catalogue()
        self.after(DELAI_ETAT, self.rafraichir_etat)

    @staticmethod
    def date_traduction():
        """Dates des fichiers que le mod écrit après le catalogue (noms dans la
        langue de la fenêtre, styles des pilotes) : s'ils changent, on recharge."""
        dates = []
        for fichier in (fichier_traduction(L.actuelle()), FICHIER_STYLES, FICHIER_DIFFICULTES):
            try:
                dates.append(fichier.stat().st_mtime)
            except OSError:
                dates.append(None)
        return tuple(dates)

    def enregistrer_preferences(self):
        if self.catalogue:
            build, capacites = self.commande_build()
            self.pref_build.update(build)
            self.pref_build["capacites"] = "|".join(capacites)   # garde la place de chaque emplacement
        self.choix["speciaux"] = str(self.var_speciaux.get())
        self.choix["au_premier_plan"] = str(self.var_dessus.get())
        try:
            self.choix["adversaires"] = str(max(0, min(NB_ADVERSAIRES_MAX, int(self.var_adversaires.get()))))
        except (tk.TclError, ValueError):
            pass
        self.pref_build["build_pilote"] = str(self.var_build_pilote.get())
        self.choix["difficulte"] = self.difficulte
        self.pref_classement["pseudo"] = self.var_pseudo.get()
        adresse = self.var_adresse.get().strip()   # (gardée seulement si on l'a changée)
        self.pref_classement["adresse"] = adresse if adresse != C.URL_PAR_DEFAUT else ""
        self.pref_classement["categorie"] = self.var_categorie.get()
        with open(FICHIER_PREFERENCES, "w", encoding="utf-8") as f:
            self.prefs.write(f)

    def relancer_jeu(self):
        """« Relancer le jeu » pendant une session : seulement avec Steam hors
        ligne et le blocage pare-feu toujours en place."""
        if not S.steam_hors_ligne(self.cfg):
            self.message(L.m("steam_en_ligne", "✖ "))
            return
        if S.etat_pare_feu(self.cfg) != "actif":
            self.message(L.m("relance_sans_pare_feu", "✖ "))
            return
        self.jeu_vu, self.absent_depuis = False, None
        S.lancer_jeu(self.cfg)

    def fermer(self):
        """Fermer la fenêtre pendant une session : sans elle, rien ne remet le
        jeu d'origine quand on le quitte (incident du 11/10/2026 : jeu moddé
        relancé plus tard, Steam en ligne). On demande donc ce qu'on fait."""
        self.enregistrer_preferences()
        if S.session_en_cours(self.cfg) and not self.fermeture_demandee:
            if S.jeu_lance(self.cfg):
                if not messagebox.askokcancel(t("fermer_titre"), t("fermer_jeu_lance")):
                    return
            else:
                choix = messagebox.askyesnocancel(t("fermer_titre"), t("fermer_terminer"))
                if choix is None:              # Annuler : on reste
                    return
                if choix:                      # Oui : remise d'origine, puis fermeture
                    self.fermeture_demandee = True
                    self.executer(self.sequence_fin)
                    self.after(500, self.fermer_apres_fin)
                    return
            # (le pare-feu reste actif d'ici la prochaine ouverture : sans danger)
            self.message(L.m("fenetre_fermee"))
        self.destroy()

    def fermer_apres_fin(self):
        """Ferme la fenêtre une fois la fin de session faite. Si elle a échoué,
        la fenêtre reste ouverte : l'erreur est dans la liste des messages."""
        if self.travail_en_cours:
            self.after(500, self.fermer_apres_fin)
        elif S.session_en_cours(self.cfg):
            self.fermeture_demandee = False
        else:
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
