; ============================================================
; KID ACID'S MUSIC VAULT
; COMMERCIAL WINDOWS INSTALLER
; Version 1.0.0
; ============================================================

#define AppName "Kid Acid's Music Vault"
#define AppVersion "1.0.0"
#define AppPublisher "Kid Acid's Music Vault"
#define AppExeName "KidAcidsMusicVault.exe"
#define BuildDir "..\dist\KidAcidsMusicVault"

[Setup]
AppId={{D7A1D2B9-5E18-4C7E-9D61-6E9C1E9A1001}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\Kid Acid's Music Vault
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\release
OutputBaseFilename=KidAcidsMusicVault-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName}

; Do not ship the developer's personal database or backups.
; The application creates/uses its own data directory at runtime.

[Files]
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "data\vinylvault.db,data\backup\*,data\backups\*,data\*.db"

[Dirs]
Name: "{app}\data"

[Icons]
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Comment: "{#AppName}"
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Start {#AppName}"; Flags: nowait postinstall skipifsilent
