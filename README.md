# CC/iClone Blender Pipeline Plugin
**(Installed in CC4 and iClone 8)**

**This plugin is for Character Creator 4 and iClone 8, for Character Creator 3 [look here](https://github.com/soupday/CC3-Blender-Tools-Plugin)**

This is a python plugin for Character Creator 4 to re-import a character from Blender generated using the **CC4 Blender Pipeline Tool** auto-setup add-on: https://github.com/soupday/cc_blender_tools.

This plugin will re-import the selected character and reconstruct the materials exactly as specified in the character Json data, which is exported with all FbxKey exports to Blender.

The character export from Blender must be generated with the **CC/iC Blender Tools** add-on as the Fbx export must be carefully altered to be compliant with CC4 and having exactly matching Object and Material names with the FbxKey, and also must have all relevent texture paths updated and changes to the material parameters written back to the exported Json data.

It is possible to include additional objects with the character exports from Blender by selecting them along with the character, but they must be parented to the character armature and have an armature modifier with valid vertex weights, otherwise CC4 will ignore them.

Installation
============

### Upgrading
- **Important**: Remove **all** previous versions of this plug-in from the OpenPlugin folder.
    - Existing previous versions will cause conflicts with the current version and it _will not_ work correctly.
- Follow the Manual Installation procedure below.

### Manual Installation
- Download the Zip file (__CCiC-Blender-Pipeline-Plugin-main.zip__) from the [**Code** button](https://github.com/soupday/CCiC-Blender-Pipeline-Plugin/archive/refs/heads/main.zip).
- Unzip the zip file. There should be a folder: **CCiC-Blender-Pipeline-Plugin-main**
- Create the folder **OpenPlugin** in the <Character Creator 4 install directory>**\Bin64\OpenPlugin**
    - e.g: **C:\Program Files\Reallusion\Character Creator 4\Bin64\OpenPlugin**
- Copy or move the folder CC4-Blender-Tools-Plugin-main into the **OpenPlugin** folder.
    - e.g: **C:\Program Files\Reallusion\Character Creator 4\Bin64\OpenPlugin\CC4-Blender-Tools-Plugin-main**
- The plugin functionality can be found from the menu: **Plugins > Blender Pipeline**

### Run Without Installing
- Alternatively the main.py script can run as a standalone script from the **Script > Load Python** menu.

Troubleshooting
===============

If after installing this plugin the plugin menu does not appear in Character Creator:

- Make sure you are using the correct version of the plugin for your version of Character Creator:
    - Character Creator 3: [CC3 Blender Tools Plugin](https://github.com/soupday/CC3-Blender-Tools-Plugin)
    - Character Creator 4 / iClone 8: [CC/iC Blender Pipeline Plugin](https://github.com/soupday/CCiC-Blender-Pipeline-Plugin)
- Make sure your version of Character Creator / iClone is up to date.
- If the plugin still does not appear it may be that the Python API did not installed correctly and you may need to re-install Character Creator from the Reallusion Hub.

Links
=====

[CC/iC Blender Tools](https://github.com/soupday/cc_blender_tools)

[Baking Add-on](https://github.com/soupday/CC3_blender_bake)

## Demo Videos

1st Demo Video: https://youtu.be/gRhbcTSt118
(Mesh editing and material parameters)

2nd Demo Video: https://youtu.be/T4ZU1EmJya0
(Using material nodes to modify textures during export)

3rd Demo Video: https://youtu.be/sr5dWQE6nQ0
(Object Management and Item creation Demo)

Known Issues
============

- By default the FBX export settings have embed textures switched on, but this makes the export incompatible with re-importing the character back into CC4 as the textures are hidden in the original Fbx and are not accessible to the file system.
**Always turn off embed textures.**

- Hidden faces information for clothing and accessories is lost upon re-importing into CC4.

Changelog
=========

### 2.2.5 (In Progress)
- Added selection box for available Blender versions to Go-B to.

### 2.2.4
- Set keyframes option, when toggled off Send Pose and Sequence will not create an action or set any keyframes.
- Fixed displacement channel strength being overridden by normal channel.

### 2.2.3
- Corrected avatar type detection on importing characters, preventing facial profile restore.

### 2.2.2
- Facial expression drivers will only be used when bones control expressions in Blender (i.e. Rigify)
- When another instance of Blender connects to DataLink, the previous connection will be correctly terminated.

### 2.2.1
- Plugin toolbar visibility can now be toggled.
- DataLink Receive Sequence will calculate facial expressions for the Eye look and Jaw open expressions based on the bone rotations.
- DataLink send motion will use correct project FPS.

### 2.2.0
- Fix to motion exports not using project FPS.
- Fix to datalink not detecting MD Props on send.
- Default datalink path changed to user documents folder.

### 2.1.10
- Support for exporting MDProps.
- Update materials through the datalink will use exact name matching and will no longer update materials on partial name matches.

### 2.1.9
- Some UI Restructure.
- Fix to exporting Lite Avatars.

### 2.1.7
- Normal map fix for imported characters.
- Sync lights includes scene IBL from visual settings.

### 2.1.6
- Export supports selection of multiple objects.
    - When exporting multiple objects, the exporter will create a folder and export each individual object to that folder.
    - When importing into Blender, all the FBX objects should be selected and imported all at once.

### 2.1.5
- Go-B Morph will use existing connection if there is one.
- Re-importing GameBase/ActorCore/AccuRig morph crash fix.
- GameBase and AccuRig characters will always export from CC4 with facial expression profile and data.

### 2.1.4
- Send Update / Replace function, for sending additions or replacements to selected meshes or whole characters.
- Settings detect and find button.
- Scrollable datalink window.

### 2.1.3
- Expression rotation corrections check for existence of expression, as sometimes (ActorCore) they aren't really there.

### 2.1.2
- Replace mesh searches sub-object names as well as mesh names for object / mesh name matching.
    - Note: Replace mesh does not currently work for conformed facial hair meshes (Beard / Brows).

### 2.1.0
- Motion set prefix and use fake user option for datalink animation transfer.
- DataLink pose/sequence twist bone translation fix.

### 2.0.9
- DataLink:
    - Live Sequence speed improvements.
    - Receive Replace Mesh function.
    - Receive Material/Texture updates.
    - Sequence / Pose transfer takes facial expression bone rotations into account.
    - Live Sequence stop button.

### 2.0.8
- Fix to error messages when importing invalid characters.
- Send Prop pose and sequence.
    - DataLink skeleton bone order enforced, for more accurate matching of duplicate bone names.
    - Adds prop structure data to json export.
- Send Motion to Blender character/prop (direct motion export/import).
- More robust & partial name matching for json meshes and materials.
- iC motion export settings fix.

### 2.0.7
- DataLink receives facial expression data for pose and sequence.
- DataLink settings for exporting characters with animation, pose or none.

### 2.0.5
- Receiving pose or animation sequence from Blender resets character transform.
- Better data transfer rate synchronization. iClone/Blender will drop view port updates to maintain transfer speed.

### 2.0.4
- Prop posing disabled for now until a solution can be found to match or remove the pivot bones.
- Go-B launch fix when link not listening or connected.
- Version sync with Blender Add-on.

### 2.0.3
- Context enable/disable buttons

### 2.0.2
- iClone export settings.
- Character generation correction on export of ActorBuild or ActorScan (were exporting as AccuRig).
- Non-standard characters always export from CC4 with HIK and facial profile.

### 2.0.1
- GoB toolbar added.
    - Go-B, Go-B morph, Export, Import, DataLink, Settings.
    - Plugin settings for Blender Path, DataLink working directory, Morph slider default path.
    - Go-B automatically launches blender and imports selected characters/props into Blender, matches lighting and camera.
    - In Blender single button click to send back character or character morph (if morph editing with Go-B Morph).
- DataLink:
    - Prop import/export. Currently props aren't cooperating when posing.
    - Lighting and Camera Sync added
    - Receive Character import direct from Blender.
    - Receive Morph import direct from Blender with automatic slider creation.
    - Send facial expressions and visemes with character pose and animation sequences.
        - Currently not receiving these back into CC4. Didn't get around to it this time.
- Fixes Accessory name duplication by CC4 causing material detection to fail. (White material fix)

### 2.0.0
- Code refactored
- WIP Data Link added

### 1.1.4
- Fix for importing from UNC network paths.

### 1.1.3
- Temporarily blocked the facial expression import of Jaw, EyeLook and Head categories as a bug in CC4 breaks the relationship between the expression blend shape and the facial bones.

### 1.1.2
- Export toggle buttons and info labels.

### 1.1.1
- Characterization import for non-standard humanoid characters now working.
- Accessory physics export / import fixed.

### 1.1.0
- Added HIK profile export/import for Humanoid Characters.
- Added Facial profile export/import for Standard and humanoid Characters.
- Added Facial expression Blend shape import for Standard and humanoid Characters.

### 1.0.10
- Fixed long path names causing textures to fail to load.

### 1.0.9
- Physics data reconstruction now includes hair meshes.
- Added export menu option to export with current pose. (For replace mesh and/or accessory editing)

### 1.0.8
- Support for importing props.
- Fix for empty texture paths.

### 1.0.7
- Unlocked import for non-standard characters (Humanoid, Creature, Prop), no longer requires an FBX key.
    - But do still require JSON data from the CC/iC Blender Tools add-on export.
- Fixed Diffuse maps with Alpha channels not applying Opacity channel on import.

### 1.0.6
- SSS and Tessellation data restoration added.
- Physics data restoration added.
- Added Export To Blender menu function.
- Some support for Humanoid imports.
    - Recommended that you Save the HIK profile in the **Modify** > **Characterization** panel first, then reload the profile and activate the Human-IK on re-importing.

### 1.0.5
- Ported to CC4

### 1.0.4
- Fixed AO Maps causing Bump maps to import with zero strength.
- Added Fbx Key check and warning message box.
- Added JSON data check and warning message box.

### 1.0.3
- Fixed error with absolute texture paths on different drives from the FBX file.

### 1.0.2
- First attempt to add automatic export button to CC4. (Didn't work, CC4 API needs updating, disabled for now.)

### 1.0.1
- Progress bars added.
- Fixed Duplicate materials causing Pbr import errors.

### 1.0.0
- First Release.


