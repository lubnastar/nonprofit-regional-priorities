<#
Runs against the RegionalPriorities model while it is open in Power BI Desktop.

  -Refresh            full refresh of the model through XMLA (TMSL)
  -QueryFile f.dax    run the DAX queries in the file (separated by lines that start with "-- @name")
  -OutDir dir         one CSV per query: <name>.csv

Example (from the project root, in Windows PowerShell 5.1):
  powershell -File powerbi_project\01_scripts\pbi_dax.ps1 -Refresh
  powershell -File powerbi_project\01_scripts\pbi_dax.ps1 -QueryFile powerbi_project\01_scripts\validation_queries.dax -OutDir powerbi_project\04_docs\validation\dax_results
#>
param([switch]$Refresh, [string]$QueryFile, [string]$OutDir, [string]$WindowTitle = "RegionalPriorities")

$ErrorActionPreference = "Stop"
Add-Type -Path "C:\Program Files\Microsoft Power BI Desktop\bin\Microsoft.PowerBI.AdomdClient.dll"

# the msmdsrv.exe child of the Power BI Desktop window showing this project
$pbi = Get-Process PBIDesktop | Where-Object { $_.MainWindowTitle -like "$WindowTitle*" } | Select-Object -First 1
if (-not $pbi) { throw "Power BI Desktop with '$WindowTitle' is not open." }
$as = Get-CimInstance Win32_Process -Filter "Name='msmdsrv.exe' AND ParentProcessId=$($pbi.Id)"
$wsName = [regex]::Match($as.CommandLine, "-n (\S+)").Groups[1].Value
$port = (Get-Content "$env:LOCALAPPDATA\Microsoft\Power BI Desktop\AnalysisServicesWorkspaces\$wsName\Data\msmdsrv.port.txt" -Encoding Unicode) -join ""

$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection "Data Source=localhost:$port"
$conn.Open()
$cat = $conn.CreateCommand(); $cat.CommandText = 'SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS'
$r = $cat.ExecuteReader(); [void]$r.Read(); $db = $r.GetString(0); $r.Close()
$conn.ChangeDatabase($db)
Write-Host "Connected to localhost:$port, database $db"

if ($Refresh) {
    $tmsl = '{"refresh":{"type":"full","objects":[{"database":"' + $db + '"}]}}'
    $cmd = $conn.CreateCommand(); $cmd.CommandText = $tmsl; $cmd.CommandTimeout = 600
    $sw = [Diagnostics.Stopwatch]::StartNew(); [void]$cmd.ExecuteNonQuery()
    Write-Host ("Refresh completed in {0:N1} s" -f $sw.Elapsed.TotalSeconds)
}

if ($QueryFile) {
    New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
    $text = [IO.File]::ReadAllText((Resolve-Path $QueryFile), [Text.Encoding]::UTF8)
    $blocks = [regex]::Split($text, "(?m)^-- @") | Where-Object { $_.Trim() }
    foreach ($blk in $blocks) {
        $nl = $blk.IndexOf("`n"); $name = $blk.Substring(0, $nl).Trim(); $dax = $blk.Substring($nl + 1)
        $cmd = $conn.CreateCommand(); $cmd.CommandText = $dax; $cmd.CommandTimeout = 600
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $rdr = $cmd.ExecuteReader()
        $lines = New-Object System.Collections.Generic.List[string]
        $lines.Add(((0..($rdr.FieldCount - 1) | ForEach-Object { '"' + ($rdr.GetName($_) -replace '^.*\[(.*)\]$', '$1') + '"' }) -join ","))
        $inv = [Globalization.CultureInfo]::InvariantCulture
        while ($rdr.Read()) {
            $vals = foreach ($i in 0..($rdr.FieldCount - 1)) {
                $v = $rdr.GetValue($i)
                if ($v -is [DBNull] -or $null -eq $v) { "" }
                elseif ($v -is [double]) { $v.ToString("R", $inv) }
                elseif ($v -is [decimal] -or $v -is [long] -or $v -is [int]) { $v.ToString($inv) }
                else { '"' + ([string]$v -replace '"', '""') + '"' }
            }
            $lines.Add(($vals -join ","))
        }
        $rdr.Close()
        [IO.File]::WriteAllLines((Join-Path $OutDir "$name.csv"), $lines, (New-Object Text.UTF8Encoding $false))
        Write-Host ("{0,-28} {1,4} rows  {2,6:N0} ms" -f $name, ($lines.Count - 1), $sw.Elapsed.TotalMilliseconds)
    }
}
$conn.Close()
