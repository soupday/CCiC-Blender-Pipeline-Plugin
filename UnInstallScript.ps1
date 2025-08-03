# elevation handled by the calling .bat file to allow script execution policy override
<#
param([switch]$elevated)

function Test-Admin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal $([Security.Principal.WindowsIdentity]::GetCurrent())
    $currentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

if ((Test-Admin) -eq $false)  {
    if ($elevated) {
        # tried to elevate, did not work, aborting
    } else {
        Start-Process powershell.exe -Verb RunAs -ArgumentList ('-noprofile -noexit -file "{0}" -elevated' -f ($myinvocation.MyCommand.Definition))
    }
    exit
}
#>

# registry vars
$iCloneKeyPath = "HKLM:\SOFTWARE\Reallusion\iClone\8.0"
$charCreatorKeyPath = "HKLM:\SOFTWARE\Reallusion\Character Creator\4.0"
$charCreatorFiveKeyPath = "HKLM:\SOFTWARE\Reallusion\Character Creator\5.0"
$valueName = "Install Path"

# path vars
$subFolder = "OpenPlugin"

# script vars
$scriptFolder = $PSScriptRoot
#$scriptFolderName = Split-Path -Path $scriptFolder -Leaf
$scriptFolderName = "Blender Pipeline Plugin"

function Remove-Junction($keyPath){
    $keyExists = Test-Path -Path $keyPath
    if($keyExists){
        Write-Host "`n Found $keyPath in the registry."

        # check if the entry "Install Path" is present within the key
        $entryExists = Get-ItemProperty -Path $keyPath -Name $valueName -ErrorAction SilentlyContinue

        if ($entryExists){
            $entryValue = Get-ItemPropertyValue -Path $keyPath -Name $valueName

            # find directory junction
            $junctionPath = "$entryValue\$subFolder\$scriptFolderName"
            $junctionExists = Test-Path -Path $junctionPath

            if($junctionExists){
                cmd /c rmdir $junctionPath
                Write-Host "`n Folder link $junctionPath deleted."
            }else{
                Write-Host "`n Expected folder link $junctionPath is absent."
            }
        }else{
            Write-Host "`n Cannot find $valueName in the registry key... skipping."
        }
    }else{
        Write-Host "`n Cannot find $keyPath in the registry... skipping."
    }
}

Write-Host "`n*******************************************************************"
Write-Host "`n This script will remove links created by the installation script."
Write-Host "`n*******************************************************************"

$keyPaths = @($iCloneKeyPath, $charCreatorKeyPath, $charCreatorFiveKeyPath)

foreach ($entry in $keyPaths){
    Write-Host "`n`n Processing $entry ..."

    Remove-Junction($entry)
}

Write-Host "`n`n Process Complete - Press any key to exit...`n"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")