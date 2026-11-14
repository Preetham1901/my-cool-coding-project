import os
import math
import random
import pygame

# ---------------------------------------------------------------------------
# Initialisation & Audio Setup
# ---------------------------------------------------------------------------
pygame.init()
pygame.font.init()

try:
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.mixer.init()
except Exception:
    pass

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Haven Hackathon - Shinobi: Legend of Zhao")
W, H = screen.get_size()
clock = pygame.time.Clock()

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


# ---------------------------------------------------------------------------
# Audio (SFX) Manager
# ---------------------------------------------------------------------------
SFX = {}
for s_name in ["parry_metal", "slash_hit", "ground_slam", "kunai_throw", "heal_spell", "block_wood", "posture_break"]:
    try:
        p = os.path.join(ASSETS, "sfx", f"{s_name}.wav")
        if os.path.exists(p):
            SFX[s_name] = pygame.mixer.Sound(p)
    except Exception:
        pass


def play_sfx(name, vol=1.0):
    if name in SFX:
        try:
            SFX[name].set_volume(vol)
            SFX[name].play()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Typography (Gang of Three font from Fruit Ninja with graceful fallback)
# ---------------------------------------------------------------------------
FONT_PATH = os.path.join(ASSETS, "go3v2.ttf")


def get_font(size):
    if os.path.exists(FONT_PATH):
        try:
            return pygame.font.Font(FONT_PATH, size)
        except Exception:
            pass
    return pygame.font.SysFont(["georgia", "cinzel", "arial"], size, bold=True)


font_title = get_font(int(H * 0.055))
font_sub = get_font(int(H * 0.024))
font_bar_name = get_font(int(H * 0.026))
font_bar_val = get_font(int(H * 0.017))
font_hud_info = get_font(int(H * 0.017))
font_btn = get_font(int(H * 0.023))
font_guide_head = get_font(int(H * 0.034))
font_guide_sec = get_font(int(H * 0.022))
font_guide_text = get_font(int(H * 0.016))
font_end_title = get_font(int(H * 0.065))
font_bounce_back = get_font(int(H * 0.078))
font_end_sub = get_font(int(H * 0.023))
font_stun_banner = get_font(int(H * 0.030))
font_round_banner = get_font(int(H * 0.024))
font_round_score = get_font(int(H * 0.019))


# ---------------------------------------------------------------------------
# Asset Loading Helpers
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
    """Extract individual frames from a transparent sprite sheet grid."""
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
# Load Arena Background & Environmental Assets
# ---------------------------------------------------------------------------
bg_raw = load_image("background.jpg")
bg = pygame.transform.scale(bg_raw, (W, H))

FLAG_SCALE = 0.35
flag_h = int(H * FLAG_SCALE)

flag1_a_raw = load_image("flag1_a.png")
flag1_b_raw = load_image("flag1_b.png")
f1_scale = flag_h / flag1_a_raw.get_height()
flag1_w = int(flag1_a_raw.get_width() * f1_scale)
flag1_a = pygame.transform.smoothscale(flag1_a_raw, (flag1_w, flag_h))
flag1_b = pygame.transform.smoothscale(flag1_b_raw, (flag1_w, flag_h))

flag2_a_raw = load_image("flag2_a.png")
flag2_b_raw = load_image("flag2_b.png")
f2_scale = flag_h / flag2_a_raw.get_height()
flag2_w = int(flag2_a_raw.get_width() * f2_scale)
flag2_a = pygame.transform.smoothscale(flag2_a_raw, (flag2_w, flag_h))
flag2_b = pygame.transform.smoothscale(flag2_b_raw, (flag2_w, flag_h))

GROUND_Y = int(H * 0.88)
FLAG_BOTTOM_Y = GROUND_Y

flag1_x = int(W * 0.08)
flag1_y = FLAG_BOTTOM_Y - flag_h

flag2_x = int(W * 0.90)
flag2_y = FLAG_BOTTOM_Y - flag_h

# Clouds (animated drifting across sky)
cloud_img1 = load_image("clouds_1.png")
cloud_img2 = load_image("clouds_2.png")
cloud_variants = [cloud_img1, cloud_img2]

clouds = []
for _ in range(6):
    clouds.append({
        "x": random.randint(-W // 4, W),
        "y": random.randint(0, int(H * 0.12)),
        "speed": random.uniform(0.15, 0.45),
        "scale": random.uniform(0.7, 1.3),
        "alpha": random.randint(140, 220),
    })

# Smoke particles rising from battlefield
smoke_img1 = load_image("smoke_1.png")
smoke_img2 = load_image("smoke_2.png")
smoke_variants = [smoke_img1, smoke_img2]


def new_smoke():
    return {
        "x": random.randint(int(W * 0.70), int(W * 0.90)),
        "y": random.randint(int(H * 0.08), int(H * 0.25)),
        "vx": random.uniform(-0.2, 0.2),
        "vy": random.uniform(-0.4, -1.0),
        "life": random.randint(180, 360),
        "age": 0,
        "variant": random.randint(0, len(smoke_variants) - 1),
    }


smoke_particles = [new_smoke() for _ in range(8)]


# ---------------------------------------------------------------------------
# Player (Great General Zhao) Sprites & Scaling
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
# Boss (The Hollow Magistrate) Sprites & Scaling
# Sized 120% of player. Source sheets natively face RIGHT.
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

# 3. Boss Enraged Roar / Activation (New 150-frame sheet: 15 rows x 10 cols, plays over 5s!)
raw_boss_enrage = extract_grid_frames("boss_enrage.png", 15, 10)
be_scale = boss_h / 55.0
be_w = int(68.2 * be_scale)
be_h = int(68.266 * be_scale)
be_feet = int(62 * be_scale)
be_center = be_w // 2
boss_enrage_frames = [pygame.transform.smoothscale(f, (be_w, be_h)) for f in raw_boss_enrage]

# 4. Boss Heavy Smash (greatsword slam with 2-second screen shake)
raw_boss_smash = extract_grid_frames("boss_smash.png", 5, 6)
bs_w = int(170.67 * boss_scale)
bs_h = int(170.6 * boss_scale)
bs_feet = int(162 * boss_scale)
bs_center = bs_w // 2
boss_smash_frames = [pygame.transform.smoothscale(f, (bs_w, bs_h)) for f in raw_boss_smash]

# 5. Boss Spear Throw (SHRINKING FIXED: scaled by character pixel height 131.0!)
raw_boss_spear = extract_grid_frames("boss_spear.png", 5, 6)
spear_scale = boss_h / 131.0
bsp_w = int(170.67 * spear_scale)
bsp_h = int(184.8 * spear_scale)
bsp_feet = int(159 * spear_scale)
bsp_center = bsp_w // 2
boss_spear_frames = [pygame.transform.smoothscale(f, (bsp_w, bsp_h)) for f in raw_boss_spear]


# ---------------------------------------------------------------------------
# Projectiles
# ---------------------------------------------------------------------------
raw_kunai_item = load_image("kunai_projectile.png")
kw = int(player_h * 0.32)
kh = int(kw * (188.0 / 948.0))
kunai_item_right = pygame.transform.smoothscale(raw_kunai_item, (kw, kh))
kunai_item_left = pygame.transform.flip(kunai_item_right, True, False)

raw_spear_sub = raw_boss_spear[16].subsurface(pygame.Rect(
    int(raw_boss_spear[16].get_width() * 0.45),
    int(raw_boss_spear[16].get_height() * 0.25),
    int(raw_boss_spear[16].get_width() * 0.50),
    int(raw_boss_spear[16].get_height() * 0.30)
))
sp_w = int(boss_h * 0.52)
sp_h = int(sp_w * (raw_spear_sub.get_height() / raw_spear_sub.get_width()))
spear_proj_right = pygame.transform.smoothscale(raw_spear_sub, (sp_w, sp_h))
spear_proj_left = pygame.transform.flip(spear_proj_right, True, False)


# ---------------------------------------------------------------------------
# Best of 5 (BO5) Match State & Player Buffs
# ---------------------------------------------------------------------------
current_round = 1
player_round_wins = 0
boss_round_wins = 0

player_hp_buff = 0          # +30 Max HP after 1st loss
player_speed_buff = False   # +25% move speed & attack speed after 2nd loss

BASE_MOVE_SPEED = 7.0
JUMP_FORCE = -17.5
GRAVITY = 0.85
BASE_KUNAI_SPEED = 24.0      # +20% base hit speed for kunai (was 20.0, always active!)


player = {
    "name": "Great General Zhao",
    "x": int(flag1_x - (frame_w * 0.18)),
    "y": GROUND_Y,
    "vy": 0.0,
    "on_ground": True,
    "facing_right": True,
    "state": "idle",             # "idle", "walk", "dodge", "slash", "parry", "kunai", "heal"
    "frame_idx": 0,
    "anim_time": 0.0,
    "tick_count": 0,
    "blink_timer": random.randint(120, 180),
    "is_blinking": False,
    "hp": 100,
    "max_hp": 100,
    "displayed_hp": 100.0,
    "kunai_spawned": False,
    "heal_used": False,          # 1 use per round
    "heal_timer": 0,             # 120 ticks = 2.0s channel
    "kunai_count": 3,            # Rechargeable Kunai pouch (max 3)
    "kunai_max": 3,
    "kunai_recharge_timer": 0,   # 240 ticks = 4.0s per recharge
    "is_blocking": False,
}

boss = {
    "name": "The Hollow Magistrate",
    "title": "Titan of the Ashen Peak",
    "x": int(W * 0.82),
    "y": GROUND_Y,
    "vx": 0.0,                  # Smooth velocity easing for fluid movement
    "facing_right": False,      # initially facing left towards player
    "state": "idle",            # "idle", "walk", "smash", "spear", "kunai", "enrage_intro", "stunned"
    "frame_idx": 0,
    "anim_time": 0.0,           # Continuous animation timer for ultra-smooth fluid transitions
    "tick_count": 0,
    "hp": 1000,
    "max_hp": 1000,
    "displayed_hp": 1000.0,
    "posture": 0.0,             # Stagger / Posture meter (0.0 to 100.0)
    "max_posture": 100.0,
    "posture_decay_delay": 0,
    "is_stunned": False,
    "stun_timer": 0,            # 210 ticks = 3.5s posture break stun window
    "action_timer": random.uniform(1.0, 3.5),
    "walk_dir": 0,
    "attack_cooldown": random.uniform(3.0, 4.8),
    "projectile_spawned": False,
    "smash_hit": False,
    "enraged_triggered": False,
    "enrage_intro_timer": 0,    # 330 ticks = 5.5s intro!
}

ground_shake_timer = 0
ground_shake_intensity = 0.0

projectiles = []
sparks = []
red_mist_particles = []


def spawn_sparks(x, y, count=20, is_golden=True):
    """Spawns dynamic burst of spark particles on parry/clash."""
    golden_cols = [(255, 235, 140), (255, 195, 70), (255, 255, 220), (255, 130, 40)]
    silver_cols = [(220, 220, 220), (180, 180, 180), (240, 240, 240)]
    palette = golden_cols if is_golden else silver_cols
    for _ in range(count):
        ang = random.uniform(0, math.pi * 2)
        spd = random.uniform(4.0, 14.0)
        col = random.choice(palette)
        sparks.append({
            "x": float(x),
            "y": float(y),
            "vx": math.cos(ang) * spd,
            "vy": math.sin(ang) * spd - random.uniform(1.0, 4.0),
            "color": col,
            "life": random.randint(14, 28),
            "max_life": 28,
            "size": max(1, int(random.uniform(2.0, 4.5))),
        })


def spawn_red_mist(bx, by, count=2):
    """Spawns ominous dark red mist aura around the Magistrate."""
    for _ in range(count):
        red_mist_particles.append({
            "x": bx + random.uniform(-boss_h * 0.35, boss_h * 0.35),
            "y": by - random.uniform(0, boss_h * 0.95),
            "vx": random.uniform(-0.6, 0.6),
            "vy": random.uniform(-1.2, -0.4),
            "radius": random.uniform(8.0, 22.0),
            "alpha": random.randint(60, 130),
            "life": random.randint(30, 60),
            "max_life": 60,
        })


def reset_round_entities():
    """Resets round combatants, applying any active buffs."""
    global ground_shake_timer, ground_shake_intensity, projectiles, sparks, red_mist_particles
    ground_shake_timer = 0
    ground_shake_intensity = 0.0
    projectiles = []
    sparks = []
    red_mist_particles = []

    # Apply HP buff if earned from a previous loss
    effective_max_hp = 100 + player_hp_buff
    player["max_hp"] = effective_max_hp
    player["hp"] = effective_max_hp
    player["displayed_hp"] = float(effective_max_hp)

    player["x"] = int(flag1_x - (frame_w * 0.18))
    player["y"] = GROUND_Y
    player["vy"] = 0.0
    player["on_ground"] = True
    player["facing_right"] = True
    player["state"] = "idle"
    player["frame_idx"] = 0
    player["anim_time"] = 0.0
    player["tick_count"] = 0
    player["blink_timer"] = random.randint(120, 180)
    player["is_blinking"] = False
    player["kunai_spawned"] = False
    player["heal_used"] = False
    player["heal_timer"] = 0
    player["kunai_count"] = player["kunai_max"]
    player["kunai_recharge_timer"] = 0
    player["is_blocking"] = False

    boss["hp"] = boss["max_hp"]
    boss["displayed_hp"] = float(boss["max_hp"])
    boss["posture"] = 0.0
    boss["is_stunned"] = False
    boss["stun_timer"] = 0
    boss["x"] = int(W * 0.82)
    boss["y"] = GROUND_Y
    boss["vx"] = 0.0
    boss["facing_right"] = False
    boss["state"] = "idle"
    boss["frame_idx"] = 0
    boss["anim_time"] = 0.0
    boss["tick_count"] = 0
    boss["action_timer"] = random.uniform(1.0, 3.5)
    boss["walk_dir"] = 0
    boss["attack_cooldown"] = random.uniform(3.0, 4.5)
    boss["projectile_spawned"] = False
    boss["smash_hit"] = False
    boss["enraged_triggered"] = False
    boss["enrage_intro_timer"] = 0


def start_next_round():
    """Advances to the next round of the Best of 5."""
    global current_round, game_state
    current_round += 1
    reset_round_entities()
    game_state = "PLAYING"


def reset_full_match():
    """Resets entire Best of 5 match from Round 1."""
    global current_round, player_round_wins, boss_round_wins, player_hp_buff, player_speed_buff, game_state
    current_round = 1
    player_round_wins = 0
    boss_round_wins = 0
    player_hp_buff = 0
    player_speed_buff = False
    reset_round_entities()
    game_state = "PLAYING"


# ---------------------------------------------------------------------------
# Traditional Feudal UI & Crossed Swords Crest
# ---------------------------------------------------------------------------
def draw_feudal_panel(surface, rect, border_col=(130, 32, 28), bg_col=(22, 16, 14, 235), gold_corners=True):
    """Draws an antique Japanese / Dark Souls style plaque with corner brackets."""
    panel_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel_surf.fill(bg_col)
    surface.blit(panel_surf, (rect.x, rect.y))

    # Outer border & inner subtle border
    pygame.draw.rect(surface, border_col, rect, 2, border_radius=3)
    inner_rect = rect.inflate(-6, -6)
    pygame.draw.rect(surface, (border_col[0] // 2, border_col[1] // 2, border_col[2] // 2), inner_rect, 1, border_radius=2)

    # Gold leaf corner brackets (Antique Feudal styling)
    if gold_corners:
        gold = (212, 163, 75)
        c_len = min(14, rect.width // 6, rect.height // 6)
        # Top-Left
        pygame.draw.line(surface, gold, (rect.x, rect.y), (rect.x + c_len, rect.y), 3)
        pygame.draw.line(surface, gold, (rect.x, rect.y), (rect.x, rect.y + c_len), 3)
        # Top-Right
        pygame.draw.line(surface, gold, (rect.right - 1, rect.y), (rect.right - 1 - c_len, rect.y), 3)
        pygame.draw.line(surface, gold, (rect.right - 1, rect.y), (rect.right - 1, rect.y + c_len), 3)
        # Bottom-Left
        pygame.draw.line(surface, gold, (rect.x, rect.bottom - 1), (rect.x + c_len, rect.bottom - 1), 3)
        pygame.draw.line(surface, gold, (rect.x, rect.bottom - 1), (rect.x, rect.bottom - 1 - c_len), 3)
        # Bottom-Right
        pygame.draw.line(surface, gold, (rect.right - 1, rect.bottom - 1), (rect.right - 1 - c_len, rect.bottom - 1), 3)
        pygame.draw.line(surface, gold, (rect.right - 1, rect.bottom - 1), (rect.right - 1, rect.bottom - 1 - c_len), 3)


def draw_crossed_swords(surface, cx, cy, radius=int(H * 0.038)):
    """Draws an authentic intersecting katana crest between health bars."""
    # Outer crimson seal ring
    pygame.draw.circle(surface, (18, 12, 11), (cx, cy), radius)
    pygame.draw.circle(surface, (140, 32, 28), (cx, cy), radius, 2)
    pygame.draw.circle(surface, (212, 163, 75), (cx, cy), radius - 3, 1)

    # Two crossed swords at 45 degree diagonals
    blade_len = radius * 1.35
    for angle in [math.pi * 0.25, math.pi * 0.75]:
        dx = math.cos(angle)
        dy = math.sin(angle)

        p_tip = (cx + dx * blade_len, cy - dy * blade_len)
        p_pommel = (cx - dx * (blade_len * 0.85), cy + dy * (blade_len * 0.85))

        # Silver steel blade with blood groove
        pygame.draw.line(surface, (230, 235, 240), (cx, cy), p_tip, 3)
        pygame.draw.line(surface, (160, 170, 180), (cx, cy), p_tip, 1)

        # Crossguard (Tsuba) in antique gold
        guard_dx = -dy * 7
        guard_dy = dx * 7
        g1 = (cx - dx * 6 + guard_dx, cy + dy * 6 + guard_dy)
        g2 = (cx - dx * 6 - guard_dx, cy + dy * 6 - guard_dy)
        pygame.draw.line(surface, (220, 180, 85), g1, g2, 4)

        # Hilt (Tsuka) wrapped in dark crimson
        pygame.draw.line(surface, (145, 28, 24), (cx - dx * 6, cy + dy * 6), p_pommel, 3)
        # Gold pommel ring
        pygame.draw.circle(surface, (220, 180, 85), (int(p_pommel[0]), int(p_pommel[1])), 3)

    # Central golden rivet
    pygame.draw.circle(surface, (240, 210, 110), (cx, cy), 3)


def draw_health_bars(surface, p, b, boss_phase, is_enraged):
    """Draws feudal health bars, posture meter, Best-of-5 round tracker, and buffs."""
    margin_x = int(W * 0.04)
    bar_w = int(W * 0.38)
    bar_h = int(H * 0.030)
    bar_y = int(H * 0.052)

    # --- TOP CENTER: BEST OF 5 ROUND STATUS ---
    center_x = W // 2
    round_str = f"ROUND {current_round} OF 5"
    r_surf = font_round_banner.render(round_str, True, (255, 225, 130))
    surface.blit(r_surf, r_surf.get_rect(center=(center_x, bar_y - int(H * 0.030))))

    # Win Pips: Zhao ● ○ ○ vs ○ ○ ● Magistrate
    p_pips = "● " * player_round_wins + "○ " * (3 - player_round_wins)
    b_pips = "○ " * (3 - boss_round_wins) + "● " * boss_round_wins
    score_str = f"ZHAO [ {p_pips.strip()} ]  vs  [ {b_pips.strip()} ] MAGISTRATE"
    score_surf = font_round_score.render(score_str, True, (225, 205, 175))
    surface.blit(score_surf, score_surf.get_rect(center=(center_x, bar_y - int(H * 0.010))))

    # --- 1. PLAYER HEALTH BAR (LEFT) ---
    p["displayed_hp"] += (p["hp"] - p["displayed_hp"]) * 0.12
    p_pct = max(0.0, min(1.0, p["hp"] / p["max_hp"]))
    p_lag_pct = max(0.0, min(1.0, p["displayed_hp"] / p["max_hp"]))

    # Label & Flask / Kunai status
    p_title = font_bar_name.render(p["name"], True, (240, 230, 210))
    surface.blit(p_title, (margin_x, bar_y - int(H * 0.034)))

    p_bg_rect = pygame.Rect(margin_x, bar_y, bar_w, bar_h)
    draw_feudal_panel(surface, p_bg_rect, border_col=(120, 30, 25), bg_col=(18, 12, 10, 230))

    if p_lag_pct > 0:
        lag_rect = pygame.Rect(margin_x + 3, bar_y + 3, int((bar_w - 6) * p_lag_pct), bar_h - 6)
        pygame.draw.rect(surface, (210, 160, 60), lag_rect)

    if p_pct > 0:
        fill_w = int((bar_w - 6) * p_pct)
        fill_rect = pygame.Rect(margin_x + 3, bar_y + 3, fill_w, bar_h - 6)
        pygame.draw.rect(surface, (190, 32, 28), fill_rect)

    p_hp_str = f"{p['hp']} / {p['max_hp']} HP"
    p_hp_surf = font_bar_val.render(p_hp_str, True, (255, 245, 235))
    surface.blit(p_hp_surf, (margin_x + 10, bar_y + (bar_h - p_hp_surf.get_height()) // 2))

    # Player Sub-Bar: Flask, Kunai, and Active Bounce Back Buffs
    sub_y = bar_y + bar_h + 8

    # Flask Status
    if p["heal_used"]:
        flask_str = "[E] FLASK: EMPTY"
        flask_col = (110, 100, 95)
    elif is_enraged:
        flask_str = "[E] FLASK: LOCKED (ENRAGED!)"
        flask_col = (235, 60, 60)
    elif p["state"] == "heal":
        flask_str = f"[E] HEALING... ({p['heal_timer'] // 60 + 1}s)"
        flask_col = (90, 245, 130)
    else:
        flask_str = "[E] FLASK: READY (+50% HP)"
        flask_col = (95, 225, 120)

    f_surf = font_hud_info.render(flask_str, True, flask_col)
    surface.blit(f_surf, (margin_x, sub_y))

    # Rechargeable Kunai Display
    kunai_str = f"KUNAI [Q]: {'◆ ' * p['kunai_count']}{'◇ ' * (p['kunai_max'] - p['kunai_count'])}"
    k_col = (220, 200, 140) if p["kunai_count"] > 0 else (130, 120, 110)
    k_surf = font_hud_info.render(kunai_str, True, k_col)
    surface.blit(k_surf, (margin_x + int(bar_w * 0.50), sub_y))

    # Active Bounce Back Buff Indicators
    buff_badges = []
    if player_hp_buff > 0:
        buff_badges.append(f"[+30 HP BUFF]")
    if player_speed_buff:
        buff_badges.append(f"[+25% SPEED BUFF]")
    if buff_badges:
        b_str = "  ".join(buff_badges)
        b_surf = font_hud_info.render(b_str, True, (255, 215, 80))
        surface.blit(b_surf, (margin_x, sub_y + 18))

    # --- 2. CROSSED SWORDS CREST (CENTER) ---
    center_y = bar_y + bar_h // 2 + 6
    draw_crossed_swords(surface, center_x, center_y, radius=int(bar_h * 0.95))

    # --- 3. BOSS HEALTH & POSTURE BAR (RIGHT) ---
    b_x = W - margin_x - bar_w
    b["displayed_hp"] += (b["hp"] - b["displayed_hp"]) * 0.12
    b_pct = max(0.0, min(1.0, b["hp"] / b["max_hp"]))
    b_lag_pct = max(0.0, min(1.0, b["displayed_hp"] / b["max_hp"]))

    # Boss Name, Title, and Phase Tag
    p_tag = " [PHASE III: ENRAGED]" if boss_phase == 3 else (" [PHASE II: RED MIST]" if boss_phase == 2 else " [PHASE I]")
    p_tag_col = (255, 60, 60) if boss_phase == 3 else ((255, 150, 70) if boss_phase == 2 else (210, 195, 160))
    b_name_surf = font_bar_name.render(b["name"], True, (245, 225, 205))
    b_tag_surf = font_hud_info.render(p_tag, True, p_tag_col)

    surface.blit(b_name_surf, (b_x + bar_w - b_name_surf.get_width() - b_tag_surf.get_width() - 8, bar_y - int(H * 0.034)))
    surface.blit(b_tag_surf, (b_x + bar_w - b_tag_surf.get_width(), bar_y - int(H * 0.031)))

    b_bg_rect = pygame.Rect(b_x, bar_y, bar_w, bar_h)
    draw_feudal_panel(surface, b_bg_rect, border_col=(140, 32, 28) if is_enraged else (100, 30, 25), bg_col=(18, 10, 10, 230))

    if b_lag_pct > 0:
        lag_rect = pygame.Rect(b_x + 3, bar_y + 3, int((bar_w - 6) * b_lag_pct), bar_h - 6)
        pygame.draw.rect(surface, (215, 160, 60), lag_rect)

    if b_pct > 0:
        fill_w = int((bar_w - 6) * b_pct)
        fill_rect = pygame.Rect(b_x + 3, bar_y + 3, fill_w, bar_h - 6)
        boss_fill_col = (220, 25, 25) if is_enraged else (165, 30, 26)
        pygame.draw.rect(surface, boss_fill_col, fill_rect)

    b_hp_str = f"{b['hp']} / {b['max_hp']} HP"
    b_hp_surf = font_bar_val.render(b_hp_str, True, (255, 245, 235))
    surface.blit(b_hp_surf, (b_x + bar_w - b_hp_surf.get_width() - 10, bar_y + (bar_h - b_hp_surf.get_height()) // 2))

    # --- 4. BOSS POSTURE / STAGGER METER ---
    posture_h = int(H * 0.010)
    posture_y = sub_y + 2
    posture_rect = pygame.Rect(b_x, posture_y, bar_w, posture_h)
    pygame.draw.rect(surface, (14, 10, 10), posture_rect)
    pygame.draw.rect(surface, (90, 70, 45), posture_rect, 1)

    posture_pct = max(0.0, min(1.0, b["posture"] / b["max_posture"]))
    if posture_pct > 0:
        p_fill_w = int((bar_w - 2) * posture_pct)
        p_col = (255, 80, 50) if posture_pct >= 0.85 else (235, 175, 45)
        pygame.draw.rect(surface, p_col, pygame.Rect(b_x + 1, posture_y + 1, p_fill_w, posture_h - 2))

    # Posture Label
    p_label = "POSTURE: BROKEN!" if b["is_stunned"] else f"POSTURE ({int(b['posture'])}%)"
    p_label_col = (255, 75, 75) if b["is_stunned"] else (190, 170, 140)
    p_lbl_surf = font_hud_info.render(p_label, True, p_label_col)
    surface.blit(p_lbl_surf, (b_x, posture_y + posture_h + 3))


# ---------------------------------------------------------------------------
# Guide Content Data
# ---------------------------------------------------------------------------
GUIDE_SECTIONS = [
    {
        "title": "BEST OF 5 (BO5) SYSTEM & BOUNCE BACK BUFFS",
        "color": (255, 225, 120),
        "lines": [
            "  • Format          : Best of 5 rounds. First to win 3 rounds claims victory!",
            "  • 1st Loss Buff   : Suffer a round loss to receive a permanent +30 Max HP Buff (BOUNCE BACK)!",
            "  • 2nd Loss Buff   : Suffer a second loss to gain +25% Movement Speed and +25% Attack Speed (FINAL BOUNCE BACK)!",
            "  • 3rd Loss Defeat : If the Magistrate claims 3 rounds, he wins the match.",
        ]
    },
    {
        "title": "COMBAT CONTROLS (ALWAYS-ACTIVE +20% HIT SPEED)",
        "color": (235, 185, 90),
        "lines": [
            "  [ A ] / [ D ]  : Movement (Left / Right across the battlefield)",
            "  [ W ]          : Jump (Leap over ground smash shockwaves)",
            "  [ Left Shift ] : Dodge / Roll (Full invulnerability frames through attacks)",
            "  [ Right Shift ]: Sword Slash (High-speed 20% faster combo, builds posture damage)",
            "  [ Q ]          : Throw Kunai (20% faster projectile, pouch holds 3, auto-recharges every 4s)",
            "  [ F ]          : Parry (Perfect deflect triggers golden sparks, sound, & +25 Posture Damage!)",
            "                   Mistimed parry acts as a NORMAL BLOCK (mitigates 60% damage).",
            "  [ E ]          : Healing Flask (Heals 50% HP over 2s, 1 use per round; LOCKED during Enraged Mode!)",
            "  [ Spacebar ]   : Combat Guide / Pause",
            "  [ Esc ]        : Return to Menu / Exit Game",
        ]
    },
    {
        "title": "SOULSLIKE BOSS PHASES & REBALANCED DAMAGE",
        "color": (235, 110, 95),
        "lines": [
            "  • Phase I  (100% - 66% HP): Tactical pacing. Spear throws at range, greatsword slams close.",
            "  • Phase II (66% - 33% HP) : Red Mist awakens! Magistrate speeds up with +25% damage.",
            "  • Phase III (<= 33% HP / Enraged <= 10%): 5.5-second dark roar transition! Attacks 70% faster,",
            "                              healing flask locked, red glowing outline active!",
            "  • Balance Adjustments     : Boss sword damage decreased by 20%, spear damage decreased by 10%.",
        ]
    },
    {
        "title": "DEVELOPER TESTING KEYS",
        "color": (160, 200, 240),
        "lines": [
            "  [ T ] : Strike Magistrate (-200 HP from boss to test damage, posture, & rounds)",
        ]
    }
]


def draw_button(surface, rect, text, is_hover, primary_col=(130, 32, 28), border_col=(212, 163, 75)):
    """Draws a feudal plaque button with gold corners and calligraphy styling."""
    bg = (min(primary_col[0] + 35, 255), min(primary_col[1] + 25, 255), min(primary_col[2] + 20, 255)) if is_hover else primary_col
    draw_feudal_panel(surface, rect, border_col=border_col, bg_col=bg, gold_corners=True)

    txt_surf = font_btn.render(text, True, (255, 245, 220) if is_hover else (235, 220, 195))
    surface.blit(txt_surf, txt_surf.get_rect(center=rect.center))


# ---------------------------------------------------------------------------
# Main Game Loop State
# ---------------------------------------------------------------------------
game_state = "MENU"   # "MENU", "CONTROLS", "PLAYING", "ROUND_WON", "BOUNCE_BACK", "FINAL_BOUNCE_BACK", "MATCH_VICTORY", "MATCH_DEFEAT"
scroll_y = 0
frame_count = 0
running = True

btn_w = int(W * 0.28)
btn_h = int(H * 0.060)
btn_x = (W - btn_w) // 2

btn_start_rect = pygame.Rect(btn_x, int(H * 0.52), btn_w, btn_h)
btn_guide_rect = pygame.Rect(btn_x, int(H * 0.62), btn_w, btn_h)
btn_exit_rect = pygame.Rect(btn_x, int(H * 0.72), btn_w, btn_h)

btn_back_rect = pygame.Rect(int(W * 0.05), int(H * 0.90), int(W * 0.16), int(H * 0.055))

# Round End Buttons (3 Options: Continue / Reset / Menu)
btn_continue_rect = pygame.Rect(btn_x, int(H * 0.52), btn_w, btn_h)
btn_reset_rect = pygame.Rect(btn_x, int(H * 0.61), btn_w, btn_h)
btn_menu_rect = pygame.Rect(btn_x, int(H * 0.70), btn_w, btn_h)


# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------
while running:
    frame_count += 1
    events = pygame.event.get()
    mouse_pos = pygame.mouse.get_pos()
    mouse_clicked = False

    for event in events:
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state in ("PLAYING", "CONTROLS", "ROUND_WON", "BOUNCE_BACK", "FINAL_BOUNCE_BACK", "MATCH_VICTORY", "MATCH_DEFEAT"):
                    reset_full_match()
                    game_state = "MENU"
                elif game_state == "MENU":
                    running = False

            if event.key == pygame.K_SPACE:
                if game_state == "PLAYING":
                    game_state = "CONTROLS"
                elif game_state == "CONTROLS":
                    game_state = "PLAYING"
                elif game_state in ("ROUND_WON", "BOUNCE_BACK", "FINAL_BOUNCE_BACK"):
                    start_next_round()
                elif game_state in ("MATCH_VICTORY", "MATCH_DEFEAT"):
                    reset_full_match()

            if event.key == pygame.K_RETURN:
                if game_state in ("ROUND_WON", "BOUNCE_BACK", "FINAL_BOUNCE_BACK"):
                    start_next_round()
                elif game_state in ("MATCH_VICTORY", "MATCH_DEFEAT"):
                    reset_full_match()

            if event.key == pygame.K_r:
                if game_state in ("ROUND_WON", "BOUNCE_BACK", "FINAL_BOUNCE_BACK", "MATCH_VICTORY", "MATCH_DEFEAT"):
                    reset_full_match()

            # The ONLY remaining testing key: [T] Deletes 200 HP from the boss
            if game_state == "PLAYING":
                if event.key == pygame.K_t:
                    boss["hp"] = max(0, boss["hp"] - 200)
                    boss["posture"] = min(100.0, boss["posture"] + 25.0)
                    play_sfx("slash_hit", 0.9)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_clicked = True

        if event.type == pygame.MOUSEWHEEL and game_state == "CONTROLS":
            scroll_y = max(-350, min(0, scroll_y + event.y * 30))

    # -----------------------------------------------------------------------
    # 1. State: MENU
    # -----------------------------------------------------------------------
    if game_state == "MENU":
        screen.blit(bg, (0, 0))

        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((14, 10, 8, 175))
        screen.blit(dim, (0, 0))

        # Title Emblem
        t_surf = font_title.render("SHINOBI : LEGEND OF ZHAO", True, (245, 225, 185))
        t_shadow = font_title.render("SHINOBI : LEGEND OF ZHAO", True, (20, 8, 8))
        t_rect = t_surf.get_rect(center=(W // 2, int(H * 0.24)))
        screen.blit(t_shadow, (t_rect.x + 3, t_rect.y + 3))
        screen.blit(t_surf, t_rect)

        sub_surf = font_sub.render("Best of 5 Combat  •  The Hollow Magistrate Boss Encounter", True, (212, 163, 75))
        screen.blit(sub_surf, sub_surf.get_rect(center=(W // 2, int(H * 0.32))))

        draw_crossed_swords(screen, W // 2, int(H * 0.41), radius=int(H * 0.045))

        draw_button(screen, btn_start_rect, "START BEST-OF-5 MATCH", btn_start_rect.collidepoint(mouse_pos), primary_col=(140, 32, 28))
        draw_button(screen, btn_guide_rect, "COMBAT GUIDE & CONTROLS", btn_guide_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))
        draw_button(screen, btn_exit_rect, "EXIT TO DESKTOP", btn_exit_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        if mouse_clicked:
            if btn_start_rect.collidepoint(mouse_pos):
                reset_full_match()
                game_state = "PLAYING"
            elif btn_guide_rect.collidepoint(mouse_pos):
                game_state = "CONTROLS"
                scroll_y = 0
            elif btn_exit_rect.collidepoint(mouse_pos):
                running = False

    # -----------------------------------------------------------------------
    # 2. State: CONTROLS
    # -----------------------------------------------------------------------
    elif game_state == "CONTROLS":
        screen.blit(bg, (0, 0))
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((16, 12, 10, 225))
        screen.blit(dim, (0, 0))

        content_box = pygame.Rect(int(W * 0.08), int(H * 0.06), int(W * 0.84), int(H * 0.80))
        draw_feudal_panel(screen, content_box, border_col=(140, 32, 28), bg_col=(20, 14, 12, 240))

        g_title = font_guide_head.render("HAVEN HACKATHON — SHINOBI COMBAT MANUAL", True, (245, 225, 185))
        screen.blit(g_title, g_title.get_rect(center=(W // 2, int(H * 0.12))))
        pygame.draw.line(screen, (212, 163, 75), (int(W * 0.15), int(H * 0.16)), (int(W * 0.85), int(H * 0.16)), 2)

        clip_area = pygame.Rect(int(W * 0.10), int(H * 0.18), int(W * 0.80), int(H * 0.65))
        screen.set_clip(clip_area)

        curr_y = int(H * 0.19) + scroll_y
        for sec in GUIDE_SECTIONS:
            sec_surf = font_guide_sec.render(sec["title"], True, sec["color"])
            screen.blit(sec_surf, (int(W * 0.12), curr_y))
            curr_y += int(H * 0.038)

            for line in sec["lines"]:
                line_surf = font_guide_text.render(line, True, (225, 215, 200))
                screen.blit(line_surf, (int(W * 0.14), curr_y))
                curr_y += int(H * 0.027)
            curr_y += int(H * 0.020)

        screen.set_clip(None)

        draw_button(screen, btn_back_rect, "< RETURN", btn_back_rect.collidepoint(mouse_pos), primary_col=(130, 32, 28))
        hint_surf = font_bar_val.render("Use Mouse Wheel to Scroll  |  Press [SPACE] or [ESC] to Return", True, (190, 175, 150))
        screen.blit(hint_surf, hint_surf.get_rect(center=(W // 2, int(H * 0.93))))

        if mouse_clicked and btn_back_rect.collidepoint(mouse_pos):
            game_state = "PLAYING" if player["hp"] > 0 else "MENU"

    # -----------------------------------------------------------------------
    # 3. State: PLAYING
    # -----------------------------------------------------------------------
    elif game_state == "PLAYING":
        p = player
        b = boss
        keys = pygame.key.get_pressed()

        # Phase Calculation
        is_enraged = (b["hp"] <= b["max_hp"] * 0.10)
        if is_enraged or b["hp"] <= b["max_hp"] * 0.33:
            boss_phase = 3
        elif b["hp"] <= b["max_hp"] * 0.66:
            boss_phase = 2
        else:
            boss_phase = 1

        # Enraged Mode Transition (5.5s dark roar sequence)
        if is_enraged and not b["enraged_triggered"]:
            b["enraged_triggered"] = True
            b["state"] = "enrage_intro"
            b["enrage_intro_timer"] = 330
            b["frame_idx"] = 0
            b["tick_count"] = 0
            b["vx"] = 0.0
            play_sfx("ground_slam", 0.8)

        # Posture Decay
        if b["posture"] > 0 and not b["is_stunned"]:
            b["posture_decay_delay"] += 1
            if b["posture_decay_delay"] >= 180:
                b["posture"] = max(0.0, b["posture"] - (4.0 / 60.0))

        # Posture Break Stun
        if b["posture"] >= b["max_posture"] and not b["is_stunned"]:
            b["is_stunned"] = True
            b["stun_timer"] = 210
            b["state"] = "stunned"
            b["frame_idx"] = 0
            b["vx"] = 0.0
            ground_shake_timer = 20
            ground_shake_intensity = 14.0
            play_sfx("posture_break", 1.0)

        # Screen Shake Update
        shake_x, shake_y = 0, 0
        if ground_shake_timer > 0:
            ground_shake_timer -= 1
            decay = ground_shake_timer / 120.0
            cur_intensity = ground_shake_intensity * min(1.0, decay + 0.25)
            shake_x = random.randint(int(-cur_intensity), int(cur_intensity))
            shake_y = random.randint(int(-cur_intensity), int(cur_intensity))

        # Clouds & Smoke
        for c in clouds:
            c["x"] += c["speed"]
            if c["x"] > W + 200:
                c["x"] = -300
                c["y"] = random.randint(0, int(H * 0.12))

        for smk in smoke_particles:
            smk["x"] += smk["vx"]
            smk["y"] += smk["vy"]
            smk["age"] += 1
            if smk["age"] >= smk["life"]:
                smoke_particles.remove(smk)
                smoke_particles.append(new_smoke())

        if boss_phase >= 2:
            spawn_red_mist(b["x"], b["y"], count=3 if boss_phase == 3 else 1)

        for rm in list(red_mist_particles):
            rm["x"] += rm["vx"]
            rm["y"] += rm["vy"]
            rm["radius"] += 0.35
            rm["life"] -= 1
            if rm["life"] <= 0:
                red_mist_particles.remove(rm)

        for spk in list(sparks):
            spk["x"] += spk["vx"]
            spk["y"] += spk["vy"]
            spk["vy"] += 0.35
            spk["life"] -= 1
            if spk["life"] <= 0:
                sparks.remove(spk)

        # Kunai Pouch Recharge
        if p["kunai_count"] < p["kunai_max"]:
            p["kunai_recharge_timer"] += 1
            if p["kunai_recharge_timer"] >= 240:
                p["kunai_count"] += 1
                p["kunai_recharge_timer"] = 0

        # --- PLAYER MOVEMENT & ACTIONS ---
        # Base hit speed is increased by 20% ALWAYS; +25% more if player_speed_buff is active!
        player_hit_speed_mult = 1.45 if player_speed_buff else 1.20
        player_move_speed = (BASE_MOVE_SPEED * 1.25) if player_speed_buff else BASE_MOVE_SPEED

        p["is_blocking"] = False

        if p["state"] in ("dodge", "slash", "parry", "kunai", "heal"):
            p["tick_count"] += 1

            if p["state"] == "heal":
                p["heal_timer"] -= 1
                if p["tick_count"] >= 4:
                    p["tick_count"] = 0
                    p["frame_idx"] = (p["frame_idx"] + 1) % len(player_heal_frames)

                if p["heal_timer"] <= 0:
                    p["hp"] = min(p["max_hp"], p["hp"] + int(p["max_hp"] * 0.50))
                    p["state"] = "idle"
                    p["frame_idx"] = 0
                    p["tick_count"] = 0
                    play_sfx("heal_spell", 0.9)

            elif p["state"] == "dodge":
                dodge_vx = (player_move_speed * 1.6) if p["facing_right"] else (-player_move_speed * 1.6)
                p["x"] += dodge_vx
                if p["tick_count"] >= 1:
                    p["tick_count"] = 0
                    p["frame_idx"] += 1
                    if p["frame_idx"] >= len(dodge_frames):
                        p["state"] = "idle"
                        p["frame_idx"] = 0

            elif p["state"] == "slash":
                # Advance 20% faster (always active) + bounce back buff!
                prev_idx = p["frame_idx"]
                p["anim_time"] += player_hit_speed_mult
                new_idx = int(p["anim_time"])
                p["frame_idx"] = new_idx

                # Strike hits at frame 14
                if prev_idx < 14 and new_idx >= 14:
                    play_sfx("slash_hit", 0.8)
                    dist = abs(p["x"] - b["x"])
                    facing_boss = (b["x"] > p["x"] and p["facing_right"]) or (b["x"] < p["x"] and not p["facing_right"])
                    if dist < int(W * 0.16) and facing_boss:
                        if b["is_stunned"]:
                            # CRITICAL STRIKE!
                            b["hp"] = max(0, b["hp"] - 250)
                            b["is_stunned"] = False
                            b["stun_timer"] = 0
                            b["posture"] = 0.0
                            ground_shake_timer = 20
                            ground_shake_intensity = 16.0
                            spawn_sparks(b["x"], b["y"] - boss_h * 0.5, count=30, is_golden=True)
                            play_sfx("slash_hit", 1.0)
                        else:
                            b["hp"] = max(0, b["hp"] - 35)
                            b["posture"] = min(b["max_posture"], b["posture"] + 8.0)
                            b["posture_decay_delay"] = 0
                            spawn_sparks(b["x"], b["y"] - boss_h * 0.5, count=8, is_golden=False)

                if p["frame_idx"] >= len(slash_frames):
                    p["state"] = "idle"
                    p["frame_idx"] = 0
                    p["anim_time"] = 0.0

            elif p["state"] == "parry":
                if p["tick_count"] >= 1:
                    p["tick_count"] = 0
                    p["frame_idx"] += 1
                    if p["frame_idx"] >= len(parry_frames):
                        p["state"] = "idle"
                        p["frame_idx"] = 0

            elif p["state"] == "kunai":
                prev_idx = p["frame_idx"]
                p["anim_time"] += player_hit_speed_mult
                new_idx = int(p["anim_time"])
                p["frame_idx"] = new_idx

                if prev_idx < 15 and new_idx >= 15 and not p["kunai_spawned"]:
                    p["kunai_spawned"] = True
                    cur_k_speed = (BASE_KUNAI_SPEED * 1.25) if player_speed_buff else BASE_KUNAI_SPEED
                    k_vx = cur_k_speed if p["facing_right"] else -cur_k_speed
                    spawn_x = p["x"] + (int(player_h * 0.35) if p["facing_right"] else -int(player_h * 0.35))
                    spawn_y = p["y"] - int(player_h * 0.45)
                    projectiles.append({
                        "x": spawn_x,
                        "y": spawn_y,
                        "vx": k_vx,
                        "type": "kunai",
                        "owner": "player",
                        "facing_right": p["facing_right"],
                        "damage": 22,
                        "active": True,
                    })
                    play_sfx("kunai_throw", 0.7)

                if p["frame_idx"] >= len(player_kunai_frames):
                    p["state"] = "idle"
                    p["frame_idx"] = 0
                    p["anim_time"] = 0.0
                    p["kunai_spawned"] = False

        else:
            # Action Triggers
            if keys[pygame.K_e] and not p["heal_used"] and not is_enraged:
                p["heal_used"] = True
                p["state"] = "heal"
                p["heal_timer"] = 120
                p["frame_idx"] = 0
                p["tick_count"] = 0

            elif keys[pygame.K_LSHIFT]:
                p["state"] = "dodge"
                p["frame_idx"] = 0
                p["tick_count"] = 0

            elif keys[pygame.K_RSHIFT]:
                p["state"] = "slash"
                p["frame_idx"] = 0
                p["anim_time"] = 0.0
                p["tick_count"] = 0

            elif keys[pygame.K_f]:
                p["state"] = "parry"
                p["frame_idx"] = 0
                p["tick_count"] = 0

            elif keys[pygame.K_q] and p["kunai_count"] > 0:
                p["kunai_count"] -= 1
                p["state"] = "kunai"
                p["frame_idx"] = 0
                p["anim_time"] = 0.0
                p["tick_count"] = 0
                p["kunai_spawned"] = False

            else:
                # Movement
                dx = 0
                if keys[pygame.K_a]:
                    dx -= player_move_speed
                    p["facing_right"] = False
                if keys[pygame.K_d]:
                    dx += player_move_speed
                    p["facing_right"] = True

                if dx != 0:
                    p["state"] = "walk"
                    p["x"] += dx
                    p["tick_count"] += 1
                    if p["tick_count"] >= 1:
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

            # Jump
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

        # --- BOSS (THE HOLLOW MAGISTRATE) FLUID AI & BEHAVIOR ---
        if b["is_stunned"]:
            b["stun_timer"] -= 1
            b["vx"] = 0.0
            if b["stun_timer"] <= 0:
                b["is_stunned"] = False
                b["posture"] = 0.0
                b["state"] = "idle"

        elif b["state"] == "enrage_intro":
            b["vx"] = 0.0
            b["enrage_intro_timer"] -= 1
            progress = (330 - b["enrage_intro_timer"]) / 330.0
            b["frame_idx"] = min(len(boss_enrage_frames) - 1, int(progress * len(boss_enrage_frames)))

            if frame_count % 4 == 0:
                ground_shake_timer = 4
                ground_shake_intensity = 6.0

            if b["enrage_intro_timer"] <= 0:
                b["state"] = "idle"
                b["frame_idx"] = 0
                b["tick_count"] = 0

        elif b["state"] in ("smash", "spear", "kunai"):
            # Ease velocity to plant feet smoothly before striking
            b["vx"] *= 0.5
            b["x"] += b["vx"]

            if b["state"] == "smash":
                tick_interval = 1 if boss_phase == 3 else (2 if b["frame_idx"] < 17 else 1)
            else:
                tick_interval = 1 if boss_phase == 3 else 2

            b["tick_count"] += 1
            if b["tick_count"] >= tick_interval:
                b["tick_count"] = 0
                b["frame_idx"] += 1

                if b["state"] == "smash":
                    if b["frame_idx"] == 16:
                        ground_shake_timer = 120
                        ground_shake_intensity = 22.0
                        play_sfx("ground_slam", 1.0)

                        if not b["smash_hit"]:
                            b["smash_hit"] = True
                            dist_to_player = abs(b["x"] - p["x"])
                            if dist_to_player < int(W * 0.18) and p["on_ground"]:
                                # BOSS SWORD DAMAGE: DECREASED BY 20% (36 / 30 / 24, down from 45 / 38 / 30)
                                base_dmg = 36 if boss_phase == 3 else (30 if boss_phase == 2 else 24)

                                if p["state"] == "dodge":
                                    pass
                                elif p["state"] == "parry" and p["frame_idx"] <= 14:
                                    # PERFECT PARRY!
                                    play_sfx("parry_metal", 1.0)
                                    ground_shake_timer = 14
                                    ground_shake_intensity = 10.0
                                    spawn_sparks(p["x"], p["y"] - player_h * 0.5, count=24, is_golden=True)
                                    b["posture"] = min(b["max_posture"], b["posture"] + 25.0)
                                    b["posture_decay_delay"] = 0
                                elif p["state"] == "parry":
                                    # NORMAL BLOCK (mitigates 60% of damage!)
                                    play_sfx("block_wood", 0.9)
                                    p["hp"] = max(0, p["hp"] - int(base_dmg * 0.40))
                                    spawn_sparks(p["x"], p["y"] - player_h * 0.5, count=8, is_golden=False)
                                else:
                                    p["hp"] = max(0, p["hp"] - base_dmg)

                    if b["frame_idx"] >= len(boss_smash_frames):
                        b["state"] = "idle"
                        b["frame_idx"] = 0
                        b["tick_count"] = 0

                elif b["state"] == "spear":
                    if b["frame_idx"] == 16 and not b["projectile_spawned"]:
                        b["projectile_spawned"] = True
                        base_sp_speed = 17.0
                        sp_speed = int(base_sp_speed * 1.30) if boss_phase == 3 else base_sp_speed
                        sp_vx = sp_speed if b["facing_right"] else -sp_speed
                        spawn_x = b["x"] + (int(boss_h * 0.40) if b["facing_right"] else -int(boss_h * 0.40))
                        spawn_y = b["y"] - int(boss_h * 0.55)
                        # BOSS SPEAR DAMAGE: DECREASED BY 10% (34 / 28 / 22, down from 38 / 32 / 25)
                        projectiles.append({
                            "x": spawn_x,
                            "y": spawn_y,
                            "vx": sp_vx,
                            "type": "spear",
                            "owner": "boss",
                            "facing_right": b["facing_right"],
                            "damage": 34 if boss_phase == 3 else (28 if boss_phase == 2 else 22),
                            "active": True,
                        })
                        play_sfx("kunai_throw", 0.9)

                    if b["frame_idx"] >= len(boss_spear_frames):
                        b["state"] = "idle"
                        b["frame_idx"] = 0
                        b["tick_count"] = 0
                        b["projectile_spawned"] = False

                elif b["state"] == "kunai":
                    if b["frame_idx"] == 14 and not b["projectile_spawned"]:
                        b["projectile_spawned"] = True
                        base_k_speed = 22.0
                        k_speed = int(base_k_speed * 1.30) if boss_phase == 3 else base_k_speed
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
                            "damage": 22 if boss_phase == 3 else (18 if boss_phase == 2 else 15),
                            "active": True,
                        })
                        play_sfx("kunai_throw", 0.7)

                    if b["frame_idx"] >= len(boss_spear_frames):
                        b["state"] = "idle"
                        b["frame_idx"] = 0
                        b["tick_count"] = 0
                        b["projectile_spawned"] = False

        else:
            # Boss Attack Decisions
            b["attack_cooldown"] -= 1.0 / 60.0
            if b["attack_cooldown"] <= 0:
                base_cd = random.uniform(3.0, 4.8)
                if boss_phase == 3:
                    b["attack_cooldown"] = base_cd * 0.30
                elif boss_phase == 2:
                    b["attack_cooldown"] = base_cd * 0.70
                else:
                    b["attack_cooldown"] = base_cd

                dist = abs(b["x"] - p["x"])
                is_far = dist > (W * 0.25)

                b["facing_right"] = (p["x"] > b["x"])
                b["vx"] = 0.0

                if is_far:
                    b["state"] = "spear"
                    b["frame_idx"] = 0
                    b["tick_count"] = 0
                    b["projectile_spawned"] = False
                else:
                    chosen_atk = random.choice(["smash", "kunai"])
                    b["state"] = chosen_atk
                    b["frame_idx"] = 0
                    b["tick_count"] = 0
                    b["projectile_spawned"] = False
                    b["smash_hit"] = False

            else:
                # Fluid Patrol & Motion Smoothing
                b["action_timer"] -= 1.0 / 60.0
                if b["action_timer"] <= 0:
                    b["action_timer"] = random.uniform(1.0, 3.8)
                    b["walk_dir"] = random.choice([-1, 0, 1])

                # Smooth velocity easing
                target_speed = (3.4 if boss_phase == 3 else 2.2) * b["walk_dir"]
                b["vx"] += (target_speed - b["vx"]) * 0.12
                b["x"] += b["vx"]

                if abs(b["vx"]) > 0.35:
                    b["state"] = "walk"
                    b["facing_right"] = (b["vx"] > 0)
                else:
                    b["state"] = "idle"

                # Arena Boundaries with soft dampening
                min_bx = int(W * 0.18)
                max_bx = int(W * 0.94)
                if b["x"] < min_bx:
                    b["x"] = min_bx
                    b["walk_dir"] = 1
                    b["vx"] = abs(b["vx"]) * 0.4
                    b["facing_right"] = True
                elif b["x"] > max_bx:
                    b["x"] = max_bx
                    b["walk_dir"] = -1
                    b["vx"] = -abs(b["vx"]) * 0.4
                    b["facing_right"] = False

                # Continuous fluid animation stepping
                step_rate = (0.50 if boss_phase == 3 else 0.36) if b["state"] == "walk" else (0.40 if boss_phase == 3 else 0.28)
                b["anim_time"] += step_rate
                if b["state"] == "walk":
                    b["frame_idx"] = int(b["anim_time"]) % len(boss_walk_frames)
                else:
                    b["frame_idx"] = int(b["anim_time"]) % len(boss_idle_frames)

        # --- PROJECTILE COLLISION & PARRIES ---
        for proj in list(projectiles):
            proj["x"] += proj["vx"]

            if proj["x"] < -100 or proj["x"] > W + 100:
                proj["active"] = False

            if proj["active"]:
                if proj["owner"] == "player":
                    if abs(proj["x"] - b["x"]) < int(boss_h * 0.28) and abs(proj["y"] - (b["y"] - boss_h * 0.50)) < int(boss_h * 0.40):
                        proj["active"] = False
                        b["hp"] = max(0, b["hp"] - proj["damage"])
                        b["posture"] = min(b["max_posture"], b["posture"] + 5.0)
                        b["posture_decay_delay"] = 0
                        spawn_sparks(proj["x"], proj["y"], count=10, is_golden=False)
                        play_sfx("slash_hit", 0.7)

                elif proj["owner"] == "boss":
                    if abs(proj["x"] - p["x"]) < int(player_h * 0.28) and abs(proj["y"] - (p["y"] - player_h * 0.50)) < int(player_h * 0.40):
                        if p["state"] == "dodge":
                            pass
                        elif p["state"] == "parry" and p["frame_idx"] <= 14:
                            # PERFECT PARRY ON PROJECTILE
                            proj["active"] = False
                            play_sfx("parry_metal", 1.0)
                            spawn_sparks(proj["x"], proj["y"], count=20, is_golden=True)
                            b["posture"] = min(b["max_posture"], b["posture"] + 18.0)
                            b["posture_decay_delay"] = 0
                        elif p["state"] == "parry":
                            # NORMAL BLOCK
                            proj["active"] = False
                            play_sfx("block_wood", 0.8)
                            p["hp"] = max(0, p["hp"] - int(proj["damage"] * 0.40))
                            spawn_sparks(proj["x"], proj["y"], count=6, is_golden=False)
                        else:
                            proj["active"] = False
                            p["hp"] = max(0, p["hp"] - proj["damage"])

            if not proj["active"]:
                projectiles.remove(proj)

        # --- BEST OF 5 ROUND OUTCOME DETECTION ---
        if b["hp"] <= 0:
            player_round_wins += 1
            if player_round_wins >= 3:
                game_state = "MATCH_VICTORY"
            else:
                game_state = "ROUND_WON"

        elif p["hp"] <= 0:
            boss_round_wins += 1
            if boss_round_wins >= 3:
                game_state = "MATCH_DEFEAT"
            elif boss_round_wins == 1:
                player_hp_buff = 30         # 1st loss: HP buff (+30 HP)
                game_state = "BOUNCE_BACK"
            elif boss_round_wins == 2:
                player_speed_buff = True     # 2nd loss: Movement & Attack Speed buff!
                game_state = "FINAL_BOUNCE_BACK"

        # --- RENDERING BATTLEFIELD ---
        screen.blit(bg, (shake_x, shake_y))

        for c in clouds:
            c_surf = cloud_variants[0]
            screen.blit(c_surf, (int(c["x"]) + shake_x, int(c["y"]) + shake_y))

        for smk in smoke_particles:
            smk_surf = smoke_variants[smk["variant"]]
            alpha = int(255 * (1.0 - smk["age"] / smk["life"]))
            smk_surf.set_alpha(alpha)
            screen.blit(smk_surf, (int(smk["x"]) + shake_x, int(smk["y"]) + shake_y))

        flag_f = (frame_count // 12) % 2
        f1_img = flag1_b if flag_f == 1 else flag1_a
        f2_img = flag2_b if flag_f == 1 else flag2_a
        screen.blit(f1_img, (flag1_x + shake_x, flag1_y + shake_y))
        screen.blit(f2_img, (flag2_x + shake_x, flag2_y + shake_y))

        for rm in red_mist_particles:
            rad = max(2, int(rm["radius"]))
            diam = rad * 2
            mist_surf = pygame.Surface((diam, diam), pygame.SRCALPHA)
            alpha = max(0, min(255, int(rm.get("alpha", 80))))
            pygame.draw.circle(mist_surf, (160, 20, 20, alpha), (rad, rad), rad)
            screen.blit(mist_surf, (int(rm["x"] - rad) + shake_x, int(rm["y"] - rad) + shake_y))

        # 1. Render Player
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

        # 2. Render Boss (The Hollow Magistrate)
        if b["state"] == "enrage_intro":
            b_sprite = boss_enrage_frames[b["frame_idx"] % len(boss_enrage_frames)]
            b_draw_x = int(b["x"] - be_center) + shake_x
            b_draw_y = int(b["y"] - be_feet) + shake_y
        elif b["state"] == "walk":
            b_sprite = boss_walk_frames[b["frame_idx"] % len(boss_walk_frames)]
            b_draw_x = int(b["x"] - bw_center) + shake_x
            b_draw_y = int(b["y"] - bw_feet) + shake_y
        elif b["state"] == "idle" or b["state"] == "stunned":
            b_sprite = boss_idle_frames[b["frame_idx"] % len(boss_idle_frames)]
            b_draw_x = int(b["x"] - bi_center) + shake_x
            b_draw_y = int(b["y"] - bi_feet) + shake_y
        elif b["state"] == "smash":
            b_sprite = boss_smash_frames[b["frame_idx"] % len(boss_smash_frames)]
            b_draw_x = int(b["x"] - bs_center) + shake_x
            b_draw_y = int(b["y"] - bs_feet) + shake_y
        elif b["state"] in ("spear", "kunai"):
            b_sprite = boss_spear_frames[b["frame_idx"] % len(boss_spear_frames)]
            b_draw_x = int(b["x"] - bsp_center) + shake_x
            b_draw_y = int(b["y"] - bsp_feet) + shake_y

        if not b["facing_right"]:
            b_sprite = pygame.transform.flip(b_sprite, True, False)

        if is_enraged and b["state"] != "enrage_intro":
            pulse = abs(math.sin(frame_count * 0.28))
            outline_alpha = int(140 + 115 * pulse)
            mask = pygame.mask.from_surface(b_sprite)
            outline_surf = mask.to_surface(setcolor=(255, 25, 25, outline_alpha), unsetcolor=(0, 0, 0, 0))
            for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)]:
                screen.blit(outline_surf, (b_draw_x + ox, b_draw_y + oy))

        screen.blit(b_sprite, (b_draw_x, b_draw_y))

        if b["is_stunned"]:
            st_text = font_stun_banner.render("★ POSTURE BROKEN — CRITICAL STRIKE! ★", True, (255, 220, 60))
            st_shadow = font_stun_banner.render("★ POSTURE BROKEN — CRITICAL STRIKE! ★", True, (20, 10, 5))
            st_rect = st_text.get_rect(center=(int(b["x"]) + shake_x, int(b["y"] - boss_h * 1.15) + shake_y))
            screen.blit(st_shadow, (st_rect.x + 2, st_rect.y + 2))
            screen.blit(st_text, st_rect)

        # 3. Render Sparks
        for spk in sparks:
            col = spk.get("color", (255, 220, 100))
            if isinstance(col, (tuple, list)) and len(col) >= 3 and isinstance(col[0], (int, float)):
                safe_col = (max(0, min(255, int(col[0]))), max(0, min(255, int(col[1]))), max(0, min(255, int(col[2]))))
            else:
                safe_col = (255, 220, 100)
            sz = max(1, int(spk.get("size", 2)))
            pygame.draw.circle(screen, safe_col, (int(spk["x"]) + shake_x, int(spk["y"]) + shake_y), sz)

        # 4. Render Projectiles
        for proj in projectiles:
            if proj["type"] == "kunai":
                k_img = kunai_item_right if proj["facing_right"] else kunai_item_left
                screen.blit(k_img, (int(proj["x"] - k_img.get_width() // 2) + shake_x, int(proj["y"] - k_img.get_height() // 2) + shake_y))
            elif proj["type"] == "spear":
                sp_img = spear_proj_right if proj["facing_right"] else spear_proj_left
                screen.blit(sp_img, (int(proj["x"] - sp_img.get_width() // 2) + shake_x, int(proj["y"] - sp_img.get_height() // 2) + shake_y))

        # 5. Render Health Bars & Feudal UI
        draw_health_bars(screen, p, b, boss_phase, is_enraged)

    # -----------------------------------------------------------------------
    # 4. State: ROUND_WON (Magistrate loses round, next round starting)
    # -----------------------------------------------------------------------
    elif game_state == "ROUND_WON":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((14, 10, 6, 215))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((W - int(W * 0.64)) // 2, int(H * 0.16), int(W * 0.64), int(H * 0.70))
        draw_feudal_panel(screen, box, border_col=(212, 163, 75), bg_col=(20, 14, 10, 245), gold_corners=True)

        rw_title = font_end_title.render("ROUND WON", True, (255, 220, 95))
        rw_shadow = font_end_title.render("ROUND WON", True, (20, 10, 5))
        rw_rect = rw_title.get_rect(center=(W // 2, int(H * 0.26)))
        screen.blit(rw_shadow, (rw_rect.x + 3, rw_rect.y + 3))
        screen.blit(rw_title, rw_rect)

        sub_str = f"Great General Zhao claims Round {current_round}! The next round is starting..."
        rw_sub = font_end_sub.render(sub_str, True, (240, 230, 200))
        screen.blit(rw_sub, rw_sub.get_rect(center=(W // 2, int(H * 0.35))))

        score_info = f"Current Match Score: Zhao {player_round_wins} — {boss_round_wins} Hollow Magistrate"
        rw_score = font_bar_val.render(score_info, True, (215, 185, 110))
        screen.blit(rw_score, rw_score.get_rect(center=(W // 2, int(H * 0.40))))

        draw_crossed_swords(screen, W // 2, int(H * 0.46), radius=int(H * 0.038))

        draw_button(screen, btn_continue_rect, f"CONTINUE TO ROUND {current_round + 1}", btn_continue_rect.collidepoint(mouse_pos), primary_col=(35, 120, 50))
        draw_button(screen, btn_reset_rect, "RESET MATCH", btn_reset_rect.collidepoint(mouse_pos), primary_col=(130, 32, 28))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        hint = font_bar_val.render("Press [ENTER] or [SPACE] to Continue  |  Press [R] to Reset Match  |  Press [ESC] for Menu", True, (200, 190, 160))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.78))))

        if mouse_clicked:
            if btn_continue_rect.collidepoint(mouse_pos):
                start_next_round()
            elif btn_reset_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_menu_rect.collidepoint(mouse_pos):
                reset_full_match()
                game_state = "MENU"

    # -----------------------------------------------------------------------
    # 5. State: BOUNCE_BACK (Player 1st Loss: Big letters + HP Buff)
    # -----------------------------------------------------------------------
    elif game_state == "BOUNCE_BACK":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((25, 6, 6, 225))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((W - int(W * 0.64)) // 2, int(H * 0.16), int(W * 0.64), int(H * 0.70))
        draw_feudal_panel(screen, box, border_col=(212, 163, 75), bg_col=(22, 10, 10, 245), gold_corners=True)

        bb_title = font_bounce_back.render("BOUNCE BACK", True, (255, 215, 80))
        bb_shadow = font_bounce_back.render("BOUNCE BACK", True, (30, 0, 0))
        bb_rect = bb_title.get_rect(center=(W // 2, int(H * 0.26)))
        screen.blit(bb_shadow, (bb_rect.x + 4, bb_rect.y + 4))
        screen.blit(bb_title, bb_rect)

        bb_sub = font_end_sub.render(f"General Zhao fell in Round {current_round}! Play again to receive an HP Buff (+30 Max HP)!", True, (240, 225, 200))
        screen.blit(bb_sub, bb_sub.get_rect(center=(W // 2, int(H * 0.35))))

        perk_msg = f"Perk Granted: Max HP boosted from 100 to 130 for Round {current_round + 1}!"
        bb_perk = font_bar_val.render(perk_msg, True, (110, 245, 130))
        screen.blit(bb_perk, bb_perk.get_rect(center=(W // 2, int(H * 0.40))))

        draw_crossed_swords(screen, W // 2, int(H * 0.46), radius=int(H * 0.038))

        draw_button(screen, btn_continue_rect, f"PLAY AGAIN WITH BUFF (ROUND {current_round + 1})", btn_continue_rect.collidepoint(mouse_pos), primary_col=(160, 30, 26))
        draw_button(screen, btn_reset_rect, "RESET MATCH", btn_reset_rect.collidepoint(mouse_pos), primary_col=(110, 28, 24))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        hint = font_bar_val.render("Press [ENTER] or [SPACE] to Play Again  |  Press [R] to Reset Match  |  Press [ESC] for Menu", True, (210, 180, 180))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.78))))

        if mouse_clicked:
            if btn_continue_rect.collidepoint(mouse_pos):
                start_next_round()
            elif btn_reset_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_menu_rect.collidepoint(mouse_pos):
                reset_full_match()
                game_state = "MENU"

    # -----------------------------------------------------------------------
    # 6. State: FINAL_BOUNCE_BACK (Player 2nd Loss: Movement & Atk Speed Buff)
    # -----------------------------------------------------------------------
    elif game_state == "FINAL_BOUNCE_BACK":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((30, 4, 4, 230))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((W - int(W * 0.64)) // 2, int(H * 0.16), int(W * 0.64), int(H * 0.70))
        draw_feudal_panel(screen, box, border_col=(255, 60, 60), bg_col=(24, 8, 8, 245), gold_corners=True)

        fbb_title = font_bounce_back.render("FINAL BOUNCE BACK", True, (255, 80, 60))
        fbb_shadow = font_bounce_back.render("FINAL BOUNCE BACK", True, (20, 0, 0))
        fbb_rect = fbb_title.get_rect(center=(W // 2, int(H * 0.26)))
        screen.blit(fbb_shadow, (fbb_rect.x + 4, fbb_rect.y + 4))
        screen.blit(fbb_title, fbb_rect)

        fbb_sub = font_end_sub.render(f"On the brink! Play again to receive Movement Speed & Attack Speed Buffs!", True, (255, 220, 200))
        screen.blit(fbb_sub, fbb_sub.get_rect(center=(W // 2, int(H * 0.35))))

        perk_msg = f"Perks Active: +30 Max HP  •  +25% Movement Speed  •  +25% Attack Speed!"
        fbb_perk = font_bar_val.render(perk_msg, True, (100, 240, 255))
        screen.blit(fbb_perk, fbb_perk.get_rect(center=(W // 2, int(H * 0.40))))

        draw_crossed_swords(screen, W // 2, int(H * 0.46), radius=int(H * 0.038))

        draw_button(screen, btn_continue_rect, f"PLAY AGAIN WITH BUFFS (ROUND {current_round + 1})", btn_continue_rect.collidepoint(mouse_pos), primary_col=(175, 30, 26))
        draw_button(screen, btn_reset_rect, "RESET MATCH", btn_reset_rect.collidepoint(mouse_pos), primary_col=(110, 28, 24))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        hint = font_bar_val.render("Press [ENTER] or [SPACE] to Play Again  |  Press [R] to Reset Match  |  Press [ESC] for Menu", True, (220, 180, 180))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.78))))

        if mouse_clicked:
            if btn_continue_rect.collidepoint(mouse_pos):
                start_next_round()
            elif btn_reset_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_menu_rect.collidepoint(mouse_pos):
                reset_full_match()
                game_state = "MENU"

    # -----------------------------------------------------------------------
    # 7. State: MATCH_DEFEAT (Player loses 3 rounds -> Magistrate Wins)
    # -----------------------------------------------------------------------
    elif game_state == "MATCH_DEFEAT":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((30, 5, 5, 235))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((W - int(W * 0.64)) // 2, int(H * 0.16), int(W * 0.64), int(H * 0.70))
        draw_feudal_panel(screen, box, border_col=(180, 32, 28), bg_col=(24, 8, 8, 250), gold_corners=True)

        d_title = font_end_title.render("THE MAGISTRATE WINS", True, (245, 45, 45))
        d_shadow = font_end_title.render("THE MAGISTRATE WINS", True, (15, 0, 0))
        d_rect = d_title.get_rect(center=(W // 2, int(H * 0.26)))
        screen.blit(d_shadow, (d_rect.x + 4, d_rect.y + 4))
        screen.blit(d_title, d_rect)

        d_sub = font_end_sub.render(f"The Hollow Magistrate has claimed 3 rounds to conquer the match! Will you try again?", True, (235, 200, 200))
        screen.blit(d_sub, d_sub.get_rect(center=(W // 2, int(H * 0.35))))

        score_info = f"Final Score: Hollow Magistrate {boss_round_wins} — {player_round_wins} Great General Zhao"
        d_score = font_bar_val.render(score_info, True, (215, 120, 110))
        screen.blit(d_score, d_score.get_rect(center=(W // 2, int(H * 0.40))))

        draw_crossed_swords(screen, W // 2, int(H * 0.46), radius=int(H * 0.038))

        draw_button(screen, btn_continue_rect, "TRY AGAIN (RESET MATCH)", btn_continue_rect.collidepoint(mouse_pos), primary_col=(175, 30, 26))
        draw_button(screen, btn_reset_rect, "NEW GAME", btn_reset_rect.collidepoint(mouse_pos), primary_col=(110, 28, 24))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        hint = font_bar_val.render("Press [R] or [ENTER] to Try Again  |  Press [ESC] for Main Menu", True, (200, 160, 160))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.78))))

        if mouse_clicked:
            if btn_continue_rect.collidepoint(mouse_pos) or btn_reset_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_menu_rect.collidepoint(mouse_pos):
                reset_full_match()
                game_state = "MENU"

    # -----------------------------------------------------------------------
    # 8. State: MATCH_VICTORY (Player wins 3 rounds -> Zhao claims triumph)
    # -----------------------------------------------------------------------
    elif game_state == "MATCH_VICTORY":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((14, 10, 6, 220))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((W - int(W * 0.64)) // 2, int(H * 0.16), int(W * 0.64), int(H * 0.70))
        draw_feudal_panel(screen, box, border_col=(212, 163, 75), bg_col=(20, 14, 10, 250), gold_corners=True)

        v_title = font_end_title.render("MATCH VICTORY", True, (255, 220, 95))
        v_shadow = font_end_title.render("MATCH VICTORY", True, (20, 10, 5))
        v_rect = v_title.get_rect(center=(W // 2, int(H * 0.26)))
        screen.blit(v_shadow, (v_rect.x + 3, v_rect.y + 3))
        screen.blit(v_title, v_rect)

        v_sub = font_end_sub.render(f"Great General Zhao claims match triumph ({player_round_wins} - {boss_round_wins})! The Magistrate is vanquished!", True, (240, 230, 200))
        screen.blit(v_sub, v_sub.get_rect(center=(W // 2, int(H * 0.35))))

        score_info = f"Final Score: Great General Zhao {player_round_wins} — {boss_round_wins} The Hollow Magistrate"
        v_score = font_bar_val.render(score_info, True, (212, 185, 90))
        screen.blit(v_score, v_score.get_rect(center=(W // 2, int(H * 0.40))))

        draw_crossed_swords(screen, W // 2, int(H * 0.46), radius=int(H * 0.038))

        draw_button(screen, btn_continue_rect, "PLAY AGAIN (NEW MATCH)", btn_continue_rect.collidepoint(mouse_pos), primary_col=(35, 125, 55))
        draw_button(screen, btn_reset_rect, "RESET MATCH", btn_reset_rect.collidepoint(mouse_pos), primary_col=(130, 32, 28))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        hint = font_bar_val.render("Press [R] or [ENTER] to Play Again  |  Press [ESC] for Main Menu", True, (200, 190, 160))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.78))))

        if mouse_clicked:
            if btn_continue_rect.collidepoint(mouse_pos) or btn_reset_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_menu_rect.collidepoint(mouse_pos):
                reset_full_match()
                game_state = "MENU"

    # Display Flip & Tick
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
