"""
Render the 400-frame (13.3-second @ 30 FPS) Master Cinematic Showcase
of the JANUS Mini 16-Tile (Model 1A) Monolithic Photonic AI Processor.

Features:
- Seamless 5-shot cinematic camera sequence driven by timeline markers:
  * Shot 1 (Frames 001 - 070): Macro Package Hero Orbit
  * Shot 2 (Frames 071 - 160): Exploded Z-Axis Stratigraphy Lift & Cu TDV Forest
  * Shot 3 (Frames 161 - 260): Microscopic Deep Dive into Tile 0 (Beneš Butterfly & APDs)
  * Shot 4 (Frames 261 - 330): Cross-Stratum Avalanche Discharge into 65nm CMOS
  * Shot 5 (Frames 331 - 400): Sub-Micron Physics Station & Monolithic Re-assembly
- Blender 5.2 Compositor Photonic Bloom & Fog Glow
- High-Bitrate H.264 MP4 encoding via FFmpeg (CRF 17, 1080p30)
- Automatic 12-frame storyboard contact sheet generation
"""
import bpy
import os
import subprocess
import shutil

blend_file = r"c:\Users\hp\Desktop\Janus Interactive Visulaization\JANUS_Mini16_Model1A.blend"
renders_dir = r"c:\Users\hp\Desktop\Janus Interactive Visulaization\renders"
frames_dir = os.path.join(renders_dir, "temp_cinematic_frames")
output_mp4 = r"c:\Users\hp\Desktop\Janus Interactive Visulaization\JANUS_Mini16_Cinematic_Showcase.mp4"
contact_sheet_path = os.path.join(renders_dir, "contact_sheet_cinematic.png")

os.makedirs(frames_dir, exist_ok=True)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene, 'eevee'):
    scene.eevee.taa_render_samples = 16

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'

scene.frame_start = 1
scene.frame_end = 400
scene.render.fps = 60

scene.render.filepath = os.path.join(frames_dir, "frame_")

print("=" * 80, flush=True)
print(f"RENDERING 400-FRAME CINEMATIC ANIMATION (Frames 1 to 400)...", flush=True)
print("Timeline markers will automatically cut between the 5 specialized cinematic cameras:", flush=True)
for m in sorted(scene.timeline_markers, key=lambda x: x.frame):
    print(f"  - Frame {m.frame:03d}: Marker '{m.name}' -> Camera '{m.camera.name if m.camera else 'Default'}'", flush=True)
print("=" * 80, flush=True)

bpy.ops.render.render(animation=True)
print("\n[SUCCESS] Blender frame rendering complete!", flush=True)

# ------------------------------------------------------------------------------
# 1. ASSEMBLE HIGH-BITRATE 1080P MP4 WITH FFMPEG
# ------------------------------------------------------------------------------
ffmpeg_bin = r"C:\Users\hp\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe"
if not os.path.exists(ffmpeg_bin):
    ffmpeg_bin = "ffmpeg"

ffmpeg_cmd = [
    ffmpeg_bin, "-y",
    "-framerate", "60",
    "-i", os.path.join(frames_dir, "frame_%04d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-crf", "17",
    "-preset", "slow",
    output_mp4
]

print(f"Encoding MP4: {' '.join(ffmpeg_cmd)}", flush=True)
res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
if res.returncode == 0:
    print(f"\n[SUCCESS] Master Cinematic Video Encoded: {output_mp4}", flush=True)
else:
    print(f"FFmpeg error:\n{res.stderr}", flush=True)

# ------------------------------------------------------------------------------
# 2. GENERATE 12-FRAME STORYBOARD CONTACT SHEET VIA FFMPEG
# ------------------------------------------------------------------------------
sheet_cmd = [
    ffmpeg_bin, "-y",
    "-i", output_mp4,
    "-vf", "select='not(mod(n\\,33))',scale=480:270,tile=4x3",
    "-frames:v", "1",
    contact_sheet_path
]

print(f"Generating contact sheet: {' '.join(sheet_cmd)}", flush=True)
res_sheet = subprocess.run(sheet_cmd, capture_output=True, text=True)
if res_sheet.returncode == 0:
    print(f"[SUCCESS] Contact sheet saved: {contact_sheet_path}", flush=True)
    # Clean up temporary frames
    shutil.rmtree(frames_dir, ignore_errors=True)
    print("Temporary frame directory cleaned up successfully.", flush=True)
else:
    print(f"FFmpeg contact sheet error:\n{res_sheet.stderr}", flush=True)

print("=" * 80, flush=True)
