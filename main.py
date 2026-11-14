import os
import math
import random
import pygame

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------
pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Haven Hackathon - Shinobi: Legend of Zhao")
W, H = screen.get_size()
clock = pygame.time.Clock()

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


# ---------------------------------------------------------------------------
# Asset Loading Helpers (with full alpha preservation and opacity enforcement)
# ---------------------------------------------------------------------------

def load_image(name):
    """Load an image from the assets folder preserving alpha channel."""
    path = os.path.join(ASSETS, name)
    if name.lower().endswith((".jpg", ".jpeg")):
        return pygame.image.load(path).convert()
    return pygame.image.load(path).convert_alpha()


def solidify_surface(surf, passes=4):
    """Reinforces alpha so character sprites are completely solid and not see-through."""
    solid = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    for _ in range(passes):
        solid.blit(surf, (0, 0))
    return solid


def extract_grid_frames(name, rows, cols, solidify=False):
    """Extract individual frames from a transparent sprite sheet grid, handling fractional sizes smoothly."""
    path = os.path.join(ASSETS, name)
    sheet = pygame.image.load(path).convert_alpha()
    sw, sh = sheet.get_size()

    frames = []
    for r in range(rows):
        y0 = int(r * sh / rows)
        y1 = int((r + 1) * sh / rows)
        fh = y1 - y0
        for c in range(cols):
            x0 = int(c * sw / cols)
            x1 = int((c + 1) * sw / cols)
            fw = x1 - x0
            rect = pygame.Rect(x0, y0, fw, fh)
            frame = sheet.subsurface(rect).copy()
            if solidify:
                frame = solidify_surface(frame, passes=4)
            frames.append(frame)
    return frames


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
font_title = pygame.font.SysFont(["cinzel", "georgia", "trajan", "arial"], int(H * 0.055), bold=True)
font_subtitle = pygame.font.SysFont(["cinzel", "georgia", "arial"], int(H * 0.024), bold=False)
font_end_title = pygame.font.SysFont(["cinzel", "georgia", "trajan", "arial"], int(H * 0.075), bold=True)
font_end_sub = pygame.font.SysFont(["cinzel", "georgia", "arial"], int(H * 0.026), bold=False)
font_btn = pygame.font.SysFont(["cinzel", "georgia", "arial"], int(H * 0.028), bold=True)
font_bar_name = pygame.font.SysFont(["georgia", "cinzel", "arial"], int(H * 0.023), bold=True)
font_bar_val = pygame.font.SysFont(["consolas", "georgia", "arial"], int(H * 0.016), bold=True)
font_heal_status = pygame.font.SysFont(["consolas", "georgia", "arial"], int(H * 0.018), bold=True)
font_guide_head = pygame.font.SysFont(["georgia", "cinzel", "arial"], int(H * 0.030), bold=True)
font_guide_sec = pygame.font.SysFont(["georgia", "cinzel", "arial"], int(H * 0.022), bold=True)
font_guide_body = pygame.font.SysFont(["consolas", "georgia", "arial"], int(H * 0.018), bold=False)


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------
background = pygame.transform.scale(load_image("background.jpg"), (W, H))

# ---------------------------------------------------------------------------
# Flags (2 frames each – waving animation)
# ---------------------------------------------------------------------------
FLAG_SCALE = 0.27
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
# Player Sprites & Animations (Solidified to eliminate any transparency!)
# ---------------------------------------------------------------------------
PLAYER_SCALE = FLAG_SCALE * 1.10
player_h = int(H * PLAYER_SCALE)

# 1. Standard 30-frame sheets (Walking, Rolling/Dodge, Slash, Parry)
raw_walk_frames = extract_grid_frames("walking_30_frames.png", 5, 6, solidify=True)
raw_dodge_frames = extract_grid_frames("rolling_30_frames.png", 5, 6, solidify=True)
raw_slash_frames = extract_grid_frames("basic_slash_30_frames.png", 5, 6, solidify=True)
raw_parry_frames = extract_grid_frames("perfect_parry_30_frames.png", 5, 6, solidify=True)

sheet_scale = player_h / 270.0
frame_w = int(360 * sheet_scale)
frame_h = int(360 * sheet_scale)
feet_offset = int(337 * sheet_scale)
center_offset = frame_w // 2

walk_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_walk_frames]
dodge_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_dodge_frames]
slash_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_slash_frames]
parry_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_parry_frames]

# 2. Idle Animation: Blink style (Solidified)
raw_idle_open = raw_slash_frames[0].copy()
raw_idle_blink = raw_slash_frames[0].copy()
eyelid_color = (48, 38, 38, 255)
for ex in range(186, 194):
    for ey in range(101, 104):
        raw_idle_blink.set_at((ex, ey), eyelid_color)

idle_open = pygame.transform.smoothscale(raw_idle_open, (frame_w, frame_h))
idle_blink = pygame.transform.smoothscale(raw_idle_blink, (frame_w, frame_h))

# 3. Player Kunai Throw Animation (Solidified)
raw_player_kunai = extract_grid_frames("player_kunai_new.png", 5, 6, solidify=True)
pk_scale = player_h / 140.0
pk_w = int(171 * pk_scale)
pk_h = int(171 * pk_scale)
pk_feet_offset = int(164 * pk_scale)
pk_center_offset = pk_w // 2
player_kunai_frames = [pygame.transform.smoothscale(f, (pk_w, pk_h)) for f in raw_player_kunai]

# 4. Player Healing Animation (Image 4: player_heal.png, 5 rows x 6 cols = 30 frames, Solidified)
raw_player_heal = extract_grid_frames("player_heal.png", 5, 6, solidify=True)
ph_scale = player_h / 155.0
pheal_w = int(171 * ph_scale)
pheal_h = int(171 * ph_scale)
pheal_feet_offset = int(165 * ph_scale)
pheal_center_offset = pheal_w // 2
player_heal_frames = [pygame.transform.smoothscale(f, (pheal_w, pheal_h)) for f in raw_player_heal]

# ---------------------------------------------------------------------------
# Boss (Titan) Sprites & Animations (120% size of player)
# Note: Boss source sheets natively face RIGHT.
# When facing LEFT towards player, flip horizontally!
# ---------------------------------------------------------------------------
boss_h = int(player_h * 1.20)
boss_scale = boss_h / 148.0

# 1. Boss Idle (Image 1: boss_idle_new.png, 5 rows x 6 cols = 30 frames)
raw_boss_idle = extract_grid_frames("boss_idle_new.png", 5, 6)
bi_w = int(170.67 * boss_scale)
bi_h = int(170.6 * boss_scale)
bi_feet = int(152 * boss_scale)
bi_center = bi_w // 2
boss_idle_frames = [pygame.transform.smoothscale(f, (bi_w, bi_h)) for f in raw_boss_idle]

# 2. Boss Walk (Image 2: boss_walk.png, 5 rows x 6 cols = 30 frames)
raw_boss_walk = extract_grid_frames("boss_walk.png", 5, 6)
bw_w = int(170.67 * boss_scale)
bw_h = int(170.6 * boss_scale)
bw_feet = int(165 * boss_scale)
bw_center = bw_w // 2
boss_walk_frames = [pygame.transform.smoothscale(f, (bw_w, bw_h)) for f in raw_boss_walk]

# 3. Boss Enraged Roar / Activation (Image 3: boss_enrage.png, 5 rows x 6 cols = 30 frames)
raw_boss_enrage = extract_grid_frames("boss_enrage.png", 5, 6)
be_w = int(170.67 * boss_scale)
be_h = int(170.6 * boss_scale)
be_feet = int(165 * boss_scale)
be_center = be_w // 2
boss_enrage_frames = [pygame.transform.smoothscale(f, (be_w, be_h)) for f in raw_boss_enrage]

# 4. Boss Heavy Smash (greatsword slam with screen shake)
raw_boss_smash = extract_grid_frames("boss_smash.png", 5, 6)
bs_w = int(170.67 * boss_scale)
bs_h = int(170.6 * boss_scale)
bs_feet = int(162 * boss_scale)
bs_center = bs_w // 2
boss_smash_frames = [pygame.transform.smoothscale(f, (bs_w, bs_h)) for f in raw_boss_smash]

# 5. Boss Spear Throw (long-range spear throw)
raw_boss_spear = extract_grid_frames("boss_spear.png", 5, 6)
bsp_w = int(170.67 * boss_scale)
bsp_h = int(184.8 * boss_scale)
bsp_feet = int(164 * boss_scale)
bsp_center = bsp_w // 2
boss_spear_frames = [pygame.transform.smoothscale(f, (bsp_w, bsp_h)) for f in raw_boss_spear]

# ---------------------------------------------------------------------------
# Projectiles (Kunai Item: Image 5)
# ---------------------------------------------------------------------------
raw_kunai_item = load_image("kunai_projectile.png")
kw = int(player_h * 0.32)
kh = int(kw * (188.0 / 948.0))
kunai_item_right = pygame.transform.smoothscale(raw_kunai_item, (kw, kh))
kunai_item_left = pygame.transform.flip(kunai_item_right, True, False)

raw_spear_sub = raw_boss_spear[16].subsurface(pygame.Rect(int(raw_boss_spear[16].get_width() * 0.45), int(raw_boss_spear[16].get_height() * 0.25), int(raw_boss_spear[16].get_width() * 0.50), int(raw_boss_spear[16].get_height() * 0.30)))
sp_w = int(boss_h * 0.45)
sp_h = int(sp_w * (raw_spear_sub.get_height() / raw_spear_sub.get_width()))
spear_proj_right = pygame.transform.smoothscale(raw_spear_sub, (sp_w, sp_h))
spear_proj_left = pygame.transform.flip(spear_proj_right, True, False)

projectiles = []

# ---------------------------------------------------------------------------
# Entities (Player & Boss State)
# ---------------------------------------------------------------------------
GROUND_Y = flag1_bottom[1]
GRAVITY = 0.65
JUMP_FORCE = -14
WALK_SPEED = 5
DODGE_SPEED = 9
KUNAI_SPEED = 18

player = {
    "x": int(W * 0.05),
    "y": GROUND_Y,
    "vy": 0,
    "on_ground": True,
    "facing_right": True,
    "state": "idle",             # "idle", "walk", "dodge", "slash", "parry", "kunai", "heal"
    "frame_idx": 0,
    "tick_count": 0,
    "blink_timer": random.randint(120, 180),
    "is_blinking": False,
    "hp": 100,
    "max_hp": 100,
    "displayed_hp": 100.0,
    "kunai_spawned": False,
    "heal_used": False,          # Can heal only ONCE per game
    "heal_timer": 0,             # 120 ticks = 2.0s channel
}

boss = {
    "name": "Titan",
    "x": int(W * 0.82),
    "y": GROUND_Y,
    "facing_right": False,      # initially facing left towards player
    "state": "idle",            # "idle", "walk", "smash", "spear", "kunai", "enrage_intro"
    "frame_idx": 0,
    "tick_count": 0,
    "hp": 1000,
    "max_hp": 1000,
    "displayed_hp": 1000.0,
    "action_timer": random.uniform(1.0, 4.0),       # Random patrol duration (switches directions completely randomly!)
    "walk_dir": 0,                                  # -1 (left), 0 (still), 1 (right)
    "attack_cooldown": random.uniform(3.0, 5.0),    # interval 3-5s for boss attacks
    "projectile_spawned": False,
    "smash_hit": False,
    "enraged_triggered": False,                     # Has enrage 3s intro played
    "enrage_intro_timer": 0,                        # 180 ticks = 3.0s intro
    "enraged_override": False,
}

# Ground Shake (120 frames at 60 FPS = 2.0 Seconds)
ground_shake_timer = 0
ground_shake_intensity = 0.0


def reset_battle():
    """Resets both player, boss, and combat systems to initial state."""
    global projectiles, ground_shake_timer, ground_shake_intensity
    projectiles.clear()
    ground_shake_timer = 0
    ground_shake_intensity = 0.0

    player["hp"] = player["max_hp"]
    player["displayed_hp"] = float(player["max_hp"])
    player["x"] = int(W * 0.05)
    player["y"] = GROUND_Y
    player["vy"] = 0
    player["on_ground"] = True
    player["facing_right"] = True
    player["state"] = "idle"
    player["frame_idx"] = 0
    player["tick_count"] = 0
    player["blink_timer"] = random.randint(120, 180)
    player["is_blinking"] = False
    player["kunai_spawned"] = False
    player["heal_used"] = False
    player["heal_timer"] = 0

    boss["hp"] = boss["max_hp"]
    boss["displayed_hp"] = float(boss["max_hp"])
    boss["x"] = int(W * 0.82)
    boss["y"] = GROUND_Y
    boss["facing_right"] = False
    boss["state"] = "idle"
    boss["frame_idx"] = 0
    boss["tick_count"] = 0
    boss["action_timer"] = random.uniform(1.0, 4.0)
    boss["walk_dir"] = 0
    boss["attack_cooldown"] = random.uniform(3.0, 5.0)
    boss["projectile_spawned"] = False
    boss["smash_hit"] = False
    boss["enraged_triggered"] = False
    boss["enrage_intro_timer"] = 0
    boss["enraged_override"] = False


# ---------------------------------------------------------------------------
# UI Guide Content (Haven Hackathon)
# ---------------------------------------------------------------------------
GUIDE_SECTIONS = [
    {
        "title": "HAVEN HACKATHON - COMBAT SPECIFICATION",
        "color": (255, 215, 120),
        "lines": [
            "Welcome to the Haven Hackathon combat demo.",
            "Take command of Great General Zhao against the ancient Titan.",
        ]
    },
    {
        "title": "CONTROLS & KEYBINDS",
        "color": (120, 210, 255),
        "lines": [
            "  [ W ]          : Jump (Vertical leap with gravity)",
            "  [ A ]          : Move Left (Facing directional turn)",
            "  [ D ]          : Move Right",
            "  [ Left Shift ] : Dodge (Forward evasive roll, invulnerable to projectiles & shockwaves)",
            "  [ Right Shift ]: Sword Slash (High-impact close-range combo)",
            "  [ Q ]          : Throw Kunai (Launches projectile in facing direction)",
            "  [ F ]          : Parry (Defensive counter-stance; blocks attacks/projectiles)",
            "  [ E ]          : Healing Flask (Heals 50% HP, takes 2s, 1 use per game; LOCKED when Boss is enraged!)",
            "  [ Spacebar ]   : Pause Menu (Time Rewind 10s, Reset, Keybinds)",
            "  [ U ]          : Toggle Enraged Mode (Test 3s intro roar, red glowing outline & 70% faster attacks)",
            "  [ S ]          : Trigger Boss Sword Slam (Test 2-second screen shake)",
            "  [ K ]          : Self-Damage Test (-25 HP to test Defeat screen)",
            "  [ T ]          : Strike Titan Test (-200 HP to test Victory screen)",
            "  [ Esc ]        : Return to Menu / Exit Game",
        ]
    },
    {
        "title": "COMBAT RULES & MECHANICS",
        "color": (255, 140, 140),
        "lines": [
            "  • Healing Flask     : Press E to channel healing for 2 seconds to restore 50% HP. Can only be used ONCE per game.",
            "                        CANNOT be used when Titan is Enraged!",
            "  • Parry Risk/Reward : Precise parry reflects attacks safely.",
            "                        MISSING parry timing inflicts HIGHER damage penalty than not parrying!",
            "  • 2-Second Quake    : When Titan's sword impacts the ground, a violent ground shake lasts for 2 full seconds!",
            "  • Enrage Activation : At <= 10% HP, Titan stops to roar with crimson dark rage for 3 seconds,",
            "                        then gains a glowing red outline with 70% faster attacks!",
        ]
    },
    {
        "title": "BOSS: TITAN AI & BEHAVIOR",
        "color": (255, 180, 80),
        "lines": [
            "  • Random Patrol     : Titan walks and switches directions completely randomly across the arena.",
            "  • Red Aura Idle     : Titan's signature stance animation plays with clean transparency.",
            "  • Distance Check    : If far from player (> 1/4 screen width), Titan EXCLUSIVELY throws his Spear.",
            "                        If close to player (<= 1/4 screen width), Titan randomly slams with Greatsword or throws Kunai.",
        ]
    }
]

# ---------------------------------------------------------------------------
# UI Helpers & Drawing
# ---------------------------------------------------------------------------
def draw_button(surface, rect, text, is_hover, primary_col=(180, 35, 35), border_col=(220, 185, 110)):
    """Draws a stylized button with borders and hover highlights."""
    btn_col = (min(primary_col[0] + 40, 255), min(primary_col[1] + 40, 255), min(primary_col[2] + 40, 255)) if is_hover else primary_col
    border_c = (255, 235, 160) if is_hover else border_col

    pygame.draw.rect(surface, btn_col, rect, border_radius=6)

    top_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 2)
    glass = pygame.Surface((top_rect.width, top_rect.height), pygame.SRCALPHA)
    glass.fill((255, 255, 255, 30 if not is_hover else 50))
    surface.blit(glass, top_rect)

    pygame.draw.rect(surface, border_c, rect, width=2, border_radius=6)

    txt_surf = font_btn.render(text, True, (255, 255, 255) if not is_hover else (255, 240, 190))
    txt_rect = txt_surf.get_rect(center=rect.center)
    surface.blit(txt_surf, txt_rect)


def draw_health_bars(surface, p, b, is_enraged):
    """Draws the player's red health bar on the left, boss's bar on the right, and healing flask status."""
    p["displayed_hp"] += (p["hp"] - p["displayed_hp"]) * 0.1
    b["displayed_hp"] += (b["hp"] - b["displayed_hp"]) * 0.1

    bar_w = int(W * 0.36)
    bar_h = 24
    top_y = int(H * 0.055)

    # ── Player Health Bar (Left) ──────────────────────────────────────────
    px = int(W * 0.04)
    p_name = font_bar_name.render("Great General Zhao", True, (240, 220, 170))
    p_name_shadow = font_bar_name.render("Great General Zhao", True, (20, 15, 10))
    surface.blit(p_name_shadow, (px + 2, top_y - 28))
    surface.blit(p_name, (px, top_y - 30))

    p_bg_rect = pygame.Rect(px, top_y, bar_w, bar_h)
    pygame.draw.rect(surface, (25, 20, 20), p_bg_rect, border_radius=4)

    p_pct_lag = max(0.0, min(1.0, p["displayed_hp"] / p["max_hp"]))
    if p_pct_lag > 0:
        p_lag_rect = pygame.Rect(px, top_y, int(bar_w * p_pct_lag), bar_h)
        pygame.draw.rect(surface, (220, 160, 50), p_lag_rect, border_radius=4)

    p_pct = max(0.0, min(1.0, p["hp"] / p["max_hp"]))
    if p_pct > 0:
        p_fill_rect = pygame.Rect(px, top_y, int(bar_w * p_pct), bar_h)
        pygame.draw.rect(surface, (215, 30, 30), p_fill_rect, border_radius=4)
        highlight_rect = pygame.Rect(px, top_y, int(bar_w * p_pct), bar_h // 2)
        hl = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 45))
        surface.blit(hl, highlight_rect)

    pygame.draw.rect(surface, (200, 170, 90), p_bg_rect, width=2, border_radius=4)

    p_val_surf = font_bar_val.render(f"{int(p['hp'])} / {p['max_hp']} HP", True, (255, 245, 225))
    surface.blit(p_val_surf, (px + 8, top_y + 4))

    # Healing Flask Status Display Below Bar
    if p["heal_used"]:
        h_txt = "[E] Healing Flask: USED (1/1)"
        h_col = (130, 130, 130)
    elif is_enraged:
        h_txt = "[E] Healing Flask: LOCKED (Boss Enraged!)"
        h_col = (255, 75, 75)
    elif p["state"] == "heal":
        h_txt = f"[E] Channeling Heal... ({p['heal_timer'] // 60 + 1}s)"
        h_col = (100, 255, 140)
    else:
        h_txt = "[E] Healing Flask: READY (+50% HP)"
        h_col = (110, 245, 120)

    h_surf = font_heal_status.render(h_txt, True, h_col)
    surface.blit(h_surf, (px, top_y + bar_h + 8))

    # ── Boss Health Bar (Right) ───────────────────────────────────────────
    bx = W - int(W * 0.04) - bar_w
    b_title = "Titan [ENRAGED]" if is_enraged else "Titan"
    b_name = font_bar_name.render(b_title, True, (255, 60, 60) if is_enraged else (240, 220, 170))
    b_name_shadow = font_bar_name.render(b_title, True, (20, 15, 10))
    b_name_rect = b_name.get_rect(topright=(bx + bar_w, top_y - 30))
    surface.blit(b_name_shadow, (b_name_rect.x + 2, b_name_rect.y + 2))
    surface.blit(b_name, b_name_rect)

    b_bg_rect = pygame.Rect(bx, top_y, bar_w, bar_h)
    pygame.draw.rect(surface, (25, 20, 20), b_bg_rect, border_radius=4)

    b_pct_lag = max(0.0, min(1.0, b["displayed_hp"] / b["max_hp"]))
    if b_pct_lag > 0:
        b_lag_rect = pygame.Rect(bx, top_y, int(bar_w * b_pct_lag), bar_h)
        pygame.draw.rect(surface, (220, 160, 50), b_lag_rect, border_radius=4)

    b_pct = max(0.0, min(1.0, b["hp"] / b["max_hp"]))
    if b_pct > 0:
        b_color = (245, 30, 30) if is_enraged else (180, 35, 55)
        b_fill_rect = pygame.Rect(bx, top_y, int(bar_w * b_pct), bar_h)
        pygame.draw.rect(surface, b_color, b_fill_rect, border_radius=4)
        highlight_rect = pygame.Rect(bx, top_y, int(bar_w * b_pct), bar_h // 2)
        hl = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 45))
        surface.blit(hl, highlight_rect)

    border_color = (255, 40, 40) if is_enraged else (215, 140, 70)
    pygame.draw.rect(surface, border_color, b_bg_rect, width=2, border_radius=4)

    b_val_surf = font_bar_val.render(f"{int(b['hp'])} / {b['max_hp']} HP", True, (255, 245, 225))
    b_val_rect = b_val_surf.get_rect(topright=(bx + bar_w - 8, top_y + 4))
    surface.blit(b_val_surf, b_val_rect)


# ---------------------------------------------------------------------------
# Game States & Button Rectangles
# ---------------------------------------------------------------------------
game_state = "MENU"
controls_scroll_y = 0
max_scroll_y = 0

btn_w = int(W * 0.28)
btn_h = int(H * 0.065)
btn_start_rect = pygame.Rect((W - btn_w) // 2, int(H * 0.50), btn_w, btn_h)
btn_ctrls_rect = pygame.Rect((W - btn_w) // 2, int(H * 0.60), btn_w, btn_h)
btn_exit_rect = pygame.Rect((W - btn_w) // 2, int(H * 0.70), btn_w, btn_h)

btn_back_rect = pygame.Rect(int(W * 0.08), int(H * 0.88), int(W * 0.16), int(H * 0.055))
btn_reset_rect = pygame.Rect((W - btn_w) // 2, int(H * 0.52), btn_w, btn_h)
btn_menu_rect = pygame.Rect((W - btn_w) // 2, int(H * 0.62), btn_w, btn_h)

# ---------------------------------------------------------------------------
# Main Game Loop
# ---------------------------------------------------------------------------
frame_count = 0
FLAG_ANIM_SPEED = 12
CLOUD_ANIM_SPEED = 30
SMOKE_ANIM_SPEED = 18

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    frame_count += 1
    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state in ("PLAYING", "CONTROLS", "VICTORY", "DEFEAT"):
                    reset_battle()
                    game_state = "MENU"
                elif game_state == "MENU":
                    running = False

            if game_state == "MENU":
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    reset_battle()
                    game_state = "PLAYING"
                elif event.key == pygame.K_c:
                    game_state = "CONTROLS"

            elif game_state == "CONTROLS":
                if event.key in (pygame.K_BACKSPACE, pygame.K_RETURN):
                    game_state = "MENU"

            elif game_state in ("VICTORY", "DEFEAT"):
                if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                    reset_battle()
                    game_state = "PLAYING"
                elif event.key == pygame.K_m:
                    reset_battle()
                    game_state = "MENU"

            elif game_state == "PLAYING":
                if event.key == pygame.K_k:
                    player["hp"] = max(0, player["hp"] - 25)
                elif event.key == pygame.K_t:
                    boss["hp"] = max(0, boss["hp"] - 200)
                elif event.key == pygame.K_u:
                    # Toggle Enraged mode test
                    boss["enraged_override"] = not boss["enraged_override"]
                elif event.key == pygame.K_s:
                    # Trigger boss sword slam test
                    boss["state"] = "smash"
                    boss["frame_idx"] = 0
                    boss["tick_count"] = 0
                    boss["smash_hit"] = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == "MENU":
                if btn_start_rect.collidepoint(event.pos):
                    reset_battle()
                    game_state = "PLAYING"
                elif btn_ctrls_rect.collidepoint(event.pos):
                    game_state = "CONTROLS"
                    controls_scroll_y = 0
                elif btn_exit_rect.collidepoint(event.pos):
                    running = False

            elif game_state == "CONTROLS":
                if btn_back_rect.collidepoint(event.pos):
                    game_state = "MENU"

            elif game_state in ("VICTORY", "DEFEAT"):
                if btn_reset_rect.collidepoint(event.pos):
                    reset_battle()
                    game_state = "PLAYING"
                elif btn_menu_rect.collidepoint(event.pos):
                    reset_battle()
                    game_state = "MENU"

        if event.type == pygame.MOUSEWHEEL and game_state == "CONTROLS":
            controls_scroll_y = max(0, min(max_scroll_y, controls_scroll_y - event.y * 30))

    # ══════════════════════════════════════════════════════════════════════
    # SCREEN SHAKE CALCULATION (Exact 2.0 Seconds = 120 Frames)
    # ══════════════════════════════════════════════════════════════════════
    if ground_shake_timer > 0:
        ground_shake_timer -= 1
        progress = ground_shake_timer / 120.0
        cur_intensity = ground_shake_intensity * (progress ** 0.70)
        shake_x = int(random.uniform(-cur_intensity, cur_intensity))
        shake_y = int(random.uniform(-cur_intensity * 0.75, cur_intensity * 0.75))
    else:
        shake_x = 0
        shake_y = 0

    # ══════════════════════════════════════════════════════════════════════
    # BACKGROUND SIMULATION (Active across all screens)
    # ══════════════════════════════════════════════════════════════════════
    screen.blit(background, (shake_x, shake_y))

    # Clouds
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
        screen.blit(img, (int(c["x"]) + shake_x, c["y"] + shake_y))
        if c["x"] > W + 50:
            c["x"] = -img.get_width() - random.randint(0, W // 4)
            c["y"] = random.randint(0, int(H * 0.12))

    # Flags
    flag_frame_idx = (frame_count // FLAG_ANIM_SPEED) % 2
    sway = math.sin(frame_count * 0.04) * 3

    f1 = flag1_frames[flag_frame_idx]
    f1_y = flag1_bottom[1] - f1.get_height()
    screen.blit(f1, (flag1_bottom[0] + int(sway) + shake_x, f1_y + shake_y))

    f2 = flag2_frames[flag_frame_idx]
    f2_y = flag2_bottom[1] - f2.get_height()
    screen.blit(f2, (flag2_bottom[0] - int(sway) + shake_x, f2_y + shake_y))

    # Smoke Particles
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
        screen.blit(img, (int(s["x"]) + shake_x, int(s["y"]) + shake_y))

        if s["age"] >= s["life"]:
            s.update(new_smoke())

    # ══════════════════════════════════════════════════════════════════════
    # SCREEN STATE ROUTING
    # ══════════════════════════════════════════════════════════════════════

    if game_state == "MENU":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((10, 8, 8, 140))
        screen.blit(overlay, (0, 0))

        title_surf = font_title.render("HAVEN HACKATHON", True, (255, 225, 150))
        title_shadow = font_title.render("HAVEN HACKATHON", True, (15, 10, 5))
        t_rect = title_surf.get_rect(center=(W // 2, int(H * 0.26)))
        screen.blit(title_shadow, (t_rect.x + 3, t_rect.y + 3))
        screen.blit(title_surf, t_rect)

        subtitle_surf = font_subtitle.render("GREAT GENERAL ZHAO  vs  TITAN", True, (230, 200, 170))
        st_rect = subtitle_surf.get_rect(center=(W // 2, int(H * 0.34)))
        screen.blit(subtitle_surf, st_rect)

        divider_w = int(W * 0.40)
        pygame.draw.line(screen, (215, 180, 100), (W // 2 - divider_w // 2, int(H * 0.40)), (W // 2 + divider_w // 2, int(H * 0.40)), 2)

        draw_button(screen, btn_start_rect, "START GAME", btn_start_rect.collidepoint(mouse_pos), primary_col=(170, 35, 35))
        draw_button(screen, btn_ctrls_rect, "CONTROLS & GUIDE", btn_ctrls_rect.collidepoint(mouse_pos), primary_col=(40, 60, 95))
        draw_button(screen, btn_exit_rect, "EXIT GAME", btn_exit_rect.collidepoint(mouse_pos), primary_col=(50, 45, 50))

    elif game_state == "CONTROLS":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((5, 5, 8, 195))
        screen.blit(overlay, (0, 0))

        panel_w = int(W * 0.84)
        panel_h = int(H * 0.84)
        panel_x = (W - panel_w) // 2
        panel_y = int(H * 0.05)

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((16, 18, 22, 230))
        pygame.draw.rect(panel_surf, (215, 185, 110), pygame.Rect(0, 0, panel_w, panel_h), width=2, border_radius=8)

        header_h = int(H * 0.08)
        header_surf = pygame.Surface((panel_w - 4, header_h), pygame.SRCALPHA)
        header_surf.fill((30, 34, 42, 255))
        panel_surf.blit(header_surf, (2, 2))

        head_txt = font_guide_head.render("HAVEN HACKATHON — SYSTEM & COMBAT GUIDE", True, (255, 220, 140))
        panel_surf.blit(head_txt, (30, (header_h - head_txt.get_height()) // 2))

        content_w = panel_w - 60
        content_h = int(H * 1.35)
        max_scroll_y = max(0, content_h - (panel_h - header_h - 20))

        content_surf = pygame.Surface((content_w, content_h), pygame.SRCALPHA)
        curr_y = 15

        for sec in GUIDE_SECTIONS:
            sec_title = font_guide_sec.render(sec["title"], True, sec["color"])
            content_surf.blit(sec_title, (0, curr_y))
            curr_y += sec_title.get_height() + 8

            for line in sec["lines"]:
                line_surf = font_guide_body.render(line, True, (225, 225, 230))
                content_surf.blit(line_surf, (15, curr_y))
                curr_y += line_surf.get_height() + 5

            curr_y += 20

        clip_area = pygame.Rect(0, controls_scroll_y, content_w, panel_h - header_h - 20)
        panel_surf.blit(content_surf, (30, header_h + 10), area=clip_area)

        screen.blit(panel_surf, (panel_x, panel_y))
        draw_button(screen, btn_back_rect, "← BACK TO MENU", btn_back_rect.collidepoint(mouse_pos), primary_col=(180, 40, 40))

        scroll_hint = font_bar_val.render("Scroll with Mouse Wheel | Press ESC or BACKSPACE to return", True, (190, 180, 160))
        screen.blit(scroll_hint, (panel_x + panel_w - scroll_hint.get_width() - 20, int(H * 0.90)))

    elif game_state == "PLAYING":
        keys = pygame.key.get_pressed()
        p = player
        b = boss

        # Check Enrage Condition (<= 10% HP or override test)
        is_enraged = (b["hp"] <= b["max_hp"] * 0.10) or b["enraged_override"]

        # Trigger Boss Enraged Mode Animation (plays Image 3 for 3 seconds once upon enraging)
        if is_enraged and not b["enraged_triggered"]:
            b["enraged_triggered"] = True
            b["state"] = "enrage_intro"
            b["enrage_intro_timer"] = 180    # 180 frames at 60 FPS = 3.0 seconds!
            b["frame_idx"] = 0
            b["tick_count"] = 0

        # Check Victory / Defeat Transitions
        if b["hp"] <= 0:
            b["hp"] = 0
            game_state = "VICTORY"
        elif p["hp"] <= 0:
            p["hp"] = 0
            game_state = "DEFEAT"

        # ── PLAYER STATE MACHINE & ACTIONS ────────────────────────────────
        if p["state"] in ("dodge", "slash", "parry", "kunai", "heal"):
            p["tick_count"] += 1

            if p["state"] == "heal":
                # Channel healing for 2 seconds (120 frames)
                p["heal_timer"] -= 1
                # Advance 30-frame healing animation over the 2 seconds (1 frame every 4 ticks)
                if p["tick_count"] >= 4:
                    p["tick_count"] = 0
                    p["frame_idx"] = (p["frame_idx"] + 1) % len(player_heal_frames)

                if p["heal_timer"] <= 0:
                    # Healing finishes: restore 50% HP!
                    p["hp"] = min(p["max_hp"], p["hp"] + int(p["max_hp"] * 0.50))
                    p["state"] = "idle"
                    p["frame_idx"] = 0
                    p["tick_count"] = 0

            elif p["state"] == "dodge":
                dx = DODGE_SPEED if p["facing_right"] else -DODGE_SPEED
                p["x"] += dx
                p["frame_idx"] += 1
                if p["frame_idx"] >= len(dodge_frames):
                    p["state"] = "idle"
                    p["frame_idx"] = 0
                    p["tick_count"] = 0

            elif p["state"] == "slash":
                p["frame_idx"] += 1
                # When sword strike connects (~frame 12), damage Titan if in range
                if p["frame_idx"] == 12:
                    dist_to_boss = abs(p["x"] - b["x"])
                    if dist_to_boss < int(player_h * 0.9):
                        b["hp"] = max(0, b["hp"] - 35)
                if p["frame_idx"] >= len(slash_frames):
                    p["state"] = "idle"
                    p["frame_idx"] = 0
                    p["tick_count"] = 0

            elif p["state"] == "parry":
                p["frame_idx"] += 1
                if p["frame_idx"] >= len(parry_frames):
                    p["state"] = "idle"
                    p["frame_idx"] = 0
                    p["tick_count"] = 0

            elif p["state"] == "kunai":
                p["frame_idx"] += 1
                # Spawn kunai projectile at release frame (~frame 12)
                if p["frame_idx"] == 12 and not p["kunai_spawned"]:
                    p["kunai_spawned"] = True
                    k_vx = KUNAI_SPEED if p["facing_right"] else -KUNAI_SPEED
                    spawn_x = p["x"] + (int(player_h * 0.25) if p["facing_right"] else -int(player_h * 0.25))
                    spawn_y = p["y"] - int(player_h * 0.52)
                    projectiles.append({
                        "x": spawn_x,
                        "y": spawn_y,
                        "vx": k_vx,
                        "type": "kunai",
                        "owner": "player",
                        "facing_right": p["facing_right"],
                        "damage": 25,
                        "active": True,
                    })

                if p["frame_idx"] >= len(player_kunai_frames):
                    p["state"] = "idle"
                    p["frame_idx"] = 0
                    p["kunai_spawned"] = False

        else:
            # ── Check Action Key Triggers ─────────────────────────────────
            # E: Healing Flask (Click once per game, heals 50%, takes 2s; blocked if boss is enraged!)
            if keys[pygame.K_e] and not p["heal_used"] and not is_enraged:
                p["heal_used"] = True
                p["state"] = "heal"
                p["heal_timer"] = 120    # 120 frames at 60 FPS = 2.0 seconds
                p["frame_idx"] = 0
                p["tick_count"] = 0

            elif keys[pygame.K_LSHIFT]:
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
                p["kunai_spawned"] = False
            else:
                # ── Horizontal Movement (A / D) ───────────────────────────
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
                        if p["tick_count"] >= 2:
                            p["tick_count"] = 0
                            p["frame_idx"] = (p["frame_idx"] + 1) % len(walk_frames)
                else:
                    p["state"] = "idle"
                    p["blink_timer"] -= 1
                    if p["blink_timer"] <= 0:
                        if not p["is_blinking"]:
                            p["is_blinking"] = True
                            p["blink_timer"] = 6
                        else:
                            p["is_blinking"] = False
                            p["blink_timer"] = random.randint(120, 200)

            # Jump (W)
            if keys[pygame.K_w] and p["on_ground"]:
                p["vy"] = JUMP_FORCE
                p["on_ground"] = False

        # Gravity
        if not p["on_ground"]:
            p["vy"] += GRAVITY
            p["y"] += p["vy"]
            if p["y"] >= GROUND_Y:
                p["y"] = GROUND_Y
                p["vy"] = 0
                p["on_ground"] = True

        p["x"] = max(center_offset, min(p["x"], W - center_offset))

        # ── BOSS (TITAN) AI & BEHAVIOR ────────────────────────────────────
        if b["state"] == "enrage_intro":
            # Play Enraged Mode animation (Image 3) for 3 full seconds!
            b["enrage_intro_timer"] -= 1
            b["tick_count"] += 1
            if b["tick_count"] >= 3:
                b["tick_count"] = 0
                b["frame_idx"] = (b["frame_idx"] + 1) % len(boss_enrage_frames)

            if b["enrage_intro_timer"] <= 0:
                b["state"] = "idle"
                b["frame_idx"] = 0
                b["tick_count"] = 0

        elif b["state"] in ("smash", "spear", "kunai"):
            # Attack speed: 70% faster when enraged!
            # Sword smash takes 1.5x time during wind-up when normal so it's telegraphed and easier to dodge
            if b["state"] == "smash":
                tick_interval = 1 if is_enraged else (2 if b["frame_idx"] < 17 else 1)
            else:
                tick_interval = 1 if is_enraged else 2

            b["tick_count"] += 1
            if b["tick_count"] >= tick_interval:
                b["tick_count"] = 0
                b["frame_idx"] += 1

                if b["state"] == "smash":
                    # Sword slams ground at frame 16 -> triggers EXACT 2.0 SECONDS OF SCREEN SHAKE!
                    if b["frame_idx"] == 16:
                        ground_shake_timer = 120    # 120 frames at 60 FPS = 2.0 full seconds
                        ground_shake_intensity = 22.0

                        if not b["smash_hit"]:
                            b["smash_hit"] = True
                            dist_to_player = abs(b["x"] - p["x"])
                            if dist_to_player < int(W * 0.18) and p["on_ground"]:
                                if p["state"] != "dodge":
                                    dmg = 45 if is_enraged else 30
                                    p["hp"] = max(0, p["hp"] - dmg)

                    if b["frame_idx"] >= len(boss_smash_frames):
                        b["state"] = "idle"
                        b["frame_idx"] = 0
                        b["tick_count"] = 0
                        b["smash_hit"] = False

                elif b["state"] == "spear":
                    # Spear release at frame 16
                    if b["frame_idx"] == 16 and not b["projectile_spawned"]:
                        b["projectile_spawned"] = True
                        base_sp_speed = KUNAI_SPEED + 4
                        sp_speed = int(base_sp_speed * 1.35) if is_enraged else base_sp_speed
                        sp_vx = sp_speed if b["facing_right"] else -sp_speed
                        spawn_x = b["x"] + (int(boss_h * 0.3) if b["facing_right"] else -int(boss_h * 0.3))
                        spawn_y = b["y"] - int(boss_h * 0.52)
                        projectiles.append({
                            "x": spawn_x,
                            "y": spawn_y,
                            "vx": sp_vx,
                            "type": "spear",
                            "owner": "boss",
                            "facing_right": b["facing_right"],
                            "damage": 35 if is_enraged else 25,
                            "active": True,
                        })

                    if b["frame_idx"] >= len(boss_spear_frames):
                        b["state"] = "idle"
                        b["frame_idx"] = 0
                        b["tick_count"] = 0
                        b["projectile_spawned"] = False

                elif b["state"] == "kunai":
                    # Boss throws kunai at frame 14
                    if b["frame_idx"] == 14 and not b["projectile_spawned"]:
                        b["projectile_spawned"] = True
                        base_k_speed = KUNAI_SPEED
                        k_speed = int(base_k_speed * 1.35) if is_enraged else base_k_speed
                        k_vx = k_speed if b["facing_right"] else -k_speed
                        spawn_x = b["x"] + (int(boss_h * 0.25) if b["facing_right"] else -int(boss_h * 0.25))
                        spawn_y = b["y"] - int(boss_h * 0.50)
                        projectiles.append({
                            "x": spawn_x,
                            "y": spawn_y,
                            "vx": k_vx,
                            "type": "kunai",
                            "owner": "boss",
                            "facing_right": b["facing_right"],
                            "damage": 25 if is_enraged else 18,
                            "active": True,
                        })

                    if b["frame_idx"] >= len(boss_spear_frames):
                        b["state"] = "idle"
                        b["frame_idx"] = 0
                        b["tick_count"] = 0
                        b["projectile_spawned"] = False

        else:
            # Boss Attack Decision (Interval 3-5 seconds, 70% FASTER when enraged: 0.9-1.5s!)
            b["attack_cooldown"] -= 1.0 / 60.0
            if b["attack_cooldown"] <= 0:
                base_cd = random.uniform(3.0, 5.0)
                b["attack_cooldown"] = base_cd * 0.30 if is_enraged else base_cd

                dist = abs(b["x"] - p["x"])
                is_far = dist > (W * 0.25)  # More than 1/4 horizontal screen width away

                # Face player when launching attack
                b["facing_right"] = (p["x"] > b["x"])

                if is_far:
                    # Far away: exclusively throw spear
                    b["state"] = "spear"
                    b["frame_idx"] = 0
                    b["tick_count"] = 0
                    b["projectile_spawned"] = False
                else:
                    # Close range: randomly pick between greatsword smash or kunai throw
                    chosen_atk = random.choice(["smash", "kunai"])
                    b["state"] = chosen_atk
                    b["frame_idx"] = 0
                    b["tick_count"] = 0
                    b["projectile_spawned"] = False
                    b["smash_hit"] = False

            else:
                # ── Random Walking & Completely Random Direction Switching ─
                b["action_timer"] -= 1.0 / 60.0
                if b["action_timer"] <= 0:
                    b["action_timer"] = random.uniform(1.0, 4.5)
                    # Randomly pick walk left, stand idle, walk right, or randomly flip facing direction!
                    b["walk_dir"] = random.choice([-1, 0, 1])
                    if b["walk_dir"] != 0:
                        b["facing_right"] = (b["walk_dir"] > 0)
                    else:
                        # Completely random facing change even when standing!
                        b["facing_right"] = random.choice([True, False])

                if b["walk_dir"] != 0:
                    walk_spd = 3.2 if is_enraged else 2.0
                    b["x"] += b["walk_dir"] * walk_spd
                    b["facing_right"] = (b["walk_dir"] > 0)

                    # Stay within battle arena bounds
                    min_bx = int(W * 0.18)
                    max_bx = int(W * 0.94)
                    if b["x"] < min_bx:
                        b["x"] = min_bx
                        b["walk_dir"] = 1
                        b["facing_right"] = True
                    elif b["x"] > max_bx:
                        b["x"] = max_bx
                        b["walk_dir"] = -1
                        b["facing_right"] = False
                    b["state"] = "walk"
                else:
                    b["state"] = "idle"

                # Advance walk / idle animations
                b["tick_count"] += 1
                idle_speed = 1 if is_enraged else 2
                if b["tick_count"] >= idle_speed:
                    b["tick_count"] = 0
                    if b["state"] == "walk":
                        b["frame_idx"] = (b["frame_idx"] + 1) % len(boss_walk_frames)
                    else:
                        b["frame_idx"] = (b["frame_idx"] + 1) % len(boss_idle_frames)

        # ── PROJECTILES UPDATE & COLLISION ────────────────────────────────
        for proj in projectiles:
            if not proj["active"]:
                continue

            proj["x"] += proj["vx"]

            # Check off-screen
            if proj["x"] < -100 or proj["x"] > W + 100:
                proj["active"] = False
                continue

            if proj["owner"] == "player":
                # Collision with Boss
                if abs(proj["x"] - b["x"]) < int(boss_h * 0.28) and abs(proj["y"] - (b["y"] - boss_h * 0.5)) < int(boss_h * 0.5):
                    b["hp"] = max(0, b["hp"] - proj["damage"])
                    proj["active"] = False

            elif proj["owner"] == "boss":
                # Collision with Player
                if abs(proj["x"] - p["x"]) < int(player_h * 0.25) and abs(proj["y"] - (p["y"] - player_h * 0.5)) < int(player_h * 0.5):
                    if p["state"] == "dodge":
                        pass  # Evasively rolled under!
                    elif p["state"] == "parry":
                        proj["active"] = False  # Parried!
                    else:
                        p["hp"] = max(0, p["hp"] - proj["damage"])
                        proj["active"] = False

        projectiles = [proj for proj in projectiles if proj["active"]]

        # ── RENDER CHARACTERS & PROJECTILES ───────────────────────────────
        # 1. Render Player (General Zhao - Solid, completely opaque!)
        if p["state"] == "heal":
            p_sprite = player_heal_frames[p["frame_idx"] % len(player_heal_frames)]
            p_draw_x = int(p["x"] - pheal_center_offset) + shake_x
            p_draw_y = int(p["y"] - pheal_feet_offset) + shake_y
        elif p["state"] == "idle":
            p_sprite = idle_blink if p["is_blinking"] else idle_open
            p_draw_x = int(p["x"] - center_offset) + shake_x
            p_draw_y = int(p["y"] - feet_offset) + shake_y
        elif p["state"] == "walk":
            p_sprite = walk_frames[p["frame_idx"]]
            p_draw_x = int(p["x"] - center_offset) + shake_x
            p_draw_y = int(p["y"] - feet_offset) + shake_y
        elif p["state"] == "dodge":
            p_sprite = dodge_frames[p["frame_idx"]]
            p_draw_x = int(p["x"] - center_offset) + shake_x
            p_draw_y = int(p["y"] - feet_offset) + shake_y
        elif p["state"] == "slash":
            p_sprite = slash_frames[p["frame_idx"]]
            p_draw_x = int(p["x"] - center_offset) + shake_x
            p_draw_y = int(p["y"] - feet_offset) + shake_y
        elif p["state"] == "parry":
            p_sprite = parry_frames[p["frame_idx"]]
            p_draw_x = int(p["x"] - center_offset) + shake_x
            p_draw_y = int(p["y"] - feet_offset) + shake_y
        elif p["state"] == "kunai":
            p_sprite = player_kunai_frames[p["frame_idx"]]
            p_draw_x = int(p["x"] - pk_center_offset) + shake_x
            p_draw_y = int(p["y"] - pk_feet_offset) + shake_y

        if not p["facing_right"]:
            p_sprite = pygame.transform.flip(p_sprite, True, False)

        screen.blit(p_sprite, (p_draw_x, p_draw_y))

        # 2. Render Boss (Titan)
        if b["state"] == "enrage_intro":
            b_sprite = boss_enrage_frames[b["frame_idx"] % len(boss_enrage_frames)]
            b_draw_x = int(b["x"] - be_center) + shake_x
            b_draw_y = int(b["y"] - be_feet) + shake_y
        elif b["state"] == "walk":
            b_sprite = boss_walk_frames[b["frame_idx"] % len(boss_walk_frames)]
            b_draw_x = int(b["x"] - bw_center) + shake_x
            b_draw_y = int(b["y"] - bw_feet) + shake_y
        elif b["state"] == "idle":
            b_sprite = boss_idle_frames[b["frame_idx"] % len(boss_idle_frames)]
            b_draw_x = int(b["x"] - bi_center) + shake_x
            b_draw_y = int(b["y"] - bi_feet) + shake_y
        elif b["state"] == "smash":
            b_sprite = boss_smash_frames[b["frame_idx"] % len(boss_smash_frames)]
            b_draw_x = int(b["x"] - bs_center) + shake_x
            b_draw_y = int(b["y"] - bs_feet) + shake_y
        elif b["state"] == "spear":
            b_sprite = boss_spear_frames[b["frame_idx"] % len(boss_spear_frames)]
            b_draw_x = int(b["x"] - bsp_center) + shake_x
            b_draw_y = int(b["y"] - bsp_feet) + shake_y
        elif b["state"] == "kunai":
            b_sprite = boss_spear_frames[b["frame_idx"] % len(boss_spear_frames)]
            b_draw_x = int(b["x"] - bsp_center) + shake_x
            b_draw_y = int(b["y"] - bsp_feet) + shake_y

        # Boss source images natively face RIGHT.
        # If facing_right is False (facing LEFT towards player), flip horizontally!
        if not b["facing_right"]:
            b_sprite = pygame.transform.flip(b_sprite, True, False)

        # ── ENRAGED RED FLASHING OUTLINE ──────────────────────────────────
        if is_enraged and b["state"] != "enrage_intro":
            pulse = abs(math.sin(frame_count * 0.28))
            outline_alpha = int(140 + 115 * pulse)
            mask = pygame.mask.from_surface(b_sprite)
            outline_surf = mask.to_surface(setcolor=(255, 25, 25, outline_alpha), unsetcolor=(0, 0, 0, 0))
            for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)]:
                screen.blit(outline_surf, (b_draw_x + ox, b_draw_y + oy))

        screen.blit(b_sprite, (b_draw_x, b_draw_y))

        # 3. Render Projectiles
        for proj in projectiles:
            if proj["type"] == "kunai":
                k_img = kunai_item_right if proj["facing_right"] else kunai_item_left
                screen.blit(k_img, (int(proj["x"] - k_img.get_width() // 2) + shake_x, int(proj["y"] - k_img.get_height() // 2) + shake_y))
            elif proj["type"] == "spear":
                sp_img = spear_proj_right if proj["facing_right"] else spear_proj_left
                screen.blit(sp_img, (int(proj["x"] - sp_img.get_width() // 2) + shake_x, int(proj["y"] - sp_img.get_height() // 2) + shake_y))

        # 4. Render Health Bars at Top (Kept steady for UI clarity)
        draw_health_bars(screen, p, b, is_enraged)

    elif game_state == "VICTORY":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((15, 12, 5, 190))
        screen.blit(overlay, (0, 0))

        v_title = font_end_title.render("VICTORY ACHIEVED", True, (255, 220, 90))
        v_shadow = font_end_title.render("VICTORY ACHIEVED", True, (20, 15, 5))
        v_rect = v_title.get_rect(center=(W // 2, int(H * 0.28)))
        screen.blit(v_shadow, (v_rect.x + 3, v_rect.y + 3))
        screen.blit(v_title, v_rect)

        v_sub = font_end_sub.render("Titan has fallen before Great General Zhao!", True, (240, 230, 200))
        vs_rect = v_sub.get_rect(center=(W // 2, int(H * 0.38)))
        screen.blit(v_sub, vs_rect)

        pygame.draw.line(screen, (220, 185, 90), (W // 2 - int(W * 0.25), int(H * 0.44)), (W // 2 + int(W * 0.25), int(H * 0.44)), 2)

        draw_button(screen, btn_reset_rect, "PLAY AGAIN (RESET)", btn_reset_rect.collidepoint(mouse_pos), primary_col=(35, 130, 60))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(50, 45, 50))

        hint = font_bar_val.render("Press [R] or [ENTER] to Play Again  |  Press [ESC] for Main Menu", True, (200, 190, 160))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.74))))

    elif game_state == "DEFEAT":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((30, 5, 5, 205))
        screen.blit(overlay, (0, 0))

        d_title = font_end_title.render("YOU DIED", True, (230, 40, 40))
        d_shadow = font_end_title.render("YOU DIED", True, (10, 0, 0))
        d_rect = d_title.get_rect(center=(W // 2, int(H * 0.28)))
        screen.blit(d_shadow, (d_rect.x + 4, d_rect.y + 4))
        screen.blit(d_title, d_rect)

        d_sub = font_end_sub.render("Great General Zhao has perished in battle against Titan...", True, (230, 190, 190))
        ds_rect = d_sub.get_rect(center=(W // 2, int(H * 0.38)))
        screen.blit(d_sub, ds_rect)

        pygame.draw.line(screen, (200, 50, 50), (W // 2 - int(W * 0.25), int(H * 0.44)), (W // 2 + int(W * 0.25), int(H * 0.44)), 2)

        draw_button(screen, btn_reset_rect, "TRY AGAIN (RESET)", btn_reset_rect.collidepoint(mouse_pos), primary_col=(180, 35, 35))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(50, 45, 50))

        hint = font_bar_val.render("Press [R] or [ENTER] to Try Again  |  Press [ESC] for Main Menu", True, (190, 150, 150))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.74))))

    # ── Display Flip & Clock ──────────────────────────────────────────────
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
