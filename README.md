# CC4 Blender Tools Plugin

Conversion to CC4 so far...

Known issues:

physics_component = obj.GetPhysicsComponent()
- Unable to find object handles for Hair meshes, thus cannot get/set physics data for hair objects.

Physics Sim:
- After importing character from Blender, the collision shapes are missing.
    - Saving the project and reloading seems to fix it.
- Remember to turn on Soft Cloth Simulation, otherwise the physics won't work in the CC4 Animation player.
