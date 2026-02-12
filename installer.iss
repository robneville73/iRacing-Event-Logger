; Inno Setup script for iRacing Event Logger
; Build with: iscc installer.iss
; Prerequisites: Run pyinstaller event_logger.spec first to produce dist\iRacingEventLogger.exe

#define MyAppName "iRacing Event Logger"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "iRacing Event Logger"
#define MyAppURL "https://github.com/"
#define MyAppExeName "iRacingEventLogger.exe"

[Setup]
AppId={{B2C4D6E8-F0A2-4B6C-8E1D-3F5A7B9C0E2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=iRacingEventLogger-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "iRacing Event Logger - log session events by lap"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Code]
var
  ConfigPage: TInputQueryWizardPage;
  FocusPage: TInputOptionWizardPage;
  TelemetryPage: TInputOptionWizardPage;

procedure InitializeWizard;
begin
  { Config page: focus type (car vs driver) }
  FocusPage := CreateInputOptionPage(wpWelcome,
    'Focus Settings',
    'How should the logger focus on a car or driver?',
    'Select whether to focus by car number or driver name, then enter the value.',
    True, False);
  FocusPage.Add('Focus by &car number');
  FocusPage.Add('Focus by &driver name');
  FocusPage.SelectedValueIndex := 0;

  { Config page: input fields }
  ConfigPage := CreateInputQueryPage(FocusPage.ID,
    'Configuration',
    'Configure the event logger',
    'Enter the settings below. At least one of Car number or Driver name must be set.');
  ConfigPage.Add('Car number (e.g. 5):', False);
  ConfigPage.Add('Driver name (UserName or AbbrevName):', False);
  ConfigPage.Add('Log file name:', False);
  ConfigPage.Add('Battle gap (seconds, for close_battle):', False);
  ConfigPage.Values[0] := '5';
  ConfigPage.Values[1] := '';
  ConfigPage.Values[2] := 'event_log.json';
  ConfigPage.Values[3] := '1.5';

  { Telemetry option }
  TelemetryPage := CreateInputOptionPage(ConfigPage.ID,
    'Telemetry',
    'Start iRacing telemetry recording when the logger connects?',
    'Check the box below to automatically start telemetry recording on connect.',
    False, False);
  TelemetryPage.Add('&Start telemetry recording when the logger connects');
  TelemetryPage.Values[0] := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  FocusCar, FocusDriver: String;
begin
  Result := True;
  if CurPageID = ConfigPage.ID then
  begin
    FocusCar := Trim(ConfigPage.Values[0]);
    FocusDriver := Trim(ConfigPage.Values[1]);
    if (FocusCar = '') and (FocusDriver = '') then
    begin
      MsgBox('Please enter either a car number or driver name.', mbError, MB_OK);
      Result := False;
    end
    else if (FocusPage.SelectedValueIndex = 0) and (FocusCar = '') then
    begin
      MsgBox('Please enter a car number when focusing by car.', mbError, MB_OK);
      Result := False;
    end
    else if (FocusPage.SelectedValueIndex = 1) and (FocusDriver = '') then
    begin
      MsgBox('Please enter a driver name when focusing by driver.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigDir, ConfigPath, ConfigContent, UserProfile: String;
  FocusCar, FocusDriver, LogFile, BattleGap: String;
  FocusByCar, StartTelemetryCheck: Boolean;
begin
  if CurStep = ssPostInstall then
  begin
    FocusByCar := FocusPage.SelectedValueIndex = 0;
    FocusCar := Trim(ConfigPage.Values[0]);
    FocusDriver := Trim(ConfigPage.Values[1]);
    LogFile := Trim(ConfigPage.Values[2]);
    if LogFile = '' then LogFile := 'event_log.json';
    BattleGap := Trim(ConfigPage.Values[3]);
    if BattleGap = '' then BattleGap := '1.5';
    StartTelemetryCheck := TelemetryPage.Values[0];

    UserProfile := GetEnv('USERPROFILE');
    if UserProfile = '' then
      UserProfile := ExtractFileDir(ExtractFileDir(ExpandConstant('{userappdata}')));
    ConfigDir := UserProfile + '\.config\iracing-event-logger';
    ConfigPath := ConfigDir + '\config.yaml';

    if not ForceDirectories(ConfigDir) then
    begin
      MsgBox('Could not create config directory: ' + ConfigDir, mbError, MB_OK);
      Exit;
    end;

    StringChangeEx(FocusCar, '\', '\\', True);
    StringChangeEx(FocusDriver, '\', '\\', True);
    StringChangeEx(LogFile, '\', '\\', True);

    ConfigContent := '# iRacing Event Logger config (written by installer)' + #13#10;
    if FocusByCar and (Trim(ConfigPage.Values[0]) <> '') then
      ConfigContent := ConfigContent + 'focus_car: "' + FocusCar + '"' + #13#10
    else if Trim(ConfigPage.Values[1]) <> '' then
      ConfigContent := ConfigContent + 'focus_driver: "' + FocusDriver + '"' + #13#10;
    if not FocusByCar and (Trim(ConfigPage.Values[0]) <> '') then
      ConfigContent := ConfigContent + '# focus_car: "' + FocusCar + '"' + #13#10;
    if FocusByCar and (Trim(ConfigPage.Values[1]) <> '') then
      ConfigContent := ConfigContent + '# focus_driver: "' + FocusDriver + '"' + #13#10;

    ConfigContent := ConfigContent + 'log_file: "' + LogFile + '"' + #13#10;
    ConfigContent := ConfigContent + 'battle_gap_s: ' + BattleGap + #13#10;
    if StartTelemetryCheck then
      ConfigContent := ConfigContent + 'start_telemetry: true' + #13#10
    else
      ConfigContent := ConfigContent + 'start_telemetry: false' + #13#10;

    SaveStringToFile(ConfigPath, ConfigContent, False);
  end;
end;
