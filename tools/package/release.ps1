$ErrorActionPreference = "Stop"

# Windows PowerShell 5.1 does not load System.Net.Http by default (HttpClient / HttpClientHandler).
Add-Type -AssemblyName System.Net.Http

if (-not ("TrackingReadStream" -as [type])) {
Add-Type -Language CSharp @"
using System;
using System.IO;
using System.Threading;

public sealed class TrackingReadStream : Stream
{
    private readonly Stream _inner;
    private long _bytesRead;

    public TrackingReadStream(Stream inner)
    {
        if (inner == null)
        {
            throw new ArgumentNullException("inner");
        }
        _inner = inner;
    }

    public long BytesRead
    {
        get { return Interlocked.Read(ref _bytesRead); }
    }

    public override bool CanRead { get { return _inner.CanRead; } }
    public override bool CanSeek { get { return _inner.CanSeek; } }
    public override bool CanWrite { get { return false; } }
    public override long Length { get { return _inner.Length; } }

    public override long Position
    {
        get { return _inner.Position; }
        set { _inner.Position = value; }
    }

    public override void Flush()
    {
        _inner.Flush();
    }

    public override int Read(byte[] buffer, int offset, int count)
    {
        int read = _inner.Read(buffer, offset, count);
        if (read > 0)
        {
            Interlocked.Add(ref _bytesRead, read);
        }
        return read;
    }

    public override long Seek(long offset, SeekOrigin origin)
    {
        return _inner.Seek(offset, origin);
    }

    public override void SetLength(long value)
    {
        _inner.SetLength(value);
    }

    public override void Write(byte[] buffer, int offset, int count)
    {
        throw new NotSupportedException();
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _inner.Dispose();
        }
        base.Dispose(disposing);
    }
}
"@
}

function Format-ByteSize {
    param([long]$Bytes)

    if ($Bytes -lt 1KB) { return "$Bytes B" }
    if ($Bytes -lt 1MB) { return "{0:N2} KB" -f ($Bytes / 1KB) }
    if ($Bytes -lt 1GB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
    return "{0:N2} GB" -f ($Bytes / 1GB)
}

function Format-Duration {
    param([double]$Seconds)

    if ($Seconds -lt 60) {
        return "{0:N0}s" -f [Math]::Ceiling($Seconds)
    }

    $ts = [TimeSpan]::FromSeconds([Math]::Ceiling($Seconds))
    if ($ts.TotalHours -ge 1) {
        return "{0:%h}h {0:%m}m {0:%s}s" -f $ts
    }

    return "{0:%m}m {0:%s}s" -f $ts
}

function Get-GitHubToken {
    if ($env:GH_TOKEN) { return $env:GH_TOKEN }
    if ($env:GITHUB_TOKEN) { return $env:GITHUB_TOKEN }

    $token = (& gh auth token 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $token) {
        throw "Could not retrieve GitHub token. Please run 'gh auth login' or set GH_TOKEN."
    }

    return $token.Trim()
}

function Get-RepoSlug {
    $remoteUrl = (& git remote get-url origin 2>$null)
    if ($LASTEXITCODE -eq 0 -and $remoteUrl) {
        $remoteUrl = $remoteUrl.Trim()

        if ($remoteUrl -match 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+?)(?:\.git)?$') {
            return "$($Matches.owner)/$($Matches.repo)"
        }
    }

    $repoSlug = (& gh repo view --json nameWithOwner --jq ".nameWithOwner" 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $repoSlug) {
        throw "Could not determine GitHub repository slug from git remote or gh CLI."
    }

    return $repoSlug.Trim()
}

function Get-ReleaseInfo {
    param(
        [Parameter(Mandatory = $true)][string]$RepoSlug,
        [Parameter(Mandatory = $true)][string]$Tag,
        [int]$MaxAttempts = 6,
        [int]$InitialDelaySeconds = 2
    )

    $delaySeconds = [Math]::Max(1, $InitialDelaySeconds)

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        $json = & gh api "repos/$RepoSlug/releases/tags/$Tag" 2>$null
        if ($LASTEXITCODE -eq 0 -and $json) {
            return $json | ConvertFrom-Json
        }

        if ($attempt -lt $MaxAttempts) {
            Write-Host ("Release metadata for tag '{0}' is not ready yet. Retry {1}/{2} in {3}s..." -f $Tag, $attempt, $MaxAttempts, $delaySeconds) -ForegroundColor DarkYellow
            Start-Sleep -Seconds $delaySeconds
            $delaySeconds = [Math]::Min($delaySeconds * 2, 10)
        }
    }

    throw "Could not load release info for tag '$Tag' after $MaxAttempts attempts."
}

function Remove-ExistingAssetIfNeeded {
    param(
        [Parameter(Mandatory = $true)][string]$RepoSlug,
        [Parameter(Mandatory = $true)]$ReleaseInfo,
        [Parameter(Mandatory = $true)][string]$AssetName
    )

    $existingAsset = $ReleaseInfo.assets | Where-Object { $_.name -eq $AssetName } | Select-Object -First 1
    if (-not $existingAsset) {
        return
    }

    Write-Host "Deleting existing asset '$AssetName'..." -ForegroundColor Yellow
    & gh api --method DELETE "repos/$RepoSlug/releases/assets/$($existingAsset.id)" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to delete existing asset '$AssetName'."
    }
}

function Upload-ReleaseAssetWithProgress {
    param(
        [Parameter(Mandatory = $true)]$ReleaseInfo,
        [Parameter(Mandatory = $true)][string]$ZipPath,
        [Parameter(Mandatory = $true)][string]$AssetName,
        [Parameter(Mandatory = $true)][string]$Token
    )

    $uploadUrlBase = $ReleaseInfo.upload_url -replace '\{\?name,label\}$', ''
    $uploadUrl = "${uploadUrlBase}?name=$([System.Uri]::EscapeDataString($AssetName))"

    $fileInfo = Get-Item -LiteralPath $ZipPath
    $totalBytes = $fileInfo.Length
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $progressState = @{
        LastConsoleUpdateMs = -1
    }

    Write-Host "Uploading asset with progress..." -ForegroundColor Cyan
    Write-Host ("Asset: {0}" -f $AssetName) -ForegroundColor Gray
    Write-Host ("Size:  {0}" -f (Format-ByteSize $totalBytes)) -ForegroundColor Gray

    $rawFileStream = $null
    $trackingStream = $null
    $client = $null
    $content = $null

    try {
        $rawFileStream = [System.IO.File]::Open($ZipPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
        $trackingStream = New-Object TrackingReadStream($rawFileStream)

        # HttpClientHandler works on Windows PowerShell 5.1; SocketsHttpHandler requires .NET Core / PS 7+.
        $handler = New-Object System.Net.Http.HttpClientHandler
        $handler.AllowAutoRedirect = $false

        $client = New-Object System.Net.Http.HttpClient($handler)
        $client.Timeout = [TimeSpan]::FromHours(2)
        $client.DefaultRequestHeaders.Authorization = [System.Net.Http.Headers.AuthenticationHeaderValue]::new("Bearer", $Token)
        $client.DefaultRequestHeaders.UserAgent.ParseAdd("cultivation-world-simulator-release-script")
        $client.DefaultRequestHeaders.Accept.ParseAdd("application/vnd.github+json")
        $client.DefaultRequestHeaders.Add("X-GitHub-Api-Version", "2022-11-28")

        $renderProgress = {
            param([long]$uploadedBytes)
            $percent = if ($totalBytes -gt 0) { [Math]::Min(100, ($uploadedBytes / $totalBytes) * 100) } else { 100 }
            $elapsedSeconds = [Math]::Max($sw.Elapsed.TotalSeconds, 0.001)
            $speedBytesPerSec = $uploadedBytes / $elapsedSeconds
            $remainingSeconds = if ($speedBytesPerSec -gt 0 -and $uploadedBytes -lt $totalBytes) {
                ($totalBytes - $uploadedBytes) / $speedBytesPerSec
            } else {
                0
            }

            Write-Progress -Activity "Uploading GitHub release asset" `
                -Status ("{0:N1}% | {1} / {2} | {3}/s | ETA {4}" -f $percent, (Format-ByteSize $uploadedBytes), (Format-ByteSize $totalBytes), (Format-ByteSize ([long]$speedBytesPerSec)), (Format-Duration $remainingSeconds)) `
                -PercentComplete $percent

            if ($progressState.LastConsoleUpdateMs -lt 0 -or ($sw.ElapsedMilliseconds - $progressState.LastConsoleUpdateMs) -ge 1000 -or $uploadedBytes -eq $totalBytes) {
                $progressState.LastConsoleUpdateMs = $sw.ElapsedMilliseconds
            }
        }

        $content = [System.Net.Http.StreamContent]::new($trackingStream)
        $content.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/zip")
        $content.Headers.ContentLength = $totalBytes

        $uploadTask = $client.PostAsync($uploadUrl, $content)
        while (-not $uploadTask.IsCompleted) {
            Start-Sleep -Milliseconds 500
            & $renderProgress $trackingStream.BytesRead
        }

        & $renderProgress $trackingStream.BytesRead
        $response = $uploadTask.GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) {
            $responseBody = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
            throw "GitHub asset upload failed with status $([int]$response.StatusCode) $($response.ReasonPhrase). $responseBody"
        }

        Write-Progress -Activity "Uploading GitHub release asset" -Completed
        $sw.Stop()
        Write-Host ("Upload completed in {0}." -f (Format-Duration $sw.Elapsed.TotalSeconds)) -ForegroundColor Green
    } catch {
        $errorDetails = $_.Exception.Message
        $inner = $_.Exception.InnerException
        while ($inner) {
            $errorDetails += " | Inner: $($inner.Message)"
            $inner = $inner.InnerException
        }

        throw "Release asset upload failed. $errorDetails"
    } finally {
        if ($content) { $content.Dispose() }
        if ($client) { $client.Dispose() }
        if ($trackingStream) { $trackingStream.Dispose() }
        elseif ($rawFileStream) { $rawFileStream.Dispose() }
    }
}

# ==============================================================================
# 1. Environment & Path Setup
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

# ==============================================================================
# 2. Get Git Tag (Version)
# ==============================================================================
Push-Location $RepoRoot
try {
    $tag = git describe --tags --abbrev=0 2>$null
    if (-not $tag) {
        throw "Git tag not found"
    }
    $tag = $tag.Trim()
} catch {
    Write-Error "Could not determine git tag. Please ensure this is a git repository with at least one tag."
    exit 1
} finally {
    Pop-Location
}

Write-Host "Target Release Version (Tag): $tag" -ForegroundColor Cyan

# ==============================================================================
# 3. Build & Compress
# ==============================================================================
# # Call pack.ps1 to build executable
# Write-Host "`n>>> [1/3] Building package (pack.ps1)..." -ForegroundColor Cyan
# & "$ScriptDir\pack.ps1"

# # Call compress.ps1 to create archive
# Write-Host "`n>>> [2/3] Compressing archive (compress.ps1)..." -ForegroundColor Cyan
# & "$ScriptDir\compress.ps1"

# ==============================================================================
# 4. GitHub Release
# ==============================================================================
$ZipFileName = "AI_Cultivation_World_Simulator_${tag}.zip"
$ZipPath = Join-Path $RepoRoot "tmp\$ZipFileName"
$RepoSlug = $null
$GitHubToken = $null

if (-not (Test-Path $ZipPath)) {
    Write-Error "Archive not found: $ZipPath"
    exit 1
}

Write-Host "`n>>> [3/3] Processing GitHub Release..." -ForegroundColor Cyan

# Check if release exists using gh cli
$releaseExists = $false
try {
    # Temporarily ignore errors to check for existence
    $null = gh release view $tag 2>&1
    if ($LASTEXITCODE -eq 0) {
        $releaseExists = $true
    }
} catch {
    # If gh returns non-zero or writes to stderr, it might throw due to ErrorActionPreference='Stop'
    $releaseExists = $false
}


# Ensure tag is pushed to remote before creating/updating release
Write-Host "Ensuring tag '$tag' is pushed to remote..."
git push origin $tag
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to push tag to origin. If the tag already exists on remote, this is fine."
}

if ($releaseExists) {
    Write-Warning "Release '$tag' already exists. Updating to 'latest' and uploading assets..."
    # Ensure it is not a draft and is marked as latest
    gh release edit $tag --draft=false --latest
    if ($LASTEXITCODE -ne 0) { Write-Warning "Could not update release status (might already be correct)." }
} else {
    Write-Host "Creating new release (latest)..."
    # --latest: Mark as latest release
    # --generate-notes: Auto-generate notes from git commits
    gh release create $tag --title "$tag" --generate-notes --latest
    if ($LASTEXITCODE -ne 0) { throw "Failed to create release." }
}

$RepoSlug = Get-RepoSlug
$GitHubToken = Get-GitHubToken
$releaseInfo = Get-ReleaseInfo -RepoSlug $RepoSlug -Tag $tag

Remove-ExistingAssetIfNeeded -RepoSlug $RepoSlug -ReleaseInfo $releaseInfo -AssetName $ZipFileName
Upload-ReleaseAssetWithProgress -ReleaseInfo $releaseInfo -ZipPath $ZipPath -AssetName $ZipFileName -Token $GitHubToken

Write-Host "Verifying uploaded asset..." -ForegroundColor Cyan
$verifiedReleaseInfo = Get-ReleaseInfo -RepoSlug $RepoSlug -Tag $tag
$uploadedAsset = $verifiedReleaseInfo.assets | Where-Object { $_.name -eq $ZipFileName } | Select-Object -First 1
if (-not $uploadedAsset) {
    throw "Upload finished but asset '$ZipFileName' was not found on the release."
}

Write-Host "`n[Success] Release process completed!" -ForegroundColor Green
Write-Host ("View Release: {0}" -f $verifiedReleaseInfo.html_url)
