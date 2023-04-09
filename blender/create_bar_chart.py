import setup_python_blender
setup_python_blender.install_packages(['pandas', 'numpy', 'pyproj'])
import pandas as pd
import bpy
import numpy as np
import pyproj
from mathutils import Vector, Matrix


FILE_DIR = '/Users/luis/Library/CloudStorage/GoogleDrive-luis.s.calejo@gmail.com/My Drive/Memeable Data/Videos/2023-03 Plastic Pollution/Data/plastic_particles.csv'
FONT_DIR = '/Users/luis/Library/CloudStorage/GoogleDrive-luis.s.calejo@gmail.com/My Drive/Memeable Data/Fonts/roboto/Roboto-Regular.ttf'
COORDINATES = (0, 0, 0)
FRAME_START = 200
FRAME_END = 300
SPACING = 0.2
COLUMN_WIDTH = 2
Y_MAX = 30
LABEL_SPACING_Y = 1
LABEL_SPACING_Y_VALUE = 0.5
NUMBER_SUFFIX = ''
NAME_SUFFIX = '_test3'
ROUNDING = 0


def unselect_all_objects():
    for obj in bpy.context.selected_objects:
        obj.select_set(False)  # deselect all objects

def update_fonts(font_dir):
    # Iterate through all the text objects
    for obj in bpy.data.objects:
        if obj.type == 'FONT':
            # Change the font
            obj.data.font = bpy.data.fonts.load(font_dir)


def insert_and_change_text(coordinates, label, label_name):
    text_data = bpy.data.curves.new(name=label_name, type='FONT')
    text_object = bpy.data.objects.new(name=label_name, object_data=text_data)
    text_object.location = coordinates
    text_data.align_x = 'CENTER'
    bpy.context.scene.collection.objects.link(text_object)
    bpy.context.view_layer.objects.active = text_object
    bpy.ops.object.editmode_toggle()
    for k in range(4):
        bpy.ops.font.delete(type='PREVIOUS_OR_SELECTION')
    for char in label:
        bpy.ops.font.text_insert(text=char)
    bpy.ops.object.editmode_toggle()

def create_keyframe_position(object, frame, coordinates):
    unselect_all_objects()
    bpy.data.objects[object].select_set(True)
    for obj in bpy.context.selected_objects:
        obj.location[0] = coordinates[0]
        obj.location[1] = coordinates[1]
        obj.location[2] = coordinates[2]
        obj.keyframe_insert(data_path="location", index=-1, frame=frame)


COLOR = (0.8, 0.2, 0.2, 1.0)

# Read the CSV file
df = pd.read_csv(FILE_DIR)
y_max_value = max(df.iloc[:, 1])
# df.iloc[:, 1] = [str(x) for x in df.iloc[:, 1]]
df['year'] = [str(x) for x in df['year']] #(!!) temp!

# Create the material
mat = bpy.data.materials.new(name="BarMaterial")
mat.diffuse_color = COLOR

# Create the bars
bars = []
labels = []
scene = bpy.context.scene
y_values = []
for index, row in df.iterrows():
    x = row[0]
    y = float(row[1])
    y_dimension = (y/y_max_value)*Y_MAX
    coordinates = (COORDINATES[0] + index*(COLUMN_WIDTH+SPACING), COORDINATES[1]+y_dimension/2, COORDINATES[2])
    bpy.ops.mesh.primitive_plane_add(size=COLUMN_WIDTH, enter_editmode=False, location=coordinates)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.context.active_object.scale = (1, y_dimension/COLUMN_WIDTH, 1)
    bar_obj = bpy.context.object
    bar_obj.name = 'Bar Chart ' + str(index) + NAME_SUFFIX  # Set the name of the object

    # Update origin
    bpy.context.scene.cursor.location = Vector((coordinates[0], coordinates[1]-y_dimension/2, coordinates[2]))
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    # Add keyframes
    obj = bpy.context.active_object
    obj.keyframe_insert(data_path='scale', frame=FRAME_END)
    obj.scale[1] = 0.0
    obj.keyframe_insert(data_path='scale', frame=FRAME_START)

    # Add color
    obj.active_material = mat

    # Add labels:
    insert_and_change_text((coordinates[0], coordinates[1]-y_dimension/2 - LABEL_SPACING_Y, coordinates[2]), x, 'Chart Label ' + str(index) + NAME_SUFFIX)
    insert_and_change_text((coordinates[0], coordinates[1]-y_dimension/2 + LABEL_SPACING_Y_VALUE, coordinates[2]), x, 'Chart Label Value ' + str(index) + NAME_SUFFIX)
    create_keyframe_position('Chart Label Value ' + str(index) + NAME_SUFFIX, FRAME_START, (coordinates[0], coordinates[1]-y_dimension/2 + LABEL_SPACING_Y_VALUE, coordinates[2]))
    create_keyframe_position('Chart Label Value ' + str(index) + NAME_SUFFIX, FRAME_END, (coordinates[0], coordinates[1]+y_dimension/2 + LABEL_SPACING_Y_VALUE, coordinates[2]))

    # Store objects:
    bars.append(scene.objects['Bar Chart ' + str(index) + NAME_SUFFIX])
    labels.append(scene.objects['Chart Label Value ' + str(index) + NAME_SUFFIX])
    y_values.append(y)

update_fonts(FONT_DIR)


# Update text labels:
def recalculate_text(scene):
    for i in range(0, len(bars)):
        if scene.frame_current >= FRAME_START:
            if ROUNDING == 0:
                labels[i].data.body = str(round(bars[i].dimensions[1] * y_max_value / Y_MAX)) + NUMBER_SUFFIX
            else:
                labels[i].data.body = str(round(bars[i].dimensions[1]*y_max_value/Y_MAX, ROUNDING)) + NUMBER_SUFFIX
        else:
            labels[i].data.body = ''
bpy.app.handlers.frame_change_pre.append(recalculate_text)
