import setup_python_blender
setup_python_blender.install_packages(['pandas', 'numpy', 'pyproj'])
import pandas as pd
import bpy
import numpy as np
import pyproj


GIS_CRS = 'EPSG:3857'  # Found in GIS preferences
BLENDER_CRS = 'Blender'
SCALE_FACTOR = 1.0  # Define the scale factor to match the size of scene in Blender
CIRCLE_OBJECT = 'Circle_default'
STEPS = [0, 10, 1000, 10000, 100000, 9999999999999]
COLOR_START = '#ffffff'
COLORS = ['#115061', '#72b9c7', '#FEE640', '#FD721A', '#EE2733']
# COLORS = ['#ffffff', '#72b9c7', '#FDFC14', '#ffffff', '#b22a0c']
# FDD773

GROUP_HEIGHTS = [100, 300, 500, 700, 900]
GROUP_MATERIALS = ['Circle Group 1', 'Circle Group 2', 'Circle Group 3', 'Circle Group 4', 'Circle Group 5']
GROUP_START_FRAME = 1000
GROUP_TIME_SPACING = 30  # number of frames between start of each group
GROUP_START_DURATION = 45



def unselect_all_objects():
    for obj in bpy.context.selected_objects:
        obj.select_set(False)  # deselect all objects


def create_keyframe_position(object, frame, coordinates):
    unselect_all_objects()
    bpy.data.objects[object].select_set(True)
    for obj in bpy.context.selected_objects:
        obj.location[0] = coordinates[0]
        obj.location[1] = coordinates[1]
        obj.location[2] = coordinates[2]
        obj.keyframe_insert(data_path="location", index=-1, frame=frame)


def get_color_group(STEPS, value):
    steps_index = [x for x in range(0, len(STEPS) - 1)]
    is_bigger = [value >= step_start for step_start in STEPS[0:-1]]
    is_smaller = [value < step_start for step_start in STEPS[1:len(STEPS)]]
    in_step = [is_bigger[i] and is_smaller[i] for i in steps_index]
    result = [i for i, x in enumerate(in_step) if x][0]
    return result


def delete_objects(objects):
    for obj in objects:
        unselect_all_objects()
        if obj in bpy.data.objects:
            bpy.data.objects[obj].select_set(True)
            bpy.ops.object.delete(use_global=False, confirm=False)


def get_color_decimals(hex):
    decimals = tuple(int(hex[i:i + 2], 16) / 255.0 for i in (1, 3, 5)) + (1.0,)
    return decimals

df = pd.read_csv('/Users/luis/Git/plastic-pollution/data/plastic_count_2019.csv',
                 dtype={'Latitude': float, 'Longitude': float, 'count_total': float})
# df = df.head(200)
gis_proj = pyproj.Proj(GIS_CRS)

# Delete previous circles:
# delete_objects(['Circle Group ' + str(x) for x in range(0, len(STEPS) - 1)])

# Create Circles
circle_group = dict()
group_circles = dict(zip([x for x in range(0, len(STEPS) - 1)], [[] for x in range(0, len(STEPS) - 1)]))

# Update Circle Materials
for material in bpy.data.materials:
    if material.name in GROUP_MATERIALS:
        index = GROUP_MATERIALS.index(material.name)
        color = COLORS[index]
        color_value = get_color_decimals(color)
        color_value_white = get_color_decimals(COLOR_START)

        # Insert white keyframe:
        frame_start = GROUP_START_FRAME + index * GROUP_TIME_SPACING
        bpy.context.scene.frame_set(frame_start)
        bpy.data.materials[material.name].node_tree.nodes["Principled BSDF"].inputs[0].default_value = color_value_white
        # material = bpy.data.materials.get(material.name)
        principled_bsdf = material.node_tree.nodes.get("Principled BSDF")
        base_color_input = principled_bsdf.inputs.get("Base Color")
        base_color_input.keyframe_insert(data_path="default_value", index=-1, frame=frame_start)
        emission_input = principled_bsdf.inputs.get("Emission")
        emission_input.default_value = color_value_white
        emission_input.keyframe_insert(data_path="default_value", index=-1, frame=frame_start)

        frame_end = GROUP_START_FRAME + index * GROUP_TIME_SPACING + GROUP_START_DURATION
        bpy.context.scene.frame_set(frame_end)
        bpy.data.materials[material.name].node_tree.nodes["Principled BSDF"].inputs[0].default_value = color_value
        # material = bpy.data.materials.get("MyMaterial")
        principled_bsdf = material.node_tree.nodes.get("Principled BSDF")
        base_color_input = principled_bsdf.inputs.get("Base Color")
        base_color_input.keyframe_insert(data_path="default_value", index=-1, frame=frame_end)
        emission_input = principled_bsdf.inputs.get("Emission")
        emission_input.default_value = color_value
        emission_input.keyframe_insert(data_path="default_value", index=-1, frame=frame_end)

        # Update emission:
        bpy.data.materials[material.name].node_tree.nodes["Principled BSDF"].inputs[19].default_value = color_value


for index, row in df.iterrows():
    circle_name = 'Circle_' + str(index)
    print(circle_name)
    delete_objects([circle_name])
    unselect_all_objects()
    if circle_name in bpy.data.objects:
        bpy.data.objects[circle_name].select_set(True)
        bpy.ops.object.delete(use_global=False, confirm=False)
    bpy.data.objects[CIRCLE_OBJECT].select_set(True)
    bpy.ops.object.duplicate(linked=False)
    bpy.data.objects[CIRCLE_OBJECT].select_set(False)
    # Calculate Blender coordinates
    lat = row['Latitude']
    lon = row['Longitude']
    x_gis, y_gis = gis_proj(lon, lat)
    transformation_matrix = np.array([[1, 0, 0],
                                      [0, 0, -1],
                                      [0, 1, 0]])
    x_blender, z_blender, y_blender = np.matmul(transformation_matrix, [x_gis, y_gis, 0])
    # Scale the coordinates to match the size of scene in Blender
    x_blender /= SCALE_FACTOR
    y_blender /= SCALE_FACTOR

    for obj in bpy.context.selected_objects:
        obj.name = circle_name

    # Get group:
    group = get_color_group(STEPS, row['count_total'])
    group_circles[group].append(circle_name)
    z_blender = GROUP_HEIGHTS[group]

    # Assign material:
    # Get the material object from the material name
    material = bpy.data.materials.get(GROUP_MATERIALS[group])
    circle_object = bpy.data.objects.get(circle_name)
    # circle_object.data.materials.append(material)
    circle_object.active_material = material

    # Create position keyframe:
    create_keyframe_position(circle_name, 1, (x_blender, y_blender, GROUP_HEIGHTS[group]))

    # Create scale keyframes:
    frame_end = GROUP_START_FRAME + group * GROUP_TIME_SPACING + GROUP_START_DURATION
    bpy.context.scene.frame_set(frame_end)
    circle_object.scale = (1, 1, 1)
    circle_object.keyframe_insert(data_path="scale")

    frame_start = GROUP_START_FRAME + group*GROUP_TIME_SPACING
    bpy.context.scene.frame_set(frame_start)
    circle_object.scale = (0, 0, 0)
    circle_object.keyframe_insert(data_path="scale")


