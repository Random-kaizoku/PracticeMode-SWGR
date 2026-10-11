<#
    pare-feu-session.ps1 : blocage Internet du jeu pendant une session d'entraînement
    ===============================================================================

    Lancé par la fenêtre PracticeMode, EN ADMINISTRATEUR (fenêtre de confirmation
    Windows), parce que modifier le pare-feu exige ces droits.

    Mode Session (début d'entraînement) :
        1. retire d'éventuelles règles PracticeMode oubliées ;
        2. bloque l'entrée et la sortie réseau du jeu, de ses lanceurs et de
           ses programmes de rapports de crash ;
        3. écrit « actif » dans echange\pare-feu.txt ;
        4. ATTEND que la fenêtre dépose echange\liberer-pare-feu.txt, ce
           qu'elle fait seulement APRÈS avoir remis le jeu d'origine ;
        5. retire les règles et écrit « retire ».
       → une seule confirmation administrateur par session.

    Mode Retirer (secours, par ex. après un redémarrage du PC) :
        retire les règles et écrit « retire ».

    Toutes les règles portent le groupe « PracticeMode » : faciles à retrouver
    (Pare-feu Windows → Règles de trafic sortant) et à supprimer.
#>
param(
    [ValidateSet('Session', 'Retirer')]
    [string]$Mode = 'Session',
    [Parameter(Mandatory = $true)][string]$RacineJeu,
    [Parameter(Mandatory = $true)][string]$Echange
)

$ErrorActionPreference = 'Stop'
$Groupe = 'PracticeMode'
$FichierEtat = Join-Path $Echange 'pare-feu.txt'
$FichierSignal = Join-Path $Echange 'liberer-pare-feu.txt'

# Programmes bloqués (relatifs à la racine du jeu)
$Programmes = @(
    'Griffin\Binaries\Win64\SWGR-Win64-Shipping.exe',            # le jeu
    'SWGR.exe',                                                   # son petit lanceur
    'Launcher.exe',                                               # lanceur Epic Online Services
    'Griffin\Plugins\External\Sentry\Binaries\Win64\crashpad_handler.exe',  # rapports de crash
    'Engine\Binaries\Win64\CrashReportClient.exe'                 # rapports de crash Unreal
)

function Ecrire-Etat($texte) {
    Set-Content -LiteralPath $FichierEtat -Value $texte -Encoding UTF8
}

function Retirer-Regles {
    Get-NetFirewallRule -Group $Groupe -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    Ecrire-Etat 'retire'
}

try {
    if ($Mode -eq 'Retirer') {
        Retirer-Regles
        exit 0
    }

    # 1. Repartir propre
    Remove-Item -LiteralPath $FichierSignal -ErrorAction SilentlyContinue
    Get-NetFirewallRule -Group $Groupe -ErrorAction SilentlyContinue | Remove-NetFirewallRule

    # 2. Blocage, dans les deux sens, pour chaque programme qui existe
    $nb = 0
    foreach ($relatif in $Programmes) {
        $chemin = Join-Path $RacineJeu $relatif
        if (Test-Path -LiteralPath $chemin) {
            $nom = Split-Path $chemin -Leaf
            foreach ($sens in 'Outbound', 'Inbound') {
                New-NetFirewallRule -DisplayName "PracticeMode - $nom ($sens)" -Group $Groupe `
                    -Direction $sens -Action Block -Program $chemin -Profile Any | Out-Null
                $nb++
            }
        }
    }
    if ($nb -eq 0) { throw "aucun programme du jeu trouvé dans $RacineJeu" }

    # 3. Prévenir la fenêtre
    Ecrire-Etat 'actif'

    # 4. Attendre la fin de session (la fenêtre dépose le fichier signal)
    while (-not (Test-Path -LiteralPath $FichierSignal)) {
        Start-Sleep -Seconds 2
    }
    Remove-Item -LiteralPath $FichierSignal -ErrorAction SilentlyContinue

    # 5. Lever le blocage
    Retirer-Regles
}
catch {
    Ecrire-Etat ("erreur : " + $_.Exception.Message)
    exit 1
}
