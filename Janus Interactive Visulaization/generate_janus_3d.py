"""
JANUS Mini 16-Tile (Model 1A) Monolithic Photonic AI Processor
Master Procedural 3D Architectural CAD & Cinematic Animation Generator
Built for Blender 5.2.1 LTS

Specification Compliance:
- JANUS_Mini16_Simulation_Report.pdf (Multi-physics sign-off, Model 1A)
- JANUS_Mini16_CMOS_Architecture.pdf (65nm LP/GP CMOS backend, 3.125 GHz)
- JANUS_IEEE_Manuscript.pdf (One-Hot optical RNS, dilated Beneš, SAC2M APDs)

Hierarchy:
- Level 4: Macro Package (FCBGA substrate, HS2 convective lid with fluid ports, V-groove fiber bench)
- Level 3: Meso Tile Array (4x4 tiles = 16 tiles, 2.5x2.5 mm, 10-stage Fractal H-Tree distribution)
- Level 2: Micro Multiplier Engine (1x256 LiTaO3 router, 15-stage dilated Beneš with butterfly crossovers,
          monolithic Ge/Si SAC2M APDs inside tile on SiPh, vertical Cu TDVs into CMOS)
- Level 1: Sub-Micron Physics Station (60 µm Sb2S3 cell with 1 nm graphene heater, MMI crossing, SAC2M mesa)
- 5-Shot Choreographed Cinematic Animation Rig (400 Frames @ 30 FPS) with timeline markers
- Blender 5.2 Compositor Glare / Photonic Bloom Node Group
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler

# ==============================================================================
# 1. PHYSICAL DIMENSIONS & ARCHITECTURAL CONSTANTS (1 BU = 1.0 mm)
# ==============================================================================
DIE_XY = 10.0            # 10.0 mm x 10.0 mm (100.00 mm²)
TILES_X = 4              # 4x4 Grid = 16 Tiles total
TILES_Y = 4
TILE_XY = 2.5            # 2.5 mm x 2.5 mm per tile (6.25 mm²)
TILE_GAP = 0.05          # 50 µm isolation streets

# Heterogeneous Physical Strata Z-Thicknesses
THICK_CMOS = 0.050       # 50 µm 65nm LP/GP CMOS base die
THICK_SIO2 = 0.250       # 250 µm Monolithic SiO2 thermal isolation buffer
THICK_SIPH = 0.030       # 30 µm Silicon Photonics (SiPh) stratum
THICK_HS1  = 0.030       # 30 µm Cu-pillar micro-matrix (Heat Spreader 1)
THICK_GAP  = 0.050       # 50 µm Cu-Cu pillar array gap
THICK_HS2  = 0.250       # 250 µm Convective slim-lid microchannel heat sink

SHUNT_WIDTH = 0.250      # 250 µm Solid Copper perimeter thermal shunt & Faraday ring

# Base Z elevations (unexploded monolithic state)
Z_CMOS_BASE = 0.0
Z_SIO2_BASE = THICK_CMOS
Z_SIPH_BASE = Z_SIO2_BASE + THICK_SIO2
Z_HS1_BASE  = Z_SIPH_BASE + THICK_SIPH
Z_GAP_BASE  = Z_HS1_BASE + THICK_HS1
Z_HS2_BASE  = Z_GAP_BASE + THICK_GAP

# Exploded Z Offsets (at Explode_Progress = 1.0, balanced for front showcase framing)
EXP_CMOS_Z = 0.0
EXP_SIO2_Z = 2.2         # SiO2 buffer lifts by 2.2 mm
EXP_SIPH_Z = 5.0         # SiPh stratum lifts by 5.0 mm
EXP_HS1_Z  = 7.5         # HS1 lifts by 7.5 mm
EXP_HS2_Z  = 10.2        # HS2 convective lid lifts by 10.2 mm

# Sub-micron physics inspection station coordinates
CALLOUT_X = 17.5
CALLOUT_Y = 0.0


# ==============================================================================
# 2. SCENE INITIALIZATION & UTILITIES
# ==============================================================================
def clean_scene():
    """Wipe default scene completely clean."""
    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)


def get_or_create_collection(name, parent=None):
    """Retrieve or create a nested collection."""
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
        if parent:
            parent.children.link(col)
        else:
            bpy.context.scene.collection.children.link(col)
    return col


def add_3d_label(text, location, scale=0.28, rotation=(math.radians(86.8), 0, 0), align='CENTER', mat=None, col=None):
    """Create clean 3D technical typography facing front camera."""
    bpy.ops.object.text_add(location=location)
    txt_obj = bpy.context.active_object
    txt_obj.name = f"Label_{text[:20].replace(' ', '_').replace(':', '').replace('µ', 'u')}"
    txt_obj.data.body = text
    txt_obj.data.size = scale
    txt_obj.data.align_x = align
    txt_obj.data.align_y = 'CENTER'
    txt_obj.data.extrude = 0.025
    txt_obj.data.bevel_depth = 0.003
    txt_obj.rotation_euler = rotation
    if mat:
        txt_obj.data.materials.append(mat)
    if col:
        for c in txt_obj.users_collection: c.objects.unlink(txt_obj)
        col.objects.link(txt_obj)
    return txt_obj


def get_action_fcurves(action):
    """Retrieve all fcurves from an Action across Blender versions (supports legacy and Blender 5.2 layered actions)."""
    fcurves = []
    if not action:
        return fcurves
    if hasattr(action, 'fcurves'):
        return list(action.fcurves)
    if hasattr(action, 'layers'):
        for layer in action.layers:
            for strip in layer.strips:
                for cb in getattr(strip, 'channelbags', []):
                    fcurves.extend(cb.fcurves)
    return fcurves


# ==============================================================================
# 3. ADVANCED PBR MATERIALS & OPTICAL EMISSION SHADERS
# ==============================================================================
def create_materials():
    """Build all physically based materials and photonic shaders."""
    mats = {}

    def make_principled(name, color, metallic=0.0, roughness=0.3, transmission=0.0, ior=1.45, alpha=1.0):
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Transmission Weight"].default_value = transmission
        bsdf.inputs["IOR"].default_value = ior
        bsdf.inputs["Alpha"].default_value = alpha
        return mat

    # 1. 65nm Silicon CMOS Substrate (Polished, dark anisotropic metallic + thin-film iridescence)
    mat_si = bpy.data.materials.new(name="Mat_Silicon_CMOS")
    mat_si.use_nodes = True
    si_nodes = mat_si.node_tree.nodes
    si_links = mat_si.node_tree.links
    si_bsdf = si_nodes.get("Principled BSDF")
    si_bsdf.inputs["Metallic"].default_value = 0.92
    si_bsdf.inputs["Roughness"].default_value = 0.18

    # Thin-film iridescence: Layer Weight Fresnel -> Rainbow ColorRamp -> Mix with base
    lw = si_nodes.new(type="ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.42
    cr = si_nodes.new(type="ShaderNodeValToRGB")
    cr.color_ramp.interpolation = 'LINEAR'
    # Create rainbow stops
    stops = cr.color_ramp.elements
    stops[0].position = 0.0;  stops[0].color = (0.045, 0.05, 0.065, 1.0)
    stops[1].position = 0.35; stops[1].color = (0.08, 0.04, 0.12, 1.0)
    s2 = cr.color_ramp.elements.new(0.55); s2.color = (0.04, 0.08, 0.14, 1.0)
    s3 = cr.color_ramp.elements.new(0.72); s3.color = (0.10, 0.06, 0.04, 1.0)
    s4 = cr.color_ramp.elements.new(0.88); s4.color = (0.06, 0.10, 0.08, 1.0)
    s5 = cr.color_ramp.elements.new(1.0);  s5.color = (0.12, 0.08, 0.10, 1.0)
    si_links.new(lw.outputs["Fresnel"], cr.inputs["Fac"])
    si_links.new(cr.outputs["Color"], si_bsdf.inputs["Base Color"])
    mats['silicon'] = mat_si

    # 2. Package Interposer Substrate (Matte dark green/charcoal PCB)
    mats['pcb'] = make_principled("Mat_Package_Substrate", (0.018, 0.042, 0.025, 1.0), metallic=0.15, roughness=0.45)

    # 3. Monolithic SiO2 Thermal Buffer (Crystal fused silica glass)
    mats['sio2'] = make_principled("Mat_SiO2_Buffer", (0.80, 0.92, 1.0, 0.28), metallic=0.0, roughness=0.04, transmission=0.92, ior=1.458, alpha=0.30)

    # 4. Silicon Photonics (SiPh) Waveguide Substrate (Dark navy semiconductor)
    mats['siph_core'] = make_principled("Mat_SiPh_Substrate", (0.04, 0.06, 0.09, 1.0), metallic=0.88, roughness=0.14)

    # 5. 1064 nm Passive Optical Waveguides (Subtle radiant cyan core)
    mat_opt = bpy.data.materials.new(name="Mat_1064nm_Waveguide")
    mat_opt.use_nodes = True
    nodes = mat_opt.node_tree.nodes
    nodes.clear()
    out = nodes.new(type="ShaderNodeOutputMaterial")
    emit = nodes.new(type="ShaderNodeEmission")
    emit.inputs["Color"].default_value = (0.0, 0.85, 1.0, 1.0)
    emit.inputs["Strength"].default_value = 5.0
    mat_opt.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mats['optical_wave'] = mat_opt

    # 6. High-Intensity 1064 nm Active Optical Pulse Packet (Glowing Cyan-White Core)
    mat_pulse = bpy.data.materials.new(name="Mat_1064nm_Active_Pulse")
    mat_pulse.use_nodes = True
    nodes = mat_pulse.node_tree.nodes
    nodes.clear()
    out = nodes.new(type="ShaderNodeOutputMaterial")
    emit = nodes.new(type="ShaderNodeEmission")
    emit.inputs["Color"].default_value = (0.5, 0.95, 1.0, 1.0)
    emit.inputs["Strength"].default_value = 35.0
    mat_pulse.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mats['active_pulse'] = mat_pulse

    # 7. Monolithic Ge/Si SAC2M APD Germanium Absorption Layer (Dark glossy violet)
    mats['germanium'] = make_principled("Mat_Germanium_Absorber", (0.16, 0.06, 0.24, 1.0), metallic=0.85, roughness=0.12)

    # 8. Silicon Avalanche Multiplication Mesa (Dark specular gray)
    mats['silicon_cliff'] = make_principled("Mat_Silicon_Avalanche_Cliff", (0.08, 0.08, 0.10, 1.0), metallic=0.80, roughness=0.20)

    # 9. Sb2S3 Amorphous Phase-Change State (Warm translucent amber, na = 2.70)
    mats['sb2s3_amorphous'] = make_principled("Mat_Sb2S3_Amorphous_Amber", (0.95, 0.45, 0.05, 1.0), metallic=0.20, roughness=0.22, transmission=0.15)

    # 10. Sb2S3 Crystalline Phase-Change State (Reflective silvery-blue, nc = 3.30)
    mats['sb2s3_crystalline'] = make_principled("Mat_Sb2S3_Crystalline_Blue", (0.45, 0.65, 0.90, 1.0), metallic=0.92, roughness=0.10)

    # 11. Monolayer Graphene Electro-Thermal Heater (1 nm carbon mesh)
    mats['graphene'] = make_principled("Mat_Graphene_MicroHeater", (0.02, 0.02, 0.02, 0.92), metallic=0.98, roughness=0.10)

    # 12. Pure Copper (TDVs, Perimeter Shunt, Package Lid)
    mats['copper'] = make_principled("Mat_Pure_Copper", (0.95, 0.48, 0.28, 1.0), metallic=0.98, roughness=0.18)

    # 13. Translucent Copper (For viewing internal microchannel ribs and TDVs)
    mats['copper_translucent'] = make_principled("Mat_Copper_Translucent", (0.92, 0.46, 0.26, 0.45), metallic=0.85, roughness=0.15, transmission=0.55, alpha=0.50)

    # 14. Pure Gold (Bond pads, APD top contact rings, graphene electrodes)
    mats['gold'] = make_principled("Mat_Pure_Gold", (1.0, 0.78, 0.16, 1.0), metallic=0.98, roughness=0.12)

    # 15. Thin-Film LiTaO3 Pockels Electro-Optic Crystal
    mats['litao3'] = make_principled("Mat_LiTaO3_Crystal", (0.70, 0.90, 0.98, 0.65), metallic=0.20, roughness=0.08, transmission=0.72, ior=2.13)

    # 16. Electrical Avalanche Charge Pulse (Intense orange-amber emission)
    mat_elec = bpy.data.materials.new(name="Mat_Electrical_Avalanche_Pulse")
    mat_elec.use_nodes = True
    nodes = mat_elec.node_tree.nodes
    nodes.clear()
    out = nodes.new(type="ShaderNodeOutputMaterial")
    emit = nodes.new(type="ShaderNodeEmission")
    emit.inputs["Color"].default_value = (1.0, 0.55, 0.05, 1.0)
    emit.inputs["Strength"].default_value = 30.0
    mat_elec.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mats['electric_pulse'] = mat_elec

    # 17. CMOS 65nm Logic Sub-Blocks
    mats['cmos_rom']   = make_principled("Mat_CMOS_ROM", (0.92, 0.76, 0.18, 1.0), metallic=0.85, roughness=0.20)
    mats['cmos_sram']  = make_principled("Mat_CMOS_SRAM", (0.15, 0.55, 0.95, 1.0), metallic=0.75, roughness=0.25)
    mats['cmos_simd']  = make_principled("Mat_CMOS_SIMD", (0.10, 0.88, 0.50, 1.0), metallic=0.82, roughness=0.22)
    mats['cmos_jir']   = make_principled("Mat_CMOS_JIR", (0.95, 0.20, 0.25, 1.0), metallic=0.85, roughness=0.18)
    mats['cmos_latch'] = make_principled("Mat_CMOS_StrongARM", (0.80, 0.30, 0.98, 1.0), metallic=0.78, roughness=0.22)
    mats['cmos_power'] = make_principled("Mat_CMOS_PowerGrid", (0.85, 0.42, 0.20, 1.0), metallic=0.95, roughness=0.30)

    # 18. Clean Self-Illuminating Technical Typography Material (Sharp white emission for front legibility)
    mat_lbl = bpy.data.materials.new(name="Mat_Typography_Technical")
    mat_lbl.use_nodes = True
    l_nodes = mat_lbl.node_tree.nodes
    l_nodes.clear()
    l_out = l_nodes.new(type="ShaderNodeOutputMaterial")
    l_emit = l_nodes.new(type="ShaderNodeEmission")
    l_emit.inputs["Color"].default_value = (0.96, 0.98, 1.0, 1.0)
    l_emit.inputs["Strength"].default_value = 2.8
    mat_lbl.node_tree.links.new(l_emit.outputs["Emission"], l_out.inputs["Surface"])
    mats['label'] = mat_lbl

    return mats


# ==============================================================================
# 4. MASTER CONTROLLER & EXPLODED VIEW RIG
# ==============================================================================
def create_master_rig():
    """Create the master empty driving the procedural Z explosion."""
    bpy.ops.object.empty_add(type='SPHERE', radius=0.8, location=(0, 0, 0))
    ctrl = bpy.context.active_object
    ctrl.name = "JANUS_Master_Controller"
    
    ctrl["Explode_Progress"] = 0.0
    ctrl["Pulse_Progress"] = 0.0
    
    id_props = ctrl.id_properties_ui("Explode_Progress")
    id_props.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, description="Z-Axis Strata Lift")

    id_props2 = ctrl.id_properties_ui("Pulse_Progress")
    id_props2.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, description="Optical Signal Cycle")

    return ctrl


def attach_explode_driver(obj, base_z, explode_delta, ctrl):
    """Attach a procedural Z-location driver keyed to Explode_Progress."""
    fcurve = obj.driver_add("location", 2)
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    var = driver.variables.new()
    var.name = "exp"
    var.type = 'SINGLE_PROP'
    target = var.targets[0]
    target.id_type = 'OBJECT'
    target.id = ctrl
    target.data_path = '["Explode_Progress"]'
    driver.expression = f"{base_z} + exp * {explode_delta}"


# ==============================================================================
# 5. MACRO PACKAGING & STRATA GENERATOR
# ==============================================================================
def build_packaging_and_strata(col_parent, mats, ctrl):
    """
    Build the full macro package:
    - Ceramic/PCB interposer package substrate (14.0 x 14.0 mm) with SMD caps & gold fiducials
    - 65nm CMOS Base Die (10.0 x 10.0 x 0.050 mm)
    - Monolithic SiO2 Thermal Buffer (250 µm) with Copper perimeter thermal shunt & Faraday cage
    - SiPh Photonic Stratum (30 µm)
    - Heat Spreader 1 (HS1, 30 µm Cu-pillar matrix)
    - Heat Spreader 2 (HS2, 250 µm microchannel slim lid with fluid ports)
    - V-Groove Fiber Launch Bench on west die edge
    """
    col_strata = get_or_create_collection("01_Packaging_and_Heterogeneous_Strata", col_parent)

    # 1. Package Interposer Substrate (14.0 x 14.0 x 0.60 mm)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    sub = bpy.context.active_object
    sub.name = "PACKAGE_01_FCBGA_Substrate"
    sub.scale = (14.0, 14.0, 0.60)
    sub.location = (0, 0, -0.30)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sub.data.materials.append(mats['pcb'])
    for c in sub.users_collection: c.objects.unlink(sub)
    col_strata.objects.link(sub)

    # Gold corner fiducials and perimeter decoupling capacitors
    for cx in [-5.8, 5.8]:
        for cy in [-5.8, 5.8]:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=0.03, vertices=16)
            fid = bpy.context.active_object
            fid.name = "Package_Fiducial"
            fid.location = (cx, cy, 0.015)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            fid.data.materials.append(mats['gold'])
            for c in fid.users_collection: c.objects.unlink(fid)
            col_strata.objects.link(fid)

    for i in range(12):
        px = -5.2 + i * 0.95
        for py in [-5.5, 5.5]:
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            cap = bpy.context.active_object
            cap.name = f"SMD_Decoupling_Cap_{i}"
            cap.scale = (0.50, 0.30, 0.25)
            cap.location = (px, py, 0.125)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            cap.data.materials.append(mats['copper'])
            for c in cap.users_collection: c.objects.unlink(cap)
            col_strata.objects.link(cap)

    # 2. 65nm CMOS Base Die (10.0 x 10.0 x 0.050 mm)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    cmos_die = bpy.context.active_object
    cmos_die.name = "STRATUM_03_CMOS_65nm_BaseDie"
    cmos_die.scale = (DIE_XY, DIE_XY, THICK_CMOS)
    cmos_die.location = (0, 0, Z_CMOS_BASE + THICK_CMOS / 2.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    cmos_die.data.materials.append(mats['silicon'])
    attach_explode_driver(cmos_die, cmos_die.location.z, EXP_CMOS_Z, ctrl)
    for c in cmos_die.users_collection: c.objects.unlink(cmos_die)
    col_strata.objects.link(cmos_die)

    # 3. Monolithic SiO2 Thermal Buffer (10.0 x 10.0 x 0.250 mm)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    sio2_layer = bpy.context.active_object
    sio2_layer.name = "STRATUM_02_SiO2_ThermalBuffer"
    sio2_layer.scale = (DIE_XY - 2 * SHUNT_WIDTH, DIE_XY - 2 * SHUNT_WIDTH, THICK_SIO2)
    sio2_layer.location = (0, 0, Z_SIO2_BASE + THICK_SIO2 / 2.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sio2_layer.data.materials.append(mats['sio2'])
    attach_explode_driver(sio2_layer, sio2_layer.location.z, EXP_SIO2_Z, ctrl)
    for c in sio2_layer.users_collection: c.objects.unlink(sio2_layer)
    col_strata.objects.link(sio2_layer)

    # 4. Perimeter Solid Copper Thermal Shunt & 100 GHz EMI Faraday Ring
    w_out = DIE_XY / 2.0
    border_objs = []
    for y_pos in [-w_out + SHUNT_WIDTH/2.0, w_out - SHUNT_WIDTH/2.0]:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        b = bpy.context.active_object
        b.scale = (DIE_XY, SHUNT_WIDTH, THICK_SIO2)
        b.location = (0, y_pos, Z_SIO2_BASE + THICK_SIO2 / 2.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        border_objs.append(b)
    for x_pos in [-w_out + SHUNT_WIDTH/2.0, w_out - SHUNT_WIDTH/2.0]:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        b = bpy.context.active_object
        b.scale = (SHUNT_WIDTH, DIE_XY - 2*SHUNT_WIDTH, THICK_SIO2)
        b.location = (x_pos, 0, Z_SIO2_BASE + THICK_SIO2 / 2.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        border_objs.append(b)
    
    for obj in border_objs: obj.select_set(True)
    bpy.context.view_layer.objects.active = border_objs[0]
    bpy.ops.object.join()
    shunt_ring = border_objs[0]
    shunt_ring.name = "Perimeter_Cu_Thermal_Shunt_Faraday_Cage"
    shunt_ring.data.materials.append(mats['copper'])
    attach_explode_driver(shunt_ring, shunt_ring.location.z, EXP_SIO2_Z, ctrl)
    for c in shunt_ring.users_collection: c.objects.unlink(shunt_ring)
    col_strata.objects.link(shunt_ring)

    # 5. Silicon Photonics (SiPh) Stratum (10.0 x 10.0 x 0.030 mm)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    siph_layer = bpy.context.active_object
    siph_layer.name = "STRATUM_01_SiPh_Photonic_Stratum"
    siph_layer.scale = (DIE_XY, DIE_XY, THICK_SIPH)
    siph_layer.location = (0, 0, Z_SIPH_BASE + THICK_SIPH / 2.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    siph_layer.data.materials.append(mats['siph_core'])
    attach_explode_driver(siph_layer, siph_layer.location.z, EXP_SIPH_Z, ctrl)
    for c in siph_layer.users_collection: c.objects.unlink(siph_layer)
    col_strata.objects.link(siph_layer)

    # 6. Heat Spreader 1 (HS1): 30 µm Cu-Pillar Dense Matrix (900k/mm²)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    hs1 = bpy.context.active_object
    hs1.name = "PACKAGE_Heat_Spreader_1_MicroMatrix"
    hs1.scale = (DIE_XY * 0.98, DIE_XY * 0.98, THICK_HS1)
    hs1.location = (0, 0, Z_HS1_BASE + THICK_HS1 / 2.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    hs1.data.materials.append(mats['copper_translucent'])
    attach_explode_driver(hs1, hs1.location.z, EXP_HS1_Z, ctrl)
    for c in hs1.users_collection: c.objects.unlink(hs1)
    col_strata.objects.link(hs1)

    # 7. Heat Spreader 2 (HS2): 250 µm Convective Microchannel Slim-Lid
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    hs2 = bpy.context.active_object
    hs2.name = "PACKAGE_Heat_Spreader_2_Convective_Lid"
    hs2.scale = (DIE_XY + 0.5, DIE_XY + 0.5, THICK_HS2)
    hs2.location = (0, 0, Z_HS2_BASE + THICK_HS2 / 2.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    hs2.data.materials.append(mats['copper'])
    attach_explode_driver(hs2, hs2.location.z, EXP_HS2_Z, ctrl)
    for c in hs2.users_collection: c.objects.unlink(hs2)
    col_strata.objects.link(hs2)

    # HS2 Microchannel Surface Grooves (Suggest internal cooling ribs)
    groove_z = Z_HS2_BASE + THICK_HS2 + 0.002
    for gi in range(18):
        gy = -4.0 + gi * 0.47
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        groove = bpy.context.active_object
        groove.name = f"HS2_MicroChannel_Groove_{gi}"
        groove.scale = (9.8, 0.06, 0.008)
        groove.location = (0, gy, groove_z)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        groove.data.materials.append(mats['gold'])
        attach_explode_driver(groove, groove.location.z, EXP_HS2_Z, ctrl)
        for c in groove.users_collection: c.objects.unlink(groove)
        col_strata.objects.link(groove)

    # A6: Bevel Modifiers on strata slabs for catch-light edge reflections
    for slab in [cmos_die, sio2_layer, siph_layer, hs2]:
        bev = slab.modifiers.new(name="Edge_Bevel", type='BEVEL')
        bev.width = 0.02
        bev.segments = 2
        bev.limit_method = 'ANGLE'
        bev.angle_limit = math.radians(60)

    # Fluid Coolant Inlet & Outlet Ports (Microchannel cooling manifold)
    for port_i, port_y in enumerate([-3.5, 3.5]):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=0.8, vertices=16)
        port = bpy.context.active_object
        port.name = f"HS2_Coolant_Port_{'Inlet' if port_i==0 else 'Outlet'}"
        port.location = (4.2, port_y, Z_HS2_BASE + THICK_HS2 + 0.4)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        port.data.materials.append(mats['gold'])
        attach_explode_driver(port, port.location.z, EXP_HS2_Z, ctrl)
        for c in port.users_collection: c.objects.unlink(port)
        col_strata.objects.link(port)

    # 8. Master 1064 nm Laser Launch Facet & Fiber Alignment Bench (West edge)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    bench = bpy.context.active_object
    bench.name = "V_Groove_Optical_Bench_Facet"
    bench.scale = (0.8, 1.2, 0.15)
    bench.location = (-DIE_XY/2.0 - 0.45, 0.0, Z_SIPH_BASE + 0.05)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bench.data.materials.append(mats['silicon'])
    attach_explode_driver(bench, bench.location.z, EXP_SIPH_Z, ctrl)
    for c in bench.users_collection: c.objects.unlink(bench)
    col_strata.objects.link(bench)

    # Fiber ferrule
    bpy.ops.mesh.primitive_cylinder_add(radius=0.22, depth=1.4, vertices=16)
    fiber = bpy.context.active_object
    fiber.name = "1064nm_SingleMode_Fiber_Pigtail"
    fiber.rotation_euler = (0, math.pi/2.0, 0)
    fiber.location = (-DIE_XY/2.0 - 1.1, 0.0, Z_SIPH_BASE + 0.05)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    fiber.data.materials.append(mats['copper'])
    attach_explode_driver(fiber, fiber.location.z, EXP_SIPH_Z, ctrl)
    for c in fiber.users_collection: c.objects.unlink(fiber)
    col_strata.objects.link(fiber)

    # High-tech Strata 3D Labels (Centered directly in front of each stratum facing the front camera)
    col_lbl = get_or_create_collection("07_Technical_3D_Labels", col_parent)
    lbl_y = -6.2
    
    lbl1 = add_3d_label("HS2: 250 um Convective Microchannel Slim-Lid", (0.0, lbl_y, Z_HS2_BASE + 0.12), scale=0.28, align='CENTER', mat=mats['label'], col=col_lbl)
    attach_explode_driver(lbl1, lbl1.location.z, EXP_HS2_Z, ctrl)

    lbl1b = add_3d_label("HS1: 30 um Cu-Pillar Dense Thermal Micro-Matrix", (0.0, lbl_y, Z_HS1_BASE + 0.12), scale=0.28, align='CENTER', mat=mats['label'], col=col_lbl)
    attach_explode_driver(lbl1b, lbl1b.location.z, EXP_HS1_Z, ctrl)

    lbl2 = add_3d_label("SiPh Stratum: 30 um (16 Photonic Tiles & SAC2M APDs)", (0.0, lbl_y, Z_SIPH_BASE + 0.12), scale=0.28, align='CENTER', mat=mats['label'], col=col_lbl)
    attach_explode_driver(lbl2, lbl2.location.z, EXP_SIPH_Z, ctrl)

    lbl3 = add_3d_label("SiO2 Buffer: 250 um (Vertical Cu TDV Interconnects)", (0.0, lbl_y, Z_SIO2_BASE + 0.12), scale=0.28, align='CENTER', mat=mats['label'], col=col_lbl)
    attach_explode_driver(lbl3, lbl3.location.z, EXP_SIO2_Z, ctrl)

    lbl4 = add_3d_label("CMOS Base Die: 50 um (65nm Logic & SIMD Datapaths)", (0.0, lbl_y, Z_CMOS_BASE + 0.12), scale=0.28, align='CENTER', mat=mats['label'], col=col_lbl)
    attach_explode_driver(lbl4, lbl4.location.z, EXP_CMOS_Z, ctrl)

    # Dynamic scale driver for labels — smoothly scales up as strata lift apart
    for lbl in [lbl1, lbl1b, lbl2, lbl3, lbl4]:
        for axis_idx in (0, 1, 2):
            fc = lbl.driver_add("scale", axis_idx)
            drv = fc.driver
            drv.type = 'SCRIPTED'
            var = drv.variables.new()
            var.name = "exp"
            var.type = 'SINGLE_PROP'
            target = var.targets[0]
            target.id_type = 'OBJECT'
            target.id = ctrl
            target.data_path = '["Explode_Progress"]'
            drv.expression = "0.0 if exp < 0.08 else min(1.0, (exp - 0.08) * 2.8)"


# ==============================================================================
# 6. 65nm CMOS BASE DIE FLOORPLAN & SUB-BLOCKS
# ==============================================================================
def build_cmos_floorplan(col_parent, mats, ctrl):
    """
    Construct 65nm CMOS floorplan directly on the CMOS silicon surface:
    - 1.5 MB Central Non-Volatile ROM Macro (1.80 mm²)
    - 32 Localized SRAM Slices (6.20 mm² total)
    - 32-Lane SIMD Calculation Array (4.50 mm²)
    - StrongARM Sensing & 1:32 Deserializer Front-End (3.00 mm²)
    - 18.5 kHz JIR Thermal Scheduler FSM (0.50 mm²)
    - High-density VDD/VSS Power Distribution Mesh (84.00 mm²)
    """
    col_cmos = get_or_create_collection("02_CMOS_65nm_Floorplan", col_parent)
    z_surf = Z_CMOS_BASE + THICK_CMOS + 0.002

    def add_cmos_block(name, w, h, x, y, mat):
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        obj = bpy.context.active_object
        obj.name = f"CMOS_{name}"
        obj.scale = (w, h, 0.006)
        obj.location = (x, y, z_surf)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(mat)
        attach_explode_driver(obj, obj.location.z, EXP_CMOS_Z, ctrl)
        for c in obj.users_collection: c.objects.unlink(obj)
        col_cmos.objects.link(obj)
        return obj

    # 1. Central ROM Macro (1.80 mm²)
    add_cmos_block("Central_NonVolatile_ROM_1.5MB", 1.34, 1.34, 0.0, 0.0, mats['cmos_rom'])

    # 2. JIR 18.5 kHz Thermal Scheduler (0.50 mm²)
    add_cmos_block("JIR_Thermal_Scheduler_FSM", 0.71, 0.71, 0.0, 1.35, mats['cmos_jir'])

    # 3. 32 Localized Dual-LUT SRAM Slices (48 KB each)
    sram_w, sram_h = 0.55, 0.36
    for i in range(16):
        xl = -3.4 + (i % 4) * 0.72
        yl = -3.2 + (i // 4) * 1.8
        add_cmos_block(f"SRAM_DualLUT_Slice_{i}_L", sram_w, sram_h, xl, yl, mats['cmos_sram'])
        
        xr = 1.3 + (i % 4) * 0.72
        yr = -3.2 + (i // 4) * 1.8
        add_cmos_block(f"SRAM_DualLUT_Slice_{i+16}_R", sram_w, sram_h, xr, yr, mats['cmos_sram'])

    # 4. 32-Lane SIMD Calculation Array (Wallace 8:2 CSA + 64-bit Kogge-Stone Adder)
    simd_w, simd_h = 0.24, 0.58
    for lane in range(32):
        side = -1 if lane < 16 else 1
        idx = lane if lane < 16 else lane - 16
        lx = side * 4.3
        ly = -3.6 + idx * 0.48
        add_cmos_block(f"SIMD_Lane_{lane}_Wallace_Kogge", simd_w, simd_h, lx, ly, mats['cmos_simd'])

    # 5. StrongARM Sensing Latches & 1:32 Deserializer Front-End (Directly beneath TDVs)
    deser_w, deser_h = 0.35, 1.80
    add_cmos_block("StrongARM_Deserializer_North", deser_h*2, deser_w, 0.0, 4.3, mats['cmos_latch'])
    add_cmos_block("StrongARM_Deserializer_South", deser_h*2, deser_w, 0.0, -4.3, mats['cmos_latch'])

    # 6. Orthogonal M1-M7 Copper Power Distribution Mesh Grid
    grid_lines = 16
    for g in range(grid_lines):
        pos = -4.5 + g * (9.0 / (grid_lines - 1))
        add_cmos_block(f"Power_Mesh_VDD_H_{g}", 9.2, 0.025, 0.0, pos, mats['cmos_power'])
        add_cmos_block(f"Power_Mesh_VSS_V_{g}", 0.025, 9.2, pos, 0.0, mats['cmos_power'])


# ==============================================================================
# 7. VERTICAL THROUGH-DIELECTRIC VIAS (Cu TDVs)
# ==============================================================================
def build_tdv_array(col_parent, mats, ctrl):
    """
    Construct vertical Cu Through-Dielectric Vias (TDVs) traversing the 250 µm SiO2 buffer.
    In the physical chip, Cu TDVs have 10,000 mm⁻² density and directly route avalanche
    charge from SiPh APDs down to CMOS StrongARM latches.
    """
    col_tdv = get_or_create_collection("03_Through_Dielectric_Vias_TDVs", col_parent)
    via_radius = 0.018       # 18 µm via radius
    via_height = THICK_SIO2  # 250 µm buffer height
    z_center = Z_SIO2_BASE + THICK_SIO2 / 2.0

    vias_per_tile = 5
    step = TILE_XY / (vias_per_tile + 1)
    seg = 8  # vertices per via cross-section

    # C1: BMesh-based TDV forest — build all vias in a single mesh (~20x faster)
    bm = bmesh.new()
    for tx in range(TILES_X):
        for ty in range(TILES_Y):
            t_cx = -DIE_XY/2.0 + (tx + 0.5) * TILE_XY
            t_cy = -DIE_XY/2.0 + (ty + 0.5) * TILE_XY
            for vx in range(vias_per_tile):
                for vy in range(vias_per_tile):
                    px = t_cx - TILE_XY/2.0 + (vx + 1) * step
                    py = t_cy - TILE_XY/2.0 + (vy + 1) * step
                    # Create a cylinder ring of vertices at top and bottom
                    top_verts = []
                    bot_verts = []
                    for s in range(seg):
                        angle = 2.0 * math.pi * s / seg
                        dx = via_radius * math.cos(angle)
                        dy = via_radius * math.sin(angle)
                        top_verts.append(bm.verts.new((px + dx, py + dy, z_center + via_height / 2.0)))
                        bot_verts.append(bm.verts.new((px + dx, py + dy, z_center - via_height / 2.0)))
                    # Top and bottom cap faces
                    bm.faces.new(top_verts)
                    bm.faces.new(bot_verts[::-1])
                    # Side faces connecting top to bottom
                    for s in range(seg):
                        s_next = (s + 1) % seg
                        bm.faces.new([top_verts[s], top_verts[s_next], bot_verts[s_next], bot_verts[s]])

    mesh_data = bpy.data.meshes.new("Cu_TDV_Forest_Mesh")
    bm.to_mesh(mesh_data)
    bm.free()

    tdv_forest = bpy.data.objects.new("Cu_TDV_Vertical_Via_Forest_10000_mm2", mesh_data)
    tdv_forest.location = (0, 0, 0)
    bpy.context.scene.collection.objects.link(tdv_forest)
    tdv_forest.data.materials.append(mats['copper'])
    
    attach_explode_driver(tdv_forest, z_center, (EXP_CMOS_Z + EXP_SIPH_Z) / 2.0, ctrl)
    
    # Driver stretches TDVs to bridge the gap during exploded view
    fcurve_sz = tdv_forest.driver_add("scale", 2)
    drv = fcurve_sz.driver
    drv.type = 'SCRIPTED'
    var = drv.variables.new()
    var.name = "exp"
    var.type = 'SINGLE_PROP'
    target = var.targets[0]
    target.id_type = 'OBJECT'
    target.id = ctrl
    target.data_path = '["Explode_Progress"]'
    drv.expression = f"1.0 + exp * ({(EXP_SIPH_Z - EXP_CMOS_Z) / THICK_SIO2})"

    for c in tdv_forest.users_collection: c.objects.unlink(tdv_forest)
    col_tdv.objects.link(tdv_forest)


# ==============================================================================
# 8. SILICON PHOTONICS (SiPh) 16-TILE MATRIX, BENES FABRIC & MONOLITHIC APDS
# ==============================================================================
def build_siph_photonic_tiles(col_parent, mats, ctrl):
    """
    Construct the complete 16-Tile SiPh Optical Stratum (30 µm):
    - 10-Stage Fractal H-Tree optical distribution network
    - 16 Optical Residue Tiles (2.5 mm x 2.5 mm each)
    - Focus Tile [0, 0]: High-resolution micro-architecture:
      * 1x256 LiTaO3 electro-optic Pockels router
      * 16 visible parallel waveguide tracks
      * 15-Stage Dilated Beneš Permutation Fabric with Sb2S3 phase-change cells
        AND visible butterfly shuffle crossover waveguides between stages!
      * Monolithic Ge/Si SAC2M APDs INSIDE the tile at waveguide terminus
        (Silicon multiplication cliff + Germanium absorber + Gold annular ring)
    - Tiles 1..15: High-density procedural waveguide tracks, H-tree spines, and APD banks
    """
    col_siph = get_or_create_collection("04_SiPh_16_Tile_Photonic_Mesh", col_parent)
    z_siph_top = Z_SIPH_BASE + THICK_SIPH + 0.002

    # 1. 10-Stage Fractal H-Tree Optical Distribution Network
    tree_objs = []
    
    # Main injection trunk from West facet
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    trunk = bpy.context.active_object
    trunk.name = "Optical_MMI_Main_Trunk"
    trunk.scale = (1.6, 0.05, 0.010)
    trunk.location = (-DIE_XY/2.0 + 0.80, 0.0, z_siph_top)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    trunk.data.materials.append(mats['optical_wave'])
    tree_objs.append(trunk)

    # Primary vertical spine
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    v_spine = bpy.context.active_object
    v_spine.name = "Fractal_HTree_Central_Spine_Y"
    v_spine.scale = (0.05, 5.2, 0.010)
    v_spine.location = (0.0, 0.0, z_siph_top)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    v_spine.data.materials.append(mats['optical_wave'])
    tree_objs.append(v_spine)

    # Secondary horizontal H-branches (Top and Bottom)
    for hy in [-2.5, 2.5]:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        h_branch = bpy.context.active_object
        h_branch.name = f"Fractal_HTree_Branch_H_{hy}"
        h_branch.scale = (5.2, 0.04, 0.010)
        h_branch.location = (0.0, hy, z_siph_top)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        h_branch.data.materials.append(mats['optical_wave'])
        tree_objs.append(h_branch)

    # Tertiary vertical distribution feeders into each tile center
    for tx in [-3.75, -1.25, 1.25, 3.75]:
        for ty in [-3.75, -1.25, 1.25, 3.75]:
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            feeder = bpy.context.active_object
            feeder.name = f"HTree_Feeder_T_{tx}_{ty}"
            feeder.scale = (0.03, 1.2, 0.008)
            feeder.location = (tx, ty, z_siph_top)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            feeder.data.materials.append(mats['optical_wave'])
            tree_objs.append(feeder)

    for tobj in tree_objs:
        attach_explode_driver(tobj, tobj.location.z, EXP_SIPH_Z, ctrl)
        for c in tobj.users_collection: c.objects.unlink(tobj)
        col_siph.objects.link(tobj)

    # 2. Build the 16 Optical Residue Tiles with Full 15-Stage Dilated Beneš Crossover Matrix
    proto_col = bpy.data.collections.new("SiPh_Benes_Tile_Fabric_Prototype")
    proto_col.use_fake_user = True
    _build_benes_tile_prototype(proto_col, mats)

    for tx in range(TILES_X):
        for ty in range(TILES_Y):
            tile_id = ty * TILES_X + tx
            cx = -DIE_XY/2.0 + (tx + 0.5) * TILE_XY
            cy = -DIE_XY/2.0 + (ty + 0.5) * TILE_XY

            # Tile Boundary Plate (Silicon-on-Insulator base)
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            t_obj = bpy.context.active_object
            t_obj.name = f"Tile_{tile_id:02d}_Plate"
            t_obj.scale = (TILE_XY - TILE_GAP, TILE_XY - TILE_GAP, 0.005)
            t_obj.location = (cx, cy, z_siph_top)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            t_obj.data.materials.append(mats['siph_core'])
            attach_explode_driver(t_obj, t_obj.location.z, EXP_SIPH_Z, ctrl)
            for c in t_obj.users_collection: c.objects.unlink(t_obj)
            col_siph.objects.link(t_obj)

            # Beneš Permutation Fabric Instance (present on ALL 16 TILES!)
            inst = bpy.data.objects.new(f"SiPh_Benes_TileFabric_{tile_id:02d}", None)
            inst.instance_type = 'COLLECTION'
            inst.instance_collection = proto_col
            inst.location = (cx, cy, z_siph_top)
            attach_explode_driver(inst, z_siph_top, EXP_SIPH_Z, ctrl)
            col_siph.objects.link(inst)


def _build_benes_tile_prototype(col, mats):
    """
    Build the complete authentic micro-architecture of a 16-lane, 15-stage dilated
    Beneš permutation network at origin (0, 0, 0) for instancing across all 16 tiles:
    - 1x256 LiTaO3 electro-optic Pockels input router bank
    - 16 parallel single-mode waveguide lanes
    - 15-stage Dilated Beneš Permutation Fabric:
      * 15 vertical columns of 2x2 Sb2S3 directional coupler phase-change cells (crystalline vs amorphous)
      * Butterfly crossover waveguides between stages!
    - Monolithic Ge/Si SAC2M APDs at waveguide terminus (Si cliff, Ge absorber, Au ring, Cu TDV stem)
    """
    mult_w = 2.15
    mult_h = 2.15
    z_m = 0.006

    # 1. LiTaO3 Electro-Optic Pockels Router Bank (West edge)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    pockels = bpy.context.active_object
    pockels.name = "Proto_LiTaO3_Pockels_Router"
    pockels.scale = (0.16, mult_h * 0.88, 0.014)
    pockels.location = (-mult_w/2.0 + 0.10, 0.0, z_m + 0.004)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pockels.data.materials.append(mats['litao3'])
    for c in pockels.users_collection: c.objects.unlink(pockels)
    col.objects.link(pockels)

    # 2. 16 Waveguide Lanes & Butterfly Crossovers (Material: optical_wave)
    num_lanes = 16
    lane_step = (mult_h * 0.82) / (num_lanes - 1)
    lane_ys = [-(mult_h * 0.41) + l * lane_step for l in range(num_lanes)]
    
    wg_objs = []
    for l in range(num_lanes):
        ly = lane_ys[l]
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        lane = bpy.context.active_object
        lane.scale = (mult_w * 0.72, 0.010, 0.006)
        lane.location = (0.02, ly, z_m)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        wg_objs.append(lane)

    # 3. 15-Stage Beneš Cells & Butterfly Crossovers
    num_stages = 15
    stage_step = (mult_w * 0.52) / (num_stages - 1)
    start_x = -(mult_w * 0.26)

    cryst_cells = []
    amorph_cells = []

    for s in range(num_stages):
        sx = start_x + s * stage_step

        # 2x2 Switch Cells in this stage (8 cells per stage)
        for cell_idx in range(num_lanes // 2):
            cell_y = (lane_ys[cell_idx * 2] + lane_ys[cell_idx * 2 + 1]) / 2.0
            bpy.ops.mesh.primitive_cube_add(size=1.0)
            cell = bpy.context.active_object
            cell.scale = (0.024, lane_step * 0.90, 0.012)
            cell.location = (sx, cell_y, z_m + 0.005)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            if (s + cell_idx) % 3 == 0:
                cryst_cells.append(cell)
            else:
                amorph_cells.append(cell)

        # Butterfly Crossover Waveguides between stage s and stage s+1
        if s < num_stages - 1:
            next_sx = sx + stage_step
            # Connect all pairs with butterfly shuffle crossovers
            for pair in range(0, num_lanes, 4):
                if pair + 3 < num_lanes:
                    for (i1, i2) in [(pair, pair + 2), (pair + 1, pair + 3)]:
                        y_a = lane_ys[i1]
                        y_b = lane_ys[i2]
                        dx = next_sx - sx
                        dy = y_b - y_a
                        cross_len = math.sqrt(dx*dx + dy*dy)
                        cross_ang = math.atan2(dy, dx)

                        bpy.ops.mesh.primitive_cube_add(size=1.0)
                        cw1 = bpy.context.active_object
                        cw1.scale = (cross_len, 0.008, 0.006)
                        cw1.rotation_euler = (0, 0, cross_ang)
                        cw1.location = ((sx + next_sx)/2.0, (y_a + y_b)/2.0, z_m + 0.002)
                        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                        wg_objs.append(cw1)

                        bpy.ops.mesh.primitive_cube_add(size=1.0)
                        cw2 = bpy.context.active_object
                        cw2.scale = (cross_len, 0.008, 0.006)
                        cw2.rotation_euler = (0, 0, -cross_ang)
                        cw2.location = ((sx + next_sx)/2.0, (y_a + y_b)/2.0, z_m + 0.002)
                        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                        wg_objs.append(cw2)

    # Join all waveguides & crossovers into 1 unified mesh object
    if wg_objs:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in wg_objs: obj.select_set(True)
        bpy.context.view_layer.objects.active = wg_objs[0]
        bpy.ops.object.join()
        wg_mesh = wg_objs[0]
        wg_mesh.name = "Proto_Benes_Waveguides_and_Crossovers"
        wg_mesh.data.materials.append(mats['optical_wave'])
        for c in wg_mesh.users_collection: c.objects.unlink(wg_mesh)
        col.objects.link(wg_mesh)

    # Join crystalline switch cells into 1 object
    if cryst_cells:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in cryst_cells: obj.select_set(True)
        bpy.context.view_layer.objects.active = cryst_cells[0]
        bpy.ops.object.join()
        cryst_mesh = cryst_cells[0]
        cryst_mesh.name = "Proto_Benes_Cells_Crystalline"
        cryst_mesh.data.materials.append(mats['sb2s3_crystalline'])
        for c in cryst_mesh.users_collection: c.objects.unlink(cryst_mesh)
        col.objects.link(cryst_mesh)

    # Join amorphous switch cells into 1 object
    if amorph_cells:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in amorph_cells: obj.select_set(True)
        bpy.context.view_layer.objects.active = amorph_cells[0]
        bpy.ops.object.join()
        amorph_mesh = amorph_cells[0]
        amorph_mesh.name = "Proto_Benes_Cells_Amorphous"
        amorph_mesh.data.materials.append(mats['sb2s3_amorphous'])
        for c in amorph_mesh.users_collection: c.objects.unlink(amorph_mesh)
        col.objects.link(amorph_mesh)

    # 4. SAC2M APDs at waveguide terminus
    apd_x = mult_w * 0.40
    si_bases = []
    ge_tops = []
    au_rings = []
    cu_stems = []

    for l_idx, ay in enumerate(lane_ys):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.038, depth=0.016, vertices=12)
        si = bpy.context.active_object
        si.location = (apd_x, ay, z_m + 0.008)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        si_bases.append(si)

        bpy.ops.mesh.primitive_cylinder_add(radius=0.032, depth=0.014, vertices=12)
        ge = bpy.context.active_object
        ge.location = (apd_x, ay, z_m + 0.022)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        ge_tops.append(ge)

        bpy.ops.mesh.primitive_torus_add(major_radius=0.026, minor_radius=0.005, major_segments=12, minor_segments=6)
        au = bpy.context.active_object
        au.location = (apd_x, ay, z_m + 0.030)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        au_rings.append(au)

        bpy.ops.mesh.primitive_cylinder_add(radius=0.014, depth=0.08, vertices=8)
        stem = bpy.context.active_object
        stem.location = (apd_x, ay, z_m - 0.04)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        cu_stems.append(stem)

    for (group, mat, name) in [
        (si_bases, mats['silicon_cliff'], "Proto_SAC2M_Si_Cliffs"),
        (ge_tops, mats['germanium'], "Proto_SAC2M_Ge_Absorbers"),
        (au_rings, mats['gold'], "Proto_SAC2M_Au_Rings"),
        (cu_stems, mats['copper'], "Proto_SAC2M_Cu_Stems")
    ]:
        if group:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in group: obj.select_set(True)
            bpy.context.view_layer.objects.active = group[0]
            bpy.ops.object.join()
            j_obj = group[0]
            j_obj.name = name
            j_obj.data.materials.append(mat)
            for c in j_obj.users_collection: c.objects.unlink(j_obj)
            col.objects.link(j_obj)


# ==============================================================================
# 9. SUB-MICRON DEVICE PHYSICS INSPECTION STATION (LEVEL 1)
# ==============================================================================
def build_submicron_physics_station(col_parent, mats, ctrl):
    """
    Construct standalone high-detail inspection station to the right of the chip die.
    Features:
    1. Single 2x2 Sb2S3 Switch Cell (60 µm length, directional coupler, 1 nm graphene heater, gold vias)
    2. Parabolic MMI Waveguide Crossing (1.6 µm waist, 6.4 µm taper, 0.018 dB loss)
    3. Ge/Si SAC2M APD Mesa Cutaway (Silicon avalanche cliff + Germanium absorber + Gold ring + Cu TDV)
    """
    col_micro = get_or_create_collection("06_SubMicron_Device_Physics_Station", col_parent)

    # Base Pedestal for Micro-Physics Models
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    pedestal = bpy.context.active_object
    pedestal.name = "MicroPhysics_Display_Pedestal"
    pedestal.scale = (11.0, 10.0, 0.20)
    pedestal.location = (CALLOUT_X, CALLOUT_Y, -0.10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    pedestal.data.materials.append(mats['silicon'])
    for c in pedestal.users_collection: c.objects.unlink(pedestal)
    col_micro.objects.link(pedestal)

    # Station Header 3D Label
    add_3d_label("JANUS-Mini16 Sub-Micron Device Physics Station", (CALLOUT_X - 4.6, 4.2, 0.15), scale=0.32, mat=mats['label'], col=col_micro)

    # --------------------------------------------------------------------------
    # Sub-Block A: Single 2x2 Sb2S3 Phase-Change Switch Cell (L = 60 µm)
    # --------------------------------------------------------------------------
    sw_cx, sw_cy = CALLOUT_X, CALLOUT_Y + 1.8
    add_3d_label("Sb2S3 2x2 Switch Cell (60 µm)", (sw_cx - 2.6, sw_cy + 1.2, 0.15), scale=0.25, mat=mats['label'], col=col_micro)

    wg_len = 5.6
    wg_w   = 0.30
    wg_gap = 0.25
    for dy in [-wg_gap/2 - wg_w/2, wg_gap/2 + wg_w/2]:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        wg = bpy.context.active_object
        wg.name = "Callout_Sb2S3_Waveguide"
        wg.scale = (wg_len, wg_w, 0.18)
        wg.location = (sw_cx, sw_cy + dy, 0.10)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        wg.data.materials.append(mats['optical_wave'])
        for c in wg.users_collection: c.objects.unlink(wg)
        col_micro.objects.link(wg)

    # Active Sb2S3 Patch (60 µm length)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    sb_patch = bpy.context.active_object
    sb_patch.name = "Callout_Sb2S3_Phase_Change_Patch_60um"
    sb_patch.scale = (3.0, wg_gap + wg_w*2 + 0.12, 0.12)
    sb_patch.location = (sw_cx, sw_cy, 0.24)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sb_patch.data.materials.append(mats['sb2s3_amorphous'])
    for c in sb_patch.users_collection: c.objects.unlink(sb_patch)
    col_micro.objects.link(sb_patch)

    # Monolayer Graphene Electro-Thermal Micro-Heater (1 nm layer)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    graphene = bpy.context.active_object
    graphene.name = "Callout_1nm_Monolayer_Graphene_MicroHeater"
    graphene.scale = (2.8, wg_gap + wg_w*2 + 0.06, 0.03)
    graphene.location = (sw_cx, sw_cy, 0.32)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    graphene.data.materials.append(mats['graphene'])
    for c in graphene.users_collection: c.objects.unlink(graphene)
    col_micro.objects.link(graphene)

    # Gold Contact Electrodes (4.2 pJ/cell electrical SET/RESET pulses)
    for side_x in [-1.5, 1.5]:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        gold_pad = bpy.context.active_object
        gold_pad.name = "Callout_Graphene_Gold_Electrode"
        gold_pad.scale = (0.40, 1.1, 0.15)
        gold_pad.location = (sw_cx + side_x, sw_cy, 0.35)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        gold_pad.data.materials.append(mats['gold'])
        for c in gold_pad.users_collection: c.objects.unlink(gold_pad)
        col_micro.objects.link(gold_pad)

    # --------------------------------------------------------------------------
    # Sub-Block B: Parabolic MMI Low-Loss Waveguide Crossing (0.018 dB Loss)
    # --------------------------------------------------------------------------
    mmi_cx, mmi_cy = CALLOUT_X - 2.8, CALLOUT_Y - 2.5
    add_3d_label("Parabolic MMI Crossing", (mmi_cx - 2.0, mmi_cy + 1.2, 0.15), scale=0.22, mat=mats['label'], col=col_micro)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.95, depth=0.18, vertices=4)
    mmi_waist = bpy.context.active_object
    mmi_waist.name = "Callout_Parabolic_MMI_Waist"
    mmi_waist.rotation_euler = (0, 0, math.pi/4.0)
    mmi_waist.location = (mmi_cx, mmi_cy, 0.10)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mmi_waist.data.materials.append(mats['siph_core'])
    for c in mmi_waist.users_collection: c.objects.unlink(mmi_waist)
    col_micro.objects.link(mmi_waist)

    for ang in [0, math.pi/2.0]:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        cw = bpy.context.active_object
        cw.name = f"Callout_MMI_Arm_{int(math.degrees(ang))}"
        cw.scale = (3.8, 0.28, 0.14)
        cw.rotation_euler = (0, 0, ang)
        cw.location = (mmi_cx, mmi_cy, 0.10)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        cw.data.materials.append(mats['optical_wave'])
        for c in cw.users_collection: c.objects.unlink(cw)
        col_micro.objects.link(cw)

    # --------------------------------------------------------------------------
    # Sub-Block C: Monolithic Ge/Si SAC2M APD Mesa Cutaway
    # --------------------------------------------------------------------------
    apd_cx, apd_cy = CALLOUT_X + 2.8, CALLOUT_Y - 2.5
    add_3d_label("SAC2M Ge/Si APD Mesa", (apd_cx - 1.8, apd_cy + 1.2, 0.15), scale=0.22, mat=mats['label'], col=col_micro)

    # 1. Silicon Multiplication Mesa (M = 7)
    bpy.ops.mesh.primitive_cylinder_add(radius=1.1, depth=0.45, vertices=32)
    si_mesa = bpy.context.active_object
    si_mesa.name = "Callout_SAC2M_Silicon_Mesa"
    si_mesa.location = (apd_cx, apd_cy, 0.22)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    si_mesa.data.materials.append(mats['silicon_cliff'])
    for c in si_mesa.users_collection: c.objects.unlink(si_mesa)
    col_micro.objects.link(si_mesa)

    # 2. Pure Germanium Absorption Layer (R = 1.2 A/W @ 1064 nm)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.85, depth=0.40, vertices=32)
    ge_layer = bpy.context.active_object
    ge_layer.name = "Callout_SAC2M_Germanium_Absorber"
    ge_layer.location = (apd_cx, apd_cy, 0.60)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ge_layer.data.materials.append(mats['germanium'])
    for c in ge_layer.users_collection: c.objects.unlink(ge_layer)
    col_micro.objects.link(ge_layer)

    # 3. Top Annular Contact Ring (Gold)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.75, minor_radius=0.08, major_segments=32, minor_segments=12)
    ring = bpy.context.active_object
    ring.name = "Callout_SAC2M_Top_Anode_Contact"
    ring.location = (apd_cx, apd_cy, 0.82)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ring.data.materials.append(mats['gold'])
    for c in ring.users_collection: c.objects.unlink(ring)
    col_micro.objects.link(ring)

    # 4. Vertical Cu TDV Stem dropping down to CMOS base
    bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=1.4, vertices=16)
    tdv_stem = bpy.context.active_object
    tdv_stem.name = "Callout_SAC2M_Cu_TDV_Stem"
    tdv_stem.location = (apd_cx, apd_cy, -0.70)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    tdv_stem.data.materials.append(mats['copper'])
    for c in tdv_stem.users_collection: c.objects.unlink(tdv_stem)
    col_micro.objects.link(tdv_stem)


# ==============================================================================
# 10. SYNCHRONIZED SIGNAL PULSE ANIMATION (OPTICAL TO ELECTRICAL)
# ==============================================================================
def build_signal_pulse_animation(col_parent, mats, ctrl):
    """
    Construct the synchronized wave-pipelined operating cycle:
    1. 1064 nm Laser Pulse launches at fiber facet -> branches down Fractal H-Tree into Tile 0.
    2. Enters LiTaO3 Pockels Router -> selected active One-Hot waveguide.
    3. Traverses 15-stage dilated Beneš permutation fabric.
    4. Absorbed at Ge/Si SAC2M APD inside the tile (avalanche photocarrier flash).
    5. Discharges down vertical Cu TDV through 250 µm SiO2 buffer into CMOS StrongARM latch.
    6. Triggers 32-lane SIMD calculation array!
    Upgrades:
    - B3: Comet trail (ghost spheres trailing the photon packet)
    - B4: Pulse_Progress driven intensity ramp-up
    - B2: Smooth SINE easing on keyframes
    """
    col_pulse = get_or_create_collection("08_Signal_Flow_Pulse_Animation", col_parent)
    z_siph = Z_SIPH_BASE + THICK_SIPH + 0.018

    # 1. Optical In-Flight Pulse (1064 nm Glowing Cyan Core)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, segments=16, ring_count=12)
    opt_pulse = bpy.context.active_object
    opt_pulse.name = "InFlight_1064nm_Optical_Pulse"
    opt_pulse.data.materials.append(mats['active_pulse'])
    for c in opt_pulse.users_collection: c.objects.unlink(opt_pulse)
    col_pulse.objects.link(opt_pulse)

    # B3: Comet Trail Ghosts (3 trailing spheres)
    trail_ghosts = []
    for ti in range(3):
        ghost_scale = 0.72 - ti * 0.18
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, segments=12, ring_count=8)
        ghost = bpy.context.active_object
        ghost.name = f"Pulse_Trail_Ghost_{ti}"
        ghost.scale = (ghost_scale, ghost_scale, ghost_scale)

        mat_ghost = bpy.data.materials.new(name=f"Mat_Trail_Ghost_{ti}")
        mat_ghost.use_nodes = True
        g_nodes = mat_ghost.node_tree.nodes
        g_nodes.clear()
        g_out = g_nodes.new(type="ShaderNodeOutputMaterial")
        g_emit = g_nodes.new(type="ShaderNodeEmission")
        g_emit.inputs["Color"].default_value = (0.0, 0.70, 0.90, 1.0)
        g_emit.inputs["Strength"].default_value = 14.0 - ti * 4.0
        mat_ghost.node_tree.links.new(g_emit.outputs["Emission"], g_out.inputs["Surface"])
        ghost.data.materials.append(mat_ghost)

        attach_explode_driver(ghost, z_siph, EXP_SIPH_Z, ctrl)
        for c in ghost.users_collection: c.objects.unlink(ghost)
        col_pulse.objects.link(ghost)
        trail_ghosts.append(ghost)

    pulse_waypoints = [
        ((-DIE_XY/2.0 - 0.40, 0.0, z_siph), 1),
        ((-2.5, 0.0, z_siph), 100),
        ((-3.75, -2.5, z_siph), 240),
        ((-4.65, -3.75, z_siph), 270),
        ((-3.75, -3.75, z_siph), 300),
        ((-2.90, -3.75, z_siph), 330),
    ]

    opt_pulse.scale = (1, 1, 1)
    opt_pulse.keyframe_insert(data_path="scale", frame=1)
    for loc, frame in pulse_waypoints:
        opt_pulse.location = loc
        opt_pulse.keyframe_insert(data_path="location", frame=frame)

    for ti, ghost in enumerate(trail_ghosts):
        delay = (ti + 1) * 3
        ghost.scale = (1, 1, 1)
        ghost.keyframe_insert(data_path="scale", frame=1)
        for loc, frame in pulse_waypoints:
            ghost.location = loc
            ghost.keyframe_insert(data_path="location", frame=frame + delay)

    # Frame 332: Photonic Absorption Flash! (Scale explodes then collapses)
    opt_pulse.scale = (2.2, 2.2, 2.2)
    opt_pulse.keyframe_insert(data_path="scale", frame=332)
    opt_pulse.scale = (0.001, 0.001, 0.001)
    opt_pulse.keyframe_insert(data_path="scale", frame=336)

    for ghost in trail_ghosts:
        ghost.keyframe_insert(data_path="scale", frame=332)
        ghost.scale = (0.001, 0.001, 0.001)
        ghost.keyframe_insert(data_path="scale", frame=338)

    # Attach explode driver so the pulse tracks SiPh layer lift!
    attach_explode_driver(opt_pulse, z_siph, EXP_SIPH_Z, ctrl)

    # B4: Pulse_Progress keyframe driver on controller
    ctrl["Pulse_Progress"] = 0.0
    ctrl.keyframe_insert(data_path='["Pulse_Progress"]', frame=1)
    ctrl["Pulse_Progress"] = 0.25
    ctrl.keyframe_insert(data_path='["Pulse_Progress"]', frame=240)
    ctrl["Pulse_Progress"] = 1.0
    ctrl.keyframe_insert(data_path='["Pulse_Progress"]', frame=330)
    ctrl["Pulse_Progress"] = 0.0
    ctrl.keyframe_insert(data_path='["Pulse_Progress"]', frame=338)

    # B2: SINE Easing on optical pulse and ghosts
    for animated_obj in [opt_pulse] + trail_ghosts:
        if animated_obj.animation_data and animated_obj.animation_data.action:
            for fc in get_action_fcurves(animated_obj.animation_data.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'SINE'
                    kp.easing = 'EASE_IN_OUT'

    # 2. Electrical Avalanche Charge Pulse (Descends down vertical Cu TDV)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.06, segments=16, ring_count=12)
    elec_pulse = bpy.context.active_object
    elec_pulse.name = "Electrical_Avalanche_TDV_Charge_Pulse"
    elec_pulse.data.materials.append(mats['electric_pulse'])
    for c in elec_pulse.users_collection: c.objects.unlink(elec_pulse)
    col_pulse.objects.link(elec_pulse)

    # Hidden before frame 334
    elec_pulse.scale = (0.001, 0.001, 0.001)
    elec_pulse.location = (-2.90, -3.75, z_siph)
    elec_pulse.keyframe_insert(data_path="scale", frame=334)
    elec_pulse.keyframe_insert(data_path="location", frame=334)

    # Frame 335: Spawns at APD base on SiPh
    elec_pulse.scale = (1, 1, 1)
    elec_pulse.location = (-2.90, -3.75, Z_SIPH_BASE)
    elec_pulse.keyframe_insert(data_path="scale", frame=335)
    elec_pulse.keyframe_insert(data_path="location", frame=335)

    # Descent into CMOS:
    # Frame 370: Descending through 250 µm SiO2 buffer
    elec_pulse.location = (-2.90, -3.75, Z_SIO2_BASE + THICK_SIO2 / 2.0)
    elec_pulse.keyframe_insert(data_path="location", frame=370)

    # Frame 400: Enters CMOS StrongARM latch at CMOS surface!
    elec_pulse.location = (-2.90, -3.75, Z_CMOS_BASE + THICK_CMOS)
    elec_pulse.keyframe_insert(data_path="location", frame=400)

    # Frame 430: Latched into CMOS 32-lane SIMD datapath
    elec_pulse.location = (-4.3, -3.5, Z_CMOS_BASE + THICK_CMOS)
    elec_pulse.scale = (1, 1, 1)
    elec_pulse.keyframe_insert(data_path="location", frame=430)
    elec_pulse.keyframe_insert(data_path="scale", frame=430)

    elec_pulse.scale = (0.001, 0.001, 0.001)
    elec_pulse.keyframe_insert(data_path="scale", frame=440)

    if elec_pulse.animation_data and elec_pulse.animation_data.action:
        for fc in get_action_fcurves(elec_pulse.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = 'SINE'
                kp.easing = 'EASE_IN_OUT'


# ==============================================================================
# 11. 5-SHOT CINEMATIC CAMERA CHOREOGRAPHY & TIMELINE MARKERS
# ==============================================================================
def setup_cinematic_animation_and_cameras(col_parent, ctrl):
    """
    Configure 400-frame master animation with 5 specialized camera shots:
    - Shot 1 (Frames 001 - 070): Macro Package Hero Orbit
    - Shot 2 (Frames 071 - 160): Dramatic Exploded Stratigraphy Lift (Explode_Progress: 0.0 -> 1.0)
    - Shot 3 (Frames 161 - 260): Microscopic Deep Dive into Tile 0 (Beneš butterfly + APD strike)
    - Shot 4 (Frames 261 - 330): Cross-Stratum Avalanche Discharge down Cu TDV into CMOS StrongARM
    - Shot 5 (Frames 331 - 400): Sub-Micron Physics Station Orbit & Monolithic Re-assembly
    """
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 600
    scene.render.fps = 60

    col_rig = get_or_create_collection("00_Studio_Rig_and_Cinematic_Cameras", col_parent)

    # Master Exploded View Keyframes (10-second front showcase sequence)
    # Frames 1-80: Assembled monolithic hold
    # Frames 80-220: Smooth vertical strata expansion lift
    # Frames 220-480: Full exploded inspection hold (pulse flow & readable front labels)
    # Frames 480-575: Smooth convergence reassembly back to monolithic package
    # Frames 575-600: Assembled hold
    ctrl["Explode_Progress"] = 0.0
    ctrl.keyframe_insert(data_path='["Explode_Progress"]', frame=1)
    ctrl.keyframe_insert(data_path='["Explode_Progress"]', frame=80)

    ctrl["Explode_Progress"] = 1.0
    ctrl.keyframe_insert(data_path='["Explode_Progress"]', frame=220)
    ctrl.keyframe_insert(data_path='["Explode_Progress"]', frame=480)

    ctrl["Explode_Progress"] = 0.0
    ctrl.keyframe_insert(data_path='["Explode_Progress"]', frame=575)
    ctrl.keyframe_insert(data_path='["Explode_Progress"]', frame=600)

    # Smooth Bezier easing on explode keyframes
    if ctrl.animation_data and ctrl.animation_data.action:
        for fc in get_action_fcurves(ctrl.animation_data.action):
            if 'Explode_Progress' in fc.data_path:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'BEZIER'
                    kp.easing = 'EASE_IN_OUT'

    # --------------------------------------------------------------------------
    # Studio Lighting (Cinematic dark-field with front rim highlights)
    # --------------------------------------------------------------------------
    # Key Light
    bpy.ops.object.light_add(type='AREA', radius=16.0, location=(14.0, -18.0, 22.0))
    key = bpy.context.active_object
    key.name = "Studio_Key_Light"
    key.data.energy = 1300.0
    key.data.color = (1.0, 0.98, 0.95)
    key.rotation_euler = (math.radians(45), 0, math.radians(45))
    for c in key.users_collection: c.objects.unlink(key)
    col_rig.objects.link(key)

    # Fill Light (Cool Cyan Tone from front-left)
    bpy.ops.object.light_add(type='AREA', radius=16.0, location=(-16.0, -16.0, 18.0))
    fill = bpy.context.active_object
    fill.name = "Studio_Fill_Light"
    fill.data.energy = 700.0
    fill.data.color = (0.75, 0.90, 1.0)
    fill.rotation_euler = (math.radians(50), 0, math.radians(-45))
    for c in fill.users_collection: c.objects.unlink(fill)
    col_rig.objects.link(fill)

    # Rim Light (Photonic Specular Highlights from behind)
    bpy.ops.object.light_add(type='POINT', radius=4.0, location=(0.0, 20.0, 18.0))
    rim = bpy.context.active_object
    rim.name = "Studio_Rim_Light"
    rim.data.energy = 900.0
    rim.data.color = (0.35, 0.90, 1.0)
    for c in rim.users_collection: c.objects.unlink(rim)
    col_rig.objects.link(rim)

    # Overhead Softbox Light (Highlights metallic copper sheen & ports)
    bpy.ops.object.light_add(type='AREA', radius=12.0, location=(0.0, -2.0, 16.0))
    top_light = bpy.context.active_object
    top_light.name = "Studio_Overhead_Softbox"
    top_light.data.energy = 1050.0
    top_light.data.color = (1.0, 0.98, 0.95)
    for c in top_light.users_collection: c.objects.unlink(top_light)
    col_rig.objects.link(top_light)

    # Under-Die Accent Light (Illuminates CMOS floorplan & Cu TDV stems)
    bpy.ops.object.light_add(type='POINT', radius=1.5, location=(-2.9, -3.75, 0.4))
    under_light = bpy.context.active_object
    under_light.name = "CMOS_Under_Accent_Light"
    under_light.data.energy = 400.0
    under_light.data.color = (0.25, 0.95, 0.65)
    for c in under_light.users_collection: c.objects.unlink(under_light)
    col_rig.objects.link(under_light)

    # Front Fill Light for Text Labels
    bpy.ops.object.light_add(type='AREA', radius=10.0, location=(0.0, -18.0, 6.0))
    front_lbl_light = bpy.context.active_object
    front_lbl_light.name = "Front_Label_Fill_Light"
    front_lbl_light.data.energy = 350.0
    front_lbl_light.data.color = (0.90, 0.95, 1.0)
    front_lbl_light.rotation_euler = (math.radians(75), 0, 0)
    for c in front_lbl_light.users_collection: c.objects.unlink(front_lbl_light)
    col_rig.objects.link(front_lbl_light)

    # --------------------------------------------------------------------------
    # Dedicated Front Hero Camera (Continuous 10-Second Showcase)
    # --------------------------------------------------------------------------
    scene.timeline_markers.clear()

    bpy.ops.object.camera_add(location=(0.0, -32.0, 7.0))
    cam_front = bpy.context.active_object
    cam_front.name = "Cam_Front_Hero"
    cam_front.rotation_euler = (math.radians(86.8), 0, 0)
    cam_front.data.lens = 35.0
    cam_front.data.dof.use_dof = True
    cam_front.data.dof.focus_distance = 30.0
    cam_front.data.dof.aperture_fstop = 11.0  # Crisp focus across all strata and labels
    for c in cam_front.users_collection: c.objects.unlink(cam_front)
    col_rig.objects.link(cam_front)

    # Subtle cinematic front push-in over 600 frames
    cam_front.keyframe_insert(data_path="location", frame=1)
    cam_front.location = (0.0, -29.0, 6.7)
    cam_front.keyframe_insert(data_path="location", frame=600)

    if cam_front.animation_data and cam_front.animation_data.action:
        for fc in get_action_fcurves(cam_front.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = 'SINE'
                kp.easing = 'EASE_IN_OUT'

    scene.camera = cam_front


# ==============================================================================
# 12. WORLD ENVIRONMENT & BLENDER 5.2 COMPOSITOR PHOTONIC BLOOM
# ==============================================================================
def setup_world_environment():
    """
    Configure a sleek cinematic dark slate environment with subtle fill radiance
    replacing Blender's default flat gray world (A1).
    """
    scene = bpy.context.scene
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("JANUS_World")
        scene.world = world
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    wnodes.clear()

    out = wnodes.new(type='ShaderNodeOutputWorld')
    bg = wnodes.new(type='ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.012, 0.016, 0.024, 1.0)  # Deep dark slate navy
    bg.inputs['Strength'].default_value = 0.65
    wlinks.new(bg.outputs['Background'], out.inputs['Surface'])


def setup_compositor_bloom():
    """
    Configure Blender 5.2 Compositor node group to generate brilliant photonic bloom
    on the 1064 nm laser pulses, waveguides, and APD avalanche flashes.
    """
    scene = bpy.context.scene
    scene.use_nodes = True
    
    # In Blender 5.2, compositing is controlled via compositing_node_group
    ng = bpy.data.node_groups.new('JANUS_Compositor_Bloom', 'CompositorNodeTree')
    scene.compositing_node_group = ng
    
    # 1. Render Layers Input
    rlayers = ng.nodes.new('CompositorNodeRLayers')
    rlayers.location = (-300, 0)

    # 2. Glare Node (Fog Glow / Soft Photonic Radiance)
    glare = ng.nodes.new('CompositorNodeGlare')
    glare.location = (0, 0)
    if 'Type' in glare.inputs:
        glare.inputs['Type'].default_value = 'Fog Glow'
    if 'Quality' in glare.inputs:
        glare.inputs['Quality'].default_value = 'Low'
    if 'Highlights Threshold' in glare.inputs:
        glare.inputs['Highlights Threshold'].default_value = 1.0
    if 'Size' in glare.inputs:
        glare.inputs['Size'].default_value = 7

    # 3. Node Group Output
    out = ng.nodes.new('NodeGroupOutput')
    out.location = (300, 0)
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')

    # Links: Render Layers -> Glare -> Output
    ng.links.new(rlayers.outputs['Image'], glare.inputs['Image'])
    ng.links.new(glare.outputs['Image'], out.inputs['Image'])

    # Render settings: EEVEE Next high quality & fast playback
    scene.render.engine = 'BLENDER_EEVEE'
    if hasattr(scene, 'eevee'):
        scene.eevee.taa_render_samples = 4
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100


# ==============================================================================
# 13. MASTER BUILD PIPELINE
# ==============================================================================
def build_janus_mini16_model():
    """Execute complete procedural generation of JANUS Mini 16-Tile (Model 1A)."""
    print("=" * 80)
    print("BUILDING JANUS MINI 16-TILE (MODEL 1A) 3D ARCHITECTURAL MODEL & RIG")
    print("=" * 80)

    clean_scene()
    
    master_col = get_or_create_collection("JANUS_Mini16_Model1A")
    mats = create_materials()
    ctrl = create_master_rig()
    
    print("[1/7] Building Macro Package, Substrate & Heterogeneous Strata...")
    build_packaging_and_strata(master_col, mats, ctrl)
    
    print("[2/7] Generating 65nm CMOS Floorplan & Digital SIMD Datapaths...")
    build_cmos_floorplan(master_col, mats, ctrl)
    
    print("[3/7] Installing Vertical Cu Through-Dielectric Vias (TDVs)...")
    build_tdv_array(master_col, mats, ctrl)
    
    print("[4/7] Constructing SiPh 16-Tile Photonic Mesh, Beneš Fabric & Monolithic APDs...")
    build_siph_photonic_tiles(master_col, mats, ctrl)
    
    print("[5/6] Synthesizing Synchronized Optical & Electrical Signal Pulses...")
    build_signal_pulse_animation(master_col, mats, ctrl)

    print("[7/7] Configuring 5-Shot Cinematic Camera Rig, World & Compositor Bloom...")
    setup_cinematic_animation_and_cameras(master_col, ctrl)
    setup_world_environment()
    setup_compositor_bloom()

    # Save finalized .blend file
    blend_path = os.path.abspath(r"c:\Users\hp\Desktop\Janus Interactive Visulaization\JANUS_Mini16_Model1A.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"\n[SUCCESS] JANUS Mini 16-Tile 3D Model Saved: {blend_path}")
    print("=" * 80)


if __name__ == "__main__":
    build_janus_mini16_model()
