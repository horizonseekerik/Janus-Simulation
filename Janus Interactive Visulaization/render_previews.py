"""
Render high-fidelity beauty previews of the upgraded JANUS Mini 16-Tile 3D Model
across all 5 cinematic camera perspectives.
"""
import bpy
import os

blend_file = r"c:\Users\hp\Desktop\Janus Interactive Visulaization\JANUS_Mini16_Model1A.blend"
output_dir = r"c:\Users\hp\Desktop\Janus Interactive Visulaization\renders"
os.makedirs(output_dir, exist_ok=True)

render_configs = [
    {
        "name": "01_Macro_Package_Hero",
        "cam": "Cam_Shot1_Macro",
        "frame": 1,        # Monolithic package, microchannel copper lid, fluid ports, fiber laser
    },
    {
        "name": "02_Exploded_Z_Stratigraphy",
        "cam": "Cam_Shot2_Exploded",
        "frame": 140,      # Fully exploded Z-axis view with Cu TDV forest & 3D labels
    },
    {
        "name": "03_Tile0_Benes_Butterfly_APDs",
        "cam": "Cam_Shot3_MicroDive",
        "frame": 205,      # Wafer-level Tile 0 view: Beneš butterfly crossovers & monolithic APDs
    },
    {
        "name": "04_TDV_CMOS_Avalanche",
        "cam": "Cam_Shot4_AvalancheCMOS",
        "frame": 290,      # Avalanche charge entering 65nm CMOS StrongARM latch
    },
    {
        "name": "05_SubMicron_Physics_Station",
        "cam": "Cam_Shot5_MicroPhysics",
        "frame": 335,      # Standalone sub-micron physics station & devices
    }
]

scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

if hasattr(scene, 'eevee'):
    scene.eevee.taa_render_samples = 16

for cfg in render_configs:
    cam_name = cfg["cam"]
    cam_obj = bpy.data.objects.get(cam_name)
    if not cam_obj:
        print(f"Warning: Camera {cam_name} not found!")
        continue
    
    scene.camera = cam_obj
    scene.frame_set(cfg["frame"])
    
    out_file = os.path.join(output_dir, f"{cfg['name']}.png")
    scene.render.filepath = out_file
    print(f"Rendering {cfg['name']} (Frame {cfg['frame']}, Cam {cam_name})...", flush=True)
    bpy.ops.render.render(write_still=True)
    print(f"Saved: {out_file}", flush=True)

print("All cinematic preview renders completed successfully!", flush=True)
