$ErrorActionPreference = 'Continue'
$labRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $labRoot
$logRoot = Join-Path $labRoot 'evidence\logs'
$imageRoot = Join-Path $labRoot 'static\evidence'
New-Item -ItemType Directory -Force -Path $logRoot, $imageRoot | Out-Null

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class Buoi6EvidenceWindow {
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr handle, int command);
}
'@

$checks = @(
  @{ title = 'Node.js version'; command = 'node --version' },
  @{ title = 'npm version'; command = 'npm.cmd --version' },
  @{ title = 'Git version'; command = 'git --version' },
  @{ title = 'Project scripts and runtime'; command = 'node scripts\evidence-check.mjs package' },
  @{ title = 'First GitLab job'; command = 'type examples\first.gitlab-ci.yml' },
  @{ title = 'Four job pipeline'; command = 'type examples\basic.gitlab-ci.yml' },
  @{ title = 'Pipeline tests'; command = 'node --test tests\pipeline.test.mjs' },
  @{ title = 'Documentation tests'; command = 'node --test tests\content.test.mjs' },
  @{ title = 'Complete unit test suite'; command = 'npm.cmd test' },
  @{ title = 'Security policy gate'; command = 'npm.cmd run security' },
  @{ title = 'GitLab YAML parse'; command = 'node scripts\evidence-check.mjs gitlab-yaml' },
  @{ title = 'npm dependency audit'; command = 'npm.cmd run audit' },
  @{ title = 'Docusaurus production build'; command = 'npm.cmd run build' },
  @{ title = 'Generated static files'; command = 'node scripts\evidence-check.mjs build-files' },
  @{ title = 'Build SHA-256 manifest'; command = 'npm.cmd run checksums' },
  @{ title = 'Local preview HTTP response'; command = 'node scripts\evidence-check.mjs http' },
  @{ title = 'Manifest contents'; command = 'node scripts\evidence-check.mjs manifest' },
  @{ title = 'Default branch deploy rule'; command = 'node scripts\evidence-check.mjs deploy-rule' },
  @{ title = 'Responsive breakpoints'; command = 'node scripts\evidence-check.mjs responsive' },
  @{ title = 'Git whitespace and working tree'; command = "git -C `"$repoRoot`" diff --check `& git -C `"$repoRoot`" status --short" }
)

$shell = New-Object -ComObject WScript.Shell
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
Push-Location $labRoot
try {
  for ($index = 0; $index -lt $checks.Count; $index++) {
    $number = '{0:D2}' -f ($index + 1)
    $check = $checks[$index]
    $runCommand = $check.command
    if ($index -eq 9) { $runCommand = 'node scripts\evidence-check.mjs deploy-rule' }
    $commandOutput = @(& $env:ComSpec /d /c $runCommand 2>&1 | ForEach-Object { [string]$_ })
    $exitCode = $LASTEXITCODE
    $report = New-Object 'System.Collections.Generic.List[string]'
    [void]$report.Add('Student: Nguyen Phuc Thinh | Student ID: 2387700066')
    [void]$report.Add("CMD: $runCommand")
    [void]$report.Add("Completed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')")
    [void]$report.Add("Exit code: $exitCode")
    [void]$report.Add('')
    foreach ($line in $commandOutput) {
      foreach ($part in ([string]$line -split "`r`n|`n|`r")) {
        [void]$report.Add($part)
      }
    }
    $logPath = Join-Path $logRoot "${number}-cmd.txt"
    [System.IO.File]::WriteAllLines($logPath, $report.ToArray(), [System.Text.UTF8Encoding]::new($false))

    $relativeLog = "evidence\logs\${number}-cmd.txt"
    $windowTitle = "BUOI6 $number - $($check.title)"
    $display = "chcp 65001>nul & mode con: cols=140 lines=46 & title $windowTitle & type `"$relativeLog`" & echo. & pause"
    $process = Start-Process -FilePath $env:ComSpec -ArgumentList '/k', $display -WorkingDirectory $labRoot -PassThru
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
      $process.Refresh()
      if ($process.MainWindowHandle -ne [IntPtr]::Zero) { break }
      Start-Sleep -Milliseconds 150
    }
    [void]$shell.AppActivate($process.Id)
    [void][Buoi6EvidenceWindow]::ShowWindow($process.MainWindowHandle, 3)
    Start-Sleep -Milliseconds 500

    $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
    $bitmap.Save((Join-Path $imageRoot "${number}-cmd.png"), [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Captured $number/20 - $($check.title) (exit $exitCode)"
  }
}
finally {
  Pop-Location
}

function Update-EvidenceManifest {
  $hashes = Get-ChildItem -LiteralPath $imageRoot -Filter '*-cmd.png' -File | Sort-Object Name | ForEach-Object {
    [PSCustomObject]@{ file = $_.Name; sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
  }
  $manifest = [PSCustomObject]@{ algorithm = 'SHA-256'; imageCount = @($hashes).Count; images = @($hashes) }
  $manifestJson = ($manifest | ConvertTo-Json -Depth 5) -replace "`r`n", "`n"
  [System.IO.File]::WriteAllText((Join-Path $labRoot 'evidence\sha256.json'), $manifestJson, [System.Text.UTF8Encoding]::new($false))
}

Update-EvidenceManifest
$securityCommand = 'npm.cmd run security'
$securityOutput = @(& $env:ComSpec /d /c $securityCommand 2>&1 | ForEach-Object { [string]$_ })
$securityExitCode = $LASTEXITCODE
$securityReport = New-Object 'System.Collections.Generic.List[string]'
[void]$securityReport.Add('Student: Nguyen Phuc Thinh | Student ID: 2387700066')
[void]$securityReport.Add("CMD: $securityCommand")
[void]$securityReport.Add("Completed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')")
[void]$securityReport.Add("Exit code: $securityExitCode")
[void]$securityReport.Add('')
foreach ($line in $securityOutput) {
  foreach ($part in ([string]$line -split "`r`n|`n|`r")) { [void]$securityReport.Add($part) }
}
$securityLog = Join-Path $logRoot '10-cmd.txt'
[System.IO.File]::WriteAllLines($securityLog, $securityReport.ToArray(), [System.Text.UTF8Encoding]::new($false))

$securityDisplay = 'evidence\logs\10-cmd.txt'
$securityTitle = 'BUOI6 10 - Security policy gate'
$securityWindow = "chcp 65001>nul & mode con: cols=140 lines=46 & title $securityTitle & type `"$securityDisplay`" & echo. & pause"
$securityProcess = Start-Process -FilePath $env:ComSpec -ArgumentList '/k', $securityWindow -WorkingDirectory $labRoot -PassThru
for ($attempt = 0; $attempt -lt 20; $attempt++) {
  $securityProcess.Refresh()
  if ($securityProcess.MainWindowHandle -ne [IntPtr]::Zero) { break }
  Start-Sleep -Milliseconds 150
}
[void]$shell.AppActivate($securityProcess.Id)
[void][Buoi6EvidenceWindow]::ShowWindow($securityProcess.MainWindowHandle, 3)
Start-Sleep -Milliseconds 500
$securityBitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$securityGraphics = [System.Drawing.Graphics]::FromImage($securityBitmap)
$securityGraphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$securityBitmap.Save((Join-Path $imageRoot '10-cmd.png'), [System.Drawing.Imaging.ImageFormat]::Png)
$securityGraphics.Dispose()
$securityBitmap.Dispose()
Stop-Process -Id $securityProcess.Id -Force -ErrorAction SilentlyContinue

Update-EvidenceManifest
$finalOutput = @(& $env:ComSpec /d /c 'npm.cmd run security' 2>&1 | ForEach-Object { [string]$_ })
if ($LASTEXITCODE -ne 0) {
  $finalOutput | ForEach-Object { Write-Error $_ }
  throw 'Final screenshot evidence verification failed.'
}
Write-Host "Saved 20 CMD screenshots to $imageRoot and command logs to $logRoot"
Write-Host 'Wrote evidence/sha256.json'
