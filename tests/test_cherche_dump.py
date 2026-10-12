"""Test de outils/cherche_dump.py sur un faux dump (pas besoin du jeu) :
modes proprietes et enums, rapports « ia » (difficulté des adversaires) et
« apparence » (d'où vient l'apparence d'un pod, décor d'une épreuve)."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
OUTIL = RACINE / "outils" / "cherche_dump.py"
# Sous Windows, la sortie d'un programme lancé par subprocess est en cp1252 :
# on la demande en UTF-8 pour pouvoir la relire.
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}

tmp = Path(tempfile.mkdtemp())
dump = tmp / "1-menu" / "CXXHeaderDump"
dump.mkdir(parents=True)
# Module du jeu
(dump / "Griffin.hpp").write_text("""#ifndef UE4SS_SDK_Griffin_HPP
#define UE4SS_SDK_Griffin_HPP

struct FAIState
{
    FDataTableRowHandle RacerAggressionLevel;                                         // 0x0000 (size: 0x10)
    TMap<EMPGameMode, FGameModePacingConfig> GameModePacingConfigs;                   // 0x0010 (size: 0x50)

}; // Size: 0x60

class UGameModeVariantDef : public UPrimaryDataAsset
{
    FRaceGridMakeup GridMakeup;                                                       // 0x0030 (size: 0x28)
    float SomethingElse;                                                              // 0x0058 (size: 0x4)

}; // Size: 0x60

class AGfnAIController : public AAIController
{
    FAIState AIState;                                                                 // 0x0400 (size: 0x60)

    void SetAggression(int32 Level);
}; // Size: 0x460

class AGfnPlayerState : public APlayerState
{
    uint8 bIsAIControlled : 1;                                                        // 0x0300 (size: 0x1)
    int32 Spacing;                                                                    // 0x0304 (size: 0x4)
    FVector Workspace;                                                                // 0x0308 (size: 0x18)

    void SetDifficulty(EAIDifficulty NewDifficulty);
    void Unrelated(float Pace);
}; // Size: 0x320

struct FRacerArchetypeDistribution
{
    TMap<ERacerArchetype, int32> RacerArchetypeDistribution;                          // 0x0000 (size: 0x50)

}; // Size: 0x50

class UPvpInstantActionDef : public UDataAsset
{
    TArray<UPvpRacerSetup*> Opponents;                                                // 0x00F0 (size: 0x10)
    FRacerArchetypeDistribution ArchetypeDistribution;                                // 0x0100 (size: 0x50)

}; // Size: 0x150

class UGfnGameInstance : public UGameInstance
{
    TArray<UCampaignDifficultyDef*> CampaignDifficulties;                             // 0x0258 (size: 0x10)
    class UArchetypeConfigCollection* ArchetypeConfigs;                               // 0x0268 (size: 0x8)
    TArray<FPvpRunRacerProgression> Progressions;                                     // 0x0270 (size: 0x10)
    int32 OtherValue;                                                                 // 0x0280 (size: 0x4)

    void SetArchetypeOverride(ERacerArchetype NewArchetype);
    void UnrelatedFunction(int32 X);
    void ApplyTuneSet(class UTuneSet* TuneSet);
}; // Size: 0x300

struct FGameTuneConfig
{
    FCampaignTuneConfig CampaignConfig;                                               // 0x0028 (size: 0x140)
    FRaceTuneConfig RaceConfig;                                                       // 0x01E8 (size: 0x40)

}; // Size: 0x228

class UGameTuneComponent : public UActorComponent
{
    FGameTuneConfig CurrentConfig;                                                    // 0x00B0 (size: 0x228)
    TArray<UTuneSet*> ActiveTuneSets;                                                 // 0x02D8 (size: 0x10)

    void RecalculateTune();
}; // Size: 0x300

class UTuneSetPassiveEffectConfig : public UPassiveEffectConfig
{
    class UTuneSet* TuneSet;                                                          // 0x0028 (size: 0x8)

}; // Size: 0x30

class ADrivingAIController : public AController
{
    class UGameTuneComponent* GameTuneComponent;                                      // 0x0348 (size: 0x8)

}; // Size: 0x350

class UGfnCampaignSubsystem : public UGameInstanceSubsystem
{
    EGfnRacerRank SelectedRank;                                                       // 0x0030 (size: 0x1)
    int32 RaceCount;                                                                  // 0x0034 (size: 0x4)

    void SetRank(EGfnRacerRank NewRank);
    void Reset();
}; // Size: 0x40

#endif
""", encoding="utf-8")
(dump / "Griffin_enums.hpp").write_text("""enum class EAIDifficulty : uint8 {
    Easy = 0,
    Normal = 1,
    Hard = 2,
    EAIDifficulty_MAX = 3,
};

enum class ESurfaceType {
    Sand = 0,
    Surface = 1,
};

enum class ERacerArchetype : uint8 {
    Ace = 0,
    Elite = 1,
    Challenger = 2,
    Default = 2,
    ERacerArchetype_MAX = 3,
};

enum class ERaceEventModeType : uint8 {
    Race = 0,
    TimeTrial = 1,
    ERaceEventModeType_MAX = 2,
};

enum class EGfnRacerRank : uint8 {
    EGfnRacerRank__Cadet = 0,
    EGfnRacerRank__Pilot = 1,
    EGfnRacerRank__Ace = 2,
    EGfnRacerRank__Champion = 3,
    EGfnRacerRank_MAX = 4,
};
""", encoding="utf-8")
# Véhicules, pilotes et épreuves (rapport « apparence »)
(dump / "GriffinVehicles.hpp").write_text("""class UVehicleBuildDef : public UPrimaryDataAsset
{
    TMap<EVehiclePartSlot, int32> SlotToUpgradeLevelMap;                              // 0x0030 (size: 0x50)
    TSoftObjectPtr<UVehicleVisualDef> VisualOverride;                                 // 0x0080 (size: 0x28)

}; // Size: 0xB0

class UCharacterDef : public UPrimaryDataAsset
{
    FText CharacterName;                                                              // 0x0140 (size: 0x18)
    TSoftObjectPtr<UVehicleVisualDef> SignatureVehicleVisual;                         // 0x0158 (size: 0x28)

}; // Size: 0x190

struct FCustomVehicleSetup
{
    class UVehicleBuildDef* VehicleBuildDef;                                          // 0x0000 (size: 0x8)
    FVehicleCustomizationData Customization;                                          // 0x0008 (size: 0x40)

}; // Size: 0x48

struct FVehicleCustomizationData
{
    TArray<FLinearColor> PaintColors;                                                 // 0x0000 (size: 0x10)
    class UDecalDef* Decal;                                                           // 0x0010 (size: 0x8)

}; // Size: 0x40

class UTimeTrialConfig : public UGfnRaceEventModeConfig
{
    uint8 bUseCustomVehicle : 1;                                                      // 0x0030 (size: 0x1)
    FCustomVehicleSetup CustomVehicle;                                                // 0x0038 (size: 0x48)

}; // Size: 0x80

class UArcadeEventDef : public UPrimaryDataAsset
{
    class UTrackDef* TrackDef;                                                        // 0x0040 (size: 0x8)
    int32 LapCount;                                                                   // 0x0048 (size: 0x4)

}; // Size: 0x60

class UPlanetEnvironmentDef : public UPrimaryDataAsset
{
    float TimeOfDay;                                                                  // 0x0030 (size: 0x4)
    FGameplayTag WeatherPreset;                                                       // 0x0034 (size: 0x8)
    int32 Unrelated;                                                                  // 0x003C (size: 0x4)

}; // Size: 0x40

class AGfnVehiclePawn : public APawn
{
    class USkeletalMeshComponent* BodyMesh;                                           // 0x0300 (size: 0x8)
    class UStaticMesh* PodiumTrophy;                                                  // 0x0308 (size: 0x8)
    float TopSpeed;                                                                   // 0x0310 (size: 0x4)

    void ApplyVehicleVisual(class UVehicleVisualDef* Visual);
    void SetPodVariant(int32 Index);
    void Boost();
}; // Size: 0x320
""", encoding="utf-8")
# Modules du moteur : leur IA ne doit pas noyer le rapport
(dump / "AIModule.hpp").write_text("""class AAIController : public AController
{
    class UAIPerceptionComponent* PerceptionComponent;                                // 0x0300 (size: 0x8)

}; // Size: 0x320
""", encoding="utf-8")
(dump / "Engine.hpp").write_text("""class APawn : public AActor
{
    TSubclassOf<class AController> AIControllerClass;                                 // 0x0298 (size: 0x8)

}; // Size: 0x2C0
""", encoding="utf-8")
(dump / "OnlineStuff.hpp").write_text("""class UOnlineStuff : public UObject
{
    int32 SkillLevel;                                                                 // 0x0028 (size: 0x4)

}; // Size: 0x30
""", encoding="utf-8")

echecs = []


def ok(nom, cond):
    print(("  [OK]    " if cond else "  [ÉCHEC] ") + nom)
    if not cond:
        echecs.append(nom)


def lancer(*args):
    r = subprocess.run([sys.executable, str(OUTIL), *args], capture_output=True, text=True, encoding="utf-8", env=ENV)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
    return r.stdout


print("1. Modes proprietes et enums")
sortie = lancer("proprietes", "aggress", str(dump))
ok("propriété trouvée avec sa classe", "FAIState::FDataTableRowHandle RacerAggressionLevel;" in sortie)
ok("une fonction n'est pas une propriété", "SetAggression" not in sortie)
sortie = lancer("enums", "difficulty", str(dump))
ok("énumération avec ses valeurs", "enum EAIDifficulty" in sortie and "Hard = 2" in sortie)

print("2. Rapport ia")
sortie = lancer("ia", str(dump))
fichier = tmp / "1-menu" / "rapport-ia.txt"
ok("rapport écrit à côté du dump", fichier.exists())
texte = fichier.read_text(encoding="utf-8") if fichier.exists() else ""
ok("affiché aussi dans la console", "RAPPORT IA" in sortie)
ok("énumération de difficulté", "enum EAIDifficulty { Easy = 0, Normal = 1, Hard = 2, EAIDifficulty_MAX = 3, }" in texte)
ok("énumération sans rapport absente (Surface n'est pas Ace)", "ESurfaceType" not in texte)
ok("énumération des 4 difficultés trouvée par ses valeurs", "enum EGfnRacerRank" in texte and "EGfnRacerRank__Champion = 3" in texte)
ok("propriété de ce type trouvée", "UGfnCampaignSubsystem::EGfnRacerRank SelectedRank;" in texte)
ok("fonction avec un paramètre de ce type trouvée", "UGfnCampaignSubsystem::void SetRank(EGfnRacerRank NewRank);" in texte)
ok("le reste de la classe n'est pas listé", "RaceCount" not in texte and "Reset()" not in texte)
ok("struct AIState en entier", "struct FAIState {" in texte and "GameModePacingConfigs" in texte)
ok("contrôleur d'IA du jeu en entier (avec sa fonction)", "class AGfnAIController : public AAIController" in texte
   and "void SetAggression(int32 Level);" in texte)
ok("classe utile en entier (GameModeVariantDef)", "class UGameModeVariantDef" in texte and "float SomethingElse;" in texte)
ok("propriété « AI » du jeu", "AGfnPlayerState::uint8 bIsAIControlled : 1;" in texte)
ok("fonction de difficulté du jeu", "AGfnPlayerState::void SetDifficulty(EAIDifficulty NewDifficulty);" in texte)
ok("mot précis trouvé aussi hors du jeu (SkillLevel)", "UOnlineStuff::int32 SkillLevel;" in texte)
ok("pas de bruit : Spacing, Workspace, IA du moteur",
   all(x not in texte for x in ("Spacing", "Workspace", "PerceptionComponent", "AIControllerClass",
                                "class AAIController")))
ok("pas de bruit : fonction Unrelated (seul un paramètre s'appelle Pace)", "Unrelated" not in texte)

print("3. Rapport ia-suite : types clés et qui les tient")
sortie = lancer("ia-suite", str(dump))
fichier = tmp / "1-menu" / "rapport-ia-suite.txt"
ok("rapport écrit à côté du dump", fichier.exists())
texte = fichier.read_text(encoding="utf-8") if fichier.exists() else ""
ok("énumérations clés", "enum ERacerArchetype { Ace = 0," in texte and "enum ERaceEventModeType" in texte)
ok("autres énumérations absentes", "EGfnRacerRank" not in texte and "ESurfaceType" not in texte)
ok("types clés en entier", "struct FRacerArchetypeDistribution {" in texte and "class UPvpInstantActionDef" in texte
   and "FRacerArchetypeDistribution ArchetypeDistribution;" in texte)
ok("qui les tient : la GameInstance", "UGfnGameInstance::TArray<UCampaignDifficultyDef*> CampaignDifficulties;" in texte
   and "UGfnGameInstance::class UArchetypeConfigCollection* ArchetypeConfigs;" in texte)
ok("propriétés sans type clé absentes", "OtherValue" not in texte)
ok("FPvpRunRacerProgression n'est pas FPvpRunRacer", "Progressions" not in texte)
ok("fonction qui reçoit un type clé", "UGfnGameInstance::void SetArchetypeOverride(ERacerArchetype NewArchetype);" in texte)
ok("fonction sans type clé absente", "UnrelatedFunction" not in texte)

print("4. Rapport ia-tune : où sont lus les réglages des IA")
lancer("ia-tune", str(dump))
fichier = tmp / "1-menu" / "rapport-ia-tune.txt"
texte = fichier.read_text(encoding="utf-8") if fichier.exists() else ""
ok("rapport écrit", fichier.exists())
ok("composant et config en entier", "class UGameTuneComponent" in texte and "FGameTuneConfig CurrentConfig;" in texte
   and "struct FGameTuneConfig {" in texte)
ok("classe du jeu dont le nom contient Tune, en entier", "class UTuneSetPassiveEffectConfig" in texte)
ok("qui tient le composant : le contrôleur d'IA", "ADrivingAIController::class UGameTuneComponent* GameTuneComponent;" in texte)
ok("fonction qui reçoit un TuneSet", "UGfnGameInstance::void ApplyTuneSet(class UTuneSet* TuneSet);" in texte)
ok("rien d'autre de la GameInstance", "CampaignDifficulties" not in texte and "UnrelatedFunction" not in texte)

print("5. Rapport apparence : d'où vient l'apparence d'un pod, décor d'une épreuve")
lancer("apparence", str(dump))
fichier = tmp / "1-menu" / "rapport-apparence.txt"
texte = fichier.read_text(encoding="utf-8") if fichier.exists() else ""
ok("rapport écrit", fichier.exists() and "RAPPORT APPARENCE" in texte)
ok("types clés en entier (build, pilote, épreuve, mode contre-la-montre)",
   all(x in texte for x in ("class UVehicleBuildDef", "TSoftObjectPtr<UVehicleVisualDef> VisualOverride;",
                            "class UCharacterDef", "class UArcadeEventDef", "class UTimeTrialConfig")))
ok("le véhicule imposé de l'épreuve suivi sur 2 niveaux", "struct FCustomVehicleSetup {" in texte
   and "struct FVehicleCustomizationData {" in texte and "TArray<FLinearColor> PaintColors;" in texte)
ok("apparence ailleurs dans le jeu (mesh du véhicule)", "AGfnVehiclePawn::class USkeletalMeshComponent* BodyMesh;" in texte)
ok("pas « Podium » ni la vitesse", "PodiumTrophy" not in texte and "TopSpeed" not in texte)
ok("décor : heure et météo d'une planète", "UPlanetEnvironmentDef::float TimeOfDay;" in texte
   and "UPlanetEnvironmentDef::FGameplayTag WeatherPreset;" in texte and "Unrelated;" not in texte)
ok("fonctions d'apparence (Visual, Pod), pas Boost", "AGfnVehiclePawn::void ApplyVehicleVisual(class UVehicleVisualDef* Visual);"
   in texte and "AGfnVehiclePawn::void SetPodVariant(int32 Index);" in texte and "Boost()" not in texte)
ok("pas de doublon : un type affiché en entier n'est pas relisté", "UCharacterDef::" not in texte)
sortie = lancer("ia", str(dump))
ok("les nouveaux faux types ne gênent pas le rapport ia", "VehicleVisual" not in (tmp / "1-menu" / "rapport-ia.txt")
   .read_text(encoding="utf-8"))

print("6. Dossier absent : message clair")
r = subprocess.run([sys.executable, str(OUTIL), "ia", str(tmp / "absent")], capture_output=True, text=True, encoding="utf-8", env=ENV)
ok("code d'erreur et message", r.returncode == 1 and "introuvable" in r.stdout)

if echecs:
    print(f"\n{len(echecs)} ÉCHEC(S)")
    sys.exit(1)
print("\nTOUS LES TESTS SONT PASSÉS")
