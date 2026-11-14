import os
import math
import random
import pygame

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Shinobi - Animated Scene")
W, H = screen.get_size()
clock = pygame.time.Clock()

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


# ---------------------------------------------------------------------------
# Asset Loading Helpers (with full alpha preservation)
# ---------------------------------------------------------------------------

def load_image(name):
    """Load an image from the assets folder preserving alpha channel."""
    path = os.path.join(ASSETS, name)
    if name.lower().endswith((".jpg", ".jpeg")):
        return pygame.image.load(path).convert()
    return pygame.image.load(path).convert_alpha()


def extract_grid_frames(name, rows, cols):
    """Extract individual frames from a transparent sprite sheet grid."""
    path = os.path.join(ASSETS, name)
    sheet = pygame.image.load(path).convert_alpha()
    sw, sh = sheet.get_size()
    fw = sw // cols
    fh = sh // rows

    frames = []
    for r in range(rows):
        for c in range(cols):
            rect = pygame.Rect(c * fw, r * fh, fw, fh)
            # Create a clean, transparent subsurface copy
            frame = sheet.subsurface(rect).copy()
            frames.append(frame)
    return frames


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------
background = pygame.transform.scale(load_image("background.jpg"), (W, H))

# ---------------------------------------------------------------------------
# Flags (2 frames each – waving animation)
# ---------------------------------------------------------------------------
FLAG_SCALE = 0.27  # fraction of screen height
flag_h = int(H * FLAG_SCALE)

flag1_frames_raw = [load_image("flag1_a.png"), load_image("flag1_b.png")]
flag2_frames_raw = [load_image("flag2_a.png"), load_image("flag2_b.png")]


def scale_flag(img):
    ratio = flag_h / img.get_height()
    w = int(img.get_width() * ratio)
    return pygame.transform.smoothscale(img, (w, flag_h))


flag1_frames = [scale_flag(f) for f in flag1_frames_raw]
flag2_frames = [scale_flag(f) for f in flag2_frames_raw]

# Anchor positions – defined by the BOTTOM of each flag
flag1_bottom = (int(W * 0.15), int(H * 0.73))   # left flag
flag2_bottom = (int(W * 0.77), int(H * 0.73))   # right flag

# ---------------------------------------------------------------------------
# Cloud Layer (scrolling horizontally)
# ---------------------------------------------------------------------------
CLOUD_SCALE = 0.35
cloud_frames_raw = [load_image("clouds_1.png"), load_image("clouds_2.png")]


def scale_cloud(img):
    w = int(W * CLOUD_SCALE)
    ratio = w / img.get_width()
    h = int(img.get_height() * ratio)
    return pygame.transform.smoothscale(img, (w, h))


cloud_frames = [scale_cloud(c) for c in cloud_frames_raw]

clouds = []
for _ in range(6):
    clouds.append({
        "x": random.randint(-W // 4, W),
        "y": random.randint(0, int(H * 0.12)),
        "speed": random.uniform(0.15, 0.45),
        "frame_offset": random.randint(0, 1),
        "scale": random.uniform(0.7, 1.3),
        "alpha": random.randint(140, 220),
    })

# ---------------------------------------------------------------------------
# Smoke Particles (rising from upper-right)
# ---------------------------------------------------------------------------
SMOKE_SCALE = 0.09
smoke_frames_raw = [load_image("smoke_1.png"), load_image("smoke_2.png")]


def scale_smoke(img, extra=1.0):
    h = int(H * SMOKE_SCALE * extra)
    ratio = h / img.get_height()
    w = int(img.get_width() * ratio)
    return pygame.transform.smoothscale(img, (w, h))


smoke_variants = []
for s in [0.7, 1.0, 1.3]:
    smoke_variants.append([scale_smoke(f, s) for f in smoke_frames_raw])


def new_smoke():
    return {
        "x": random.randint(int(W * 0.70), int(W * 0.90)),
        "y": random.randint(int(H * 0.08), int(H * 0.25)),
        "vx": random.uniform(-0.2, 0.2),
        "vy": random.uniform(-0.4, -1.0),
        "life": random.randint(180, 360),
        "age": 0,
        "variant": random.randint(0, len(smoke_variants) - 1),
        "frame_offset": random.randint(0, 1),
    }


smoke_particles = [new_smoke() for _ in range(10)]

# ---------------------------------------------------------------------------
# Player Sprites & Animations
# ---------------------------------------------------------------------------
# Player height is 110% of the flag height
PLAYER_SCALE = FLAG_SCALE * 1.10
player_h = int(H * PLAYER_SCALE)

# 1. 30-frame sheets (Walking, Rolling/Dodge, Slash, Parry)
# Each sheet is 2160x1800 with 5 rows x 6 cols = 30 frames (360x360 per frame).
# Character in the 360x360 frame stands approx 270px tall with feet at y=337.
raw_walk_frames = extract_grid_frames("walking_30_frames.png", 5, 6)
raw_dodge_frames = extract_grid_frames("rolling_30_frames.png", 5, 6)
raw_slash_frames = extract_grid_frames("basic_slash_30_frames.png", 5, 6)
raw_parry_frames = extract_grid_frames("perfect_parry_30_frames.png", 5, 6)

# Uniform scaling for the 360x360 character sheets
sheet_scale = player_h / 270.0
frame_w = int(360 * sheet_scale)
frame_h = int(360 * sheet_scale)
feet_offset = int(337 * sheet_scale)
center_offset = frame_w // 2

walk_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_walk_frames]
dodge_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_dodge_frames]
slash_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_slash_frames]
parry_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_parry_frames]

# 2. Idle Animation: Blink style (Frame 0 with natural eye blink)
# No fade-in/fade-out! Frame 0 is held steady, and blinks periodically.
raw_idle_open = raw_slash_frames[0].copy()
raw_idle_blink = raw_slash_frames[0].copy()

# Draw closed eyelid line across eye in raw 360x360 coordinate space (x: 186-193, y: 101-103)
eyelid_color = (48, 38, 38, 255)
for ex in range(186, 194):
    for ey in range(101, 104):
        raw_idle_blink.set_at((ex, ey), eyelid_color)

idle_open = pygame.transform.smoothscale(raw_idle_open, (frame_w, frame_h))
idle_blink = pygame.transform.smoothscale(raw_idle_blink, (frame_w, frame_h))

# 3. Kunai Throw (player_kunai.png: 1024x438, 3 rows x 7 cols = 21 frames)
raw_kunai_frames = extract_grid_frames("player_kunai.png", 3, 7)
kunai_scale = player_h / 128.0
kunai_w = int(146 * kunai_scale)
kunai_h = int(146 * kunai_scale)
kunai_feet_offset = int(140 * kunai_scale)
kunai_center_offset = kunai_w // 2
kunai_frames = [pygame.transform.smoothscale(f, (kunai_w, kunai_h)) for f in raw_kunai_frames]

# ---------------------------------------------------------------------------
# Player Physics & State Machine
# ---------------------------------------------------------------------------
GROUND_Y = flag1_bottom[1]   # Player's feet aligned with flag bottom
GRAVITY = 0.65
JUMP_FORCE = -14
WALK_SPEED = 5
DODGE_SPEED = 9

player = {
    # Position player on the left edge so flag 1 (at 15%) is visible
    "x": int(W * 0.05),
    "y": GROUND_Y,            # feet coordinate
    "vy": 0,
    "on_ground": True,
    "facing_right": True,
    "state": "idle",          # "idle", "walk", "dodge", "slash", "parry", "kunai"
    "frame_idx": 0,
    "tick_count": 0,
    "blink_timer": random.randint(120, 180),
    "is_blinking": False,
}

# ---------------------------------------------------------------------------
# Main Game Loop
# ---------------------------------------------------------------------------
frame_count = 0
FLAG_ANIM_SPEED = 12
CLOUD_ANIM_SPEED = 30
SMOKE_ANIM_SPEED = 18

running = True
while running:
    # ── Events ────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    frame_count += 1
    keys = pygame.key.get_pressed()
    p = player

    # ── State Machine & Controls ──────────────────────────────────────────
    if p["state"] in ("dodge", "slash", "parry", "kunai"):
        # Action animations play through completely
        p["tick_count"] += 1

        if p["state"] == "dodge":
            # Move forward during dodge/roll
            dx = DODGE_SPEED if p["facing_right"] else -DODGE_SPEED
            p["x"] += dx
            # 1 animation frame per game tick
            p["frame_idx"] += 1
            if p["frame_idx"] >= len(dodge_frames):
                p["state"] = "idle"
                p["frame_idx"] = 0
                p["tick_count"] = 0

        elif p["state"] == "slash":
            # 1 animation frame per game tick
            p["frame_idx"] += 1
            if p["frame_idx"] >= len(slash_frames):
                p["state"] = "idle"
                p["frame_idx"] = 0
                p["tick_count"] = 0

        elif p["state"] == "parry":
            # 1 animation frame per game tick
            p["frame_idx"] += 1
            if p["frame_idx"] >= len(parry_frames):
                p["state"] = "idle"
                p["frame_idx"] = 0
                p["tick_count"] = 0

        elif p["state"] == "kunai":
            # 1 animation frame every 2 game ticks
            if p["tick_count"] >= 2:
                p["tick_count"] = 0
                p["frame_idx"] += 1
                if p["frame_idx"] >= len(kunai_frames):
                    p["state"] = "idle"
                    p["frame_idx"] = 0

    else:
        # ── Trigger Action Animations (Priority) ─────────────────────────
        if keys[pygame.K_LSHIFT]:
            p["state"] = "dodge"
            p["frame_idx"] = 0
            p["tick_count"] = 0
        elif keys[pygame.K_RSHIFT]:
            p["state"] = "slash"
            p["frame_idx"] = 0
            p["tick_count"] = 0
        elif keys[pygame.K_f]:
            p["state"] = "parry"
            p["frame_idx"] = 0
            p["tick_count"] = 0
        elif keys[pygame.K_q]:
            p["state"] = "kunai"
            p["frame_idx"] = 0
            p["tick_count"] = 0
        else:
            # ── Horizontal Movement (A / D) ──────────────────────────────
            dx = 0
            if keys[pygame.K_a]:
                dx -= WALK_SPEED
            if keys[pygame.K_d]:
                dx += WALK_SPEED

            if dx != 0:
                p["x"] += dx
                p["facing_right"] = (dx > 0)
                if p["state"] != "walk":
                    p["state"] = "walk"
                    p["frame_idx"] = 0
                    p["tick_count"] = 0
                else:
                    p["tick_count"] += 1
                    # 1 animation frame every 2 game ticks for smooth walking
                    if p["tick_count"] >= 2:
                        p["tick_count"] = 0
                        p["frame_idx"] = (p["frame_idx"] + 1) % len(walk_frames)
            else:
                # ── Idle (Blink Style) ───────────────────────────────────
                p["state"] = "idle"
                p["blink_timer"] -= 1
                if p["blink_timer"] <= 0:
                    if not p["is_blinking"]:
                        p["is_blinking"] = True
                        p["blink_timer"] = 6   # Eyes closed for 6 frames (0.1s)
                    else:
                        p["is_blinking"] = False
                        p["blink_timer"] = random.randint(120, 200)  # Next blink in ~2.5s

        # ── Jump ─────────────────────────────────────────────────────────
        if keys[pygame.K_w] and p["on_ground"]:
            p["vy"] = JUMP_FORCE
            p["on_ground"] = False

    # ── Vertical Physics (Gravity) ────────────────────────────────────────
    if not p["on_ground"]:
        p["vy"] += GRAVITY
        p["y"] += p["vy"]
        if p["y"] >= GROUND_Y:
            p["y"] = GROUND_Y
            p["vy"] = 0
            p["on_ground"] = True

    # ── Screen Boundary Clamping ──────────────────────────────────────────
    p["x"] = max(center_offset, min(p["x"], W - center_offset))

    # ══════════════════════════════════════════════════════════════════════
    # RENDERING
    # ══════════════════════════════════════════════════════════════════════

    # 1. Background
    screen.blit(background, (0, 0))

    # 2. Clouds
    cloud_frame_idx = (frame_count // CLOUD_ANIM_SPEED) % 2
    for c in clouds:
        c["x"] += c["speed"]
        idx = (cloud_frame_idx + c["frame_offset"]) % 2
        img = cloud_frames[idx]
        if c["scale"] != 1.0:
            cw = int(img.get_width() * c["scale"])
            ch = int(img.get_height() * c["scale"])
            img = pygame.transform.smoothscale(img, (cw, ch))
        img = img.copy()
        img.set_alpha(c["alpha"])
        screen.blit(img, (int(c["x"]), c["y"]))
        if c["x"] > W + 50:
            c["x"] = -img.get_width() - random.randint(0, W // 4)
            c["y"] = random.randint(0, int(H * 0.12))

    # 3. Flags (Waving)
    flag_frame_idx = (frame_count // FLAG_ANIM_SPEED) % 2
    sway = math.sin(frame_count * 0.04) * 3

    f1 = flag1_frames[flag_frame_idx]
    f1_y = flag1_bottom[1] - f1.get_height()
    screen.blit(f1, (flag1_bottom[0] + int(sway), f1_y))

    f2 = flag2_frames[flag_frame_idx]
    f2_y = flag2_bottom[1] - f2.get_height()
    screen.blit(f2, (flag2_bottom[0] - int(sway), f2_y))

    # 4. Player (Clean, transparent sprite)
    if p["state"] == "idle":
        sprite = idle_blink if p["is_blinking"] else idle_open
        draw_x = int(p["x"] - center_offset)
        draw_y = int(p["y"] - feet_offset)
    elif p["state"] == "walk":
        sprite = walk_frames[p["frame_idx"]]
        draw_x = int(p["x"] - center_offset)
        draw_y = int(p["y"] - feet_offset)
    elif p["state"] == "dodge":
        sprite = dodge_frames[p["frame_idx"]]
        draw_x = int(p["x"] - center_offset)
        draw_y = int(p["y"] - feet_offset)
    elif p["state"] == "slash":
        sprite = slash_frames[p["frame_idx"]]
        draw_x = int(p["x"] - center_offset)
        draw_y = int(p["y"] - feet_offset)
    elif p["state"] == "parry":
        sprite = parry_frames[p["frame_idx"]]
        draw_x = int(p["x"] - center_offset)
        draw_y = int(p["y"] - feet_offset)
    elif p["state"] == "kunai":
        sprite = kunai_frames[p["frame_idx"]]
        draw_x = int(p["x"] - kunai_center_offset)
        draw_y = int(p["y"] - kunai_feet_offset)

    if not p["facing_right"]:
        sprite = pygame.transform.flip(sprite, True, False)

    screen.blit(sprite, (draw_x, draw_y))

    # 5. Smoke Particles (Rising)
    smoke_frame_idx = (frame_count // SMOKE_ANIM_SPEED) % 2
    for s in smoke_particles:
        s["x"] += s["vx"]
        s["y"] += s["vy"]
        s["age"] += 1

        life_ratio = 1.0 - (s["age"] / s["life"])
        alpha = max(0, int(200 * life_ratio))

        idx = (smoke_frame_idx + s["frame_offset"]) % 2
        img = smoke_variants[s["variant"]][idx].copy()
        img.set_alpha(alpha)
        screen.blit(img, (int(s["x"]), int(s["y"])))

        if s["age"] >= s["life"]:
            s.update(new_smoke())

    # ── Display Flip & Clock ──────────────────────────────────────────────
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
