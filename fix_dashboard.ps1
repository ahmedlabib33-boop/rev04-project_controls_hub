# PowerShell Fix Script for dashboard.py ValueError
# Fixes: "All arrays must be of the same length" in render_portfolio()

$ErrorActionPreference = "Stop"

$filePath = "D:\New SAMCO Dashboard\project_controls_hub\rev04 project_controls_hub\dashboard.py"

if (-not (Test-Path $filePath)) {
    Write-Error "File not found: $filePath"
    exit 1
}

# Read the file content
$content = Get-Content -Path $filePath -Raw -Encoding UTF8

# Create backup
$backupPath = $filePath + ".backup"
Copy-Item -Path $filePath -Destination $backupPath -Force
Write-Host "Backup created: $backupPath" -ForegroundColor Cyan

# The new code block to insert
$newCode = @"
            # --- FIX: Robust scalar extraction for trend data ---
            dates = pd.date_range(end=datetime.now(), periods=12, freq="MS")
            
            def _safe_scalar(val, default=1.0):
                if val is None or (isinstance(val, float) and pd.isna(val)):
                    return default
                if hasattr(val, "iloc"):
                    return float(val.iloc[0]) if len(val) > 0 else default
                if hasattr(val, "item"):
                    return float(val.item())
                if hasattr(val, "__len__") and not isinstance(val, (str, bytes)):
                    try:
                        arr = np.asarray(val)
                        return float(arr.flat[0]) if arr.size > 0 else default
                    except Exception:
                        return default
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return default
            
            spi_val = _safe_scalar(avg_spi, default=1.0)
            cpi_val = _safe_scalar(avg_cpi, default=1.0)
            
            spi_trend = [spi_val + np.sin(i * 0.5) * 0.1 for i in range(12)]
            cpi_trend = [cpi_val + np.cos(i * 0.5) * 0.08 for i in range(12)]
            
            trend_data = {"Date": list(dates), "SPI": spi_trend, "CPI": cpi_trend}
            _lengths = {k: len(v) for k, v in trend_data.items()}
            if len(set(_lengths.values())) != 1:
                target_len = len(dates)
                for k in trend_data:
                    if len(trend_data[k]) < target_len:
                        trend_data[k] = trend_data[k] + [trend_data[k][-1] if trend_data[k] else 0] * (target_len - len(trend_data[k]))
                    elif len(trend_data[k]) > target_len:
                        trend_data[k] = trend_data[k][:target_len]
            
            trend_df = pd.DataFrame(trend_data)
            # --- END FIX ---
"@

# Split into lines for processing
$lines = $content -split "`r?`n"
$modified = $false
$newCodeLines = $newCode -split "`r?`n"

for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match 'trend_df\s*=\s*pd\.DataFrame\(trend_data\)') {
        # Found the line, check context
        $startIdx = [Math]::Max(0, $i - 10)
        $context = $lines[$startIdx..$i] -join "`n"
        
        if ($context -match 'pd\.date_range' -and $context -match 'spi_trend') {
            # Replace the block
            $before = if ($startIdx -gt 0) { $lines[0..($startIdx-1)] } else { @() }
            $after = if ($i + 1 -lt $lines.Count) { $lines[($i+1)..($lines.Count-1)] } else { @() }
            $lines = @($before) + @($newCodeLines) + @($after)
            $modified = $true
            break
        }
    }
}

if (-not $modified) {
    Write-Error "Could not locate the code to fix. Please check the file manually."
    exit 1
}

# Write the fixed content
$newContent = $lines -join "`n"
Set-Content -Path $filePath -Value $newContent -Encoding UTF8

Write-Host "`nSUCCESS: Fixed applied to $filePath" -ForegroundColor Green
Write-Host "`nFix details:" -ForegroundColor Yellow
Write-Host "  1. Added _safe_scalar() helper function" -ForegroundColor White
Write-Host "     - None/NaN -> default 1.0" -ForegroundColor Gray
Write-Host "     - pandas Series -> extracts .iloc[0]" -ForegroundColor Gray
Write-Host "     - numpy arrays -> extracts first element" -ForegroundColor Gray
Write-Host "     - scalars -> standard float() conversion" -ForegroundColor Gray
Write-Host "  2. Added length validation before pd.DataFrame()" -ForegroundColor White
Write-Host "     - Auto-pads or truncates mismatched arrays" -ForegroundColor Gray
Write-Host "`nRun your Streamlit app again to test!" -ForegroundColor Green