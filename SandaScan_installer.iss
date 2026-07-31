; SandaScan — Inno Setup Installer Script
; Creates a standalone Windows installer (.exe)
;
; PREREQUISITES:
;   1. Build the .exe:
;      pyinstaller --onefile --windowed --name "SandaScan.exe" ^
;        --icon "SandaScan\assets\sandascan_app_icon.ico" ^
;        --add-data "SandaScan\core;SandaScan\core" ^
;        --add-data "SandaScan\gui;SandaScan\gui" ^
;        --add-data "SandaScan\assets;SandaScan\assets" ^
;        --hidden-import PIL._tkinter_finder ^
;        run.py
;
;      This creates: dist\SandaScan.exe  (single file with icon)
;
;   2. Download Inno Setup from: https://jrsoftware.org/isdl.php
;   3. Right-click this file -> Compile
;
;    Output: installer\SandaScan_v1.0.1_Setup.exe
; ---------------------------------------------------------------

#define MyAppName "SandaScan"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "SandaApps"
#define MyAppURL "https://davidsanda.com/sandascan"
#define MyAppExeName "SandaScan.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=installer
OutputBaseFilename=SandaScan_v{#MyAppVersion}_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64compatible
; Use the SandaScan icon for the installer itself
SetupIconFile=SandaScan\assets\sandascan_app_icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; The main application (single-file .exe from PyInstaller --onefile with .ico)
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; License and readme
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Tesseract OCR is NOT bundled.
; Install from: https://github.com/UB-Mannheim/tesseract/wiki

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Messages]
WelcomeLabel2=This will install [name] on your computer.%n%nSandaScan transforms phone photos of documents into scanner-quality, OCR-ready, searchable PDFs — completely offline.

[CustomMessages]
LaunchProgramAfterInstall=Launch SandaScan after installation
