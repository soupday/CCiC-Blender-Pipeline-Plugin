# CC4 Blender Tools Plugin

Conversion to CC4 so far...

Known issues:

physics_component = obj.GetPhysicsComponent()
- Unable to find object handles for Hair meshes, thus cannot get/set physics data for hair objects.

Physics Colliders:
- After importing character there are no physics colliders (or they are in the wrong place)
- Saving and reloading the project fixes this, so it's a temporary problem.
