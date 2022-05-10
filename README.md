# CC4 Blender Tools Plugin

Conversion to CC4 so far...

Known issues:

RLPy.RFileIO.ExportFbxFile
- Does not work.
- Unable to export physics data to Blender.

physics_component = obj.GetPhysicsComponent()
- Unable to find object handles for Hair meshes, thus cannot get physics data for hair objects.
