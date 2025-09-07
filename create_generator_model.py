# Blender (bpy) script to procedurally create a 1:1 scale magnetic energy generator model
# - Wooden base 0.30 x 0.30 m
# - Vertical steel shaft with rotating disk holding 8 cube magnets (red/blue poles)
# - Four fixed copper coils (yellow) around the disk
# - Green PCB with bridge rectifier and aluminum heat sink (fins)
# - Blue 12V battery and gray 500W inverter with red/black cables
# - PBR-like materials, simple studio lighting, Cycles renderer
# - Exports to /tmp/magnetic_generator.glb (change path as needed)
#
# Usage:
# - Open Blender, Text > New, paste this file and Run Script
# OR (headless): blender --background --python create_generator_model.py

import bpy
import math
from mathutils import Vector, Euler

# ---------- Helpers ----------

def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # remove orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def create_material(name, base_color=(1,1,1,1), metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = base_color
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    return mat


def add_mesh_cube(name, size=0.1, location=(0,0,0), rotation=(0,0,0), material=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size/2, size/2, size/2)  # because size=1 cube default
    bpy.ops.object.transform_apply(scale=True)
    if material:
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
    return obj


def add_cylinder(name, radius=0.05, depth=0.01, location=(0,0,0), rotation=(0,0,0), material=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    return obj


def add_torus(name, major_radius=0.05, minor_radius=0.01, location=(0,0,0), rotation=(0,0,0), material=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    return obj


def add_plane(name, size_x=1.0, size_y=1.0, thickness=0.02, location=(0,0,0), material=None):
    # create a thin box as wooden base
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size_x/2, size_y/2, thickness/2)
    bpy.ops.object.transform_apply(scale=True)
    if material:
        obj.data.materials.append(material)
    return obj


def add_bezier_cable(name, points, bevel_depth=0.003, material=None):
    curve_data = bpy.data.curves.new(name + "_curve", type='CURVE')
    curve_data.dimensions = '3D'
    poly = curve_data.splines.new('BEZIER')
    poly.bezier_points.add(len(points)-1)
    for i, p in enumerate(points):
        bp = poly.bezier_points[i]
        bp.co = Vector(p)
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    curve_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_obj)
    curve_data.bevel_depth = bevel_depth
    curve_data.bevel_resolution = 6
    if material:
        # convert to mesh later or assign material to curve (works in export)
        if curve_obj.data.materials:
            curve_obj.data.materials[0] = material
        else:
            curve_obj.data.materials.append(material)
    return curve_obj

# ---------- Scene Setup ----------
clean_scene()
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0  # meters

# Materials
mat_wood = create_material("Wood", base_color=(0.44,0.27,0.12,1), metallic=0.0, roughness=0.6)
mat_steel = create_material("Steel", base_color=(0.8,0.85,0.9,1), metallic=1.0, roughness=0.18)
mat_magnet_red = create_material("MagnetRed", base_color=(0.8,0.05,0.05,1), metallic=0.0, roughness=0.25)
mat_magnet_blue = create_material("MagnetBlue", base_color=(0.05,0.2,0.8,1), metallic=0.0, roughness=0.25)
mat_copper = create_material("Copper", base_color=(0.85,0.45,0.2,1), metallic=1.0, roughness=0.3)
mat_coil_yellow = create_material("CoilYellow", base_color=(0.95,0.82,0.2,1), metallic=0.1, roughness=0.35)
mat_plastic = create_material("Plastic", base_color=(0.95,0.95,0.95,1), metallic=0.0, roughness=0.45)
mat_pcb = create_material("PCB", base_color=(0.06,0.5,0.06,1), metallic=0.0, roughness=0.35)
mat_battery = create_material("BatteryBlue", base_color=(0.06,0.2,0.8,1), metallic=0.0, roughness=0.3)
mat_inverter = create_material("InverterGray", base_color=(0.45,0.45,0.45,1), metallic=0.0, roughness=0.35)
mat_cable_red = create_material("CableRed", base_color=(0.8,0.05,0.05,1), metallic=0.0, roughness=0.6)
mat_cable_black = create_material("CableBlack", base_color=(0.02,0.02,0.02,1), metallic=0.0, roughness=0.6)
mat_heat_sink = create_material("HeatSink", base_color=(0.6,0.63,0.65,1), metallic=1.0, roughness=0.2)

# Wooden base
base = add_plane("WoodenBase", size_x=0.30, size_y=0.30, thickness=0.02, location=(0,0,-0.01), material=mat_wood)

# Steel vertical shaft
shaft_height = 0.12
shaft = add_cylinder("Shaft", radius=0.008, depth=shaft_height, location=(0,0,shaft_height/2 - 0.01), material=mat_steel)

# Rotating disk attached to shaft
disk_radius = 0.08
disk_thickness = 0.01
disk = add_cylinder("RotatingDisk", radius=disk_radius, depth=disk_thickness, location=(0,0,shaft.location.z + shaft_height/2 + disk_thickness/2 - 0.01), material=mat_steel)
# Slightly darker top face for contrast: use same material

# Magnets: 8 cube-shaped magnets placed around disk edge
num_magnets = 8
mag_size = 0.02
mag_z = disk.location.z + disk_thickness/2 + mag_size/2 - 0.01
for i in range(num_magnets):
    angle = (2*math.pi/num_magnets) * i
    radius_pos = disk_radius - mag_size/2 - 0.005
    x = math.cos(angle) * radius_pos
    y = math.sin(angle) * radius_pos
    mat = mat_magnet_red if i % 2 == 0 else mat_magnet_blue
    mag = add_mesh_cube(f"Magnet_{i+1}", size=mag_size, location=(x,y,mag_z), rotation=(0,0,angle))
    mag.data.materials.append(mat)
    # Slightly offset orientation so face pole visible
    mag.rotation_euler = Euler((0,0,angle), 'XYZ')

# Four fixed copper coils (yellow) around the disk
coil_major = 0.055
coil_minor = 0.012
coil_z = disk.location.z
for j in range(4):
    ang = j * (math.pi/2)
    x = math.cos(ang) * coil_major
    y = math.sin(ang) * coil_major
    rot = (math.pi/2, 0, ang)
    coil = add_torus(f"Coil_{j+1}", major_radius=coil_major, minor_radius=coil_minor, location=(x,y,coil_z), rotation=rot, material=mat_coil_yellow)
    # make coil appear fixed: don't parent to disk

# Add simple copper wire wraps (thin torus or curve) - approximate with smaller torus
for j in range(4):
    ang = j * (math.pi/2)
    x = math.cos(ang) * coil_major
    y = math.sin(ang) * coil_major
    wire = add_torus(f"Wire_{j+1}", major_radius=coil_major, minor_radius=coil_minor*0.35, location=(x,y,coil_z), rotation=(math.pi/2,0,ang), material=mat_copper)

# Green PCB with bridge rectifier and heat sink
pcb_x = 0.09
pcb_y = -0.05
pcb = add_mesh_cube("PCB", size=0.06, location=(pcb_x, pcb_y, 0.01), material=mat_pcb)
pcb.scale = (0.06/2, 0.04/2, 0.003/2)
bpy.ops.object.transform_apply(scale=True)
# Bridge rectifier (small box)
rect = add_mesh_cube("BridgeRectifier", size=0.012, location=(pcb_x+0.012, pcb_y, pcb.location.z+0.008), material=mat_plastic)
# Heat sink (aluminum fins)
hs_base = add_mesh_cube("HeatSinkBase", size=0.016, location=(pcb_x-0.012, pcb_y, pcb.location.z+0.008), material=mat_heat_sink)
hs_base.scale = (0.016/2, 0.012/2, 0.002/2); bpy.ops.object.transform_apply(scale=True)
# create some fins
for f in range(4):
    fx = hs_base.location.x
    fy = hs_base.location.y - 0.004 + f*0.002
    fin = add_mesh_cube(f"Fin_{f+1}", size=0.003, location=(fx, fy, hs_base.location.z+0.003), material=mat_heat_sink)
    fin.scale = (0.003/2, 0.001/2, 0.006/2); bpy.ops.object.transform_apply(scale=True)

# Battery (blue, 12V)
battery = add_mesh_cube("Battery12V", size=0.05, location=(-0.09, -0.07, 0.02), material=mat_battery)
battery.scale = (0.05/2, 0.02/2, 0.03/2); bpy.ops.object.transform_apply(scale=True)

# Inverter (gray, 500W)
inverter = add_mesh_cube("Inverter500W", size=0.12, location=(-0.09, 0.07, 0.02), material=mat_inverter)
inverter.scale = (0.12/2, 0.06/2, 0.04/2); bpy.ops.object.transform_apply(scale=True)

# Cables: battery -> inverter -> pcb -> coils (simple curves)
cab1 = add_bezier_cable("Cable_batt_inv", [battery.location + Vector((0.03,0,0.01)), inverter.location + Vector((-0.03,0,0.01))], bevel_depth=0.003, material=mat_cable_red)
cab2 = add_bezier_cable("Cable_inv_pcb", [inverter.location + Vector((0.03,0,0.01)), pcb.location + Vector((-0.03,0,0.01))], bevel_depth=0.003, material=mat_cable_black)

# Simple cable branches to coils (red/black pairs)
for idx, coil in enumerate([obj for obj in bpy.data.objects if obj.name.startswith("Coil_")]):
    ang = idx * (math.pi/2)
    coil_pos = Vector((math.cos(ang) * coil_major, math.sin(ang) * coil_major, coil_z))
    p_start = pcb.location + Vector((0,0,0.01))
    cable_r = add_bezier_cable(f"Cable_r_{idx+1}", [p_start, coil_pos + Vector((0,0,0.02))], bevel_depth=0.0022, material=mat_cable_red)
    cable_b = add_bezier_cable(f"Cable_b_{idx+1}", [battery.location + Vector((0.03,0,0.01)), coil_pos - Vector((0,0,0.02))], bevel_depth=0.0022, material=mat_cable_black)

# Parent logical groups for cleanliness
disk.parent = shaft
for o in [o for o in bpy.data.objects if o.name.startswith("Magnet_")]:
    o.parent = disk

# ---------- Camera & Lighting ----------
# Camera
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (0.6, -0.6, 0.45)
cam.rotation_euler = Euler((math.radians(60), 0, math.radians(45)), 'XYZ')
bpy.context.scene.camera = cam

# Lighting: 3-point
light_data = bpy.data.lights.new(name="KeyLight", type='AREA')
light_data.energy = 1200
light_obj = bpy.data.objects.new("KeyLight", light_data)
light_obj.location = (0.5, -0.5, 0.5)
light_obj.data.size = 0.4
bpy.context.collection.objects.link(light_obj)

fill_data = bpy.data.lights.new(name="FillLight", type='AREA')
fill_data.energy = 400
fill = bpy.data.objects.new("FillLight", fill_data)
fill.location = (-0.4, -0.3, 0.4)
fill.data.size = 0.3
bpy.context.collection.objects.link(fill)

rim_data = bpy.data.lights.new(name="RimLight", type='AREA')
rim_data.energy = 300
rim = bpy.data.objects.new("RimLight", rim_data)
rim.location = (-0.5, 0.5, 0.5)
rim.data.size = 0.3
bpy.context.collection.objects.link(rim)

# World: soft gray + slight HDRI-ish feel via strength
world = bpy.context.scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value = (0.03, 0.03, 0.03, 1)
bg.inputs['Strength'].default_value = 0.6

# ---------- Render settings ----------
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 128
bpy.context.scene.cycles.device = 'CPU'  # change to 'GPU' if configured
bpy.context.scene.render.film_transparent = False
bpy.context.scene.view_settings.view_transform = 'Filmic'

# ---------- Export ----------
export_path = "/tmp/magnetic_generator.glb"  # change to desired path
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=export_path, export_format='GLB', export_materials='EXPORT')
print("Exported to", export_path)

# ---------- Finished ----------
print("Procedural model generation complete.")
