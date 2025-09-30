# Lambda SnapStart Performance Testing Script

Write-Host "=== Lambda SnapStart Performance Analysis ===" -ForegroundColor Green
Write-Host "Starting comprehensive performance testing..." -ForegroundColor Yellow

# Configuration
$BaselineFunction = "lambda-baseline"
$SnapStartFunction = "lambda-snapstart"
$TestRounds = 5
$ConcurrentTests = 3

# Create organized directory structure for test results
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$TestRunDir = "test-results\run-$Timestamp"
$BaselineDir = "$TestRunDir\baseline"
$SnapStartDir = "$TestRunDir\snapstart"
$ReportsDir = "$TestRunDir\reports"

# Create directories if they don't exist
@($TestRunDir, $BaselineDir, $SnapStartDir, $ReportsDir) | ForEach-Object {
    if (!(Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
    }
}

Write-Host "Test results will be organized in: $TestRunDir" -ForegroundColor Cyan

# Results arrays
$BaselineResults = @()
$SnapStartResults = @()

Write-Host "`n--- Phase 1: Cold Start Performance Test ---" -ForegroundColor Cyan

# Test Baseline Function (Cold Starts)
Write-Host "Testing Baseline Lambda cold starts..." -ForegroundColor Yellow
for ($i = 1; $i -le $TestRounds; $i++) {
    Write-Host "  Round $i..." -NoNewline
    
    # Force cold start by updating environment variable
    aws lambda update-function-configuration --function-name $BaselineFunction --environment "Variables={TEST_ROUND=$i}" | Out-Null
    Start-Sleep -Seconds 2
    
    # Measure execution time
    $StartTime = Get-Date
    $ResultFile = "$BaselineDir\baseline_test_$i.json"
    $Result = aws lambda invoke --function-name $BaselineFunction $ResultFile | ConvertFrom-Json
    $EndTime = Get-Date
    $TotalTime = ($EndTime - $StartTime).TotalMilliseconds
    
    $BaselineResults += [PSCustomObject]@{
        Round       = $i
        StatusCode  = $Result.StatusCode
        TotalTimeMs = [math]::Round($TotalTime, 2)
        Type        = "ColdStart"
    }
    
    Write-Host " Done: $([math]::Round($TotalTime, 2))ms" -ForegroundColor Green
    Start-Sleep -Seconds 1
}

# Test SnapStart Function (Cold Starts)
Write-Host "`nTesting SnapStart Lambda cold starts..." -ForegroundColor Yellow
for ($i = 1; $i -le $TestRounds; $i++) {
    Write-Host "  Round $i..." -NoNewline
    
    # Force cold start by updating environment variable
    aws lambda update-function-configuration --function-name $SnapStartFunction --environment "Variables={TEST_ROUND=$i}" | Out-Null
    Start-Sleep -Seconds 2
    
    # Measure execution time
    $StartTime = Get-Date
    $ResultFile = "$SnapStartDir\snapstart_test_$i.json"
    $Result = aws lambda invoke --function-name $SnapStartFunction $ResultFile | ConvertFrom-Json
    $EndTime = Get-Date
    $TotalTime = ($EndTime - $StartTime).TotalMilliseconds
    
    $SnapStartResults += [PSCustomObject]@{
        Round       = $i
        StatusCode  = $Result.StatusCode
        TotalTimeMs = [math]::Round($TotalTime, 2)
        Type        = "ColdStart"
    }
    
    Write-Host " Done: $([math]::Round($TotalTime, 2))ms" -ForegroundColor Green
    Start-Sleep -Seconds 1
}

Write-Host "`n--- Performance Analysis Results ---" -ForegroundColor Magenta

# Calculate statistics
$BaselineAvg = ($BaselineResults.TotalTimeMs | Measure-Object -Average).Average
$BaselineMin = ($BaselineResults.TotalTimeMs | Measure-Object -Minimum).Minimum
$BaselineMax = ($BaselineResults.TotalTimeMs | Measure-Object -Maximum).Maximum

$SnapStartAvg = ($SnapStartResults.TotalTimeMs | Measure-Object -Average).Average
$SnapStartMin = ($SnapStartResults.TotalTimeMs | Measure-Object -Minimum).Minimum
$SnapStartMax = ($SnapStartResults.TotalTimeMs | Measure-Object -Maximum).Maximum

$ImprovementPercent = [math]::Round(((($BaselineAvg - $SnapStartAvg) / $BaselineAvg) * 100), 1)

Write-Host "`nCOLD START PERFORMANCE COMPARISON:" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Baseline Lambda:" -ForegroundColor Yellow
Write-Host "  Average: $([math]::Round($BaselineAvg, 2))ms"
Write-Host "  Min: $([math]::Round($BaselineMin, 2))ms"
Write-Host "  Max: $([math]::Round($BaselineMax, 2))ms"

Write-Host "`nSnapStart Lambda:" -ForegroundColor Yellow
Write-Host "  Average: $([math]::Round($SnapStartAvg, 2))ms"
Write-Host "  Min: $([math]::Round($SnapStartMin, 2))ms"
Write-Host "  Max: $([math]::Round($SnapStartMax, 2))ms"

Write-Host "`nPERFORMANCE IMPROVEMENT:" -ForegroundColor Cyan
Write-Host "  Time Reduction: $([math]::Round(($BaselineAvg - $SnapStartAvg), 2))ms"
Write-Host "  Improvement: $ImprovementPercent%" -ForegroundColor Green

# Save detailed results to organized files
$AllResults = $BaselineResults + $SnapStartResults

# Export comprehensive CSV report
$CsvReportPath = "$ReportsDir\performance-test-results.csv"
$AllResults | Export-Csv -Path $CsvReportPath -NoTypeInformation

# Create summary report
$SummaryReportPath = "$ReportsDir\performance-summary.txt"
$SummaryReport = @"
Lambda SnapStart Performance Test Summary
========================================
Test Run: $Timestamp
Test Configuration:
- Test Rounds: $TestRounds
- Baseline Function: $BaselineFunction
- SnapStart Function: $SnapStartFunction

COLD START PERFORMANCE COMPARISON:
Baseline Lambda:
  Average: $([math]::Round($BaselineAvg, 2))ms
  Min: $([math]::Round($BaselineMin, 2))ms
  Max: $([math]::Round($BaselineMax, 2))ms

SnapStart Lambda:
  Average: $([math]::Round($SnapStartAvg, 2))ms
  Min: $([math]::Round($SnapStartMin, 2))ms
  Max: $([math]::Round($SnapStartMax, 2))ms

PERFORMANCE IMPROVEMENT:
  Time Reduction: $([math]::Round(($BaselineAvg - $SnapStartAvg), 2))ms
  Improvement: $ImprovementPercent%

Files Generated:
- Baseline results: $BaselineDir\baseline_test_*.json
- SnapStart results: $SnapStartDir\snapstart_test_*.json
- Detailed CSV: $CsvReportPath
- Summary: $SummaryReportPath
"@

$SummaryReport | Out-File -FilePath $SummaryReportPath -Encoding UTF8

# Create JSON report for programmatic access
$JsonReportPath = "$ReportsDir\performance-results.json"
$JsonReport = @{
    testRun = $Timestamp
    configuration = @{
        testRounds = $TestRounds
        baselineFunction = $BaselineFunction
        snapStartFunction = $SnapStartFunction
    }
    results = @{
        baseline = @{
            average = [math]::Round($BaselineAvg, 2)
            minimum = [math]::Round($BaselineMin, 2)
            maximum = [math]::Round($BaselineMax, 2)
            rawData = $BaselineResults
        }
        snapstart = @{
            average = [math]::Round($SnapStartAvg, 2)
            minimum = [math]::Round($SnapStartMin, 2)
            maximum = [math]::Round($SnapStartMax, 2)
            rawData = $SnapStartResults
        }
        improvement = @{
            timeReductionMs = [math]::Round(($BaselineAvg - $SnapStartAvg), 2)
            improvementPercent = $ImprovementPercent
        }
    }
    files = @{
        baselineDir = $BaselineDir
        snapstartDir = $SnapStartDir
        reportsDir = $ReportsDir
    }
}

$JsonReport | ConvertTo-Json -Depth 10 | Out-File -FilePath $JsonReportPath -Encoding UTF8

Write-Host "`n=== TEST RESULTS ORGANIZATION ===" -ForegroundColor Green
Write-Host "Test Run Directory: $TestRunDir" -ForegroundColor Cyan
Write-Host "├── baseline\" -ForegroundColor Gray
Write-Host "│   └── baseline_test_*.json (Lambda response files)" -ForegroundColor Gray
Write-Host "├── snapstart\" -ForegroundColor Gray
Write-Host "│   └── snapstart_test_*.json (Lambda response files)" -ForegroundColor Gray
Write-Host "└── reports\" -ForegroundColor Gray
Write-Host "    ├── performance-test-results.csv (Detailed data)" -ForegroundColor Gray
Write-Host "    ├── performance-summary.txt (Human-readable summary)" -ForegroundColor Gray
Write-Host "    └── performance-results.json (Programmatic access)" -ForegroundColor Gray

Write-Host "`nDetailed results saved to: $CsvReportPath" -ForegroundColor Green
Write-Host "Summary report saved to: $SummaryReportPath" -ForegroundColor Green
Write-Host "JSON report saved to: $JsonReportPath" -ForegroundColor Green
Write-Host "`nTesting Complete! Check your CloudWatch dashboard for additional metrics." -ForegroundColor Yellow
