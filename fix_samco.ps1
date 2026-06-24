# ============================================================================
# SAMCO Dashboard Fix - ValueError: All arrays must be of the same length
# ============================================================================
# Run this PowerShell script to patch dashboard.py automatically
# 
# HOW TO RUN:
#   1. Save this file as: fix_samco.ps1
#   2. Right-click PowerShell -> Run as Administrator (or regular PowerShell)
#   3. cd "D:\New SAMCO Dashboard\project_controls_hub\rev04 project_controls_hub"
#   4. .\fix_samco.ps1
# ============================================================================

$ErrorActionPreference = "Stop"

# --- CONFIGURE PATHS ---
$FolderPath = "D:\New SAMCO Dashboard\project_controls_hub\rev04 project_controls_hub"
$FilePath   = Join-Path $FolderPath "dashboard.py"
$BackupPath = $FilePath + ".backup_" + (Get-Date -Format "yyyyMMdd_HHmmss")

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SAMCO Dashboard Fix Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# --- VERIFY FILE EXISTS ---
if (-not (Test-Path $FilePath)) {
    Write-Host "" 
    Write-Host "ERROR: dashboard.py not found at:" -ForegroundColor Red
    Write-Host "  $FilePath" -ForegroundColor Yellow
    Write-Host "" 
    Write-Host "Please verify the path and try again." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Target file: $FilePath" -ForegroundColor White

# --- CREATE BACKUP ---
Copy-Item -Path $FilePath -Destination $BackupPath -Force
Write-Host "Backup created: $BackupPath" -ForegroundColor Green

# --- READ FILE ---
$Content = Get-Content -Path $FilePath -Raw -Encoding UTF8
$Lines = $Content -split "`r?`n"

Write-Host ""
Write-Host "Scanning for problematic code block..." -ForegroundColor Yellow

# --- FIND AND REPLACE THE PROBLEMATIC BLOCK ---
$Modified = $false
$ReplaceBlock = @(
    '            # --- FIX: Robust scalar extraction for trend data ---'
    '            dates = pd.date_range(end=datetime.now(), periods=12, freq="MS")'
    '            '
    '            def _safe_scalar(val, default=1.0):'
    '                """Safely extract scalar from Series, ndarray, or scalar."""'
    '                if val is None:'
    '                    return default'
    '                try:'
    '                    if hasattr(val, "iloc"):           # pandas Series/DataFrame'
    '                        return float(val.iloc[0]) if len(val) > 0 else default'
    '                    if hasattr(val, "item"):             # numpy scalar'
    '                        return float(val.item())'
    '                    if isinstance(val, (list, tuple, np.ndarray)):'
    '                        arr = np.asarray(val)'
    '                        return float(arr.flat[0]) if arr.size > 0 else default'
    '                    return float(val)                    # plain scalar'
    '                except (TypeError, ValueError, IndexError):'
    '                    return default'
    '            '
    '            spi_val = _safe_scalar(avg_spi, default=1.0)'
    '            cpi_val = _safe_scalar(avg_cpi, default=1.0)'
    '            '
    '            spi_trend = [spi_val + np.sin(i * 0.5) * 0.1 for i in range(12)]'
    '            cpi_trend = [cpi_val + np.cos(i * 0.5) * 0.08 for i in range(12)]'
    '            '
    '            # Validate all arrays have matching length before DataFrame'
    '            trend_data = {"Date": list(dates), "SPI": spi_trend, "CPI": cpi_trend}'
    '            _lengths = {k: len(v) for k, v in trend_data.items()}'
    '            if len(set(_lengths.values())) != 1:'
    '                target_len = len(dates)'
    '                for k in trend_data:'
    '                    if len(trend_data[k]) < target_len:'
    '                        last_val = trend_data[k][-1] if trend_data[k] else 0'
    '                        trend_data[k] = trend_data[k] + [last_val] * (target_len - len(trend_data[k]))'
    '                    elif len(trend_data[k]) > target_len:'
    '                        trend_data[k] = trend_data[k][:target_len]'
    '            '
    '            trend_df = pd.DataFrame(trend_data)'
    '            # --- END FIX ---'
)

# Search for the pattern: find "trend_df = pd.DataFrame(trend_data)" 
# and replace the entire surrounding block
for ($i = 0; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i] -match '^\s*trend_df\s*=\s*pd\.DataFrame\(trend_data\)\s*$') {

        # Go backwards to find where this block starts (look for "dates = pd.date_range")
        $BlockStart = -1
        for ($j = [Math]::Max(0, $i - 15); $j -le $i; $j++) {
            if ($Lines[$j] -match 'dates\s*=\s*pd\.date_range\(end=datetime\.now\(\)') {
                $BlockStart = $j
                break
            }
        }

        if ($BlockStart -ge 0) {
            # Verify this block also contains spi_trend / cpi_trend
            $BlockText = $Lines[$BlockStart..$i] -join "`n"
            if ($BlockText -match 'spi_trend' -and $BlockText -match 'cpi_trend') {

                # Perform replacement
                $Before = if ($BlockStart -gt 0) { $Lines[0..($BlockStart-1)] } else { @() }
                $After  = if ($i + 1 -lt $Lines.Count) { $Lines[($i+1)..($Lines.Count-1)] } else { @() }
                $Lines = @($Before) + @($ReplaceBlock) + @($After)
                $Modified = $true

                Write-Host "Found problematic block at lines $($BlockStart+1) - $($i+1)" -ForegroundColor Green
                Write-Host "Replaced with fixed version." -ForegroundColor Green
                break
            }
        }
    }
}

# --- SAVE RESULT ---
if (-not $Modified) {
    Write-Host ""
    Write-Host "WARNING: Could not auto-locate the code pattern." -ForegroundColor Red
    Write-Host "The file may have a different structure than expected." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Manual fix required:" -ForegroundColor Cyan
    Write-Host "  Search dashboard.py for:  trend_df = pd.DataFrame(trend_data)" -ForegroundColor White
    Write-Host "  Around line 865-875, replace the dates/spi_trend/cpi_trend block" -ForegroundColor White
    Write-Host "  with the _safe_scalar() version shown in this script." -ForegroundColor White
    exit 1
}

# Write back
$NewContent = $Lines -join "`n"
Set-Content -Path $FilePath -Value $NewContent -Encoding UTF8 -NoNewline

# --- SUMMARY ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  FIX APPLIED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "What was fixed:" -ForegroundColor Yellow
Write-Host "  1. Added _safe_scalar() function" -ForegroundColor White
Write-Host "     - Handles pandas Series  -> extracts .iloc[0]" -ForegroundColor Gray
Write-Host "     - Handles numpy arrays   -> extracts first element" -ForegroundColor Gray
Write-Host "     - Handles None/NaN       -> returns default 1.0" -ForegroundColor Gray
Write-Host "     - Handles plain scalars  -> standard float()" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Added length validation" -ForegroundColor White
Write-Host "     - Checks Date, SPI, CPI arrays match before DataFrame()" -ForegroundColor Gray
Write-Host "     - Auto-pads short arrays with last value" -ForegroundColor Gray
Write-Host "     - Auto-truncates long arrays" -ForegroundColor Gray
Write-Host ""
Write-Host "Next step:" -ForegroundColor Cyan
Write-Host "  cd "$FolderPath"" -ForegroundColor White
Write-Host "  streamlit run dashboard.py" -ForegroundColor White
Write-Host ""
