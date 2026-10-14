PracticeMode for STAR WARS: Galactic Racer — v{VERSION}
=======================================================

An offline practice mode to train on any track:
  - any track, vehicle, racer and lap count;
  - part-by-part build (stats, abilities, crash ability, affixes);
  - unlimited crashes;
  - instant restart (F6);
  - save states: 3 slots (F7 / F8), position, speed AND boost;
  - lap times saved to a file (date, track, vehicle, racer, time);
  - section timer after each save state load;
  - window in English or French (FR / EN switch);
  - AI opponents (up to 11; podracers race against podracers), with the
    story mode difficulties (Cadet, Pilot, Ace, Champion);
  - each racer's own build, abilities and buffs, in one click (Build tab);
  - podracers (work in progress): launch from the game's MAIN MENU to race in
    your pilot's own pod; from inside a race, the time trial event's pod is
    used, and some pod pilots' abilities are incomplete. Fixes coming in 2.1.


WHAT'S NEW IN 2.0.1
-------------------
  - Works again with the current Steam client: Steam changed how it stores the
    offline mode, and 2.0.0 refused to start ("Steam is not offline").

WHAT'S NEW IN 2.0.0
-------------------
  - Works with the game update of 12 October 2026 (Steam build 25880680).
  - AI opponents and AI difficulty; racer styles (build + buffs); new dark
    interface. Podracers: still being improved (see above).
  - More stable (the mod now runs on the game's main thread) and smoother races.


IMPORTANT — OFFLINE ONLY
------------------------
PracticeMode only works in single player, offline, and never touches multiplayer.
The game keeps times set offline and uploads them to the leaderboards later:
PracticeMode makes sure a time set with the mod never goes online.
  - During practice, Windows Firewall blocks every connection of the game.
  - At the end, your save is restored EXACTLY as it was before practice
    (modded times go away with it), and the game is back to 100% original.
  - The mod is locked: without this protection, it does nothing.
Never play multiplayer during a practice session.


REQUIREMENTS
------------
  - Windows 10 or 11, Windows Firewall turned on.
  - STAR WARS: Galactic Racer on Steam, current version (Steam build 25880680,
    game update of 12 October 2026).
    After a game update, PracticeMode refuses to start until it is updated too
    (otherwise the game could crash).
  - Microsoft Visual C++ 2015-2022: already installed with the game; if missing,
    PracticeMode offers the installer that ships with the game.
  - Nothing else: UE4SS is included, the window is a standalone .exe.


INSTALLATION
------------
1. Extract the "PracticeMode" folder anywhere EXCEPT "Program Files" and EXCEPT
   the game folder. Example: C:\PracticeMode
2. That's it: PracticeMode installs and removes what it needs in the game by itself.


HOW TO USE
----------
1. Steam → Steam menu → "Go Offline…".
2. Library → right-click the game → Properties → General → untick "Steam Cloud".
   (Otherwise Steam could upload your practice save to the cloud.)
3. Run PracticeMode.exe.
   Windows may show "Windows protected your PC" (unsigned program):
   "More info" → "Run anyway".
4. Click "▶ Start practice" and accept the Windows administrator prompt
   (that is the firewall block). The game starts by itself.
5. Go to the game's main menu: the window fills in (tracks, racers, build…).
6. Pick the vehicle, planet, track, racer and your build, then
   "▶ Start the race" (or double-click the track).
7. When you close the game, everything is restored automatically
   (green banner "ready for multiplayer"). Then put Steam back ONLINE.


IN-GAME KEYS
------------
  F6                      restart the race (with AI opponents: "Restart" in
                          the game's pause menu)
  F5                      relaunch the last choice (from the main menu)
  F7 / F8                 save / load — slot 1
  Shift+F7 / Shift+F8     slot 2
  Ctrl+F7 / Ctrl+F8       slot 3
  Gamepad: D-pad down = save, D-pad right = load (slot 1)
A race where you loaded a save state is marked "(save state)" and does not
count for your records.


MY TIMES
--------
In PracticeMode's "temps" folder: temps.txt (readable), temps.csv (spreadsheet),
sections.txt (section times). They stay after the session.
The window's "My times" tab shows them, with ★ on your records.


TROUBLESHOOTING
---------------
  - The game crashed or the window was closed: reopen PracticeMode.exe and
    click "■ End and restore the original game".
  - The firewall still blocks the game: "Lift the firewall block" button.
  - UE4SS log of each session: sessions\<date>\retire-du-jeu\ue4ss\UE4SS.log
  - Track, racer and affix names follow the language set IN the game.


WHAT THE "START" BUTTON REALLY DOES (transparency)
--------------------------------------------------
  1. Checks: game closed, Steam offline, Steam Cloud off, known game version.
  2. Copies (and verifies) your game data into sessions\<date>\avant:
     %LOCALAPPDATA%\StarWarsGalacticRacer\Saved\SaveGames, Saved\Config,
     Saved\Crashes and .sentry-native.
  3. Copies UE4SS + the mod into Griffin\Binaries\Win64 (dwmapi.dll and the ue4ss folder).
  4. Adds Windows Firewall rules (group "PracticeMode") blocking the game, its
     launcher and its crash reporters (outils\pare-feu-session.ps1).
  5. Starts the game through Steam.
At the end: removes UE4SS (kept in the session folder), restores your previous
data, then removes the firewall rules. Nothing is deleted without a verified copy.


UNINSTALL
---------
After a finished session (green banner), just delete the PracticeMode folder.


CREDITS
-------
  - UE4SS (RE-UE4SS), MIT license: https://github.com/UE4SS-RE/RE-UE4SS
    (see licences\UE4SS-LICENSE.txt). PracticeMode includes fixes
    (UE4SS_Signatures) for this game.
  - PracticeMode: RNGKZK.
Unofficial fan project, not affiliated with Lucasfilm, Disney or the game's publishers.
