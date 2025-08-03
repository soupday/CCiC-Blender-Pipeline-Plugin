This document refers to the Character Creator & iClone plugin (https://github.com/soupday/CCIC-Unity-Tools-Plugin) for use with the Character Creator/iClone Unity tools (https://github.com/soupday/CCiC-Unity-Tools).

iClone version 8, and Character Creator versions 4 and 5 are supported.

TLDR
====
Close iClone and/or Character Creator.
Place this folder **somewhere permanent**.
To Install: Double click 'Install.bat' to link this folder to iClone or Character Creator.
To Uninstall: Double click on 'Uninstall.bat' to remove the links.
To move folder - use Uninstall.bat followed by Install.bat after move (don't change the folder name).


Installation
============

After downloading and unpacking the .zip file from github (direct download from <>Code -> Download ZIP), place the extracted folder somewhere appropriate (the folder will need to remain in that location).  Or if cloning the GitHub repository (either by command line or with GitHub desktop) then pick a suitable location to clone the repo to.

Close iClone and/or Character Creator.

In the extracted/cloned folder (which contains this readme), double click on the 'Install.bat' file (do not move the .bat or .ps1 files; the installer will link to the folder they are run from).  This will cause a UAC (User Account Control) check on wether you wish to make changes to the device. Click 'Yes' to continue.

** If you have any doubts about the nature of the changes being made; firstly ensure that you downloaded or cloned this package from https://github.com/soupday/CCIC-Unity-Tools-Plugin; then open the 'InstallScript.ps1' file (in this folder) in notepad or VS Code (or similar) and examine the code.

** The UAC check allows the script to:
  - Examine the registry for the installation location of iClone and/or Character Creator
  - Create a plugin subdirectory with 'New-Item -Path "$entryValue\$subFolder" -ItemType Directory'
  - Create a directory junction within the plugin subdirectory to this folder with 'cmd /c mklink /J "$junctionPath" "$scriptFolder"'

Clicking 'Yes' will create directory junctions in the appropriate iClone and/or Character Creator directories which will allow those applications to use this plugin automatically.

Moving the folder will break the links made by the installer, so you must run Uninstall.bat (to remove the links) before re-running Install.bat

Close and restart iClone and/or Character Creator (if you didn't already close them).


Uninstallation
==============

In the extracted/cloned folder (which contains this readme), double click on the 'Install.bat' file.  This will cause a UAC check on wether you wish to make changes to the device. Click 'Yes' to continue.

** If you have any doubts about the nature of the changes being made; firstly ensure that you downloaded or cloned this package from https://github.com/soupday/CCIC-Unity-Tools-Plugin; then open the 'UnInstallScript.ps1' file (in this folder) in notepad or VS Code (or similar) and examine the code.

** The UAC check allows the script to:
  - Examine the registry for the installation location of iClone and/or Character Creator
  - Delete existing directory junctions pointing to this folder using 'cmd /c rmdir $junctionPath'

Clicking 'Yes' will remove the links created by 'Install.bat'

Close and restart iClone and/or Character Creator.


Moving Folder location
======================

Avoid changing the folder name.

If you need to move the folder containing the plugin then this will break any previously existing links.  This can be fixed by running 'Uninstall.bat' (to remove the links) before re-running 'Install.bat'.

Restart iClone and/or Character Creator afterwards.


Manual Installation
===================

- Navigate to the install location of iClone or Character Creator.
- In the 'iClone 8' or 'Character Creator 4/5' folder navigate to the Bin64 folder.
- Inside 'Bin64', ensure that there is a subdirectory called 'OpenPlugin'.
- Inside OpenPlugin you can either
   copy this whole folder into its OWN subdirectory (giving ...\Bin64\OpenPlugin\FolderName\...contents)
   or create a directory junction to the location of this folder with `mklink /J "path\to\Bin64\OpenPlugin\Folder Name" "path\to\this\folder"` in an administrator command prompt.

- Restart iClone and/or Character Creator.


Manual Uninstallation
=====================

- Navigate to the install location of iClone or Character Creator and find the Bin64\OpenPlugin folder.
- Delete either the junction or folder you created in the manual step above.

- Restart iClone and/or Character Creator.