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

class BE_FBX_OT_Export(bpy.types.Operator):    
    bl_idname = "befbx.export"
    bl_label = "Export"
    
    def execute(self, context):
        basedir = context.scene.target_path
        
        if basedir.startswith('//'):
            basedir = bpy.path.abspath(basedir)

        if not basedir:
            self.report({'ERROR_INVALID_INPUT'}, "Target directory is not specified!")
            return {'CANCELLED'}

        view_layer = bpy.context.view_layer

        obj_active = view_layer.objects.active
        selection = bpy.context.selected_objects

        bpy.ops.object.select_all(action='DESELECT')

        loadPreset(context)

        if len(selection) <= 0:
            self.report({'ERROR_INVALID_INPUT'}, "No objects selected!")
            return {'CANCELLED'}

        for index in range(len(selection)):
            obj = selection[index]

            obj.select_set(True)
            backupPosition = centerObject(obj)

            view_layer.objects.active = obj


            folder_name_format = context.scene.folder_name_format
            file_name = bpy.path.clean_name(obj.name)
                        
            
            if context.scene.individual_folders and folder_name_format:
                name_inserted = folder_name_format.replace('${name}', bpy.path.clean_name(obj.name))
                index_inserted = name_inserted.replace('${index}', str(index))
                folder_name = index_inserted
                file_dir = os.path.join(basedir, folder_name)
                if not os.path.isdir(file_dir):
                    os.mkdir(file_dir)
            else:
                file_dir = basedir
                
            full_path = os.path.join(file_dir, file_name + ".fbx")
            
            kwargs = loadPreset(context)
            kwargs["filepath"] = full_path
            kwargs["use_selection"] = True

            bpy.ops.export_scene.fbx(**kwargs)

            obj.select_set(False)
            obj.location = backupPosition

            print("written:", full_path)


        view_layer.objects.active = obj_active

        for obj in selection:
            obj.select_set(True)

        self.report({'INFO'}, "Selected files exported!")
        return {'FINISHED'}

class BE_FBX_OT_RefreshPresets(bpy.types.Operator):    
    bl_idname = "befbx.refresh_presets"
    bl_label = "RefreshPresets"
    
    def execute(self, context):
        bpy.types.Scene.preset_list = bpy.props.EnumProperty(items=loadPresetsList())

        self.report({'INFO'}, "Presets list reloaded!")
        return {'FINISHED'}

class BE_FBX_PT_Panel(bpy.types.Panel):
    bl_label = "FBX Batch Export"
    bl_idname = "BE_FBX_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FBX"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        
        # Export directories section
        box = layout.box()
        
        row = box.row()
        row.label(text="Export target path", icon="FILE_FOLDER")
        
        row = box.row()
        row.prop(scene, 'target_path', text="")
        
        row = box.row()
        row.prop(scene, 'individual_folders', text="Individual folders")
        
        if scene.individual_folders:        
            row = box.row()
            row.label(text="Folder name format", icon="FILE_TEXT")
        
            row = box.row()
            row.prop(scene, 'folder_name_format', text="")
    
        # Preset section
        box = layout.box()
        
        row = box.row()
        row.label(text = "Preset", icon="PRESET")
        
        row = box.row()
        row.prop_menu_enum(scene, "preset_list", text=scene.preset_list)
        
        row = box.row()
        row.operator("befbx.refresh_presets", text = "Reload presets", icon = "FILE_REFRESH")
        
        # Confirm section
        layout.row().operator("befbx.export", text = "Export", icon = "EXPORT")
        
def register():
    bpy.types.Scene.preset_list = bpy.props.EnumProperty(items=loadPresetsList())
    bpy.types.Scene.target_path = bpy.props.StringProperty \
        (
            name = "Export target path",
            default = "",
            description = "Set directory to which selected objects will be exported.",
            subtype = "DIR_PATH"
        )
    bpy.types.Scene.individual_folders = bpy.props.BoolProperty \
        (
            name="Individual folders",
            default = False,
            description = "Should each exported file be placed inside separate folder?",
        )
    bpy.types.Scene.folder_name_format = bpy.props.StringProperty \
        (
            name = "Folders name format",
            default = "${name}",
            description = "Individual folders name format.\n\nType ${name} to include object name.\nType ${index} to include object number (Warning! Naming folders by index is not reliable, you can make a mess when exporting multiple times)"
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
    currentPosition = obj.location.copy()
    obj.location = (0,0,0)
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
    return {}
    
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
