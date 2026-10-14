"""Gestion des sessions d'entraînement : la partie « launcher » de PracticeMode.

Une session d'entraînement, c'est :

    DÉBUT                                   FIN (automatique à la fermeture du jeu)
    ─────                                   ───
    1. vérifications (jeu fermé,            1. arrêt de crashpad_handler
       Steam hors ligne, Cloud coupé)          (rapports de crash du jeu)
    2. copie des données du jeu             2. retrait d'UE4SS du dossier du jeu
       → sessions/<date>/avant                 (copié dans la session, pas supprimé)
    3. installation d'UE4SS + mod           3. données du jeu remises comme avant
    4. pare-feu Windows : blocage           4. pare-feu : blocage levé
       (une fenêtre administrateur)
    5. lancement du jeu par Steam

Les fichiers et dossiers sont les MÊMES que ceux de outils/session-dev.ps1
(SESSION_EN_COURS.txt, avant/, apres-session/, retire-du-jeu/,
win64-origine.txt…) : les .bat Debut/Fin-Session restent utilisables en secours.

Ce module ne contient aucune interface : il est utilisé par la fenêtre, et
testé à part sur un faux jeu.
"""
import ctypes
import ctypes.wintypes as wt
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
import winreg
from datetime import datetime
from pathlib import Path

try:
    from langues import m      # textes en français / anglais (m : message traduisible)
except ImportError:         # module chargé par son chemin (tests) : on ajoute son dossier
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from langues import m

# Ce qui est sauvegardé puis restauré (relatif au dossier de données du jeu)
ELEMENTS_PROTEGES = ["Saved/SaveGames", "Saved/Config", "Saved/Crashes", ".sentry-native"]
EXE_JEU = "SWGR-Win64-Shipping.exe"
CRASHPAD = "crashpad_handler.exe"
GROUPE_PARE_FEU = "PracticeMode"
SANS_FENETRE = 0x08000000   # CREATE_NO_WINDOW : pas de console noire qui clignote


APP_ID = "4078430"
# DLL de Microsoft Visual C++ (2015-2022, x64) dont UE4SS a besoin
DLL_VISUAL_CPP = ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll",
                  "msvcp140_atomic_wait.dll", "msvcp140_codecvt_ids.dll"]
# Ligne du mod qui reçoit, à l'installation, le dossier de PracticeMode
LIGNE_DOSSIER_MOD = re.compile(r'^local DOSSIER_PRACTICEMODE = "[^"\r\n]*"', re.M)
# … et celle qui reçoit le fichier de Steam lu par le verrou du mod (Steam hors ligne ?)
LIGNE_STEAM_MOD = re.compile(r'^local FICHIER_STEAM = "[^"\r\n]*"', re.M)


class ErreurSession(Exception):
    """Problème qui empêche de continuer ; le message est destiné à l'utilisateur."""


def dossier_application():
    """Dossier de PracticeMode : celui de PracticeMode.exe (version distribuée),
    sinon le dossier du dépôt (fenetre/.. quand on lance le .pyw)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def trouver_steam():
    """Dossier de Steam, lu dans le registre (là où Steam l'écrit lui-même)."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as cle:
            chemin = winreg.QueryValueEx(cle, "SteamPath")[0]
        if chemin and Path(chemin).exists():
            return Path(chemin)
    except OSError:
        pass
    return Path(r"C:\Program Files (x86)\Steam")


def trouver_jeu(steam):
    """Dossier du jeu, cherché dans toutes les bibliothèques Steam
    (steamapps/libraryfolders.vdf, puis appmanifest_4078430.acf). None si absent."""
    bibliotheques = [Path(steam)]
    try:
        texte = (Path(steam) / "steamapps" / "libraryfolders.vdf").read_text(encoding="utf-8", errors="replace")
        bibliotheques += [Path(p.replace("\\\\", "\\")) for p in re.findall(r'"path"\s+"([^"]+)"', texte)]
    except OSError:
        pass
    for biblio in bibliotheques:
        manifeste = biblio / "steamapps" / f"appmanifest_{APP_ID}.acf"
        try:
            m = re.search(r'"installdir"\s+"([^"]+)"', manifeste.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if m:
            racine = biblio / "steamapps" / "common" / m.group(1)
            if (racine / "Griffin" / "Binaries" / "Win64" / EXE_JEU).exists():
                return racine
    return None


def est_dossier_du_jeu(chemin):
    return chemin is not None and (Path(chemin) / "Griffin" / "Binaries" / "Win64" / EXE_JEU).exists()


class Config:
    """Tous les chemins. Par défaut : Steam et le jeu sont trouvés tout seuls ;
    les tests passent d'autres chemins (un faux jeu dans un dossier temporaire).
    racine_jeu vaut None si le jeu est introuvable (la fenêtre demande alors
    à l'utilisateur de choisir son dossier)."""

    def __init__(self, projet=None, racine_jeu=None, donnees_jeu=None, steam=None):
        self.projet = Path(projet or dossier_application())
        self.steam = Path(steam or trouver_steam())
        self.racine_jeu = Path(racine_jeu) if racine_jeu else trouver_jeu(self.steam)
        self.win64 = self.racine_jeu / "Griffin" / "Binaries" / "Win64" if self.racine_jeu else None
        self.donnees_jeu = Path(donnees_jeu or Path(os.environ["LOCALAPPDATA"]) / "StarWarsGalacticRacer")
        self.app_id = APP_ID
        self.installation = self.projet / "installation"
        self.versions = self.installation / "versions-compatibles.txt"
        self.sessions = self.projet / "sessions"
        self.marqueur = self.sessions / "SESSION_EN_COURS.txt"
        self.echange = self.projet / "echange"
        self.script_pare_feu = self.projet / "outils" / "pare-feu-session.ps1"
        self.etat_pare_feu = self.echange / "pare-feu.txt"          # écrit par le script de pare-feu
        self.signal_pare_feu = self.echange / "liberer-pare-feu.txt"  # écrit par la fenêtre
        # Programmes bloqués par le pare-feu pendant une session
        self.programmes_bloques = [
            self.win64 / EXE_JEU,
            self.racine_jeu / "SWGR.exe",
            self.racine_jeu / "Launcher.exe",
            self.racine_jeu / "Griffin/Plugins/External/Sentry/Binaries/Win64" / CRASHPAD,
            self.racine_jeu / "Engine/Binaries/Win64/CrashReportClient.exe",
        ] if self.racine_jeu else []


def jeu_trouve(cfg):
    return cfg.win64 is not None and (cfg.win64 / EXE_JEU).exists()


# ─────────────────────────────────────────────────────────────────────────
#  PROCESSUS (sans programme externe : appels directs à Windows)
# ─────────────────────────────────────────────────────────────────────────
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_psapi = ctypes.WinDLL("psapi", use_last_error=True)
_k32.OpenProcess.restype = wt.HANDLE
_k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
_k32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
_k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
_k32.CloseHandle.argtypes = [wt.HANDLE]


def processus():
    """Liste (pid, chemin complet de l'exe) de tous les programmes lancés."""
    tableau = (wt.DWORD * 8192)()
    utilise = wt.DWORD()
    _psapi.EnumProcesses(tableau, ctypes.sizeof(tableau), ctypes.byref(utilise))
    res = []
    for pid in tableau[:utilise.value // 4]:
        h = _k32.OpenProcess(0x1000, False, pid)   # droit « lire les infos » seulement
        if not h:
            continue
        tampon = ctypes.create_unicode_buffer(1024)
        taille = wt.DWORD(1024)
        if _k32.QueryFullProcessImageNameW(h, 0, tampon, ctypes.byref(taille)):
            res.append((pid, tampon.value))
        _k32.CloseHandle(h)
    return res


def processus_du_jeu(cfg):
    """Programmes lancés depuis le dossier du jeu."""
    if not cfg.racine_jeu:
        return []
    racine = str(cfg.racine_jeu).lower()
    return [(pid, chemin) for pid, chemin in processus() if chemin.lower().startswith(racine)]


def jeu_lance(cfg):
    """Vrai si le jeu (ou son lanceur) tourne. crashpad_handler ne compte pas :
    il reste souvent ouvert après le jeu."""
    return any(not chemin.lower().endswith(CRASHPAD) for _, chemin in processus_du_jeu(cfg))


def arreter_crashpad(cfg, journal):
    for pid, chemin in processus_du_jeu(cfg):
        if chemin.lower().endswith(CRASHPAD):
            h = _k32.OpenProcess(0x0001, False, pid)   # droit « arrêter »
            if h:
                _k32.TerminateProcess(h, 0)
                _k32.CloseHandle(h)
                journal(m("crashpad_arrete", pid=pid))


# ─────────────────────────────────────────────────────────────────────────
#  VÉRIFICATIONS STEAM
# ─────────────────────────────────────────────────────────────────────────
def steam_hors_ligne(cfg):
    """Steam l'écrit dans config/loginusers.vdf : on regarde le compte connecté
    le plus récemment (plus grand « Timestamp ») et sa valeur WantsOfflineMode.
    Depuis une mise à jour de Steam (vu le 14/10/2026), la clé s'écrit
    « timestamp » : on lit les deux."""
    try:
        texte = (cfg.steam / "config" / "loginusers.vdf").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    meilleur, temps_max = None, -1
    for bloc in re.findall(r"\{[^{}]*\}", texte):
        m = re.search(r'"[Tt]imestamp"\s+"(\d+)"', bloc)
        if m and int(m.group(1)) > temps_max:
            temps_max, meilleur = int(m.group(1)), bloc
    return bool(meilleur and re.search(r'"WantsOfflineMode"\s+"1"', meilleur))


def cloud_desactive(cfg):
    for f in (cfg.steam / "userdata").glob("*/7/remote/sharedconfig.vdf"):
        try:
            texte = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(r'"' + cfg.app_id + r'"\s*\{[^{}]*"cloudenabled"\s+"0"', texte):
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────
#  ÉTAT DE LA SESSION
# ─────────────────────────────────────────────────────────────────────────
def ue4ss_installe(cfg):
    if cfg.win64 is None:
        return False
    return (cfg.win64 / "dwmapi.dll").exists() or (cfg.win64 / "ue4ss").exists()


def session_en_cours(cfg):
    """Dossier de la session ouverte, ou None."""
    try:
        return Path(cfg.marqueur.read_text(encoding="utf-8-sig").strip())
    except OSError:
        return None


# ─────────────────────────────────────────────────────────────────────────
#  COPIE VÉRIFIÉE
#  On ne supprime jamais rien tant que la copie n'est pas prouvée identique
#  (empreinte SHA1 de chaque fichier).
# ─────────────────────────────────────────────────────────────────────────
def _empreinte(chemin):
    h = hashlib.sha1()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def copie_verifiee(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise ErreurSession(m("destination_existe", chemin=destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
        fichiers = [p for p in source.rglob("*") if p.is_file()]
    else:
        shutil.copy2(source, destination)
        fichiers = [source]
    for f in fichiers:
        copie = destination / f.relative_to(source) if source.is_dir() else destination
        if not copie.exists() or _empreinte(f) != _empreinte(copie):
            raise ErreurSession(m("copie_differente", chemin=copie))


def _supprimer(chemin):
    chemin = Path(chemin)
    if chemin.is_dir():
        shutil.rmtree(chemin)
    elif chemin.exists():
        chemin.unlink()


# ─────────────────────────────────────────────────────────────────────────
#  DÉBUT ET FIN DE SESSION (fichiers seulement ; pare-feu et lancement à part)
# ─────────────────────────────────────────────────────────────────────────
def versions_compatibles(cfg):
    """Empreintes SHA1 des exe du jeu pour lesquels les correctifs d'UE4SS
    ont été faits (installation/versions-compatibles.txt, une par ligne)."""
    try:
        lignes = cfg.versions.read_text(encoding="utf-8").splitlines()
    except OSError:
        return set()
    return {l.split()[0].lower() for l in lignes if l.strip() and not l.lstrip().startswith("#")}


def verifier_version_jeu(cfg):
    """Les correctifs d'UE4SS (UE4SS_Signatures) visent UNE version de l'exe du
    jeu : après une mise à jour du jeu, ils peuvent ne plus marcher, voire le
    faire planter. On refuse donc une version inconnue."""
    empreinte = _empreinte(cfg.win64 / EXE_JEU).lower()
    if empreinte not in versions_compatibles(cfg):
        raise ErreurSession(m("version_inconnue", empreinte=empreinte[:12]))


def visual_cpp_manquant():
    """DLL de Visual C++ absentes de Windows (liste vide = tout est là)."""
    systeme = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    return [d for d in DLL_VISUAL_CPP if not (systeme / d).exists()]


def installateur_visual_cpp(cfg):
    """L'installateur de Visual C++ fourni avec le jeu (None s'il est absent)."""
    if not cfg.racine_jeu:
        return None
    chemin = cfg.racine_jeu / "Engine" / "Extras" / "Redist" / "en-us" / "vc_redist.x64.exe"
    return chemin if chemin.exists() else None


_k32.GetShortPathNameW.argtypes = [wt.LPCWSTR, wt.LPWSTR, wt.DWORD]
_k32.GetShortPathNameW.restype = wt.DWORD


def chemin_pour_lua(chemin):
    """Chemin du dossier de PracticeMode, écrit pour le mod (barres « / »).
    Le Lua d'UE4SS ouvre ses fichiers avec l'ancienne API de Windows, qui ne
    comprend pas les accents : on prend alors le nom court (8.3) du dossier,
    et si Windows n'en a pas, on demande de déplacer PracticeMode."""
    texte = str(chemin)
    if not texte.isascii():
        tampon = ctypes.create_unicode_buffer(1024)
        if _k32.GetShortPathNameW(texte, tampon, 1024) and tampon.value.isascii():
            texte = tampon.value
        else:
            raise ErreurSession(m("chemin_accents", chemin=chemin))
    return texte.replace("\\", "/").rstrip("/") + "/"


def installer_chemin_dans_mod(cfg):
    """Écrit dans le main.lua INSTALLÉ dans le jeu (celui du dossier
    « installation » n'est pas modifié) : le dossier de PracticeMode, et le
    fichier de Steam que le verrou du mod relit (Steam hors ligne ?)."""
    fichier = cfg.win64 / "ue4ss" / "Mods" / "PracticeMode" / "Scripts" / "main.lua"
    texte = fichier.read_bytes().decode("utf-8")
    dossier = f'local DOSSIER_PRACTICEMODE = "{chemin_pour_lua(cfg.projet)}"'
    steam = f'local FICHIER_STEAM = "{chemin_pour_lua(cfg.steam / "config" / "loginusers.vdf").rstrip("/")}"'
    texte, n1 = LIGNE_DOSSIER_MOD.subn(lambda m: dossier, texte)
    texte, n2 = LIGNE_STEAM_MOD.subn(lambda m: steam, texte)
    if (n1, n2) != (1, 1):
        raise ErreurSession(m("installation_echec"))
    fichier.write_bytes(texte.encode("utf-8"))


def verifier_avant_debut(cfg, exiger_steam=True):
    """Lève ErreurSession avec un message clair si on ne peut pas commencer."""
    if session_en_cours(cfg):
        raise ErreurSession(m("deja_ouverte"))
    if not jeu_trouve(cfg):
        raise ErreurSession(m("jeu_introuvable"))
    if jeu_lance(cfg):
        raise ErreurSession(m("jeu_tourne"))
    if ue4ss_installe(cfg):
        raise ErreurSession(m("ue4ss_sans_session"))
    if exiger_steam and not steam_hors_ligne(cfg):
        raise ErreurSession(m("steam_en_ligne"))
    if exiger_steam and not cloud_desactive(cfg):
        raise ErreurSession(m("steam_cloud"))
    if not (cfg.installation / "dwmapi.dll").exists():
        raise ErreurSession(m("ue4ss_introuvable", chemin=cfg.installation))
    verifier_version_jeu(cfg)
    chemin_pour_lua(cfg.projet)


def debut(cfg, journal, exiger_steam=True):
    """Sauvegarde les données du jeu puis installe UE4SS. Renvoie le dossier de session."""
    verifier_avant_debut(cfg, exiger_steam)
    for dossier in ("echange", "temps"):   # le mod y écrit, mais ne sait pas créer de dossier
        (cfg.projet / dossier).mkdir(parents=True, exist_ok=True)
    session = cfg.sessions / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    avant = session / "avant"
    avant.mkdir(parents=True)
    for element in ELEMENTS_PROTEGES:
        source = cfg.donnees_jeu / element
        if source.exists():
            copie_verifiee(source, avant / element)
            journal(m("sauvegarde_verifiee", element=element))
    (session / "win64-origine.txt").write_text(
        "\n".join(sorted(p.name for p in cfg.win64.iterdir())) + "\n", encoding="utf-8")
    # Le marqueur est écrit AVANT l'installation : si quelque chose plante
    # ensuite, la fin de session saura tout remettre en place.
    cfg.marqueur.write_text(str(session), encoding="utf-8")
    shutil.copy2(cfg.installation / "dwmapi.dll", cfg.win64 / "dwmapi.dll")
    shutil.copytree(cfg.installation / "ue4ss", cfg.win64 / "ue4ss")
    if not ue4ss_installe(cfg):
        raise ErreurSession(m("installation_echec"))
    installer_chemin_dans_mod(cfg)
    journal(m("installe"))
    return session


def fin(cfg, journal):
    """Retire UE4SS et remet les données du jeu d'avant la session."""
    session = session_en_cours(cfg)
    if not session:
        if ue4ss_installe(cfg):
            raise ErreurSession(m("ue4ss_sans_marqueur"))
        journal(m("aucune_session"))
        return None
    if jeu_lance(cfg):
        raise ErreurSession(m("jeu_tourne_encore"))
    if not jeu_trouve(cfg):
        raise ErreurSession(m("jeu_introuvable"))
    avant, apres, retire = session / "avant", session / "apres-session", session / "retire-du-jeu"
    if not avant.exists():
        raise ErreurSession(m("sauvegarde_introuvable", chemin=avant))

    arreter_crashpad(cfg, journal)

    # Retirer de Win64 tout ce qui n'y était pas au départ (copié dans la session)
    origine = set((session / "win64-origine.txt").read_text(encoding="utf-8-sig").split())
    for item in list(cfg.win64.iterdir()):
        if item.name not in origine:
            copie_verifiee(item, retire / item.name)
            _supprimer(item)
            journal(m("retire_du_jeu", nom=item.name))

    # Remettre les données du jeu
    for element in ELEMENTS_PROTEGES:
        actuel, copie_avant = cfg.donnees_jeu / element, avant / element
        if actuel.exists():
            copie_verifiee(actuel, apres / element)
            _supprimer(actuel)
        if copie_avant.exists():
            copie_verifiee(copie_avant, actuel)
            journal(m("restaure", element=element))

    # Vérification finale : le jeu doit être exactement comme avant
    if ue4ss_installe(cfg):
        raise ErreurSession(m("ue4ss_encore"))
    maintenant = {p.name for p in cfg.win64.iterdir()}
    if maintenant != origine:
        raise ErreurSession(m("win64_different", diff=sorted(maintenant ^ origine)))
    os.replace(cfg.marqueur, session / "session-terminee.txt")
    journal(m("jeu_origine"))
    return session


# ─────────────────────────────────────────────────────────────────────────
#  PARE-FEU
#  Le blocage exige les droits administrateur. On lance donc, avec la
#  fenêtre de confirmation Windows (UAC), le script outils/pare-feu-session.ps1 :
#    - mode Session : crée les règles, écrit « actif » dans pare-feu.txt,
#      puis ATTEND que la fenêtre dépose liberer-pare-feu.txt (fin de session)
#      pour retirer les règles → une seule confirmation par session ;
#    - mode Retirer : retire les règles restées après un incident.
# ─────────────────────────────────────────────────────────────────────────
def etat_pare_feu(cfg):
    """« actif », « retire », « erreur : … » ou « » (inconnu)."""
    try:
        return cfg.etat_pare_feu.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return ""


def regles_pare_feu_presentes(cfg):
    """Lit les règles du groupe PracticeMode (lecture : pas besoin d'administrateur).
    Renvoie True / False, ou None si la lecture a échoué."""
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            f"(Get-NetFirewallRule -Group '{GROUPE_PARE_FEU}' -ErrorAction SilentlyContinue | "
                            "Measure-Object).Count"],
                           capture_output=True, text=True, timeout=30, creationflags=SANS_FENETRE)
        return int(r.stdout.strip() or "0") > 0
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def pare_feu_windows_actif():
    """Vrai si le pare-feu Windows est activé sur au moins un profil réseau."""
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "(Get-NetFirewallProfile | Where-Object Enabled).Count"],
                           capture_output=True, text=True, timeout=30, creationflags=SANS_FENETRE)
        return int(r.stdout.strip() or "0") > 0
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def lancer_script_pare_feu(cfg, mode):
    """Lance le script de pare-feu en administrateur (fenêtre de confirmation
    Windows). Renvoie False si l'utilisateur a refusé ou si le lancement a échoué."""
    cfg.echange.mkdir(parents=True, exist_ok=True)
    if mode == "Session":
        for f in (cfg.etat_pare_feu, cfg.signal_pare_feu):
            if f.exists():
                f.unlink()
    parametres = (f'-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{cfg.script_pare_feu}" '
                  f'-Mode {mode} -RacineJeu "{cfg.racine_jeu}" -Echange "{cfg.echange}"')
    resultat = ctypes.windll.shell32.ShellExecuteW(None, "runas", "powershell.exe", parametres, None, 0)
    return resultat > 32   # Windows : une valeur ≤ 32 signifie une erreur (ex. confirmation refusée)


def attendre_etat_pare_feu(cfg, voulu, delai, pause=0.5):
    """Attend que pare-feu.txt contienne `voulu` (ou une erreur). Renvoie l'état final."""
    fin_attente = time.time() + delai
    while time.time() < fin_attente:
        etat = etat_pare_feu(cfg)
        if etat == voulu or etat.startswith("erreur"):
            return etat
        time.sleep(pause)
    return etat_pare_feu(cfg)


def liberer_pare_feu(cfg, journal, lanceur=lancer_script_pare_feu):
    """Fin de session : demande au script de lever le blocage. Si le script
    n'est plus là (PC redémarré…), on le relance en mode Retirer."""
    cfg.echange.mkdir(parents=True, exist_ok=True)
    if etat_pare_feu(cfg) == "actif":
        cfg.signal_pare_feu.write_text("liberer", encoding="utf-8")
        if attendre_etat_pare_feu(cfg, "retire", 15) == "retire":
            journal(m("pf_leve"))
            return True
    if regles_pare_feu_presentes(cfg) is False:
        journal(m("pf_aucun"))
        return True
    journal(m("pf_encore"))
    if not lanceur(cfg, "Retirer"):
        journal(m("pf_refuse"))
        return False
    ok = attendre_etat_pare_feu(cfg, "retire", 60) == "retire"
    journal(m("pf_leve") if ok else m("pf_non_verifie"))
    return ok


def lancer_jeu(cfg):
    """Lance le jeu par Steam (passe par le lanceur EOS du jeu, comme d'habitude)."""
    os.startfile(f"steam://rungameid/{cfg.app_id}")
