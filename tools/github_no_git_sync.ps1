param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("Watch", "Once", "DryRun")]
    [string]$Mode,

    [int]$Interval = 30
)

# Configuration
$ConfigPath = "tools\github_sync_config.json"
$LogPath = "logs\github_sync.log"
$ManifestPath = ".sync_state\local_manifest.json"

# Ensure directories exist
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path ".sync_state" | Out-Null

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Add-Content -Path $LogPath -Value $LogEntry
    Write-Host $LogEntry
}

# Load configuration
if (-not (Test-Path $ConfigPath)) {
    Write-Log "Configuration file not found: $ConfigPath" "ERROR"
    exit 1
}

$Config = Get-Content $ConfigPath | ConvertFrom-Json
$RepoOwner = $Config.repo_owner
$RepoName = $Config.repo_name
$Branch = $Config.branch
$SyncDeletions = $Config.sync_deletions
$ExcludePatterns = $Config.exclude_patterns

# Get token from environment
$Token = $env:GITHUB_TOKEN
if (-not $Token) {
    $Token = $env:GH_TOKEN
}
if (-not $Token) {
    Write-Log "GitHub token not found. Set GITHUB_TOKEN or GH_TOKEN environment variable." "ERROR"
    exit 1
}

Write-Log "Starting No-Git Sync - Mode: $Mode"
Write-Log "Repository: $RepoOwner/$RepoName, Branch: $Branch"

# Load local manifest
$LocalManifest = @{}
if (Test-Path $ManifestPath) {
    $LocalManifest = Get-Content $ManifestPath | ConvertFrom-Json -AsHashtable
}

# Get file hash
function Get-FileHashString {
    param([string]$FilePath)
    $Hash = Get-FileHash -Path $FilePath -Algorithm SHA256
    return $Hash.Hash
}

# Check if file should be excluded
function Test-Excluded {
    param([string]$FilePath)
    foreach ($Pattern in $ExcludePatterns) {
        if ($FilePath -like $Pattern) {
            return $true
        }
    }
    return $false
}

# Scan workspace
function Scan-Workspace {
    $Files = Get-ChildItem -Recurse -File | Where-Object {
        $RelativePath = $_.FullName.Substring((Get-Location).Path.Length + 1)
        -not (Test-Excluded $RelativePath)
    }
    return $Files
}

# Upload file to GitHub
function Upload-File {
    param([string]$FilePath, [string]$RelativePath)

    if ($Mode -eq "DryRun") {
        Write-Log "[DRY RUN] Would upload: $RelativePath"
        return $true
    }

    try {
        $Content = [System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes($FilePath))
        $Uri = "https://api.github.com/repos/$RepoOwner/$RepoName/contents/$RelativePath"

        # Check if file exists
        $Headers = @{
            "Authorization" = "token $Token"
            "Accept" = "application/vnd.github.v3+json"
        }

        $Existing = $null
        try {
            $Existing = Invoke-RestMethod -Uri "$Uri`?ref=$Branch" -Headers $Headers -Method GET
        } catch {
            # File doesn't exist
        }

        $Body = @{
            message = "Sync: $RelativePath"
            content = $Content
            branch = $Branch
        }

        if ($Existing) {
            $Body.sha = $Existing.sha
        }

        $JsonBody = $Body | ConvertTo-Json
        Invoke-RestMethod -Uri $Uri -Headers $Headers -Method PUT -Body $JsonBody

        Write-Log "Uploaded: $RelativePath"
        return $true
    } catch {
        Write-Log "Failed to upload $RelativePath : $_" "ERROR"
        return $false
    }
}

# Main sync logic
function Sync-Files {
    $Files = Scan-Workspace
    $Changes = 0

    foreach ($File in $Files) {
        $RelativePath = $File.FullName.Substring((Get-Location).Path.Length + 1)
        $CurrentHash = Get-FileHashString $File.FullName
        $PreviousHash = $LocalManifest[$RelativePath]

        if ($CurrentHash -ne $PreviousHash) {
            if (Upload-File -FilePath $File.FullName -RelativePath $RelativePath) {
                $LocalManifest[$RelativePath] = $CurrentHash
                $Changes++
            }
        }
    }

    # Save manifest
    $LocalManifest | ConvertTo-Json | Set-Content $ManifestPath

    Write-Log "Sync complete. $Changes files changed."
    return $Changes
}

# Run based on mode
if ($Mode -eq "Once") {
    Sync-Files
} elseif ($Mode -eq "DryRun") {
    Sync-Files
} elseif ($Mode -eq "Watch") {
    Write-Log "Watching for changes every $Interval seconds..."
    while ($true) {
        Sync-Files
        Start-Sleep -Seconds $Interval
    }
}

Write-Log "Sync session ended."
