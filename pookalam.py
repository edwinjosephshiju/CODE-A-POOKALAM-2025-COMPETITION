import math
import random
from PIL import Image
import os

# ---------- CONFIGURATION V6 (Auto-Open Final Image) ----------

# --- General Settings ---
canvas_size = 8000          # Canvas resolution in pixels (8000 is a good balance)
bg_color = (15, 25, 15, 255) # A slightly darker, more muted green

# --- IMPORTANT: UPDATE THESE PATHS ---
output_dir = "output"       # Folder for the final images and previews
flower_dir = "flowers"      # Folder containing your flower .png files
center_image_path = None    # Optional: e.g., "center_kathakali.png"

# --- Lower-Density Design Parameters ---
max_flowers = 600000        # This is a cap, not a density driver.
rings = 35                  # More rings to fill space radially
layers_per_ring = 2         # Fewer layers reduces radial density.
spacing_factor = 0.55       # Increased for looser packing. Higher is less dense.
min_scale = 0.007           # Scale of flowers in the innermost ring
max_scale = 0.032           # Scale of flowers in the outermost ring

# --- Jitter (Reduced for a clean, non-fuzzy look) ---
angle_jitter_deg = 0.5      # Minimal angle offset
radius_jitter_px = 0.5      # Minimal radius offset
size_jitter_factor = 0.02   # Flowers vary in size by only 2% (0.98 to 1.02)

# --- Flower Definitions (assumes images are in the 'flower_dir' folder) ---
flower_definitions = {
    "marigold_orange": "marigold_orange.png",
    "marigold_yellow": "marigold_yellow.png",
    "rose": "rose.png",
    "lotus": "lotus.png",
    "chrysanthemum": "chrysanthemum.png",
    "daisy": "daisy.png",
    "hibiscus": "hibiscus.png",
    "ixora": "ixora.png",
    "jasmine": "jasmine.png"
}

# ---------- Caches (for performance) ----------
thumb_cache = {}
rot_cache = {}
# ---------------------------------------------

# ========== PATTERN ENGINE (Unchanged) ==========
def pattern_plain(**kwargs): return 0
def pattern_zigzag(flower_idx, max_offset, **kwargs): return math.sin(flower_idx * 0.5) * max_offset
def pattern_wave(flower_idx, estimated_count, max_offset, **kwargs):
    num_waves = random.choice([30, 40, 50]); angle = flower_idx * (2 * math.pi / estimated_count) * num_waves; return math.sin(angle) * max_offset
def pattern_petals(flower_idx, estimated_count, max_offset, **kwargs):
    num_petals = random.choice([8, 12, 16]); angle = flower_idx * (2 * math.pi / estimated_count) * num_petals; return abs(math.sin(angle)) * max_offset * 1.5
def pattern_scallop(flower_idx, estimated_count, max_offset, **kwargs):
    num_scallops = random.choice([18, 24, 30]); angle = flower_idx * (2 * math.pi / estimated_count) * num_scallops; return -abs(math.cos(angle)) * max_offset
PATTERNS = {"plain": pattern_plain, "zigzag": pattern_zigzag, "wave": pattern_wave, "petals": pattern_petals, "scallop": pattern_scallop}
# ------------------------------------------

def get_thumb(img, name, size_px):
    key = (name, size_px)
    if key in thumb_cache: return thumb_cache[key]
    thumb = img.resize((size_px, size_px), resample=Image.LANCZOS)
    thumb_cache[key] = thumb
    return thumb

def get_rotated(name, img, size_px, angle):
    rot_key = (name, size_px, int(round(angle / 5.0) * 5))
    if rot_key in rot_cache: return rot_cache[rot_key]
    thumb = get_thumb(img, name, size_px)
    rot = thumb.rotate(rot_key[2], resample=Image.BICUBIC, expand=True)
    rot_cache[rot_key] = rot
    return rot

def load_flowers(base_dir, definitions):
    imgs = {}
    print("Loading flower images...")
    for name, filename in definitions.items():
        p = os.path.join(base_dir, filename)
        if not os.path.exists(p): raise FileNotFoundError(f"Flower PNG not found: {p}")
        imgs[name] = Image.open(p).convert("RGBA")
        print(f"   - Loaded {name}")
    return imgs

def generate_random_flower_sequence(flower_names, num_rings):
    print("Generating random flower sequence...")
    sequence, available_flowers, current_ring = [], list(flower_names), 0
    while current_ring < num_rings:
        duration = random.randint(1, 3)
        num_types = random.choice([1, 1, 1, 2])
        flowers_for_segment = random.sample(available_flowers, num_types)
        for _ in range(duration):
            if current_ring < num_rings: sequence.append(flowers_for_segment); current_ring += 1
            else: break
    print("Sequence generated.")
    return sequence

def compose_pookalam():
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    output_path = os.path.join(output_dir, "output_pookalam.png")
    flowers = load_flowers(flower_dir, flower_definitions)
    ring_flower_sequence = generate_random_flower_sequence(flowers.keys(), rings)
    
    canvas = Image.new("RGBA", (canvas_size, canvas_size), bg_color)
    cx = cy = canvas_size // 2
    outer_radius = int(canvas_size * 0.95 / 2)
    inner_radius = int(canvas_size * 0.05)
    total_flowers = 0

    for ring_idx in range(rings):
        if total_flowers >= max_flowers: break
        
        fs = ring_flower_sequence[ring_idx]
        t = ring_idx / max(1, rings - 1)
        base_radius_px = int(outer_radius * (1 - t) + inner_radius * t)
        scale_frac = min_scale + (max_scale - min_scale) * (1 - t)
        size_px = max(6, int(canvas_size * scale_frac))

        # --- NEW: Increase size of innermost flowers to create overlap ---
        # The loop starts from the outer ring (idx 0) and moves inwards.
        # So, the highest indices are the innermost rings.
        if ring_idx >= rings - 3:
            size_px = int(size_px * 1.15) # Increase size by 15% for the last 3 rings
            print(f"   -> Applying inner ring size boost. New size: {size_px}px")

        pattern_name = random.choice(["plain", "plain", "plain", "wave", "zigzag"])
        
        print(f"[Ring {ring_idx+1}/{rings}] Pattern: {pattern_name}, Flowers: {fs}, Layers: {layers_per_ring}, Size: {size_px}px")

        # ========== MULTI-LAYER RENDERING LOOP ==========
        for layer in range(layers_per_ring):
            if total_flowers >= max_flowers: break

            layer_offset = (layer - (layers_per_ring - 1) / 2.0) * size_px * 0.6
            radius_px = base_radius_px + layer_offset

            circumference = 2 * math.pi * radius_px
            estimated_count = max(4, int(circumference / (size_px * spacing_factor)))

            phase_shift = (math.pi / estimated_count) if layer % 2 != 0 else 0

            for k in range(estimated_count):
                if total_flowers >= max_flowers: break

                base_angle = (2 * math.pi * k / estimated_count) + phase_shift
                angle = base_angle + math.radians(random.uniform(-angle_jitter_deg, angle_jitter_deg))
                
                max_offset = size_px * 0.5
                pattern_args = {"flower_idx": k, "estimated_count": estimated_count, "max_offset": max_offset}
                offset = PATTERNS[pattern_name](**pattern_args)
                
                r_j = radius_px + random.uniform(-radius_jitter_px, radius_jitter_px) + offset
                x = cx + r_j * math.cos(angle)
                y = cy + r_j * math.sin(angle)

                fname = fs[k % len(fs)]
                orig_img = flowers[fname]
                rot_deg = random.uniform(0, 360)
                
                size_delta = size_px * size_jitter_factor
                size_jitter = max(4, int(size_px + random.uniform(-size_delta, size_delta)))
                
                thumb_rot = get_rotated(fname, orig_img, size_jitter, rot_deg)
                w, h = thumb_rot.size
                paste_x, paste_y = int(x - w / 2), int(y - h / 2)

                if 0 <= paste_x < canvas_size and 0 <= paste_y < canvas_size:
                    canvas.paste(thumb_rot, (paste_x, paste_y), thumb_rot)
                    total_flowers += 1

    # --- NEW: Fill Center Gap ---
    print("Filling center gap with random flowers...")
    center_fill_radius = inner_radius * 0.98 # Fill slightly smaller to avoid harsh edges
    center_flower_size = max(6, int(canvas_size * min_scale * 1.15))
    center_area = math.pi * (center_fill_radius ** 2)
    flower_area = (center_flower_size * 0.8)**2 # Use 80% of size for area calc
    num_center_flowers = int((center_area / flower_area) * 1.6) # Fill factor increased for more density

    flower_names_list = list(flowers.keys())
    for _ in range(num_center_flowers):
        if total_flowers >= max_flowers:
            print("Max flowers reached while filling center.")
            break
        
        rand_angle = random.uniform(0, 2 * math.pi)
        rand_radius = center_fill_radius * math.sqrt(random.random())
        x = cx + rand_radius * math.cos(rand_angle)
        y = cy + rand_radius * math.sin(rand_angle)

        fname = random.choice(flower_names_list)
        orig_img = flowers[fname]
        rot_deg = random.uniform(0, 360)

        size_delta = center_flower_size * size_jitter_factor
        size_jitter = max(4, int(center_flower_size + random.uniform(-size_delta, size_delta)))
        
        thumb_rot = get_rotated(fname, orig_img, size_jitter, rot_deg)
        w, h = thumb_rot.size
        paste_x, paste_y = int(x - w / 2), int(y - h / 2)

        if 0 <= paste_x < canvas_size and 0 <= paste_y < canvas_size:
            canvas.paste(thumb_rot, (paste_x, paste_y), thumb_rot)
            total_flowers += 1

    # --- Centerpiece Placement ---
    if center_image_path and os.path.exists(center_image_path):
        print("Placing center image...")
        center_img = Image.open(center_image_path).convert("RGBA")
        center_size = int(inner_radius * 2 * 0.95)
        center_img.thumbnail((center_size, center_size), Image.LANCZOS)
        w, h = center_img.size
        canvas.paste(center_img, (int(cx - w / 2), int(cy - h / 2)), center_img)
    
    # --- Final Save ---
    print("\nTotal flowers pasted:", total_flowers)
    canvas.save(output_path)
    print(f"Saved final image to: {output_path}")
    
    jpeg_path = os.path.join(output_dir, "output_pookalam_small.jpg")
    final_jpg = canvas.resize((2048, 2048), Image.LANCZOS).convert("RGB")
    final_jpg.save(jpeg_path, quality=95)
    print(f"Saved small JPEG to: {jpeg_path}")
    
    # --- NEW: Open the final JPG for viewing ---
    print("Displaying final image...")
    final_jpg.show(title="Pookalam Preview")


if __name__ == "__main__":
    compose_pookalam()

