#define MyAppName "简言"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "LHQ"
#define MyAppExeName "Jianyan.exe"
#define SourcePath "dist"

[Setup]
AppId={{C6B5C7F8-1F6D-4D37-9D72-29D2C89D0D7D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Jianyan
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=AudioToTextSetup
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
InfoBeforeFile=info_before.txt

[Languages]
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面图标"; GroupDescription: "附加任务"; Flags: unchecked

[Dirs]
Name: "{app}\models"; Permissions: users-modify
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\temp"; Permissions: users-modify

[Files]
Source: "{#SourcePath}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\models\*"; DestDir: "{app}\models"; Flags: recursesubdirs createallsubdirs
Source: "..\scripts\predownload_models.py"; DestDir: "{app}\scripts"; Flags: ignoreversion


[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]


function IsSystemProtectedDir(Path: string): Boolean;
var
  lowerPath: string;
begin
  lowerPath := Lowercase(Path);
  Result := (Pos(':\\windows', lowerPath) = 2) or
            (Pos(':\\program files', lowerPath) = 2) or
            (Pos(':\\program files (x86)', lowerPath) = 2);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    if IsSystemProtectedDir(WizardForm.DirEdit.Text) then
    begin
      MsgBox('请不要安装到系统保护目录（如 C:\\Program Files）。建议选择普通可写目录，例如 D:\\Apps 或 D:\\Tools。', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

