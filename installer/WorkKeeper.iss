; installer/WorkKeeper.iss
; Inno Setup script for WorkKeeper
; Build on Windows (locally or in CI). Requires: Inno Setup 6+

#define MyAppName       "WorkKeeper"
#define MyAppVersion    GetEnv("APP_VERSION") != "" ? GetEnv("APP_VERSION") : "1.0.0"
#define MyAppPublisher  "Niyi Adebayo"
#define MyAppURL        "https://github.com/chinesefirewall/work_flow"
#define MyExeName       "WorkKeeper.exe"

; IMPORTANT: Generate your own GUID once and never change it (keeps upgrades smooth)
; In Inno Setup: Tools -> Generate GUID -> paste below WITHOUT braces for Option A:
#define MyAppId "7F2A8D4A-9E64-4B10-9C8C-0F5E19A8C0AB"

[Setup]
AppId={{#MyAppId}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=yes
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#MyExeName}
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
; Make output path robust: put under installer\output next to this .iss
OutputDir={#SourcePath}\output
OutputBaseFilename=WorkKeeper-Setup-{#MyAppVersion}
ArchitecturesInstallIn64BitMode=x64
; Optional: EULA
; LicenseFile={#SourcePath}\..\LICENSE

; (Optional) Code signing (remove if not used)
; SignTool=msbuild
; SignToolRetryCount=2

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Source exe produced by PyInstaller. Path robust to script location.
Source: "{#SourcePath}\..\dist\{#MyExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Optional: include README/Quick Start
; Source: "{#SourcePath}\..\README_quickstart.pdf"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyExeName}"
; Desktop (optional task)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyExeName}"; Tasks: desktopicon

[Run]
; Offer to run app at the end of installation
Filename: "{app}\{#MyExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Example: clean up logs or cache (only if you create them)
; Type: filesandordirs; Name: "{localappdata}\WorkKeeper"
