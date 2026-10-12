# PracticeMode for STAR WARS: Galactic Racer

Offline practice mode: any track, vehicle, racer and part-by-part build, AI opponents with difficulty, racer styles, unlimited crashes, instant restart, save states (position, speed, boost), section timer and lap time log. Window in English and French.

Published on Nexus Mods by **RNGKZK**. This repository holds the complete source code of the release archive and the steps to build it.

## Offline only, by design

The game keeps times set offline and uploads them to the online leaderboards later. PracticeMode makes sure that no modded time can ever reach them:

- the launcher refuses to start unless Steam is in offline mode, Steam Cloud is off for the game and the game version is a known one;
- during practice, Windows Firewall rules (group `PracticeMode`) block the game, its launcher and its crash reporters. The user confirms them through the Windows administrator (UAC) prompt;
- when the game closes, the user's save and config are restored exactly as they were before the session, and the game folder goes back to 100% original;
- the mod itself is **locked**: it does nothing unless the launcher's firewall protection is active (`CONFIG.Verrou` in `main.lua`).

## Repository layout

| Path | Content |
|---|---|
| `fenetre/PracticeMode.pyw` | the window (Python 3 / Tkinter): race, build, times, launcher |
| `fenetre/session.py` | the launcher: checks, backup and restore, UE4SS install and removal, firewall |
| `fenetre/langues.py` | all texts of the window, in French and English |
| `installation/ue4ss/Mods/PracticeMode/Scripts/main.lua` | the UE4SS Lua mod |
| `installation/ue4ss/UE4SS_Signatures/*.lua` | custom AOB signatures. The game is built with Clang, and UE4SS's default patterns target MSVC builds |
| `installation/dwmapi.dll`, `installation/ue4ss/UE4SS.dll` | **unmodified** UE4SS binaries (see below) |
| `installation/versions-compatibles.txt` | SHA-1 of the supported game executables |
| `outils/pare-feu-session.ps1` | adds and removes the firewall block rules. It is started elevated by the window, with the user's consent |
| `outils/empaqueter.py` | builds the release archive (see below) |
| `outils/bootloader.py` | rebuilds PyInstaller's bootloader from source (fewer antivirus false positives) |
| `outils/verify_zip.py` | archive checks |
| `outils/captures.py` | screenshots for the mod page |
| `tests/` | automated tests (Lua mod run in Lua 5.4 with UE4SS stubs, launcher on a fake game, window) |
| `publication/` | README / LISEZMOI shipped in the archive, mod page texts and images |

Code comments and identifiers are in French (the author's language). User-facing texts are in English and French.

## Third-party: UE4SS

`installation/dwmapi.dll` and `installation/ue4ss/UE4SS.dll` come unmodified from the official RE-UE4SS release
**`UE4SS_v3.0.1-1164-g5e627997.zip`** (experimental build, the first one with Unreal Engine 5.7 support):
<https://github.com/UE4SS-RE/RE-UE4SS/releases>. They are licensed under MIT (`installation/ue4ss/LICENSE`).

| File | SHA-256 |
|---|---|
| `UE4SS_v3.0.1-1164-g5e627997.zip` | `3c72142a383e25e9f9553ac9e4d5677aa572e98cb369cac57200efb2e381e603` |
| `dwmapi.dll` | `3f11fad958a959dd7ab78ab0b42be90e33f8ef8e152fbdc3c8e4278cb590e6cc` |
| `ue4ss/UE4SS.dll` | `87b494191b7bc9bcfd938f54190c09e9aaa01dc354f6927ba661b0a18bad13ee` |

PracticeMode works only at runtime, through UE4SS reflection. It does not decrypt or modify any game file (`.pak`, executable), and it does not touch the game's anti-tamper protection.

## Building the release archive

Requirements: Windows 10/11, Python 3.12 64-bit, and Visual Studio 2022 (or Build Tools) with the "Desktop development with C++" workload.

```bat
python -m pip install pyinstaller==6.22.3 pillow lupa
python outils\bootloader.py
python outils\empaqueter.py --sans-tests
```

1. `bootloader.py` downloads the PyInstaller 6.22.3 source distribution from PyPI and checks it against the SHA-256 published by PyPI. It then compiles the bootloader with Visual Studio and installs it into PyInstaller. The original bootloaders are kept as `*.officiel`.
2. `empaqueter.py` builds the release:
   - it builds `PracticeMode.exe` from `fenetre/PracticeMode.pyw` (PyInstaller, `--onedir --windowed --noupx`);
   - it assembles the folder: the exe, the UE4SS files listed above, the mod, the firewall script, the readmes and the licences;
   - it runs the exe in a hidden self-test mode (`--auto-test`);
   - it zips everything into `construction/PracticeMode-SWGR-v<version>.zip`;
   - it checks the archive: zip integrity, extraction with Windows' `Expand-Archive` compared byte for byte, a search for personal data, and a Microsoft Defender scan.

Leave out `--sans-tests` to run the automated tests first. They need the game installed and a `echange/catalogue.json` exported by the mod during a game session.

PyInstaller builds are not byte-for-byte reproducible (timestamps), so a rebuilt `PracticeMode.exe` will not have the same hash as the released one. Every other file of `installation/` and `outils/pare-feu-session.ps1` in the archive is **byte-for-byte identical** to this repository: the Lua mod, signatures, UE4SS binaries and settings, and the firewall script. Only the readmes are written by `empaqueter.py`, which adds the version number. The repository uses LF line endings everywhere (`.gitattributes`) so that a checkout has exactly these bytes.
