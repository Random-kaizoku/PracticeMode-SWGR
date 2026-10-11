"""Images de la page Nexus : un bandeau (header 1400×400) et 3 images
(1920×1080) faites de vraies captures de la fenêtre PracticeMode.

La fenêtre est ouverte HORS de l'écran (rien n'apparaît par-dessus le jeu),
remplie avec les vraies données (echange/catalogue.json, temps/temps.csv),
puis chaque onglet est capturé par Windows lui-même (PrintWindow).

    publication/images/capture-course.png   captures brutes de la fenêtre
    publication/images/capture-build.png
    publication/images/capture-temps.png
    publication/images/header.png / .jpg     bandeau 1400×400
    publication/images/1-course.png …        images 1920×1080 avec légende

Usage : python outils\\captures.py [--langue fr|en]
À relancer après une session en jeu : le catalogue aura alors les capacités
et les noms anglais des circuits, pilotes et pièces.
"""
import configparser
import ctypes
import ctypes.wintypes as wt
import importlib.util
import json
import random
import shutil
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RACINE = Path(__file__).resolve().parent.parent
POLICES = Path(r"C:\Windows\Fonts")
LANGUE = sys.argv[sys.argv.index("--langue") + 1] if "--langue" in sys.argv else "fr"
SORTIE = RACINE / "publication" / "images" / LANGUE

# Ce qu'on montre : Jakku (beaucoup de circuits) en landspeeder avec Ary Quill,
# et le build de ta session du 10/10 (20:27)
CHOIX = {"type": "voiture", "interne": "MAS_LOOP_A_FWD", "pilote": "DA_Racer_Protege", "tours": "3"}
NIVEAUX = "0,5,0,9,7,0"
AFFIXES = ["Alarme de surtension III", "Accessoires plus rapides IV", "Puissance du statoréacteur IV",
           "Réduction de chaleur IV"]
AFFIXE_DECRIT = "Puissance du statoréacteur IV"


# ─────────────────────────────────────────────────────────────────────────
#  CAPTURE D'UNE FENÊTRE PAR WINDOWS (même cachée ou hors de l'écran)
# ─────────────────────────────────────────────────────────────────────────
u32, g32 = ctypes.windll.user32, ctypes.windll.gdi32
for f, args, res in ((u32.GetWindowRect, [wt.HWND, ctypes.POINTER(wt.RECT)], wt.BOOL),
                     (u32.GetDC, [wt.HWND], wt.HDC), (u32.ReleaseDC, [wt.HWND, wt.HDC], ctypes.c_int),
                     (u32.PrintWindow, [wt.HWND, wt.HDC, wt.UINT], wt.BOOL),
                     (g32.CreateCompatibleDC, [wt.HDC], wt.HDC),
                     (g32.CreateCompatibleBitmap, [wt.HDC, ctypes.c_int, ctypes.c_int], wt.HBITMAP),
                     (g32.SelectObject, [wt.HDC, wt.HGDIOBJ], wt.HGDIOBJ),
                     (g32.DeleteObject, [wt.HGDIOBJ], wt.BOOL), (g32.DeleteDC, [wt.HDC], wt.BOOL),
                     (g32.GetDIBits, [wt.HDC, wt.HBITMAP, wt.UINT, wt.UINT, ctypes.c_void_p, ctypes.c_void_p,
                                      wt.UINT], ctypes.c_int)):
    f.argtypes, f.restype = args, res


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


def capturer(hwnd):
    r = wt.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    ecran = u32.GetDC(None)
    dc = g32.CreateCompatibleDC(ecran)
    bmp = g32.CreateCompatibleBitmap(ecran, w, h)
    g32.SelectObject(dc, bmp)
    u32.PrintWindow(hwnd, dc, 2)   # 2 = PW_RENDERFULLCONTENT (cadre et titre compris)
    info = BITMAPINFOHEADER(biSize=ctypes.sizeof(BITMAPINFOHEADER), biWidth=w, biHeight=-h, biPlanes=1,
                            biBitCount=32, biCompression=0)
    tampon = ctypes.create_string_buffer(w * h * 4)
    g32.GetDIBits(dc, bmp, 0, h, tampon, ctypes.byref(info), 0)
    g32.DeleteObject(bmp)
    g32.DeleteDC(dc)
    u32.ReleaseDC(None, ecran)
    image = Image.frombuffer("RGB", (w, h), tampon, "raw", "BGRX", 0, 1)
    # Windows 10/11 entoure les fenêtres de bordures INVISIBLES (pour les
    # redimensionner à la souris) : PrintWindow les rend en noir. On recadre
    # sur le cadre visible, que donne DWM (DWMWA_EXTENDED_FRAME_BOUNDS = 9).
    visible = wt.RECT()
    if ctypes.windll.dwmapi.DwmGetWindowAttribute(wt.HWND(hwnd), 9, ctypes.byref(visible),
                                                  ctypes.sizeof(visible)) == 0:
        g, hh = visible.left - r.left, visible.top - r.top
        d, b = r.right - visible.right, r.bottom - visible.bottom
        if 0 <= g <= 20 and 0 <= d <= 20 and 0 <= b <= 20 and hh >= 0:
            image = image.crop((g, hh, w - d, h - b))
    return image


# ─────────────────────────────────────────────────────────────────────────
#  LA FENÊTRE, DANS UN BAC À SABLE (vraies données, aucun effet sur le jeu)
# ─────────────────────────────────────────────────────────────────────────
def preparer_fenetre():
    sys.path.insert(0, str(RACINE / "fenetre"))
    spec = importlib.util.spec_from_file_location("pm", RACINE / "fenetre" / "PracticeMode.pyw")
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    bac = Path(tempfile.mkdtemp())
    (bac / "temps").mkdir()
    catalogue = json.loads((RACINE / "echange" / "catalogue.json").read_text(encoding="utf-8"))
    (bac / "catalogue.json").write_text(json.dumps(catalogue), encoding="utf-8")
    if (RACINE / "temps" / "temps.csv").exists():
        shutil.copy2(RACINE / "temps" / "temps.csv", bac / "temps" / "temps.csv")
    pm.DOSSIER_ECHANGE = bac
    pm.FICHIER_CATALOGUE, pm.FICHIER_COMMANDE = bac / "catalogue.json", bac / "commande.txt"
    pm.FICHIER_ETAT, pm.FICHIER_LANGUE = bac / "etat.txt", bac / "langue.txt"
    pm.FICHIER_PREFERENCES, pm.FICHIER_TEMPS_CSV = bac / "prefs.ini", bac / "temps" / "temps.csv"

    # Préférences : la course et le build à montrer
    circuit = next(c for c in catalogue["circuits"] if c.get("interne") == CHOIX["interne"])
    pilote = next(p for p in catalogue["pilotes"] if p["nom"] == CHOIX["pilote"])
    meme = lambda x, y: (x or "").replace(" ", " ") == y   # le jeu met des espaces insécables
    affixes = [next(a["chemin"] for a in catalogue["affixes"] if meme(a.get("affiche"), n)) for n in AFFIXES]
    decrit = affixes[AFFIXES.index(AFFIXE_DECRIT)]
    prefs = configparser.ConfigParser(interpolation=None)
    prefs["fenetre"] = {"langue": LANGUE}
    prefs["choix"] = {"type": CHOIX["type"], "piste": circuit["chemin"], "pilote": pilote["chemin"],
                      "tours": CHOIX["tours"], "au_premier_plan": "False"}
    prefs["build"] = {"niveaux": NIVEAUX, "affixes": "|".join(affixes), "crashs_illimites": "True"}
    with open(pm.FICHIER_PREFERENCES, "w", encoding="utf-8") as f:
        prefs.write(f)

    # Bandeau « entraînement en cours » (l'état montré pendant une vraie session)
    pm.S.session_en_cours = lambda c: bac
    pm.S.jeu_lance = lambda c: True
    pm.S.regles_pare_feu_presentes = lambda c: True
    pm.Fenetre.verifier_pare_feu_au_demarrage = lambda self: None
    f = pm.Fenetre()
    # Sur l'écran (sinon Windows ne la dessine pas), mais presque invisible
    # (opacité 1 %) et derrière les autres fenêtres : rien ne gêne le jeu.
    f.attributes("-alpha", 0.01)
    f.geometry("1350x800+40+40")
    f.lower()
    f.update()
    f.after(10, lambda: None)
    for _ in range(30):
        f.update()
    # Les messages d'un vrai début de session (textes de l'application)
    t = pm.t
    for heure, texte in (("21:48:31", t("debut_sauvegarde")),
                         ("21:48:31", t("sauvegarde_verifiee", element="Saved/SaveGames")),
                         ("21:48:32", t("installe")), ("21:48:32", t("pare_feu_uac")),
                         ("21:48:40", t("pare_feu_actif")), ("21:48:40", t("lancement_jeu"))):
        f.liste_messages.insert("end", f"{heure}  {texte}")
    f.liste_messages.see("end")
    f.var_etat.set(t("jeu_prefixe") + "21:58:03  " + (
        "retour à l'emplacement 1 (389 km/h) — chrono de section lancé" if LANGUE == "fr"
        else "back to slot 1 (389 km/h) — section timer started"))
    f.rafraichir_etat = lambda: None
    f.surveiller_session()            # bandeau rouge tout de suite
    return pm, f, decrit


def captures():
    pm, f, decrit = preparer_fenetre()
    hwnd = int(f.wm_frame(), 16)
    images = {}

    def photo(nom, onglet, preparation=None):
        f.onglets.select(onglet)
        if preparation:
            preparation()
        for _ in range(20):
            f.update()
        images[nom] = capturer(hwnd)

    def build():
        f.decrire_affixe(decrit)

    def temps():
        f.remplir_temps()

    photo("course", 0, lambda: f.arbre_pilotes.yview_moveto(0))
    photo("build", 1, build)
    photo("temps", 2, temps)
    f.destroy()
    return images


# ─────────────────────────────────────────────────────────────────────────
#  MISE EN PAGE
# ─────────────────────────────────────────────────────────────────────────
def police(nom, taille, variante=None):
    p = ImageFont.truetype(str(POLICES / nom), taille)
    if variante:
        try:
            p.set_variation_by_name(variante)
        except (OSError, ValueError):
            pass
    return p


def fond(largeur, hauteur, graine=7):
    """Espace sombre : dégradé bleu nuit, étoiles, traînées de vitesse."""
    img = Image.new("RGB", (largeur, hauteur))
    d = ImageDraw.Draw(img)
    for y in range(hauteur):
        k = y / hauteur
        d.line([(0, y), (largeur, y)], fill=(int(6 + 8 * k), int(9 + 16 * k), int(20 + 34 * k)))
    lueur = Image.new("RGB", (largeur, hauteur), (0, 0, 0))
    ImageDraw.Draw(lueur).ellipse([-largeur * 0.25, hauteur * 0.35, largeur * 0.45, hauteur * 1.6],
                                  fill=(255, 120, 20))
    img = Image.blend(img, lueur.filter(ImageFilter.GaussianBlur(hauteur / 3)), 0.22)
    hasard = random.Random(graine)
    etoiles = Image.new("RGBA", (largeur, hauteur), (0, 0, 0, 0))
    de = ImageDraw.Draw(etoiles)
    for _ in range(largeur * hauteur // 2500):
        x, y, r = hasard.uniform(0, largeur), hasard.uniform(0, hauteur), hasard.choice((0.6, 0.8, 1.1, 1.6))
        de.ellipse([x - r, y - r, x + r, y + r], fill=(220, 230, 255, hasard.randint(60, 200)))
    trainees = Image.new("RGBA", (largeur, hauteur), (0, 0, 0, 0))
    dt = ImageDraw.Draw(trainees)
    for _ in range(26):
        y = hasard.uniform(0, hauteur)
        x = hasard.uniform(-largeur * 0.2, largeur * 0.8)
        long_ = hasard.uniform(largeur * 0.08, largeur * 0.35)
        couleur = hasard.choice(((90, 180, 255), (255, 150, 60), (160, 210, 255)))
        for i in range(24):
            a = int(110 * (i / 24) ** 2)
            dt.line([(x + long_ * i / 24, y), (x + long_ * (i + 1) / 24, y)], fill=couleur + (a,), width=2)
    img = img.convert("RGBA")
    img.alpha_composite(etoiles)
    img.alpha_composite(trainees.filter(ImageFilter.GaussianBlur(0.6)))
    return img


def cadre_ombre(capture, largeur):
    """La capture à la largeur voulue, avec coins arrondis et ombre portée."""
    k = largeur / capture.width
    cap = capture.resize((largeur, round(capture.height * k)), Image.LANCZOS).convert("RGBA")
    masque = Image.new("L", cap.size, 0)
    ImageDraw.Draw(masque).rounded_rectangle([0, 0, cap.width - 1, cap.height - 1], radius=10, fill=255)
    cap.putalpha(masque)
    marge = 40
    ombre = Image.new("RGBA", (cap.width + 2 * marge, cap.height + 2 * marge), (0, 0, 0, 0))
    ImageDraw.Draw(ombre).rounded_rectangle([marge, marge + 10, marge + cap.width, marge + cap.height + 10],
                                            radius=14, fill=(0, 0, 0, 170))
    ombre = ombre.filter(ImageFilter.GaussianBlur(18))
    ombre.alpha_composite(cap, (marge, marge))
    return ombre, marge


def pastille(d, x, y, texte, f):
    l = d.textlength(texte, font=f)
    d.rounded_rectangle([x, y, x + l + 28, y + 38], radius=19, fill=(40, 90, 160, 120),
                        outline=(140, 200, 255, 200), width=2)
    d.text((x + 14, y + 19), texte, font=f, fill=(230, 240, 255), anchor="lm")
    return x + l + 28 + 12


def header(capture_course):
    img = fond(1400, 400)
    vignette, marge = cadre_ombre(capture_course, 560)
    img.alpha_composite(vignette, (1400 - vignette.width + marge + 70, 400 - 300 - marge))
    voile = Image.new("RGBA", img.size, (0, 0, 0, 0))   # assombrit sous le texte
    for x in range(760):
        ImageDraw.Draw(voile).line([(x, 0), (x, 400)], fill=(4, 8, 18, int(150 * (1 - x / 760))))
    img.alpha_composite(voile)
    d = ImageDraw.Draw(img, "RGBA")   # « RGBA » : les couleurs transparentes se mélangent au fond
    titre = police("bahnschrift.ttf", 104, "Bold Condensed")
    d.text((58, 46), "PRACTICE MODE", font=titre, fill=(255, 255, 255))
    d.text((62, 168), "for STAR WARS: Galactic Racer", font=police("seguisb.ttf", 34), fill=(170, 205, 245))
    x = 60
    f = police("bahnschrift.ttf", 21, "SemiBold")
    for texte in ("ANY TRACK", "ANY BUILD", "SAVE STATES", "INSTANT RESTART"):
        x = pastille(d, x, 252, texte, f)
    d.text((62, 330), "100% offline  ·  never touches multiplayer or leaderboards",
           font=police("segoeui.ttf", 22), fill=(255, 190, 120))
    d.text((1384, 16), "by RNGKZK", font=police("segoeui.ttf", 17), fill=(190, 200, 220, 220), anchor="rt")
    return img.convert("RGB")


def image_legendee(capture, titre_en, titre_fr, graine):
    img = fond(1920, 1080, graine)
    d = ImageDraw.Draw(img)
    d.text((80, 52), titre_en, font=police("bahnschrift.ttf", 64, "Bold"), fill=(255, 255, 255))
    d.text((84, 132), titre_fr, font=police("segoeui.ttf", 30), fill=(170, 205, 245))
    vignette, marge = cadre_ombre(capture, 1330)   # sous la légende, sans la toucher
    img.alpha_composite(vignette, ((1920 - vignette.width) // 2, 205 - marge))
    return img.convert("RGB")


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    imgs = captures()
    for nom, im in imgs.items():
        if im.getextrema() == ((0, 0), (0, 0), (0, 0)):
            sys.exit(f"ERREUR : capture « {nom} » toute noire (fenêtre non dessinée)")
        im.save(SORTIE / f"capture-{nom}.png", optimize=True)
    h = header(imgs["course"])
    h.save(SORTIE / "header.png", optimize=True)
    h.save(SORTIE / "header.jpg", quality=90, optimize=True, progressive=True)
    legendes = [("course", "Any track, any vehicle, any racer", "Tous les circuits, véhicules et pilotes"),
                ("build", "Your build, part by part", "Ton build pièce par pièce : stats, capacités, affixes"),
                ("temps", "Your times and records", "Tes temps et tes records, enregistrés automatiquement")]
    for i, (nom, en, fr) in enumerate(legendes, 1):
        image_legendee(imgs[nom], en, fr, graine=i).save(SORTIE / f"{i}-{nom}.png", optimize=True)
    for p in sorted(SORTIE.iterdir()):
        with Image.open(p) as im:
            print(f"   {p.name:22} {im.width}×{im.height}  {p.stat().st_size / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
