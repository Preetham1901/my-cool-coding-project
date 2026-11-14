import os
import math
import random
import pygame

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Animated Scene")
W, H = screen.get_size()
clock = pygame.time.Clock()

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def load(name):
    """Load an image from the assets folder with per-pixel alpha."""
    return pygame.image.load(os.path.join(ASSETS, name)).convert_alpha()


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------
background = pygame.transform.scale(load("background.jpg"), (W, H))

# ---------------------------------------------------------------------------
# Flag sprites  (2 frames each, cycled to simulate waving)
# ---------------------------------------------------------------------------
FLAG_SCALE = 0.27  # fraction of screen height (50% bigger)

flag1_frames = [load("flag1_a.png"), load("flag1_b.png")]
flag2_frames = [load("flag2_a.png"), load("flag2_b.png")]


def scale_flag(img):
    """Scale a flag image proportionally to the screen."""
    h = int(H * FLAG_SCALE)
    ratio = h / img.get_height()
    w = int(img.get_width() * ratio)
    return pygame.transform.scale(img, (w, h))


flag1_frames = [scale_flag(f) for f in flag1_frames]
flag2_frames = [scale_flag(f) for f in flag2_frames]

# Positions – roughly where the flags sit in the original artwork
# Anchor positions – defined by the BOTTOM of each flag so they grow upward
flag1_bottom = (int(W * 0.15), int(H * 0.73))   # left flag
flag2_bottom = (int(W * 0.77), int(H * 0.73))   # right flag

# ---------------------------------------------------------------------------
# Cloud layer  (2 frames, scrolling horizontally)
# ---------------------------------------------------------------------------
CLOUD_SCALE = 0.35  # fraction of screen width

cloud_frames = [load("clouds_1.png"), load("clouds_2.png")]


def scale_cloud(img):
    w = int(W * CLOUD_SCALE)
    ratio = w / img.get_width()
    h = int(img.get_height() * ratio)
    return pygame.transform.scale(img, (w, h))


cloud_frames = [scale_cloud(c) for c in cloud_frames]

# We place several cloud "instances" across the top of the screen.
# Each has its own x position, speed, and y offset for variety.
clouds = []
for i in range(6):
    clouds.append({
        "x": random.randint(-W // 4, W),
        "y": random.randint(0, int(H * 0.12)),
        "speed": random.uniform(0.15, 0.45),       # pixels per frame
        "frame_offset": random.randint(0, 1),       # start on frame 0 or 1
        "scale": random.uniform(0.7, 1.3),          # slight size variation
        "alpha": random.randint(140, 220),           # slight transparency variation
    })

# ---------------------------------------------------------------------------
# Smoke particles  (2 frames, drifting upward from upper-right area)
# ---------------------------------------------------------------------------
SMOKE_SCALE = 0.09  # fraction of screen height

smoke_frames_raw = [load("smoke_1.png"), load("smoke_2.png")]


def scale_smoke(img, extra=1.0):
    h = int(H * SMOKE_SCALE * extra)
    ratio = h / img.get_height()
    w = int(img.get_width() * ratio)
    return pygame.transform.scale(img, (w, h))


# Pre-scale a few sizes so particles look varied
smoke_variants = []
for s in [0.7, 1.0, 1.3]:
    smoke_variants.append([scale_smoke(f, s) for f in smoke_frames_raw])


def new_smoke():
    """Spawn a new smoke particle near the upper-right of the scene."""
    return {
        "x": random.randint(int(W * 0.70), int(W * 0.90)),
        "y": random.randint(int(H * 0.08), int(H * 0.25)),
        "vx": random.uniform(-0.2, 0.2),
        "vy": random.uniform(-0.4, -1.0),           # drifts upward
        "life": random.randint(180, 360),            # frames until fade-out
        "age": 0,
        "variant": random.randint(0, len(smoke_variants) - 1),
        "frame_offset": random.randint(0, 1),
    }


smoke_particles = [new_smoke() for _ in range(10)]

# ---------------------------------------------------------------------------
# Animation state
# ---------------------------------------------------------------------------
frame_count = 0
FLAG_ANIM_SPEED = 12   # swap flag frame every N game-frames
CLOUD_ANIM_SPEED = 30  # swap cloud frame every N game-frames
SMOKE_ANIM_SPEED = 18  # swap smoke frame every N game-frames

running = True
while running:
    # --- Events -----------------------------------------------------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    frame_count += 1

    # --- Draw background --------------------------------------------------
    screen.blit(background, (0, 0))

    # --- Clouds (behind everything else) ----------------------------------
    cloud_frame_idx = (frame_count // CLOUD_ANIM_SPEED) % 2
    for c in clouds:
        c["x"] += c["speed"]
        # Determine which animation frame to show
        idx = (cloud_frame_idx + c["frame_offset"]) % 2
        img = cloud_frames[idx]
        # Apply per-cloud scale
        if c["scale"] != 1.0:
            cw = int(img.get_width() * c["scale"])
            ch = int(img.get_height() * c["scale"])
            img = pygame.transform.scale(img, (cw, ch))
        # Apply per-cloud transparency
        img = img.copy()
        img.set_alpha(c["alpha"])
        screen.blit(img, (int(c["x"]), c["y"]))
        # Wrap around when the cloud has fully left the right edge
        if c["x"] > W + 50:
            c["x"] = -img.get_width() - random.randint(0, W // 4)
            c["y"] = random.randint(0, int(H * 0.12))

    # --- Flags (waving) ---------------------------------------------------
    flag_frame_idx = (frame_count // FLAG_ANIM_SPEED) % 2
    # Slight horizontal sway using a sine wave
    sway = math.sin(frame_count * 0.04) * 3  # ±3 pixels

    # Flag 1 (left) – position from bottom anchor
    f1 = flag1_frames[flag_frame_idx]
    f1_y = flag1_bottom[1] - f1.get_height()
    screen.blit(f1, (flag1_bottom[0] + int(sway), f1_y))

    # Flag 2 (right) – position from bottom anchor
    f2 = flag2_frames[flag_frame_idx]
    f2_y = flag2_bottom[1] - f2.get_height()
    screen.blit(f2, (flag2_bottom[0] - int(sway), f2_y))

    # --- Smoke (rising) ---------------------------------------------------
    smoke_frame_idx = (frame_count // SMOKE_ANIM_SPEED) % 2
    for s in smoke_particles:
        s["x"] += s["vx"]
        s["y"] += s["vy"]
        s["age"] += 1

        # Fade out as the particle ages
        life_ratio = 1.0 - (s["age"] / s["life"])
        alpha = max(0, int(200 * life_ratio))

        idx = (smoke_frame_idx + s["frame_offset"]) % 2
        img = smoke_variants[s["variant"]][idx].copy()
        img.set_alpha(alpha)
        screen.blit(img, (int(s["x"]), int(s["y"])))

        # Respawn when the particle has faded out
        if s["age"] >= s["life"]:
            fresh = new_smoke()
            s.update(fresh)

    # --- Flip -------------------------------------------------------------
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
