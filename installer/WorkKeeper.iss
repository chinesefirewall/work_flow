; installer/WorkKeeper.iss
; Inno Setup script for WorkKeeper
; Build on Windows (locally or in CI). Requires: Inno Setup 6+

#define MyAppName       "WorkKeeper"
#define MyAppVersion    GetEnv("APP_VERSION") != "" ? GetEnv("APP_VERSION") : "1.0.0"
#define MyAppPublisher  "Your Company or Name"
#define MyAppURL        "https://github.com/<your-org-or-user>/<your-repo>"
#define MyExeName       "WorkKeeper.exe"

; IMPORTANT: Generate your own GUID once and never change it (keeps upgrades smooth):
; In Inno Setup: Tools -> Generate GUID -> paste below.
#define MyAppId         "{{7F2A8D4A-9E64-4B10-9C8C-0F5E19A8C0AB}}"

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
OutputDir=installer\output
OutputBaseFilename=WorkKeeper-Setup-{#MyAppVersion}
ArchitecturesInstallIn64BitMode=x64
; Optional: show EULA if you have one
; LicenseFile=..\LICENSE

; (Optional) Code signing (if you have a cert). Otherwise remove these:
; SignTool=msbuild
; SignToolRetryCount=2

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Source exe produced by PyInstaller
Source: "..\dist\{#MyExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Optional: include README or quickstart PDF
; Source: "..\README_quickstart.pdf"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyExeName}"
; Desktop (optional task)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyExeName}"; Tasks: desktopicon

[Run]
; Offer to run app at the end of installation
Filename: "{app}\{#MyExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Example: clean up logs or cache (if you create any)
; Type: filesandordirs; Name: "{localappdata}\WorkKeeper"
