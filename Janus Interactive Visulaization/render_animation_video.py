"""
Render the complete 180-frame JANUS Mini 16-Tile working demonstration video
and encode directly into MP4 using FFmpeg.
"""
import bpy
import os
import subprocess
import shutil

blend_file = r"c:\Users\hp\Desktop\Janus Interactive Visulaization\JANUS_Mini16_Model1A.blend"
frames_dir = r"c:\Users\hp\Desktop\Janus Interactive Visulaization\renders\temp_anim_frames"
output_mp4 = r"c:\Users\hp\Desktop\Janus Interactive Visulaization\JANUS_Mini16_Demonstration.mp4"
if os.path.exists(frames_dir):
    shutil.rmtree(frames_dir, ignore_errors=True)
os.makedirs(frames_dir, exist_ok=True)

scene = bpy.context.scene
scene.camera = bpy.data.objects.get("Cam_Front_Hero")
scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene, 'eevee'):
    scene.eevee.taa_render_samples = 4

if scene.compositing_node_group:
    for n in scene.compositing_node_group.nodes:
        if n.type == 'GLARE' and 'Quality' in n.inputs:
            n.inputs['Quality'].default_value = 'Low'

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

scene.frame_start = 1
scene.frame_end = 600
scene.render.fps = 60

scene.render.filepath = os.path.join(frames_dir, "frame_")

print(f"Rendering frames 1 to 600 (10.0 sec @ 60 FPS) to {frames_dir}...")
bpy.ops.render.render(animation=True)
print("Blender frame render complete!")

# Assemble into MP4 with FFmpeg
ffmpeg_bin = r"C:\Users\hp\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
if not os.path.exists(ffmpeg_bin):
    ffmpeg_bin = "ffmpeg"

ffmpeg_cmd = [
    ffmpeg_bin, "-y",
    "-framerate", "60",
    "-i", os.path.join(frames_dir, "frame_%04d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-crf", "18",
    output_mp4
]

print(f"Encoding MP4: {' '.join(ffmpeg_cmd)}")
res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
if res.returncode == 0:
    print(f"\n[SUCCESS] Video encoded successfully: {output_mp4}")
    # Clean up frames
    shutil.rmtree(frames_dir, ignore_errors=True)
else:
    print(f"FFmpeg error: {res.stderr}")
