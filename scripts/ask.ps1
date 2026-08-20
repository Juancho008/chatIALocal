param(
    [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)]
    [string[]]$Message
)

$text = $Message -join " "
$bodyObj = [ordered]@{
    model    = "phi4-mini"
    stream   = $false
    messages = @(
        [ordered]@{ role = "user"; content = $text }
    )
    options  = [ordered]@{ num_ctx = 2048 }
}
$body = $bodyObj | ConvertTo-Json -Depth 6 -Compress
# Windows PowerShell 5 serializes booleans as True/False; JSON needs false.
$body = $body.Replace(":True", ":true").Replace(":False", ":false")

$bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
$resp = Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method Post -ContentType "application/json; charset=utf-8" -Body $bytes -TimeoutSec 300
$resp.message.content
