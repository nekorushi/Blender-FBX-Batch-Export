bl_info = {
    "name" : "Batch Export FBX",
    "author" : "nekorushi",
    "descrtion" : "Export selected objects as FBX. Supports predefined presets.",
    "blender" : (2, 80, 0),
    "version" : (0, 1),
    "location" : "View3D -> Sidebar -> FBX",
    "warning" : "",
    "category" : "Import-Export"
}

import bpy
import os
from bpy.types import Panel, Operator

class BE_FBX_OT_Export(Operator):    
    bl_idname = "befbx.export"
    bl_label = "Export"
    
    def execute(self, context):
        basedir = context.scene.target_path

        if not basedir:
            raise Exception("Target directory is not specified!")

        view_layer = bpy.context.view_layer

        obj_active = view_layer.objects.active
        selection = bpy.context.selected_objects

        bpy.ops.object.select_all(action='DESELECT')

        loadPreset(context)

        for obj in selection:

            obj.select_set(True)

            view_layer.objects.active = obj

            name = bpy.path.clean_name(obj.name)
            fn = os.path.join(basedir, name)

            kwargs = loadPreset(context)
            kwargs["filepath"] = fn + ".fbx"
            kwargs["use_selection"] = True

            backupPosition = centerObject(obj)

            bpy.ops.export_scene.fbx(**kwargs)

            set_object_to_loc(obj, backupPosition)

            obj.select_set(False)

            print("written:", fn)


        view_layer.objects.active = obj_active

        for obj in selection:
            obj.select_set(True)

        self.report({'INFO'}, "Selected files exported!")
        return {'FINISHED'}

class BE_FBX_OT_RefreshPresets(Operator):    
    bl_idname = "befbx.refresh_presets"
    bl_label = "RefreshPresets"
    
    def execute(self, context):
        bpy.types.Scene.preset_list = bpy.props.EnumProperty(items=loadPresetsList())

        self.report({'INFO'}, "Presets list reloaded!")
        return {'FINISHED'}

class BE_FBX_PT_Panel(Panel):
    bl_label = "FBX Batch Export"
    bl_idname = "BE_FBX_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FBX"
    
    def draw(self, context):
        layout = self.layout
        
        layout.row().label(text="Export target path", icon="FILE_FOLDER")
        layout.row().prop(context.scene, 'target_path', text="")

        layout.row().label(text = "Preset", icon="PRESET")
        row = layout.row().split(factor=0.85)
        row.prop_menu_enum(context.scene, "preset_list", text=context.scene.preset_list)
        row.operator("befbx.refresh_presets", text = "", icon = "FILE_REFRESH")

        layout.row().operator("befbx.export", text = "Export", icon = "EXPORT")
        
def register():
    bpy.types.Scene.preset_list = bpy.props.EnumProperty(items=loadPresetsList())
    bpy.types.Scene.target_path = bpy.props.StringProperty \
        (
            name = "Export target path",
            default = os.path.dirname(bpy.data.filepath),
            description = "Set directory to which selected objects will be exported.",
            subtype = "DIR_PATH"
        )
    bpy.utils.register_class(BE_FBX_OT_Export)
    bpy.utils.register_class(BE_FBX_OT_RefreshPresets)
    bpy.utils.register_class(BE_FBX_PT_Panel)
    
def unregister():
    bpy.utils.unregister_class(BE_FBX_OT_Export)
    bpy.utils.unregister_class(BE_FBX_OT_RefreshPresets)
    bpy.utils.unregister_class(BE_FBX_PT_Panel)
    del bpy.types.Scene.preset_list
    del bpy.types.Scene.target_path

def centerObject(obj):
    currentPosition = get_object_loc(obj)
    set_object_to_loc(obj, (0,0,0))
    return currentPosition


def loadPreset(context):
    filepath = bpy.utils.preset_find(context.scene.preset_list, 'operator/export_scene.fbx/')       
    if filepath:
        class Container(object):
            __slots__ = ('__dict__',)

        op = Container()
        file = open(filepath, 'r')

        # storing the values from the preset on the class
        for line in file.readlines()[3::]:
            exec(line, globals(), locals())
        
        return op.__dict__
    
def loadPresetsList():
    preset_paths = bpy.utils.preset_paths('operator/export_scene.fbx/')

    found_presets = []
    if preset_paths:       
        path = preset_paths[0]
        files = [filename for filename in os.listdir(path) if os.path.isfile(os.path.join(path, filename))]

        for index in range(len(files)):
            filename = files[index]
            if(filename.endswith(".py")):
                fullPath = path + filename
                trimmedFilename = os.path.splitext(filename)[0]
                found_presets.append((trimmedFilename, trimmedFilename, "", index))
                    
    return found_presets
    
if __name__ == "__main__":
    register()
