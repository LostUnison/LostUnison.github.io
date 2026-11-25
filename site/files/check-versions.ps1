<#
.SYNOPSIS
  Compare the Project Reforged patches in this folder with the official Downloads page.

.DESCRIPTION
  1. Read the versions you have now from the table in README.md (same folder).
  2. Read the current versions from https://projectreforged.github.io/wotlk/downloads/
  3. Show one line per patch: OK, UPDATE, MISSING FILE or NEW ON SITE.
  4. Compare the size of each local .mpq file with the size of the file on the server.
     The patch files are searched in all subfolders (for example the folder "HD patches").
  5. Compare the tools in the "Tools" table of README.md with the latest GitHub release:
     St0ny AIO EXE Patcher, DXVK, LuxVelum, Lexara and the lights shader patch.
  6. Check that the tool files exist in your subfolders (Required, Recommended and so on).
  The script does not download or change any patch or tool file.

.PARAMETER UpdateReadme
  After you updated, write the latest versions (patches and tools) into the README.md tables.

.PARAMETER NoToolCheck
  Skip the check of the tools (St0ny patcher, DXVK, LuxVelum, Lexara, lights shader) on GitHub.

.PARAMETER NoSizeCheck
  Skip the size check (no request to the file server).

.EXAMPLE
  .\check-versions.ps1
  .\check-versions.ps1 -UpdateReadme
#>
param(
    [switch]$UpdateReadme,
    [switch]$NoSizeCheck,
    [switch]$NoToolCheck
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Url      = 'https://projectreforged.github.io/wotlk/downloads/'
$Folder   = $PSScriptRoot
if (-not $Folder) { $Folder = Split-Path -Parent $MyInvocation.MyCommand.Path }
$Readme   = Join-Path $Folder 'README.md'

# Index of every file and folder under this folder, subfolders included (one scan).
$All = @(Get-ChildItem -Path $Folder -Recurse -Force -ErrorAction SilentlyContinue)

# Find an item by name in any subfolder. Use 'a|b' for alternative names. -Dir looks for a folder.
function Find-Local([string]$Names, [switch]$Dir) {
    foreach ($n in $Names.Split('|')) {
        $hit = $All | Where-Object { $_.PSIsContainer -eq [bool]$Dir -and $_.Name -ieq $n } | Select-Object -First 1
        if ($hit) { return $hit }
    }
    return $null
}

function Get-RelPath([string]$Full) {
    if ($Full.StartsWith($Folder, [StringComparison]::OrdinalIgnoreCase)) { return $Full.Substring($Folder.Length).TrimStart('\') }
    return $Full
}

function Convert-ToVersion([string]$Text) {
    if ($Text -match '(\d+(?:\.\d+){0,3})') {
        $v = $Matches[1]
        if ($v -notmatch '\.') { $v = $v + '.0' }
        return [version]$v
    }
    return $null
}

function Get-RemoteSize([string]$Link) {
    try {
        $r = Invoke-WebRequest -Uri $Link -Method Head -UseBasicParsing -TimeoutSec 30
        $v = @($r.Headers['Content-Length'])[0]
        if ($v) { return [int64]$v }
    } catch { }
    return $null
}

function Format-Size([int64]$Bytes) {
    if ($Bytes -ge 1GB) { return ('{0:N2} GB' -f ($Bytes / 1GB)) }
    if ($Bytes -ge 1MB) { return ('{0:N1} MB' -f ($Bytes / 1MB)) }
    return ('{0:N0} KB' -f ($Bytes / 1KB))
}

# ---------- 1. Local versions (README.md) ----------
if (-not (Test-Path $Readme)) {
    $template = @'
# Patch HD - Project Reforged (WoW 3.3.5a)

Write the version of each file you have in the Version column. Leave it empty if you do not know.
Run check-versions.bat again after you edit this file.

| File | Content | Version | Type | Size |
|---|---|---|---|---|
| patch-A.mpq | Player characters and NPCs (HD) | | Core | |
| patch-B.mpq | Buildings | | B + D + E set | |
| patch-C.mpq | Creatures | | Core | |
| patch-D.mpq | Doodads | | B + D + E set | |
| patch-E.mpq | Environment | | B + D + E set | |
| patch-G.mpq | Gear and weapons | | Core | |
| patch-I.mpq | Interface | | Core | |
| patch-M.mpq | Maps and loading screens | | Optional | |
| patch-N.mpq | Darker nights | | Optional | |
| patch-P.mpq | Spell particle effects | | Optional | |
| patch-S.mpq | Sounds and music | | Optional | |
| patch-U.mpq | Upright orcs | | Optional | |

## Tools

| Tool | Version | Source |
|---|---|---|
| St0ny AIO EXE Patcher | | https://github.com/Raz0r1337/St0nys-AIO-WoW-EXE-Patcher/releases |
| DXVK | | https://github.com/Raz0r1337/DXVK/releases |
| LuxVelum | | https://github.com/Stormhand-dev/Luxvelum/releases |
| Lexara | | https://github.com/Stormhand-dev/Lexara---HD-Font-Renderer-for-WoW-3.3.5/releases |
| Lights shader | | https://github.com/Raz0r1337/WoW-lights-patch-shader/releases |
'@
    Set-Content -Path $Readme -Value $template -Encoding UTF8
    Write-Host 'README.md was not found. A new README.md was created in this folder.' -ForegroundColor Yellow
    Write-Host 'Open it and write the versions you have. Empty versions show as NOT RECORDED.' -ForegroundColor Yellow
}
$readmeLines = Get-Content -Path $Readme -Encoding UTF8
$local = @{}
foreach ($line in $readmeLines) {
    if ($line -match '^\|\s*patch-([A-Z])\.mpq\s*\|') {
        $cells = $line.Split('|')
        $local[$Matches[1].ToUpper()] = $cells[3].Trim()
    }
}
$localTools = @{}
foreach ($line in $readmeLines) {
    if ($line -match '^\|\s*(St0ny AIO EXE Patcher|DXVK|LuxVelum|Lexara|Lights shader)\s*\|') {
        $cells = $line.Split('|')
        $localTools[$Matches[1]] = $cells[2].Trim()
    }
}
if ($local.Count -eq 0) {
    Write-Host 'No patch rows found in the README.md table.' -ForegroundColor Red
    exit 2
}

# ---------- 2. Site versions ----------
Write-Host "Reading $Url ..."
try {
    $html = (Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30).Content
} catch {
    Write-Host "Cannot read the Downloads page: $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}

$site = [ordered]@{}
foreach ($card in ($html -split 'class="dl-card"')) {
    if ($card -notmatch 'class="dl-patch">Patch-([A-Z])<') { continue }
    $letter = $Matches[1].ToUpper()
    $ver = $null
    if ($card -match 'class="dl-version">.*?v(\d+(?:\.\d+)+)') { $ver = $Matches[1] }
    $links = @([regex]::Matches($card, 'href="([^"]+\.mpq)"') | ForEach-Object { $_.Groups[1].Value })
    $site[$letter] = [pscustomobject]@{ Version = $ver; Links = $links }
}
if ($site.Count -eq 0) {
    Write-Host 'No patch found on the page. The page layout may have changed.' -ForegroundColor Red
    exit 2
}

# ---------- 2b. Tools: latest GitHub release ----------
$tools = @(
    @{ Name = 'St0ny AIO EXE Patcher'; Repo = 'Raz0r1337/St0nys-AIO-WoW-EXE-Patcher' },
    @{ Name = 'DXVK';                  Repo = 'Raz0r1337/DXVK' },
    @{ Name = 'LuxVelum';              Repo = 'Stormhand-dev/Luxvelum' },
    @{ Name = 'Lexara';                Repo = 'Stormhand-dev/Lexara---HD-Font-Renderer-for-WoW-3.3.5' },
    @{ Name = 'Lights shader';         Repo = 'Raz0r1337/WoW-lights-patch-shader' }
)
$toolRows = @()
if (-not $NoToolCheck) {
    foreach ($tl in $tools) {
        $latest = $null; $link = $null
        try {
            $rel = Invoke-RestMethod -Uri ("https://api.github.com/repos/{0}/releases/latest" -f $tl.Repo) -Headers @{ 'User-Agent' = 'check-versions' } -TimeoutSec 30
            $latest = ([string]$rel.tag_name).TrimStart('v', 'V')
            $link = $rel.html_url
        } catch { }
        $have = $localTools[$tl.Name]
        if (-not $latest) { $st = 'CHECK FAILED'; $col = 'Yellow' }
        elseif (-not $have) { $st = 'NOT RECORDED'; $col = 'Yellow' }
        else {
            $a = Convert-ToVersion $have
            $b = Convert-ToVersion $latest
            if (-not $a -or -not $b) { $st = 'CHECK MANUALLY'; $col = 'Yellow' }
            elseif ($b -gt $a) { $st = 'UPDATE'; $col = 'Red' }
            else { $st = 'OK'; $col = 'Green' }
        }
        $toolRows += [pscustomobject]@{
            Tool = $tl.Name; Local = $(if ($have) { $have } else { '-' }); Latest = $(if ($latest) { $latest } else { '-' })
            Status = $st; Link = $link; Color = $col
        }
    }
}

# ---------- 3. Compare ----------
$rows = @()
$letters = @($local.Keys) + @($site.Keys) | Sort-Object -Unique
foreach ($l in $letters) {
    $found = Find-Local ("patch-$l.mpq")
    $file  = if ($found) { $found.FullName } else { $null }
    $have  = [bool]$found
    $lv    = $local[$l]
    $sv    = if ($site.Contains($l)) { $site[$l].Version } else { $null }

    if (-not $site.Contains($l)) { $status = 'NOT ON SITE'; $color = 'Yellow' }
    elseif (-not $have -and -not $lv) { $status = 'NEW ON SITE'; $color = 'Cyan' }
    elseif (-not $have) { $status = 'MISSING FILE'; $color = 'Red' }
    elseif (-not $lv) { $status = 'NOT RECORDED'; $color = 'Yellow' }
    else {
        $a = Convert-ToVersion $lv
        $b = Convert-ToVersion $sv
        if (-not $a -or -not $b) { $status = 'CHECK MANUALLY'; $color = 'Yellow' }
        elseif ($b -gt $a) { $status = 'UPDATE'; $color = 'Red' }
        elseif ($b -lt $a) { $status = 'LOCAL IS NEWER'; $color = 'Yellow' }
        else { $status = 'OK'; $color = 'Green' }
    }

    $sizeNote = ''
    if ($have -and -not $NoSizeCheck -and $site.Contains($l) -and $site[$l].Links.Count -gt 0) {
        $localSize = (Get-Item $file).Length
        $matched = $null
        $known = $false
        foreach ($lk in $site[$l].Links) {
            $rs = Get-RemoteSize $lk
            if ($null -eq $rs) { continue }
            $known = $true
            if ($rs -eq $localSize) {
                $matched = if ($lk -match '/extras/') { 'same size as the extras file' } else { 'same size as the main file' }
                break
            }
        }
        if ($matched) { $sizeNote = $matched }
        elseif ($known) {
            $sizeNote = 'size differs from the server'
            if ($status -eq 'OK') { $status = 'OK (size differs)'; $color = 'Yellow' }
        }
        else { $sizeNote = 'size not checked' }
    }

    $rows += [pscustomobject]@{
        Patch = "patch-$l"; Local = $(if ($lv) { $lv } else { '-' }); Site = $(if ($sv) { $sv } else { '-' })
        Status = $status; Size = $sizeNote; Color = $color
    }
}

# ---------- 4. Report ----------
Write-Host ''
Write-Host ('{0,-10} {1,-10} {2,-10} {3,-18} {4}' -f 'Patch', 'You have', 'Site', 'Status', 'File size')
Write-Host ('-' * 78)
foreach ($r in $rows) {
    Write-Host ('{0,-10} {1,-10} {2,-10} {3,-18} {4}' -f $r.Patch, $r.Local, $r.Site, $r.Status, $r.Size) -ForegroundColor $r.Color
}

if ($toolRows.Count -gt 0) {
    Write-Host ''
    Write-Host ('{0,-24} {1,-12} {2,-12} {3}' -f 'Tool', 'You have', 'Latest', 'Status')
    Write-Host ('-' * 78)
    foreach ($r in $toolRows) {
        Write-Host ('{0,-24} {1,-12} {2,-12} {3}' -f $r.Tool, $r.Local, $r.Latest, $r.Status) -ForegroundColor $r.Color
        if ($r.Status -in @('UPDATE', 'NOT RECORDED') -and $r.Link) { Write-Host ('{0,-24} {1}' -f '', $r.Link) }
    }
}

# ---------- 4b. Tool files in your folders ----------
$expected = @(
    @{ Tool = 'St0ny AIO EXE Patcher'; Item = 'patcher-win.bat' },
    @{ Tool = 'St0ny AIO EXE Patcher'; Item = 'apply_patches.ps1' },
    @{ Tool = 'St0ny AIO EXE Patcher'; Item = 'patcher_selection.ini' },
    @{ Tool = 'DXVK';                  Item = 'd3d9.dll' },
    @{ Tool = 'LuxVelum';              Item = 'Luxvelum.dll' },
    @{ Tool = 'LuxVelum';              Item = 'fogdata.bin' },
    @{ Tool = 'LuxVelum';              Item = 'waterdata.bin' },
    @{ Tool = 'LuxVelum';              Item = 'zones.ini' },
    @{ Tool = 'LuxVelum';              Item = 'Luxvelum.ini' },
    @{ Tool = 'Lexara';                Item = 'lexara.dll|dinput8.dll' },
    @{ Tool = 'Lexara';                Item = 'skia.dll' },
    @{ Tool = 'Lights shader';         Item = 'patch-5.MPQ'; Dir = $true }
)
$fileRows = @()
foreach ($e in $expected) {
    $hit = if ($e.Dir) { Find-Local $e.Item -Dir } else { Find-Local $e.Item }
    if ($hit) {
        $fileRows += [pscustomobject]@{ Tool = $e.Tool; Item = $e.Item.Split('|')[0]; Status = 'FOUND'; Where = (Get-RelPath $hit.FullName); Color = 'Green' }
    } else {
        $fileRows += [pscustomobject]@{ Tool = $e.Tool; Item = $e.Item.Split('|')[0]; Status = 'MISSING'; Where = '-'; Color = 'Red' }
    }
}
Write-Host ''
Write-Host ('{0,-24} {1,-22} {2,-9} {3}' -f 'Tool', 'File', 'Status', 'Found in')
Write-Host ('-' * 78)
foreach ($r in $fileRows) {
    Write-Host ('{0,-24} {1,-22} {2,-9} {3}' -f $r.Tool, $r.Item, $r.Status, $r.Where) -ForegroundColor $r.Color
}
$fileTodo = @($fileRows | Where-Object { $_.Status -eq 'MISSING' })

$todo = @($rows | Where-Object { $_.Status -in @('UPDATE', 'MISSING FILE', 'OK (size differs)') })
$toolTodo = @($toolRows | Where-Object { $_.Status -eq 'UPDATE' })
Write-Host ''
if ($toolTodo.Count -gt 0) {
    Write-Host ("{0} tool(s) to update: {1}" -f $toolTodo.Count, (($toolTodo | ForEach-Object { $_.Tool }) -join ', ')) -ForegroundColor Red
}
if ($fileTodo.Count -gt 0) {
    Write-Host ("{0} tool file(s) not found in your folders: {1}" -f $fileTodo.Count, (($fileTodo | ForEach-Object { $_.Item }) -join ', ')) -ForegroundColor Red
}
if ($todo.Count -eq 0) {
    Write-Host 'All patches match the site.' -ForegroundColor Green
} else {
    Write-Host ("{0} patch(es) to check: {1}" -f $todo.Count, (($todo | ForEach-Object { $_.Patch }) -join ', ')) -ForegroundColor Red
    Write-Host "Download: $Url"
    Write-Host 'Keep the same file names. Back up the old file first. Then run: .\check-versions.ps1 -UpdateReadme'
}
Write-Host 'Patch-A and Patch-S have 2 variants (HD or SD, Standard or Standalone). The size check tells which one you have.'

# ---------- 5. Update the README table ----------
if ($UpdateReadme) {
    $out = foreach ($line in $readmeLines) {
        if ($line -match '^\|\s*patch-([A-Z])\.mpq\s*\|') {
            $l = $Matches[1].ToUpper()
            if ($site.Contains($l) -and $site[$l].Version) {
                $cells = $line.Split('|')
                $cells[3] = ' ' + $site[$l].Version + ' '
                $line = $cells -join '|'
            }
        }
        $line
    }
    $out = foreach ($line in $out) {
        if ($line -match '^\|\s*(St0ny AIO EXE Patcher|DXVK|LuxVelum|Lexara|Lights shader)\s*\|') {
            $nm = $Matches[1]
            $tr = $toolRows | Where-Object { $_.Tool -eq $nm } | Select-Object -First 1
            if ($tr -and $tr.Latest -ne '-') {
                $cells = $line.Split('|')
                $cells[2] = ' ' + $tr.Latest + ' '
                $line = $cells -join '|'
            }
        }
        $line
    }
    Set-Content -Path $Readme -Value $out -Encoding UTF8
    Write-Host ''
    Write-Host 'README.md updated with the versions from the site.' -ForegroundColor Green
}

if ($todo.Count -gt 0 -or $toolTodo.Count -gt 0 -or $fileTodo.Count -gt 0) { exit 1 } else { exit 0 }
