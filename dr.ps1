param(
    [string]$ProjectRoot = $PSScriptRoot,
    [int]$PreviewRows = 30
)

$ErrorActionPreference = "Continue"

if (!(Test-Path -LiteralPath $ProjectRoot)) {
    Write-Host "Project folder not found: $ProjectRoot" -ForegroundColor Red
    exit 1
}

$ProjectRoot = (Get-Item -LiteralPath $ProjectRoot).FullName
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$ReportRoot       = Join-Path $ProjectRoot "_project_understanding_report"
$MainDir          = Join-Path $ReportRoot "01_MAIN_REPORT"
$InventoryDir     = Join-Path $ReportRoot "02_FILE_INVENTORY"
$FolderMapDir     = Join-Path $ReportRoot "03_FOLDER_MAPS"
$CsvDir           = Join-Path $ReportRoot "04_CSV_COLUMNS"
$PreviewDir       = Join-Path $ReportRoot "05_DATA_PREVIEWS"
$PythonDir        = Join-Path $ReportRoot "06_PYTHON_STRUCTURE"
$RecommendedDir   = Join-Path $ReportRoot "07_RECOMMENDED_STRUCTURE"
$ErrorsDir        = Join-Path $ReportRoot "08_ERRORS"

$Dirs = @(
    $ReportRoot,
    $MainDir,
    $InventoryDir,
    $FolderMapDir,
    $CsvDir,
    $PreviewDir,
    $PythonDir,
    $RecommendedDir,
    $ErrorsDir
)

foreach ($d in $Dirs) {
    New-Item -ItemType Directory -Path $d -Force | Out-Null
}

$MainReport              = Join-Path $MainDir "PROJECT_UNDERSTANDING_REPORT_$Stamp.txt"
$InventoryCsv            = Join-Path $InventoryDir "FULL_FILE_INVENTORY_$Stamp.csv"
$FolderSummaryCsv        = Join-Path $FolderMapDir "FOLDER_SUMMARY_$Stamp.csv"
$FolderFileMapCsv        = Join-Path $FolderMapDir "FOLDER_FILE_MAP_$Stamp.csv"
$CsvColumnsMaster        = Join-Path $CsvDir "CSV_COLUMNS_MASTER_$Stamp.csv"
$PythonStructureCsv      = Join-Path $PythonDir "PYTHON_STRUCTURE_$Stamp.csv"
$RecommendedPlacementCsv = Join-Path $RecommendedDir "RECOMMENDED_FILE_PLACEMENT_$Stamp.csv"

$ErrorLogTxt             = Join-Path $ErrorsDir "ERROR_LOG_$Stamp.txt"
$ScriptErrorsCsv         = Join-Path $ErrorsDir "SCRIPT_ERRORS_$Stamp.csv"
$CsvErrorsCsv            = Join-Path $ErrorsDir "CSV_ERRORS_$Stamp.csv"
$PythonErrorsCsv         = Join-Path $ErrorsDir "PYTHON_SYNTAX_ERRORS_$Stamp.csv"
$HealthWarningsCsv       = Join-Path $ErrorsDir "PROJECT_HEALTH_WARNINGS_$Stamp.csv"
$DuplicateFilesCsv       = Join-Path $ErrorsDir "DUPLICATE_FILE_NAMES_$Stamp.csv"
$EmptyFilesCsv           = Join-Path $ErrorsDir "EMPTY_FILES_$Stamp.csv"
$LongPathsCsv            = Join-Path $ErrorsDir "LONG_PATH_WARNINGS_$Stamp.csv"

$ScriptErrors = @()
$CsvErrors = @()
$PythonErrors = @()
$HealthWarnings = @()

$IgnoreFolders = @(
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "_project_understanding_report"
)

function Add-ScriptError {
    param($Area, $Message, $Path)
    $script:ScriptErrors += [PSCustomObject]@{
        Time = Get-Date
        Area = $Area
        Message = $Message
        Path = $Path
    }
}

function Add-CsvError {
    param($CsvFile, $RelativePath, $ErrorType, $Details)
    $script:CsvErrors += [PSCustomObject]@{
        CsvFile = $CsvFile
        RelativePath = $RelativePath
        ErrorType = $ErrorType
        Details = $Details
    }
}

function Add-HealthWarning {
    param($WarningType, $Details, $Path)
    $script:HealthWarnings += [PSCustomObject]@{
        WarningType = $WarningType
        Details = $Details
        Path = $Path
    }
}

function Test-Ignored {
    param($Path)

    $lower = $Path.ToLower()

    foreach ($f in $IgnoreFolders) {
        $token = "\" + $f.ToLower() + "\"
        $tokenEnd = "\" + $f.ToLower()

        if ($lower.Contains($token) -or $lower.EndsWith($tokenEnd)) {
            return $true
        }
    }

    return $false
}

function RelPath {
    param($Path)

    try {
        $full = (Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue).FullName

        if ([string]::IsNullOrWhiteSpace($full)) {
            $full = $Path
        }

        if ($full.StartsWith($ProjectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $full.Substring($ProjectRoot.Length).TrimStart("\")
        }

        return $full
    } catch {
        return $Path
    }
}

function SafeName {
    param($Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return "ROOT"
    }

    $safe = $Text -replace '[\\/:*?"<>|]', '_'
    $safe = $safe -replace '\s+', '_'

    if ($safe.Length -gt 120) {
        $safe = $safe.Substring(0, 120)
    }

    return $safe
}

function Get-Category {
    param($File)

    $ext = $File.Extension.ToLower()
    $name = $File.Name.ToLower()

    if ($name -in @("app.py", "main.py", "dashboard.py", "home.py")) {
        return "Streamlit Entry Point"
    }

    switch ($ext) {
        ".py"      { return "Python Source Code" }
        ".ps1"     { return "PowerShell Script" }
        ".bat"     { return "Batch Script" }
        ".cmd"     { return "Batch Script" }
        ".csv"     { return "CSV Data File" }
        ".xlsx"    { return "Excel Data File" }
        ".xls"     { return "Excel Data File" }
        ".xlsm"    { return "Excel Macro Workbook" }
        ".json"    { return "JSON Config Or Data" }
        ".db"      { return "Database File" }
        ".sqlite"  { return "Database File" }
        ".sqlite3" { return "Database File" }
        ".md"      { return "Documentation" }
        ".txt"     { return "Text File" }
        ".toml"    { return "Configuration" }
        ".yaml"    { return "Configuration" }
        ".yml"     { return "Configuration" }
        ".ini"     { return "Configuration" }
        ".png"     { return "Image Asset" }
        ".jpg"     { return "Image Asset" }
        ".jpeg"    { return "Image Asset" }
        ".svg"     { return "Image Asset" }
        ".ico"     { return "Image Asset" }
        ".html"    { return "Web UI File" }
        ".css"     { return "Web UI File" }
        ".js"      { return "Web UI File" }
        ".pdf"     { return "PDF Document" }
        ".docx"    { return "Word Document" }
        ".pptx"    { return "PowerPoint Document" }
        default     { return "Other Review Required" }
    }
}

function Get-Recommendation {
    param($Category)

    switch ($Category) {
        "Streamlit Entry Point"   { return "01_app_entry" }
        "Python Source Code"      { return "02_source_code_python" }
        "PowerShell Script"       { return "03_scripts_powershell" }
        "Batch Script"            { return "03_scripts_batch" }
        "CSV Data File"           { return "04_data_csv" }
        "Excel Data File"         { return "05_data_excel" }
        "Excel Macro Workbook"    { return "05_data_excel" }
        "JSON Config Or Data"     { return "06_config_or_json_data" }
        "Database File"           { return "07_database" }
        "Configuration"           { return "08_config" }
        "Documentation"           { return "09_documentation" }
        "Text File"               { return "09_documentation" }
        "Image Asset"             { return "10_assets_images" }
        "Web UI File"             { return "11_web_ui_assets" }
        "PDF Document"            { return "12_documents_pdf" }
        "Word Document"           { return "13_documents_word" }
        "PowerPoint Document"     { return "14_documents_powerpoint" }
        default                   { return "99_other_review_required" }
    }
}

function Find-Delimiter {
    param($Line)

    $c1 = ([regex]::Matches($Line, [regex]::Escape(","))).Count
    $c2 = ([regex]::Matches($Line, [regex]::Escape(";"))).Count
    $c3 = ([regex]::Matches($Line, [regex]::Escape("`t"))).Count
    $c4 = ([regex]::Matches($Line, [regex]::Escape("|"))).Count

    $best = ","
    $bestCount = $c1

    if ($c2 -gt $bestCount) {
        $best = ";"
        $bestCount = $c2
    }

    if ($c3 -gt $bestCount) {
        $best = "`t"
        $bestCount = $c3
    }

    if ($c4 -gt $bestCount) {
        $best = "|"
        $bestCount = $c4
    }

    return $best
}

function Split-Line {
    param($Line, $Delimiter)

    return $Line -split [regex]::Escape($Delimiter)
}

function Export-Safe {
    param($Data, $Path, $Message)

    if (@($Data).Count -eq 0) {
        [PSCustomObject]@{
            Status = $Message
        } | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    } else {
        $Data | Export-Csv -Path $Path -NoTypeInformation -Encoding UTF8
    }
}

function Add-Report {
    param($Text)
    Add-Content -Path $MainReport -Value $Text -Encoding UTF8
}

Write-Host "Scanning files..." -ForegroundColor Yellow

try {
    $AllFiles = Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File -Force -ErrorAction SilentlyContinue | Where-Object {
        -not (Is-Ignored $_.FullName)
    }

    $AllFolders = Get-ChildItem -LiteralPath $ProjectRoot -Recurse -Directory -Force -ErrorAction SilentlyContinue | Where-Object {
        -not (Is-Ignored $_.FullName)
    }
} catch {
    Add-ScriptError "Scan" $_.Exception.Message $ProjectRoot
    $AllFiles = @()
    $AllFolders = @()
}

$totalBytes = ($AllFiles | Measure-Object Length -Sum).Sum

if ($null -eq $totalBytes) {
    $totalBytes = 0
}

$totalMB = [math]::Round($totalBytes / 1MB, 2)

Write-Host "Building inventory..." -ForegroundColor Yellow

$Inventory = foreach ($file in $AllFiles) {
    try {
        $relativePath = RelPath $file.FullName
        $relativeFolder = RelPath $file.DirectoryName
        $category = Get-Category $file
        $recommended = Get-Recommendation $category

        if ($file.Length -eq 0) {
            Add-HealthWarning "Empty File" "File size is zero." $relativePath
        }

        if ($file.FullName.Length -gt 240) {
            Add-HealthWarning "Long Path" "Path is longer than 240 characters." $relativePath
        }

        [PSCustomObject]@{
            FileName = $file.Name
            Extension = $file.Extension
            CurrentFolder = $relativeFolder
            RelativePath = $relativePath
            FullPath = $file.FullName
            SizeKB = [math]::Round($file.Length / 1KB, 2)
            Modified = $file.LastWriteTime
            FileCategory = $category
            RecommendedFolder = $recommended
            RecommendedAction = "Review only. Script does not move files."
        }
    } catch {
        Add-ScriptError "Inventory" $_.Exception.Message $file.FullName
    }
}

Export-Safe $Inventory $InventoryCsv "No files found"
Export-Safe $Inventory $RecommendedPlacementCsv "No recommended placement generated"

Write-Host "Building folder maps..." -ForegroundColor Yellow

$FolderSummary = $Inventory | Group-Object CurrentFolder | ForEach-Object {
    $sum = ($_.Group | Measure-Object SizeKB -Sum).Sum

    if ($null -eq $sum) {
        $sum = 0
    }

    [PSCustomObject]@{
        Folder = $_.Name
        FileCount = $_.Count
        TotalSizeKB = [math]::Round($sum, 2)
        MainFileTypes = (($_.Group | Group-Object Extension | Sort-Object Count -Descending | Select-Object -First 10 | ForEach-Object { $_.Name + ":" + $_.Count }) -join " ; ")
    }
} | Sort-Object Folder

Export-Safe $FolderSummary $FolderSummaryCsv "No folder summary generated"

$FolderFileMap = $Inventory | Select-Object CurrentFolder, FileName, Extension, FileCategory, RelativePath, SizeKB, Modified | Sort-Object CurrentFolder, FileName
Export-Safe $FolderFileMap $FolderFileMapCsv "No folder file map generated"

foreach ($folderGroup in ($Inventory | Group-Object CurrentFolder)) {
    $safe = SafeName $folderGroup.Name
    $folderReport = Join-Path $FolderMapDir ("FILES_IN_FOLDER__" + $safe + ".csv")

    $folderGroup.Group | Select-Object FileName, Extension, FileCategory, RelativePath, SizeKB, Modified | Sort-Object FileName | Export-Csv -Path $folderReport -NoTypeInformation -Encoding UTF8
}

Write-Host "Creating recommended structure folders..." -ForegroundColor Yellow

$recommendedFolders = $Inventory | Select-Object -ExpandProperty RecommendedFolder -Unique | Sort-Object

foreach ($rf in $recommendedFolders) {
    New-Item -ItemType Directory -Path (Join-Path $RecommendedDir $rf) -Force | Out-Null
}

Write-Host "Extracting CSV columns..." -ForegroundColor Yellow

$CsvFiles = $AllFiles | Where-Object { $_.Extension.ToLower() -eq ".csv" }
$CsvColumnRows = @()

foreach ($csv in $CsvFiles) {
    $relativePath = RelPath $csv.FullName
    $relativeFolder = RelPath $csv.DirectoryName

    try {
        $firstLines = Get-Content -LiteralPath $csv.FullName -TotalCount $PreviewRows -ErrorAction Stop
        $cleanLines = $firstLines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

        if (@($cleanLines).Count -eq 0) {
            Add-CsvError $csv.Name $relativePath "Empty CSV" "No readable content detected."
            continue
        }

        $header = $cleanLines | Select-Object -First 1
        $delimiter = Detect-Delimiter $header
        $columns = Split-Line $header $delimiter
        $columns = $columns | ForEach-Object { $_.Trim().Trim('"') }

        if (@($columns).Count -eq 0) {
            Add-CsvError $csv.Name $relativePath "No Header" "No columns detected."
        }

        $blankColumns = $columns | Where-Object { [string]::IsNullOrWhiteSpace($_) }

        if (@($blankColumns).Count -gt 0) {
            Add-CsvError $csv.Name $relativePath "Blank Columns" ("Blank column count: " + @($blankColumns).Count)
        }

        $duplicates = $columns | Group-Object | Where-Object { $_.Count -gt 1 -and -not [string]::IsNullOrWhiteSpace($_.Name) }

        foreach ($dup in $duplicates) {
            Add-CsvError $csv.Name $relativePath "Duplicate Column" ("Column repeated: " + $dup.Name + " Count: " + $dup.Count)
        }

        $expectedCount = @($columns).Count
        $rowNumber = 1

        foreach ($line in ($cleanLines | Select-Object -Skip 1)) {
            $rowNumber++
            $rowCols = Split-Line $line $delimiter

            if (@($rowCols).Count -ne $expectedCount) {
                Add-CsvError $csv.Name $relativePath "Irregular Preview Row" ("Row " + $rowNumber + " has " + @($rowCols).Count + " columns. Expected " + $expectedCount)
            }
        }

        $i = 1

        foreach ($col in $columns) {
            $CsvColumnRows += [PSCustomObject]@{
                CsvFile = $csv.Name
                CurrentFolder = $relativeFolder
                RelativePath = $relativePath
                Delimiter = $(if ($delimiter -eq "`t") { "TAB" } else { $delimiter })
                ColumnOrder = $i
                ColumnName = $col
                ColumnCount = $expectedCount
                FileSizeKB = [math]::Round($csv.Length / 1KB, 2)
                Modified = $csv.LastWriteTime
            }

            $i++
        }

        $safeCsv = SafeName ($relativePath -replace "\.csv$", "")
        $oneCsvReport = Join-Path $CsvDir ("COLUMNS__" + $safeCsv + ".csv")

        $CsvColumnRows | Where-Object { $_.RelativePath -eq $relativePath } | Export-Csv -Path $oneCsvReport -NoTypeInformation -Encoding UTF8

        $previewFile = Join-Path $PreviewDir ("PREVIEW__" + $safeCsv + ".txt")
        $firstLines | Set-Content -Path $previewFile -Encoding UTF8

    } catch {
        Add-CsvError $csv.Name $relativePath "Read Error" $_.Exception.Message
        Add-ScriptError "CSV Read" $_.Exception.Message $csv.FullName
    }
}

Export-Safe $CsvColumnRows $CsvColumnsMaster "No CSV columns extracted"

Write-Host "Analyzing Python files..." -ForegroundColor Yellow

$PythonFiles = $AllFiles | Where-Object { $_.Extension.ToLower() -eq ".py" }
$PythonRows = @()

foreach ($py in $PythonFiles) {
    try {
        $content = ""

        if ($py.Length -lt 5MB) {
            $content = Get-Content -LiteralPath $py.FullName -Raw -ErrorAction SilentlyContinue
        }

        $imports = @()
        $classes = @()
        $functions = @()
        $streamlitHits = 0

        if (![string]::IsNullOrWhiteSpace($content)) {
            $imports = [regex]::Matches($content, '(?m)^\s*(import\s+[A-Za-z0-9_\.]+|from\s+[A-Za-z0-9_\.]+\s+import\s+.+)$') | ForEach-Object { $_.Groups[1].Value.Trim() } | Select-Object -Unique
            $classes = [regex]::Matches($content, '(?m)^\s*class\s+([A-Za-z0-9_]+)') | ForEach-Object { $_.Groups[1].Value.Trim() } | Select-Object -Unique
            $functions = [regex]::Matches($content, '(?m)^\s*def\s+([A-Za-z0-9_]+)\s*\(') | ForEach-Object { $_.Groups[1].Value.Trim() } | Select-Object -Unique
            $streamlitHits = ([regex]::Matches($content, 'st\.|streamlit')).Count
        }

        $PythonRows += [PSCustomObject]@{
            File = RelPath $py.FullName
            CurrentFolder = RelPath $py.DirectoryName
            SizeKB = [math]::Round($py.Length / 1KB, 2)
            Imports = ($imports -join " ; ")
            Classes = ($classes -join " ; ")
            Functions = ($functions -join " ; ")
            StreamlitHits = $streamlitHits
            Modified = $py.LastWriteTime
        }

    } catch {
        Add-ScriptError "Python Structure" $_.Exception.Message $py.FullName
    }
}

Export-Safe $PythonRows $PythonStructureCsv "No Python files found"

Write-Host "Checking Python syntax..." -ForegroundColor Yellow

$PythonCommand = Get-Command python -ErrorAction SilentlyContinue

if ($null -eq $PythonCommand) {
    Add-HealthWarning "Python Not Found" "Python syntax validation skipped because python command was not found." ""
} else {
    foreach ($py in $PythonFiles) {
        try {
            $out = & $PythonCommand.Source -m py_compile $py.FullName 2>&1

            if ($LASTEXITCODE -ne 0) {
                $PythonErrors += [PSCustomObject]@{
                    File = RelPath $py.FullName
                    ErrorType = "Python Compile Error"
                    Details = ($out | Out-String).Trim()
                }
            }
        } catch {
            $PythonErrors += [PSCustomObject]@{
                File = RelPath $py.FullName
                ErrorType = "Python Compile Execution Error"
                Details = $_.Exception.Message
            }
        }
    }
}

Write-Host "Checking project health..." -ForegroundColor Yellow

$EntryCandidates = $AllFiles | Where-Object { $_.Name.ToLower() -in @("app.py", "main.py", "dashboard.py", "home.py") }

if (@($EntryCandidates).Count -eq 0) {
    Add-HealthWarning "Missing Entry Point" "No app.py, main.py, dashboard.py, or Home.py detected." $ProjectRoot
}

$Requirements = $AllFiles | Where-Object { $_.Name.ToLower() -eq "requirements.txt" }

if (@($Requirements).Count -eq 0) {
    Add-HealthWarning "Missing requirements.txt" "No requirements.txt detected." $ProjectRoot
}

$DuplicateFiles = $Inventory | Group-Object FileName | Where-Object { $_.Count -gt 1 } | ForEach-Object {
    [PSCustomObject]@{
        FileName = $_.Name
        Count = $_.Count
        Locations = (($_.Group | Select-Object -ExpandProperty RelativePath) -join " ; ")
    }
}

foreach ($dup in $DuplicateFiles) {
    Add-HealthWarning "Duplicate File Name" ("File exists " + $dup.Count + " times.") $dup.FileName
}

$EmptyFiles = $Inventory | Where-Object { $_.SizeKB -eq 0 }
$LongPaths = $Inventory | Where-Object { $_.FullPath.Length -gt 240 }

Export-Safe $ScriptErrors $ScriptErrorsCsv "No script errors detected"
Export-Safe $CsvErrors $CsvErrorsCsv "No CSV errors detected"
Export-Safe $PythonErrors $PythonErrorsCsv "No Python syntax errors detected"
Export-Safe $HealthWarnings $HealthWarningsCsv "No project health warnings detected"
Export-Safe $DuplicateFiles $DuplicateFilesCsv "No duplicate file names detected"
Export-Safe $EmptyFiles $EmptyFilesCsv "No empty files detected"
Export-Safe $LongPaths $LongPathsCsv "No long path warnings detected"

Write-Host "Writing main report..." -ForegroundColor Yellow

"PROJECT CONTROLS HUB - DEEP UNDERSTANDING REPORT" | Set-Content -Path $MainReport -Encoding UTF8
Add-Report ""
Add-Report ("Project Root: " + $ProjectRoot)
Add-Report ("Generated: " + (Get-Date))
Add-Report ""
Add-Report "EXECUTIVE SNAPSHOT"
Add-Report ("Total Files: " + @($AllFiles).Count)
Add-Report ("Total Folders: " + @($AllFolders).Count)
Add-Report ("Total Size MB: " + $totalMB)
Add-Report ("Python Files: " + @($PythonFiles).Count)
Add-Report ("CSV Files: " + @($CsvFiles).Count)
Add-Report ("CSV Columns Extracted: " + @($CsvColumnRows).Count)
Add-Report ("Script Errors: " + @($ScriptErrors).Count)
Add-Report ("CSV Errors: " + @($CsvErrors).Count)
Add-Report ("Python Syntax Errors: " + @($PythonErrors).Count)
Add-Report ("Health Warnings: " + @($HealthWarnings).Count)
Add-Report ""
Add-Report "REPORT FOLDERS"
Add-Report ("01_MAIN_REPORT: " + $MainDir)
Add-Report ("02_FILE_INVENTORY: " + $InventoryDir)
Add-Report ("03_FOLDER_MAPS: " + $FolderMapDir)
Add-Report ("04_CSV_COLUMNS: " + $CsvDir)
Add-Report ("05_DATA_PREVIEWS: " + $PreviewDir)
Add-Report ("06_PYTHON_STRUCTURE: " + $PythonDir)
Add-Report ("07_RECOMMENDED_STRUCTURE: " + $RecommendedDir)
Add-Report ("08_ERRORS: " + $ErrorsDir)
Add-Report ""
Add-Report "KEY OUTPUTS"
Add-Report ("Full File Inventory: " + $InventoryCsv)
Add-Report ("Folder Summary: " + $FolderSummaryCsv)
Add-Report ("Folder File Map: " + $FolderFileMapCsv)
Add-Report ("CSV Columns Master: " + $CsvColumnsMaster)
Add-Report ("Python Structure: " + $PythonStructureCsv)
Add-Report ("Recommended Placement: " + $RecommendedPlacementCsv)
Add-Report ("Error Log: " + $ErrorLogTxt)
Add-Report ""
Add-Report "ERROR OUTPUTS"
Add-Report ("Script Errors: " + $ScriptErrorsCsv)
Add-Report ("CSV Errors: " + $CsvErrorsCsv)
Add-Report ("Python Syntax Errors: " + $PythonErrorsCsv)
Add-Report ("Project Health Warnings: " + $HealthWarningsCsv)
Add-Report ("Duplicate File Names: " + $DuplicateFilesCsv)
Add-Report ("Empty Files: " + $EmptyFilesCsv)
Add-Report ("Long Path Warnings: " + $LongPathsCsv)
Add-Report ""
Add-Report "RECOMMENDED REVIEW ORDER"
Add-Report "1. Open 08_ERRORS first."
Add-Report "2. Open CSV_ERRORS to fix bad CSV files."
Add-Report "3. Open PYTHON_SYNTAX_ERRORS to fix broken Python files."
Add-Report "4. Open PROJECT_HEALTH_WARNINGS for missing files and project risks."
Add-Report "5. Open CSV_COLUMNS_MASTER to understand all CSV file columns."
Add-Report "6. Open FULL_FILE_INVENTORY to understand where every file exists."
Add-Report "7. Open FOLDER_SUMMARY and FOLDER_FILE_MAP to understand structure."

"PROJECT CONTROLS HUB - ERROR LOG" | Set-Content -Path $ErrorLogTxt -Encoding UTF8
Add-Content -Path $ErrorLogTxt -Value ("Generated: " + (Get-Date)) -Encoding UTF8
Add-Content -Path $ErrorLogTxt -Value "" -Encoding UTF8
Add-Content -Path $ErrorLogTxt -Value ("Script Errors: " + @($ScriptErrors).Count) -Encoding UTF8
Add-Content -Path $ErrorLogTxt -Value ("CSV Errors: " + @($CsvErrors).Count) -Encoding UTF8
Add-Content -Path $ErrorLogTxt -Value ("Python Syntax Errors: " + @($PythonErrors).Count) -Encoding UTF8
Add-Content -Path $ErrorLogTxt -Value ("Health Warnings: " + @($HealthWarnings).Count) -Encoding UTF8
Add-Content -Path $ErrorLogTxt -Value "" -Encoding UTF8

if (@($ScriptErrors).Count -gt 0) {
    Add-Content -Path $ErrorLogTxt -Value "SCRIPT ERRORS" -Encoding UTF8
    $ScriptErrors | Format-List | Out-String | Add-Content -Path $ErrorLogTxt -Encoding UTF8
}

if (@($CsvErrors).Count -gt 0) {
    Add-Content -Path $ErrorLogTxt -Value "CSV ERRORS" -Encoding UTF8
    $CsvErrors | Format-List | Out-String | Add-Content -Path $ErrorLogTxt -Encoding UTF8
}

if (@($PythonErrors).Count -gt 0) {
    Add-Content -Path $ErrorLogTxt -Value "PYTHON ERRORS" -Encoding UTF8
    $PythonErrors | Format-List | Out-String | Add-Content -Path $ErrorLogTxt -Encoding UTF8
}

if (@($HealthWarnings).Count -gt 0) {
    Add-Content -Path $ErrorLogTxt -Value "HEALTH WARNINGS" -Encoding UTF8
    $HealthWarnings | Format-List | Out-String | Add-Content -Path $ErrorLogTxt -Encoding UTF8
}

Write-Host ""
Write-Host "DONE - Report generated successfully." -ForegroundColor Green
Write-Host ""
Write-Host "Main Report:" -ForegroundColor Cyan
Write-Host $MainReport
Write-Host ""
Write-Host "Errors Folder:" -ForegroundColor Red
Write-Host $ErrorsDir
Write-Host ""
Write-Host "CSV Columns Master:" -ForegroundColor Cyan
Write-Host $CsvColumnsMaster
Write-Host ""

Start-Process explorer.exe $ReportRoot
