#ifndef PayloadDir
  #error PayloadDir must point to the prepared portable bundle
#endif
#ifndef ReleaseDir
  #define ReleaseDir "..\releases"
#endif
#define AppVersion "0.2.0"

[Setup]
AppId={{281D09F9-E910-47CC-A54D-26F3134C432F}
AppName=Claus
AppVersion={#AppVersion}
AppPublisher=Claus
DefaultDirName={localappdata}\Programs\Claus
DefaultGroupName=Claus
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
DisableProgramGroupPage=yes
OutputDir={#ReleaseDir}
OutputBaseFilename=Claus-Setup-{#AppVersion}-win-x64
SetupIconFile={#PayloadDir}\transcritor-local\assets\brand\claus.ico
UninstallDisplayIcon={app}\Claus.exe
WizardStyle=modern dark includetitlebar
WizardBackColor=#090909
Compression=lzma2/fast
SolidCompression=yes
LZMANumBlockThreads=2
CloseApplications=yes
RestartApplications=no
AppMutex=Local\ClausDitadoDesktop
UninstallDisplayName=Claus
VersionInfoDescription=Instalador do Claus
VersionInfoProductName=Claus

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "{#PayloadDir}\Claus.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\transcritor-local\*"; DestDir: "{app}\transcritor-local"; Excludes: "desktop-settings.ini,*.obj,*.pdb"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\transcritor-local\.tmp"

[Icons]
Name: "{userprograms}\Claus"; Filename: "{app}\Claus.exe"; WorkingDir: "{app}"; IconFilename: "{app}\transcritor-local\assets\brand\claus.ico"; AppUserModelID: "Claus.Ditado.Local"
Name: "{userdesktop}\Claus"; Filename: "{app}\Claus.exe"; WorkingDir: "{app}"; IconFilename: "{app}\transcritor-local\assets\brand\claus.ico"; AppUserModelID: "Claus.Ditado.Local"; Tasks: desktopicon

[Run]
Filename: "{app}\Claus.exe"; Description: "Abrir o Claus"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  BaseDir, VenvConfig, Preferences: String;
begin
  if CurStep = ssPostInstall then begin
    BaseDir := ExpandConstant('{app}\transcritor-local\.python\cpython-3.12.14-windows-x86_64-none');
    VenvConfig := 'home = ' + BaseDir + #13#10 +
      'include-system-site-packages = false' + #13#10 +
      'version = 3.12.14' + #13#10 +
      'executable = ' + BaseDir + '\python.exe' + #13#10;
    if not SaveStringToFile(ExpandConstant('{app}\transcritor-local\.venv\pyvenv.cfg'), Utf8Encode(VenvConfig), False) then
      RaiseException('Não foi possível configurar o Python do Claus.');
    Preferences := ExpandConstant('{app}\transcritor-local\desktop-settings.ini');
    if not FileExists(Preferences) then
      SaveStringToFile(Preferences, '[General]' + #13#10 + 'backend=small' + #13#10 + 'wake_phrase=computador' + #13#10, False);
  end;
end;
