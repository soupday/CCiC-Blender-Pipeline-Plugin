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

function Add-Junction($keyPath){
    $keyExists = Test-Path -Path $keyPath
    if($keyExists){
        Write-Host "`n Found $keyPath in the registry."

        # check if the entry "Install Path" is present within the key
        $entryExists = Get-ItemProperty -Path $keyPath -Name $valueName -ErrorAction SilentlyContinue

        if ($entryExists){
            $entryValue = Get-ItemPropertyValue -Path $keyPath -Name $valueName

            # check if subfolder is present under the install path
            $subFolderExists = Test-Path -Path "$entryValue\$subFolder"

            if($subFolderExists){
                Write-Host "`n $subFolder folder exists (in $entryValue)."
            }else{
                Write-Host "`n Creating $subFolder folder in $entryValue."
                New-Item -Path "$entryValue\$subFolder" -ItemType Directory
            }

            # create a directory junction to the folder containing this script
            $junctionPath = "$entryValue\$subFolder\$scriptFolderName"

            $junctionExists = Test-Path -Path $junctionPath
            if($junctionExists){
                Write-Host "`n Folder link $junctionPath already exists."
                cmd /c rmdir $junctionPath
                Write-Host "`n Folder link $junctionPath deleted."
            }
            $junctionExists = Test-Path -Path $junctionPath
            if(!$junctionExists){
                cmd /c mklink /J "$junctionPath" "$scriptFolder" | Out-Null
                Write-Host "`n Folder link $junctionPath has been created."
            }
        }else{
            Write-Host "`n Cannot find $valueName in the registry key... skipping."
        }
    }else{
        Write-Host "`n Cannot find $keyPath in the registry... skipping."
    }
}

Write-Host "`n************************************************************************"
Write-Host "`n This script will create links that allow iClone/Character Creator`n to use the plugin contained in this folder - Please ensure that this`n folder stays in its current location (or the links will break).`n`n [If you need to move the folder then run the Uninstall.bat file before`n re-running the Install.bat file.]"
Write-Host "`n************************************************************************`n"

$keyPaths = @($iCloneKeyPath, $charCreatorKeyPath, $charCreatorFiveKeyPath)

foreach ($entry in $keyPaths){
    Write-Host "`n`n Processing $entry ..."

    Add-Junction($entry)
}

Write-Host "`n`n Process Complete - Press any key to exit...`n"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")