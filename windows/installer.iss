; Inno Setup Script for Burmese Audio Deduper & Myanglish Cleaner (Windows x64)

#define MyAppName "Burmese Audio Deduper & Myanglish Cleaner"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Kyaw Zin Latt"
#define MyAppURL "https://github.com"
#define MyAppExeName "Launch-WebGUI.bat"

[Setup]
AppId={{D9B38A5C-F51C-4B9F-8409-7D8E253018E1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\BurmeseMusicCleaner
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=..\dist-installer
OutputBaseFilename=BurmeseMusicCleaner-Setup-x64
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Dist folder contents
Source: "..\package-windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{sys}\shell32.dll"; IconIndex: 224
Name: "{group}\CLI Tool"; Filename: "{app}\bin\burmese-music-cleaner-cli.exe"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{sys}\shell32.dll"; IconIndex: 224

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: shellexec postinstall nowait skipifsilent
