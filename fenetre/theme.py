"""Thème de la fenêtre (v0.9.7) : « holotable » de pilote.

    fond spatial presque noir, lignes fines, néon cyan pour ce qui est
    actif ou choisi, ambre pour l'action principale (lancer la course),
    rouge / orange / vert pour l'état de la session.

Tout le style est ici. PracticeMode.pyw n'utilise que les couleurs, les
polices rendues par appliquer(), et les quelques éléments dessinés plus bas
(Entete, Voyant). Les widgets Tk « classiques » (Listbox, Text, Label)
reçoivent leurs couleurs par la base d'options de Tk (voir appliquer).
"""
import random
import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# ── Couleurs ──────────────────────────────────────────────────────────────
FOND = "#070b14"          # l'espace : fond de toute la fenêtre
FOND_ENTETE = "#04070e"   # bandeau du haut, encore plus sombre
CHAMP = "#0c1426"         # listes, tableaux, champs : des « écrans »
CHAMP_SURVOL = "#14223d"
BORD = "#1c2a45"          # lignes fines des cadres
BORD_FORT = "#2c4166"
TEXTE = "#d3e1f2"
TEXTE_DOUX = "#7b8faa"    # aides, notes
TEXTE_TITRE = "#eef8ff"
NEON = "#2fd8ff"          # cyan néon : ce qui est actif ou choisi
NEON_FONCE = "#1b8fb8"
NEON_SOMBRE = "#0d3350"   # fond d'une ligne choisie
AMBRE = "#ffb31f"         # action principale
AMBRE_CLAIR = "#ffc95a"
AMBRE_FONCE = "#d48f00"
SUR_AMBRE = "#140c00"     # texte sur l'ambre
ROUGE = "#ff4d6a"
ORANGE = "#ff9a3c"
VERT = "#36f0a0"
RECORD_FOND = "#2a2008"   # ligne d'un record (ambre sombre)
# Raretés des affixes, lisibles sur fond sombre (commun → légendaire, défectueux)
RARETES = {0: "#9aa8ba", 1: "#45e08f", 2: "#47b2ff", 3: "#c88bff", 4: "#ff5e7a", 5: "#ffab45"}


def melanger(couleur, fond, part):
    """Couleur à `part` (0 à 1) sur le fond : un néon « atténué », pour les halos."""
    a = [int(couleur[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(fond[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * part + y * (1 - part)):02x}" for x, y in zip(a, b))


# ── Polices : la première disponible ─────────────────────────────────────
# (Windows : Bahnschrift pour les titres, façon tableau de bord, Segoe UI pour
# le texte, Consolas pour les relevés ; ailleurs, des équivalents)
class Polices:
    def __init__(self, racine):
        dispo = set(tkfont.families(racine))

        def choisir(*familles):
            for f in familles:
                if f in dispo:
                    return f
            return familles[-1]   # (Tk prend alors sa police de secours)
        hud = choisir("Bahnschrift", "Segoe UI Semibold", "Segoe UI", "Inter", "DejaVu Sans")
        texte = choisir("Segoe UI", "Inter", "DejaVu Sans")
        mono = choisir("Cascadia Mono", "Consolas", "DejaVu Sans Mono")
        self.texte = (texte, 10)
        self.gras = (texte, 10, "bold")
        self.petit = (texte, 9)
        self.titre_texte = (texte, 11, "bold")
        self.hud = (hud, 10, "bold")
        self.hud_petit = (hud, 9, "bold")
        self.hud_gros = (hud, 12, "bold")
        self.etat = (hud, 13, "bold")
        self.logo = (hud, 22, "bold")
        self.sous_titre = (hud, 9)
        self.mono = (mono, 10)
        self.mono_petit = (mono, 9)
        self.valeur = (mono, 11, "bold")


def appliquer(racine):
    """Thème ttk « clam » recoloré, et couleurs par défaut des widgets Tk
    classiques. À appeler une fois, avant de construire la fenêtre."""
    p = Polices(racine)
    racine.configure(background=FOND)
    s = ttk.Style(racine)
    s.theme_use("clam")   # (le thème de Windows ignore les couleurs)
    s.configure(".", background=FOND, foreground=TEXTE, fieldbackground=CHAMP, bordercolor=BORD,
                lightcolor=FOND, darkcolor=FOND, troughcolor=CHAMP, selectbackground=NEON_SOMBRE,
                selectforeground=TEXTE_TITRE, insertcolor=NEON, focuscolor=NEON, arrowcolor=NEON,
                font=p.texte)
    s.map(".", foreground=[("disabled", TEXTE_DOUX)])

    # Textes
    s.configure("Doux.TLabel", foreground=TEXTE_DOUX)
    s.configure("Aide.TLabel", foreground=TEXTE_DOUX, font=p.petit)
    s.configure("Titre.TLabel", foreground=NEON, font=p.hud)
    s.configure("Section.TLabel", foreground=TEXTE_DOUX, font=p.hud_petit)
    s.configure("Valeur.TLabel", foreground=NEON, font=p.valeur)
    s.configure("Statut.TLabel", background=CHAMP, foreground=NEON, font=p.mono)
    s.configure("Entete.TFrame", background=FOND_ENTETE)
    s.configure("Entete.TLabel", background=FOND_ENTETE, foreground=TEXTE_DOUX, font=p.hud_petit)

    # Cadres : un titre néon et une ligne fine
    s.configure("TLabelframe", background=FOND, bordercolor=BORD, lightcolor=FOND, darkcolor=FOND,
                relief="solid", borderwidth=1)
    s.configure("TLabelframe.Label", background=FOND, foreground=NEON, font=p.hud_petit)
    s.configure("TSeparator", background=BORD)

    # Boutons : contour néon ; l'action principale en ambre
    s.configure("TButton", background=FOND, foreground=NEON, bordercolor=NEON_FONCE, lightcolor=FOND,
                darkcolor=FOND, focuscolor=FOND, padding=(10, 4), font=p.hud_petit, relief="solid",
                borderwidth=1)
    s.map("TButton",
          background=[("disabled", FOND), ("pressed", NEON_SOMBRE), ("active", CHAMP_SURVOL)],
          foreground=[("disabled", BORD_FORT), ("active", TEXTE_TITRE)],
          bordercolor=[("disabled", BORD), ("active", NEON)],
          lightcolor=[("pressed", NEON_SOMBRE), ("active", CHAMP_SURVOL)],
          darkcolor=[("pressed", NEON_SOMBRE), ("active", CHAMP_SURVOL)])
    s.configure("Accent.TButton", background=AMBRE, foreground=SUR_AMBRE, bordercolor=AMBRE, lightcolor=AMBRE,
                darkcolor=AMBRE, focuscolor=AMBRE, padding=(22, 8), font=p.hud_gros)
    s.map("Accent.TButton",
          background=[("disabled", BORD), ("pressed", AMBRE_FONCE), ("active", AMBRE_CLAIR)],
          foreground=[("disabled", TEXTE_DOUX)],
          bordercolor=[("pressed", AMBRE_FONCE), ("active", AMBRE_CLAIR)],
          lightcolor=[("pressed", AMBRE_FONCE), ("active", AMBRE_CLAIR)],
          darkcolor=[("pressed", AMBRE_FONCE), ("active", AMBRE_CLAIR)])

    # Choix en boutons segmentés (véhicule, langue) : le choix actif s'allume
    s.configure("Segment.Toolbutton", background=CHAMP, foreground=TEXTE_DOUX, bordercolor=BORD_FORT,
                lightcolor=CHAMP, darkcolor=CHAMP, padding=(14, 5), font=p.hud, anchor="center")
    s.map("Segment.Toolbutton",
          background=[("selected", NEON_SOMBRE), ("active", CHAMP_SURVOL)],
          foreground=[("selected", NEON), ("active", TEXTE_TITRE)],
          bordercolor=[("selected", NEON), ("active", NEON_FONCE)],
          lightcolor=[("selected", NEON_SOMBRE), ("active", CHAMP_SURVOL)],
          darkcolor=[("selected", NEON_SOMBRE), ("active", CHAMP_SURVOL)])

    # Cases à cocher et boutons radio
    for nom in ("TCheckbutton", "TRadiobutton"):
        s.configure(nom, background=FOND, foreground=TEXTE, indicatorbackground=CHAMP,
                    indicatorforeground=NEON, upperbordercolor=BORD_FORT, lowerbordercolor=BORD_FORT,
                    focuscolor=FOND, indicatormargin=(0, 0, 6, 0), padding=(0, 2))
        s.map(nom, background=[("active", FOND)], foreground=[("active", TEXTE_TITRE)],
              indicatorbackground=[("selected", NEON_SOMBRE), ("active", CHAMP_SURVOL)],
              upperbordercolor=[("selected", NEON), ("active", NEON_FONCE)],
              lowerbordercolor=[("selected", NEON), ("active", NEON_FONCE)])

    # Champs de saisie et listes déroulantes
    for nom in ("TEntry", "TCombobox", "TSpinbox"):
        s.configure(nom, fieldbackground=CHAMP, foreground=TEXTE, background=CHAMP, bordercolor=BORD_FORT,
                    lightcolor=CHAMP, darkcolor=CHAMP, arrowcolor=NEON, insertcolor=NEON, padding=(6, 3),
                    selectbackground=NEON_SOMBRE, selectforeground=TEXTE_TITRE, arrowsize=13)
        s.map(nom, fieldbackground=[("readonly", CHAMP), ("disabled", FOND)],
              background=[("active", CHAMP_SURVOL), ("pressed", NEON_SOMBRE)],
              bordercolor=[("focus", NEON), ("active", NEON_FONCE)],
              lightcolor=[("focus", CHAMP)], arrowcolor=[("disabled", BORD_FORT), ("active", TEXTE_TITRE)],
              foreground=[("readonly", TEXTE)], selectbackground=[("readonly", CHAMP)],
              selectforeground=[("readonly", NEON)])
    # Pseudo du classement en ligne : saisie « borne d'arcade », en ambre
    s.configure("Arcade.TEntry", foreground=AMBRE, insertcolor=AMBRE)
    # (la liste qui s'ouvre sous une Combobox est un widget Tk classique)
    racine.option_add("*TCombobox*Listbox.background", CHAMP)
    racine.option_add("*TCombobox*Listbox.foreground", TEXTE)
    racine.option_add("*TCombobox*Listbox.selectBackground", NEON_SOMBRE)
    racine.option_add("*TCombobox*Listbox.selectForeground", NEON)
    racine.option_add("*TCombobox*Listbox.font", p.texte)
    racine.option_add("*TCombobox*Listbox.borderWidth", 0)

    # Onglets
    s.configure("TNotebook", background=FOND, bordercolor=BORD, lightcolor=FOND, darkcolor=FOND,
                tabmargins=(0, 6, 0, 0))
    s.configure("TNotebook.Tab", background=FOND, foreground=TEXTE_DOUX, bordercolor=BORD, lightcolor=FOND,
                darkcolor=FOND, padding=(20, 7), font=p.hud)
    s.map("TNotebook.Tab",
          background=[("selected", CHAMP), ("active", CHAMP_SURVOL)],
          foreground=[("selected", NEON), ("active", TEXTE_TITRE)],
          bordercolor=[("selected", NEON_FONCE)],
          lightcolor=[("selected", NEON)])

    # Tableaux et arbres
    s.configure("Treeview", background=CHAMP, fieldbackground=CHAMP, foreground=TEXTE, bordercolor=BORD,
                lightcolor=CHAMP, darkcolor=CHAMP, rowheight=26, font=p.texte)
    s.map("Treeview", background=[("selected", NEON_SOMBRE)], foreground=[("selected", TEXTE_TITRE)])
    s.configure("Treeview.Heading", background=FOND, foreground=NEON, bordercolor=BORD, lightcolor=FOND,
                darkcolor=FOND, relief="flat", padding=(8, 5), font=p.hud_petit)
    s.map("Treeview.Heading", background=[("active", CHAMP_SURVOL)], foreground=[("active", TEXTE_TITRE)])

    # Séparation déplaçable entre deux panneaux (onglet Classement)
    s.configure("TPanedwindow", background=FOND)
    s.configure("Sash", sashthickness=10, gripcount=0, background=FOND, lightcolor=FOND, darkcolor=FOND,
                bordercolor=FOND)

    # Barres de défilement fines, curseurs
    for nom in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        s.configure(nom, background=BORD_FORT, troughcolor=CHAMP, bordercolor=CHAMP, lightcolor=BORD_FORT,
                    darkcolor=BORD_FORT, arrowcolor=NEON_FONCE, gripcount=0, arrowsize=12)
        s.map(nom, background=[("pressed", NEON), ("active", NEON_FONCE)],
              arrowcolor=[("active", NEON)], lightcolor=[("active", NEON_FONCE)], darkcolor=[("active", NEON_FONCE)])
    s.configure("Horizontal.TScale", background=NEON_FONCE, troughcolor=CHAMP, bordercolor=BORD_FORT,
                lightcolor=NEON_FONCE, darkcolor=NEON_FONCE, gripcount=0, sliderlength=16)
    s.map("Horizontal.TScale", background=[("pressed", NEON), ("active", NEON)],
          lightcolor=[("active", NEON)], darkcolor=[("active", NEON)])

    # Widgets Tk classiques : couleurs par défaut (base d'options de Tk)
    for nom, valeur in (("background", CHAMP), ("foreground", TEXTE), ("selectBackground", NEON_SOMBRE),
                        ("selectForeground", TEXTE_TITRE), ("highlightThickness", 1),
                        ("highlightBackground", BORD), ("highlightColor", NEON_FONCE), ("borderWidth", 0),
                        ("relief", "flat"), ("font", p.texte)):
        racine.option_add(f"*Listbox.{nom}", valeur)
    for nom, valeur in (("background", CHAMP), ("foreground", TEXTE), ("insertBackground", NEON),
                        ("selectBackground", NEON_SOMBRE), ("selectForeground", TEXTE_TITRE),
                        ("highlightThickness", 0), ("borderWidth", 0), ("relief", "flat"), ("padX", 8),
                        ("padY", 6), ("font", p.texte)):
        racine.option_add(f"*Text.{nom}", valeur)
    racine.option_add("*Label.background", FOND)
    racine.option_add("*Label.foreground", TEXTE)
    racine.option_add("*Canvas.background", FOND)
    racine.option_add("*Canvas.highlightThickness", 0)
    return p


def barre_titre_sombre(racine):
    """Windows 10/11 : barre de titre sombre et, sous Windows 11, sa couleur
    et un liseré néon autour de la fenêtre. Sans effet ailleurs."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        racine.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(racine.winfo_id())
        dwm = ctypes.windll.dwmapi

        def regler(attribut, valeur):
            v = ctypes.c_int(valeur)
            return dwm.DwmSetWindowAttribute(hwnd, attribut, ctypes.byref(v), ctypes.sizeof(v))

        def bgr(couleur):   # (Windows attend 0x00BBGGRR)
            return int(couleur[5:7] + couleur[3:5] + couleur[1:3], 16)
        if regler(20, 1) != 0:     # DWMWA_USE_IMMERSIVE_DARK_MODE
            regler(19, 1)          # (même réglage, ancien numéro : Windows 10 avant 20H1)
        regler(35, bgr(FOND_ENTETE))   # DWMWA_CAPTION_COLOR (Windows 11)
        regler(34, bgr(NEON_FONCE))    # DWMWA_BORDER_COLOR (Windows 11)
    except Exception:
        pass   # (purement décoratif)


def _rvb(couleur):
    return tuple(int(couleur[i:i + 2], 16) for i in (1, 3, 5))


def _pixel_icone(u, v):
    """Couleur (r, v, b) ou None (transparent) d'un point de l'icône, repère
    centré : anneau néon, cadran, aiguille ambre, sur fond spatial."""
    import math
    r = math.hypot(u, v)
    if r > 0.97:
        return None
    angle = math.degrees(math.atan2(-v, u))   # 0° à droite, 90° en haut
    # aiguille : du centre vers le haut à droite (30°)
    ax, ay = math.cos(math.radians(30)) * 0.62, -math.sin(math.radians(30)) * 0.62
    t = max(0.0, min(1.0, (u * ax + v * ay) / (ax * ax + ay * ay)))
    if math.hypot(u - t * ax, v - t * ay) < 0.075 or r < 0.13:
        return _rvb(AMBRE)
    if abs(r - 0.84) < 0.075:
        return _rvb(NEON)
    if abs(r - 0.84) < 0.13:
        return _rvb(melanger(NEON, FOND_ENTETE, 0.3))
    if 0.5 < r < 0.6 and (angle > -45 or angle < -135):   # cadran ouvert vers le bas
        return _rvb(NEON_FONCE)
    return _rvb(FOND_ENTETE)


def icone(racine, taille=48):
    """Icône de la fenêtre (barre de titre, barre des tâches), dessinée ici :
    pas de fichier à fournir. Lissée (4 points par pixel)."""
    try:
        image = tk.PhotoImage(master=racine, width=taille, height=taille)
        transparents = []
        lignes = []
        for y in range(taille):
            ligne = []
            for x in range(taille):
                points = [_pixel_icone((x + dx) / (taille - 1) * 2 - 1, (y + dy) / (taille - 1) * 2 - 1)
                          for dx in (-0.25, 0.25) for dy in (-0.25, 0.25)]
                pleins = [p for p in points if p is not None]
                if len(pleins) <= 1:
                    transparents.append((x, y))
                    ligne.append(FOND_ENTETE)
                    continue
                moyenne = [round(sum(p[i] for p in pleins) / len(pleins)) for i in range(3)]
                ligne.append("#%02x%02x%02x" % tuple(moyenne))
            lignes.append("{" + " ".join(ligne) + "}")
        image.put(" ".join(lignes))
        for x, y in transparents:
            image.transparency_set(x, y, True)
        racine.iconphoto(True, image)
        racine._icone = image   # (garder l'image en vie)
    except Exception:
        pass   # (purement décoratif)


def taille_initiale(racine, largeur, hauteur):
    """« LxH » sans dépasser l'écran (barre des tâches comprise)."""
    largeur = min(largeur, racine.winfo_screenwidth() - 40)
    hauteur = min(hauteur, racine.winfo_screenheight() - 90)
    return f"{largeur}x{hauteur}"


class Entete(tk.Frame):
    """Bandeau du haut : titre néon sur un fond étoilé, une ligne lumineuse en
    bas, et à droite une zone (self.droite) pour des boutons."""

    def __init__(self, parent, polices, titre, sous_titre, hauteur=60):
        super().__init__(parent, background=FOND_ENTETE, height=hauteur)
        self.pack_propagate(False)
        self.polices, self.titre, self.sous_titre = polices, titre, sous_titre
        self.toile = tk.Canvas(self, background=FOND_ENTETE, highlightthickness=0, height=hauteur)
        self.toile.place(x=0, y=0, relwidth=1, relheight=1)
        self.droite = ttk.Frame(self, style="Entete.TFrame")
        self.droite.place(relx=1.0, rely=0.5, x=-14, y=-2, anchor="e")
        self.toile.bind("<Configure>", lambda e: self.dessiner())

    def dessiner(self):
        c = self.toile
        c.delete("all")
        largeur, hauteur = max(c.winfo_width(), 1), max(c.winfo_height(), 1)
        # Étoiles : toujours les mêmes (graine fixe), quelques-unes plus vives
        hasard = random.Random(1977)
        for _ in range(max(40, largeur // 10)):
            x, y = hasard.uniform(0, largeur), hasard.uniform(2, hauteur - 6)
            eclat = hasard.choice((0.18, 0.25, 0.32, 0.45, 0.6, 0.85))
            taille = 2 if eclat > 0.8 else 1
            c.create_rectangle(x, y, x + taille, y + taille, outline="",
                               fill=melanger("#cfe8ff", FOND_ENTETE, eclat))
        # Titre néon : halo (copies décalées, de plus en plus pâles), puis le texte net
        x0, y0 = 22, hauteur // 2 - 7
        for rayon, part in ((4, 0.08), (3, 0.13), (2, 0.2), (1, 0.32)):
            couleur = melanger(NEON, FOND_ENTETE, part)
            for dx, dy in ((-rayon, 0), (rayon, 0), (0, -rayon), (0, rayon),
                           (-rayon, -rayon), (rayon, rayon), (-rayon, rayon), (rayon, -rayon)):
                c.create_text(x0 + dx, y0 + dy, text=self.titre, anchor="w", font=self.polices.logo, fill=couleur)
        c.create_text(x0, y0, text=self.titre, anchor="w", font=self.polices.logo, fill="#c8f5ff")
        c.create_text(x0 + 2, hauteur - 13, text=self.sous_titre, anchor="w", font=self.polices.sous_titre,
                      fill=AMBRE)
        # Ligne lumineuse en bas : néon vif à gauche, qui s'éteint vers la droite
        morceaux = 48
        for i in range(morceaux):
            x1, x2 = largeur * i / morceaux, largeur * (i + 1) / morceaux
            part = max(0.12, 1 - i / morceaux)
            c.create_line(x1, hauteur - 2, x2, hauteur - 2, fill=melanger(NEON, FOND_ENTETE, part * 0.35))
            c.create_line(x1, hauteur - 1, x2, hauteur - 1, fill=melanger(NEON, FOND_ENTETE, part))
        c.create_line(22, hauteur - 1, 150, hauteur - 1, fill=AMBRE, width=1)


class Voyant(tk.Canvas):
    """Petit voyant lumineux (état de la session) : un point et son halo."""

    def __init__(self, parent, taille=12):
        marge = 5
        super().__init__(parent, width=taille + 2 * marge, height=taille + 2 * marge, background=FOND,
                         highlightthickness=0)
        self.taille, self.marge = taille, marge
        self.allumer(TEXTE_DOUX)

    def allumer(self, couleur):
        self.delete("all")
        t, m = self.taille, self.marge
        for ecart, part in ((5, 0.12), (3, 0.25), (1, 0.45)):
            self.create_oval(m - ecart, m - ecart, m + t + ecart, m + t + ecart, outline="",
                             fill=melanger(couleur, FOND, part))
        self.create_oval(m, m, m + t, m + t, outline="", fill=couleur)
        self.create_oval(m + t * 0.3, m + t * 0.25, m + t * 0.55, m + t * 0.5, outline="",
                         fill=melanger("#ffffff", couleur, 0.55))
