:: https://blog.danskingdom.com/allow-others-to-run-your-powershell-scripts-from-a-batch-file-they-will-love-you-for-it/
@ECHO OFF
SET pwd=%~dp0
SET PSScriptPath=%pwd%InstallScript.ps1
:: PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& '%PSScriptPath%'";
PowerShell -NoProfile -ExecutionPolicy Bypass -Command "& {Start-Process PowerShell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%PSScriptPath%""' -Verb RunAs}";