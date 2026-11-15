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
        p = os.path.join(ASSETS, "sfx", f"{s_name}.ogg")
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
# Background Music (BGM) Manager - Japanese Combat Music
# ---------------------------------------------------------------------------
current_bgm_track = None


def play_bgm(track_name, vol=0.65):
    global current_bgm_track
    if current_bgm_track == track_name:
        return
    try:
        p = os.path.join(ASSETS, "sfx", f"{track_name}.ogg")
        if os.path.exists(p):
            pygame.mixer.music.load(p)
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(-1)
            current_bgm_track = track_name
    except Exception:
        pass


def stop_bgm(fade_ms=500):
    global current_bgm_track
    try:
        pygame.mixer.music.fadeout(fade_ms)
    except Exception:
        pass
    current_bgm_track = None


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
font_tower_title = get_font(int(H * 0.042))
font_dialogue_name = get_font(int(H * 0.024))
font_dialogue_body = get_font(int(H * 0.017))
font_tower_hud = get_font(int(H * 0.020))


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

# Authentic Pagoda Mountain Vertical Background (from uploaded artwork)
tower_bg_raw = load_image("tower_bg.jpg")
TOWER_H = max(3400, int(H * 4.0))
tower_bg = pygame.transform.smoothscale(tower_bg_raw, (W, TOWER_H))

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

# Pagoda Phase Player Scaling (Scaled down by 70%, i.e. 30% scale)
TOWER_PLAYER_SCALE_FACTOR = 0.30
tower_player_h = int(player_h * TOWER_PLAYER_SCALE_FACTOR)
tower_frame_w = max(1, int(frame_w * TOWER_PLAYER_SCALE_FACTOR))
tower_frame_h = max(1, int(frame_h * TOWER_PLAYER_SCALE_FACTOR))
tower_feet_offset = int(feet_offset * TOWER_PLAYER_SCALE_FACTOR)
tower_center_offset = tower_frame_w // 2

tower_walk_frames = [pygame.transform.smoothscale(f, (tower_frame_w, tower_frame_h)) for f in raw_walk_frames]
tower_dodge_frames = [pygame.transform.smoothscale(f, (tower_frame_w, tower_frame_h)) for f in raw_dodge_frames]
tower_slash_frames = [pygame.transform.smoothscale(f, (tower_frame_w, tower_frame_h)) for f in raw_slash_frames]
tower_parry_frames = [pygame.transform.smoothscale(f, (tower_frame_w, tower_frame_h)) for f in raw_parry_frames]
tower_idle_open = pygame.transform.smoothscale(raw_idle_open, (tower_frame_w, tower_frame_h))
tower_idle_blink = pygame.transform.smoothscale(raw_idle_blink, (tower_frame_w, tower_frame_h))

tower_pk_w = max(1, int(pk_w * TOWER_PLAYER_SCALE_FACTOR))
tower_pk_h = max(1, int(pk_h * TOWER_PLAYER_SCALE_FACTOR))
tower_pk_feet_offset = int(pk_feet_offset * TOWER_PLAYER_SCALE_FACTOR)
tower_pk_center_offset = tower_pk_w // 2
tower_player_kunai_frames = [pygame.transform.smoothscale(f, (tower_pk_w, tower_pk_h)) for f in raw_player_kunai]

tower_pheal_w = max(1, int(pheal_w * TOWER_PLAYER_SCALE_FACTOR))
tower_pheal_h = max(1, int(pheal_h * TOWER_PLAYER_SCALE_FACTOR))
tower_pheal_feet_offset = int(pheal_feet_offset * TOWER_PLAYER_SCALE_FACTOR)
tower_pheal_center_offset = tower_pheal_w // 2
tower_player_heal_frames = [pygame.transform.smoothscale(f, (tower_pheal_w, tower_pheal_h)) for f in raw_player_heal]


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

# 6. Boss Ascent (Aerial Slam Leap: Image 1, 5 rows x 6 cols = 30 frames)
raw_boss_ascent = extract_grid_frames("boss_ascent.png", 5, 6)
basc_w = int(170.67 * boss_scale)
basc_h = int(170.6 * boss_scale)
basc_feet = int(165 * boss_scale)
basc_center = basc_w // 2
boss_ascent_frames = [pygame.transform.smoothscale(f, (basc_w, basc_h)) for f in raw_boss_ascent]

# 7. Boss Descent (Aerial Slam Crash: Image 2, 5 rows x 6 cols = 30 frames)
raw_boss_descent = extract_grid_frames("boss_descent.png", 5, 6)
bdesc_w = int(170.67 * boss_scale)
bdesc_h = int(170.6 * boss_scale)
bdesc_feet = int(162 * boss_scale)
bdesc_center = bdesc_w // 2
boss_descent_frames = [pygame.transform.smoothscale(f, (bdesc_w, bdesc_h)) for f in raw_boss_descent]


# ---------------------------------------------------------------------------
# Projectiles
# ---------------------------------------------------------------------------
raw_kunai_item = load_image("kunai_projectile.png")
kw = int(player_h * 0.32)
kh = int(kw * (188.0 / 948.0))
kunai_item_right = pygame.transform.smoothscale(raw_kunai_item, (kw, kh))
kunai_item_left = pygame.transform.flip(kunai_item_right, True, False)

# Tower-scaled Kunai
tower_kw = max(1, int(kw * TOWER_PLAYER_SCALE_FACTOR))
tower_kh = max(1, int(kh * TOWER_PLAYER_SCALE_FACTOR))
tower_kunai_item_right = pygame.transform.smoothscale(raw_kunai_item, (tower_kw, tower_kh))
tower_kunai_item_left = pygame.transform.flip(tower_kunai_item_right, True, False)

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
    "jumps_left": 2,             # Double jump in tower platformer level (2 = ready)
    "jump_key_prev": False,
}

boss = {
    "name": "The Hollow Magistrate",
    "title": "Titan of the Ashen Peak",
    "x": int(W * 0.82),
    "y": GROUND_Y,
    "vx": 0.0,                  # Smooth velocity easing for fluid movement
    "facing_right": False,      # initially facing left towards player
    "state": "idle",            # "idle", "walk", "smash", "spear", "kunai", "enrage_intro", "stunned", "ascend", "airborne", "descend"
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
    "slam_target_x": int(W * 0.5),
    "slam_timer": 0,
    "slam_hit": False,
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
    player["jumps_left"] = 1     # Boss fight: single jump only!
    player["jump_key_prev"] = False

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
    boss["slam_target_x"] = int(W * 0.5)
    boss["slam_timer"] = 0
    boss["slam_hit"] = False


def start_next_round():
    """Advances to the next round of the Best of 5."""
    global current_round, game_state
    current_round += 1
    reset_round_entities()
    game_state = "PLAYING"


def reset_full_match():
    """Resets entire Best of 5 match from Round 1 (Boss Fight directly)."""
    global current_round, player_round_wins, boss_round_wins, player_hp_buff, player_speed_buff, game_state
    current_round = 1
    player_round_wins = 0
    boss_round_wins = 0
    player_hp_buff = 0
    player_speed_buff = False
    reset_round_entities()
    game_state = "PLAYING"


# ---------------------------------------------------------------------------
# Vertical Platformer Tower Level ("Pagoda of the Ashen Peak")
# ---------------------------------------------------------------------------
# TOWER_H is defined above as max(3400, int(H * 4.0)) matching tower_bg
tower_camera_y = float(TOWER_H - H)
tower_intro_dismissed = False
tower_door_msg = ""
tower_door_timer = 0
tower_damage_cooldown = 0
tower_platforms = []
tower_ladders = []
tower_minions = []
tower_npc = {}
tower_gate = {}
tower_ambient_particles = []
tower_momiji_leaves = []


def init_tower_level():
    """Initializes the Pagoda Tower vertical platformer level."""
    global tower_camera_y, tower_intro_dismissed, tower_door_msg, tower_door_timer, tower_damage_cooldown
    global tower_platforms, tower_ladders, tower_minions, tower_npc, tower_gate, tower_ambient_particles, tower_momiji_leaves
    global projectiles, sparks

    tower_camera_y = float(TOWER_H - H)
    tower_intro_dismissed = False
    tower_door_msg = ""
    tower_door_timer = 0
    tower_damage_cooldown = 0
    projectiles = []
    sparks = []

    # Reset player position to Tower Base
    effective_max_hp = 100 + player_hp_buff
    player["max_hp"] = effective_max_hp
    player["hp"] = effective_max_hp
    player["displayed_hp"] = float(effective_max_hp)
    player["x"] = int(W * 0.20)
    player["y"] = TOWER_H - 80
    player["vy"] = 0.0
    player["on_ground"] = True
    player["jumps_left"] = 2             # Double jump enabled in platformer!
    player["jump_key_prev"] = False
    player["facing_right"] = True
    player["state"] = "idle"
    player["frame_idx"] = 0
    player["anim_time"] = 0.0
    player["tick_count"] = 0
    player["kunai_count"] = player["kunai_max"]
    player["kunai_recharge_timer"] = 0
    player["heal_used"] = False
    player["heal_timer"] = 0

    # 1. Pagoda Platforms across 3 Tiers + Ground + Summit matching the uploaded artwork
    # Types: "ground", "stone", "bridge", "torii_terrace", "timber", "roof", "summit"
    summit_platform_y = TOWER_H - 2700

    tower_platforms = [
        # Ground base
        (pygame.Rect(0, TOWER_H - 80, W, 90), "ground"),

        # --- TIER 1: Lower Mountain Gorge & Stone Arches ---
        # Platform 1: Lower Left Stone Ruin Arches (matches lower left arch ruin in artwork)
        (pygame.Rect(int(W * 0.04), TOWER_H - 220, int(W * 0.34), 26), "stone"),
        # Platform 2: Lower Right Cliff Shelf (with red maple leaves)
        (pygame.Rect(int(W * 0.50), TOWER_H - 360, int(W * 0.42), 26), "timber"),
        # Platform 3: Lower Wooden Suspension Rope Bridge (spans gorge between cliffs)
        (pygame.Rect(int(W * 0.25), TOWER_H - 500, int(W * 0.32), 20), "bridge"),
        # Platform 4: Left Mountain Cliff Terrace
        (pygame.Rect(int(W * 0.04), TOWER_H - 650, int(W * 0.35), 26), "roof"),
        # Platform 5: Hidden Alcove - Key 1 Ledge (Tier 1 secluded alcove on far left)
        (pygame.Rect(int(W * 0.04), TOWER_H - 790, int(W * 0.22), 24), "stone"),

        # --- TIER 2: Sacred Torii Terrace & Shrine Ruins ---
        # Platform 6: Mid-Right Stone Arch Plateau (matching mid-right stone arch in artwork)
        (pygame.Rect(int(W * 0.46), TOWER_H - 940, int(W * 0.46), 28), "stone"),
        # Platform 7: Mid Suspension Rope Bridge (crossing the waterfall chasm)
        (pygame.Rect(int(W * 0.23), TOWER_H - 1090, int(W * 0.32), 20), "bridge"),
        # Platform 8: Grand Torii Gate Terrace on Right Cliff (Elder Musashi's Sanctuary)
        (pygame.Rect(int(W * 0.48), TOWER_H - 1240, int(W * 0.46), 32), "torii_terrace"),
        # Platform 9: Hidden Key 2 Ledge (Secret waterfall bracket on far right)
        (pygame.Rect(int(W * 0.80), TOWER_H - 1390, int(W * 0.18), 24), "timber"),
        # Platform 10: Left Colonnade / Stone Ruin Balcony
        (pygame.Rect(int(W * 0.08), TOWER_H - 1550, int(W * 0.36), 26), "stone"),

        # --- TIER 3: Upper Mountain Canopy & Pagoda Rooftops ---
        # Platform 11: Upper Rope Suspension Bridge (spans high mountain gorge)
        (pygame.Rect(int(W * 0.30), TOWER_H - 1710, int(W * 0.34), 20), "bridge"),
        # Platform 12: High Right Cliff Terrace with Crimson Banners
        (pygame.Rect(int(W * 0.54), TOWER_H - 1880, int(W * 0.38), 26), "roof"),
        # Platform 13: Left Maple Tree Canopy Spire (huge autumn tree on left in artwork)
        (pygame.Rect(int(W * 0.05), TOWER_H - 2050, int(W * 0.34), 26), "roof"),
        # Platform 14: Hidden Key 3 Ledge (High mountain spire on far left)
        (pygame.Rect(int(W * 0.04), TOWER_H - 2190, int(W * 0.20), 24), "timber"),
        # Platform 15: Sacred Mountain Stairway Approach 1
        (pygame.Rect(int(W * 0.56), TOWER_H - 2350, int(W * 0.32), 24), "timber"),
        # Platform 16: Sacred Mountain Stairway Approach 2 (Torii approach)
        (pygame.Rect(int(W * 0.40), TOWER_H - 2520, int(W * 0.32), 24), "roof"),

        # --- SUMMIT: Imperial Moonlit Pagoda Sanctum Courtyard ---
        (pygame.Rect(int(W * 0.20), summit_platform_y, int(W * 0.60), 36), "summit"),
    ]

    # 2. Wooden Ladders connecting cliff ledges (as depicted in the artwork)
    tower_ladders = [
        (int(W * 0.36), TOWER_H - 360, TOWER_H - 80),
        (int(W * 0.74), TOWER_H - 500, TOWER_H - 360),
        (int(W * 0.18), TOWER_H - 790, TOWER_H - 650),
        (int(W * 0.76), TOWER_H - 1240, TOWER_H - 940),
        (int(W * 0.22), TOWER_H - 1710, TOWER_H - 1550),
        (int(W * 0.70), TOWER_H - 2350, TOWER_H - 1880),
    ]

    # 3. Corrupted Ash Sentinels (One-Shot Minions)
    tower_minions = [
        # Tier 1 Minions
        {"x": int(W * 0.62), "y": TOWER_H - 360, "min_x": int(W * 0.52), "max_x": int(W * 0.88), "vx": 1.6, "alive": True, "facing_right": True},
        {"x": int(W * 0.18), "y": TOWER_H - 650, "min_x": int(W * 0.06), "max_x": int(W * 0.36), "vx": -1.8, "alive": True, "facing_right": False},

        # Tier 2 Minions
        {"x": int(W * 0.68), "y": TOWER_H - 940, "min_x": int(W * 0.48), "max_x": int(W * 0.88), "vx": 2.0, "alive": True, "facing_right": True},
        {"x": int(W * 0.22), "y": TOWER_H - 1550, "min_x": int(W * 0.10), "max_x": int(W * 0.40), "vx": -2.2, "alive": True, "facing_right": False},

        # Tier 3 Minions
        {"x": int(W * 0.68), "y": TOWER_H - 1880, "min_x": int(W * 0.56), "max_x": int(W * 0.88), "vx": 2.4, "alive": True, "facing_right": True},
        {"x": int(W * 0.20), "y": TOWER_H - 2050, "min_x": int(W * 0.08), "max_x": int(W * 0.36), "vx": -2.4, "alive": True, "facing_right": False},
        {"x": int(W * 0.54), "y": TOWER_H - 2520, "min_x": int(W * 0.42), "max_x": int(W * 0.70), "vx": 2.5, "alive": True, "facing_right": True},
    ]

    # 5. Friendly NPC: Elder Shinobi Musashi (at the Sacred Torii Terrace)
    tower_npc = {
        "name": "Elder Shinobi Musashi",
        "title": "Keeper of the Ashen Record",
        "x": int(W * 0.62),
        "y": TOWER_H - 1240,
        "width": 70,
        "height": 95,
    }

    # 6. Summit Sanctum Gate
    tower_gate = {
        "x": int(W * 0.42),
        "y": summit_platform_y - 180,
        "w": int(W * 0.16),
        "h": 180,
    }

    # 7. Ambient drifting ash motes
    tower_ambient_particles = []
    for _ in range(45):
        tower_ambient_particles.append({
            "x": random.randint(0, W),
            "y": random.randint(0, TOWER_H),
            "vx": random.uniform(-0.4, 0.4),
            "vy": random.uniform(-0.9, -0.3),
            "size": random.uniform(2.0, 4.5),
            "alpha": random.randint(70, 180),
        })

    # 8. Autumn Momiji (Red Maple Leaves) drifting down the gorge
    tower_momiji_leaves = []
    for _ in range(50):
        tower_momiji_leaves.append({
            "x": random.randint(0, W),
            "y": random.randint(0, TOWER_H),
            "vx": random.uniform(-0.8, -0.2),
            "vy": random.uniform(0.6, 1.4),
            "size": random.randint(5, 9),
            "color": random.choice([(195, 38, 32), (215, 58, 36), (230, 88, 42), (170, 30, 32)]),
            "phase": random.uniform(0.0, 6.28),
        })


def reset_entire_game():
    """Resets entire game back to the Pagoda Tower level entrance."""
    global current_round, player_round_wins, boss_round_wins, player_hp_buff, player_speed_buff, game_state
    current_round = 1
    player_round_wins = 0
    boss_round_wins = 0
    player_hp_buff = 0
    player_speed_buff = False
    init_tower_level()
    game_state = "TOWER"


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

    # Win Pips: Zhao â— â—‹ â—‹ vs â—‹ â—‹ â— Magistrate
    p_pips = "â— " * player_round_wins + "â—‹ " * (3 - player_round_wins)
    b_pips = "â—‹ " * (3 - boss_round_wins) + "â— " * boss_round_wins
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
    kunai_str = f"KUNAI [Q]: {'â—† ' * p['kunai_count']}{'â—‡ ' * (p['kunai_max'] - p['kunai_count'])}"
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
        "title": "PROLOGUE: PAGODA OF THE ASHEN PEAK",
        "color": (212, 163, 75),
        "lines": [
            "  â€¢ Pagoda Ascent : Climb 3 vertical tiers across stone arches, rope bridges, and Torii terraces.",
            "  â€¢ Ninja Double Jump : Press [W] / [UP] to jump, and press [W] in mid-air to DOUBLE JUMP! (Tower only).",
            "  â€¢ Ash Sentinels : Corrupted guards patrol the platforms. 1 strike with Sword or Kunai slays them!",
            "  â€¢ Elder Musashi : Hover over the hermit on the Torii Terrace (Tier II) to hear lore of Zhao & Magistrate.",
            "  â€¢ Summit Sanctum: Reach the peak gate and press [W] or [ENTER] to face the boss!",
        ]
    },
    {
        "title": "BEST OF 5 (BO5) SYSTEM & BOUNCE BACK BUFFS",
        "color": (255, 225, 120),
        "lines": [
            "  â€¢ Format          : Best of 5 rounds. First to win 3 rounds claims victory!",
            "  â€¢ 1st Loss Buff   : Suffer a round loss to receive a permanent +30 Max HP Buff (BOUNCE BACK)!",
            "  â€¢ 2nd Loss Buff   : Suffer a second loss to gain +25% Movement Speed and +25% Attack Speed (FINAL BOUNCE BACK)!",
            "  â€¢ 3rd Loss Defeat : If the Magistrate claims 3 rounds, he wins the match.",
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
            "  â€¢ Phase I  (100% - 66% HP): Tactical pacing. Spear throws at range, greatsword slams close.",
            "  â€¢ Phase II (66% - 33% HP) : Red Mist awakens! Magistrate speeds up with +25% damage.",
            "  â€¢ Phase III (<= 33% HP / Enraged <= 10%): 5.5s dark roar! Attacks 70% faster, healing locked.",
            "  â€¢ Boss Invulnerability    : The Magistrate is completely immune to damage during phase transitions",
            "                              and while leaping into the sky (Aerial Slam).",
            "  â€¢ Aerial Sky Slam Attack  : Magistrate leaps into the sky! A red light indicator appears at the",
            "                              top of the screen 1s before descent. Dodge or parry the crash AOE shockwave!",
            "  â€¢ Balance Adjustments     : Boss sword damage decreased by 20%, spear damage decreased by 10%.",
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


def update_tower_level(keys, mouse_pos, mouse_clicked):
    global tower_camera_y, tower_intro_dismissed
    global tower_door_msg, tower_door_timer, tower_damage_cooldown, game_state
    global projectiles, sparks

    p = player
    player_hit_speed_mult = 1.45 if player_speed_buff else 1.20
    player_move_speed = (BASE_MOVE_SPEED * 1.25) if player_speed_buff else BASE_MOVE_SPEED

    # Atmospheric Japanese BGM for Tower
    play_bgm("bgm_normal", vol=0.50)

    if tower_door_timer > 0:
        tower_door_timer -= 1
    if tower_damage_cooldown > 0:
        tower_damage_cooldown -= 1

    # Intro Scroll modal dismissal
    if not tower_intro_dismissed:
        if keys[pygame.K_SPACE] or keys[pygame.K_RETURN] or mouse_clicked:
            tower_intro_dismissed = True
            play_sfx("slash_hit", 0.7)
        return

    # Kunai recharge in tower
    if p["kunai_count"] < p["kunai_max"]:
        p["kunai_recharge_timer"] += 1
        if p["kunai_recharge_timer"] >= 240:
            p["kunai_count"] += 1
            p["kunai_recharge_timer"] = 0

    # Player state updates in Tower
    if p["state"] in ("dodge", "slash", "kunai"):
        p["tick_count"] += 1

        if p["state"] == "dodge":
            dodge_vx = (player_move_speed * 1.6) if p["facing_right"] else (-player_move_speed * 1.6)
            p["x"] += dodge_vx
            if p["tick_count"] >= 1:
                p["tick_count"] = 0
                p["frame_idx"] += 1
                if p["frame_idx"] >= len(tower_dodge_frames):
                    p["state"] = "idle"
                    p["frame_idx"] = 0

        elif p["state"] == "slash":
            prev_idx = p["frame_idx"]
            p["anim_time"] += player_hit_speed_mult
            new_idx = int(p["anim_time"])
            p["frame_idx"] = new_idx

            if prev_idx < 14 and new_idx >= 14:
                play_sfx("slash_hit", 0.8)
                # Strike 1-shot Minions (scaled to tower player size)
                for m in tower_minions:
                    if m["alive"] and abs(p["x"] - m["x"]) < max(48, int(W * 0.06)) and abs(p["y"] - m["y"]) < 50:
                        facing = (m["x"] > p["x"] and p["facing_right"]) or (m["x"] < p["x"] and not p["facing_right"])
                        if facing:
                            m["alive"] = False
                            play_sfx("slash_hit", 1.0)
                            spawn_sparks(m["x"], m["y"] - 35, count=22, is_golden=False)

            if p["frame_idx"] >= len(tower_slash_frames):
                p["state"] = "idle"
                p["frame_idx"] = 0
                p["anim_time"] = 0.0

        elif p["state"] == "kunai":
            prev_idx = p["frame_idx"]
            p["anim_time"] += player_hit_speed_mult
            new_idx = int(p["anim_time"])
            p["frame_idx"] = new_idx

            if prev_idx < 15 and new_idx >= 15 and not p["kunai_spawned"]:
                p["kunai_spawned"] = True
                cur_k_speed = (BASE_KUNAI_SPEED * 1.25) if player_speed_buff else BASE_KUNAI_SPEED
                k_vx = cur_k_speed if p["facing_right"] else -cur_k_speed
                spawn_x = p["x"] + (int(tower_player_h * 0.35) if p["facing_right"] else -int(tower_player_h * 0.35))
                spawn_y = p["y"] - int(tower_player_h * 0.45)
                projectiles.append({
                    "x": spawn_x,
                    "y": spawn_y,
                    "vx": k_vx,
                    "type": "kunai",
                    "owner": "player",
                    "facing_right": p["facing_right"],
                    "damage": 50,
                    "active": True,
                })
                play_sfx("kunai_throw", 0.7)

            if p["frame_idx"] >= len(tower_player_kunai_frames):
                p["state"] = "idle"
                p["frame_idx"] = 0
                p["anim_time"] = 0.0
                p["kunai_spawned"] = False

    else:
        # Movement & Actions
        if keys[pygame.K_LSHIFT]:
            p["state"] = "dodge"
            p["frame_idx"] = 0
            p["tick_count"] = 0
        elif keys[pygame.K_RSHIFT]:
            p["state"] = "slash"
            p["frame_idx"] = 0
            p["anim_time"] = 0.0
            p["tick_count"] = 0
        elif keys[pygame.K_q] and p["kunai_count"] > 0:
            p["kunai_count"] -= 1
            p["state"] = "kunai"
            p["frame_idx"] = 0
            p["anim_time"] = 0.0
            p["tick_count"] = 0
            p["kunai_spawned"] = False
        else:
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
                    p["frame_idx"] = (p["frame_idx"] + 1) % len(tower_walk_frames)
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

        # Jump & Double Jump (Edge-triggered for crisp air leap)
        jump_key_down = keys[pygame.K_w] or keys[pygame.K_UP]
        jump_just_pressed = jump_key_down and not p.get("jump_key_prev", False)
        p["jump_key_prev"] = jump_key_down

        if jump_just_pressed:
            if p["on_ground"]:
                p["vy"] = JUMP_FORCE
                p["on_ground"] = False
                p["jumps_left"] = 1
                play_sfx("kunai_throw", 0.4)
            elif p.get("jumps_left", 0) > 0:
                p["vy"] = JUMP_FORCE * 0.95
                p["jumps_left"] -= 1
                play_sfx("heal_spell", 0.6)
                # Golden chakra leap burst beneath feet
                spawn_sparks(p["x"], p["y"] - 10, count=16, is_golden=True)

        # Drop down through wooden platforms
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and p["on_ground"] and p["y"] < TOWER_H - 120:
            p["y"] += 8
            p["on_ground"] = False
            p["vy"] = 2.0

    # Gravity & Platform Collision
    prev_y = p["y"]
    if not p["on_ground"]:
        p["vy"] += GRAVITY
        p["y"] += p["vy"]

    p["on_ground"] = False
    if p["vy"] >= 0:
        for plat, p_type in tower_platforms:
            if plat.left - 20 <= p["x"] <= plat.right + 20:
                if prev_y <= plat.top + 6 and p["y"] >= plat.top - 6:
                    p["y"] = plat.top
                    p["vy"] = 0.0
                    p["on_ground"] = True
                    p["jumps_left"] = 2       # Reset double jump on landing!
                    break

    # Ground boundary
    if p["y"] >= TOWER_H - 80:
        p["y"] = TOWER_H - 80
        p["vy"] = 0.0
        p["on_ground"] = True
        p["jumps_left"] = 2               # Reset double jump on ground!

    p["x"] = max(tower_center_offset + int(W * 0.02), min(W - tower_center_offset - int(W * 0.02), p["x"]))

    # Update Sparks in Tower
    for spk in list(sparks):
        spk["x"] += spk["vx"]
        spk["y"] += spk["vy"]
        spk["vy"] += 0.28
        spk["life"] -= 1
        if spk["life"] <= 0:
            sparks.remove(spk)

    # Update Minions (1-Shot)
    for m in tower_minions:
        if m["alive"]:
            m["x"] += m["vx"]
            if m["x"] <= m["min_x"]:
                m["x"] = m["min_x"]
                m["vx"] = abs(m["vx"])
                m["facing_right"] = True
            elif m["x"] >= m["max_x"]:
                m["x"] = m["max_x"]
                m["vx"] = -abs(m["vx"])
                m["facing_right"] = False

            # Touch player damage check (scaled to tower player size)
            if abs(p["x"] - m["x"]) < 26 and abs(p["y"] - m["y"]) < 40:
                if p["state"] == "dodge":
                    pass  # rolled through
                elif tower_damage_cooldown <= 0:
                    tower_damage_cooldown = 45
                    p["hp"] = max(0, p["hp"] - 15)
                    play_sfx("slash_hit", 0.7)
                    spawn_sparks(p["x"], p["y"] - tower_player_h * 0.5, count=10, is_golden=False)
                    if p["hp"] <= 0:
                        # Instant respawn at tower base
                        p["hp"] = p["max_hp"]
                        p["x"] = int(W * 0.20)
                        p["y"] = TOWER_H - 80
                        p["vy"] = 0.0
                        p["jumps_left"] = 2
                        tower_door_msg = "â˜… DEFEATED BY SENTINELS â€” RESPAWNED AT TOWER BASE â˜…"
                        tower_door_timer = 180

    # Update Projectiles in Tower
    for proj in list(projectiles):
        proj["x"] += proj["vx"]
        if proj["x"] < -100 or proj["x"] > W + 100:
            proj["active"] = False
        if proj["active"] and proj["owner"] == "player":
            for m in tower_minions:
                if m["alive"] and abs(proj["x"] - m["x"]) < 32 and abs(proj["y"] - (m["y"] - 30)) < 40:
                    m["alive"] = False
                    proj["active"] = False
                    play_sfx("slash_hit", 0.9)
                    spawn_sparks(m["x"], m["y"] - 35, count=18, is_golden=False)
                    break
        if not proj["active"]:
            projectiles.remove(proj)

    # Summit Gate Interaction (Breach Summit Sanctum - Enter Boss Fight directly)
    gate_cx = tower_gate["x"] + tower_gate["w"] // 2
    summit_gate_bottom = tower_gate["y"] + tower_gate["h"]
    if abs(p["x"] - gate_cx) < int(W * 0.16) and p["y"] <= summit_gate_bottom + 15:
        tower_door_msg = "â˜… PRESS [W] OR [ENTER] TO UNSEAL GATE & FACE THE HOLLOW MAGISTRATE â˜…"
        tower_door_timer = 15
        if keys[pygame.K_w] or keys[pygame.K_RETURN] or keys[pygame.K_UP]:
            play_sfx("posture_break", 1.0)
            spawn_sparks(gate_cx, tower_gate["y"] + 60, count=45, is_golden=True)
            reset_full_match()
            game_state = "PLAYING"

    # Ambient particles update
    for ap in tower_ambient_particles:
        ap["x"] += ap["vx"]
        ap["y"] += ap["vy"]
        if ap["y"] < 0:
            ap["y"] = TOWER_H
            ap["x"] = random.randint(0, W)

    # Autumn Momiji Leaves drifting down
    for leaf in tower_momiji_leaves:
        leaf["phase"] += 0.04
        leaf["x"] += leaf["vx"] + math.sin(leaf["phase"]) * 0.5
        leaf["y"] += leaf["vy"]
        if leaf["y"] > TOWER_H:
            leaf["y"] = 0
            leaf["x"] = random.randint(0, W)
        if leaf["x"] < -20:
            leaf["x"] = W + 10

    # Smooth Vertical Camera Follow
    target_cam_y = p["y"] - H * 0.62
    tower_camera_y += (target_cam_y - tower_camera_y) * 0.12
    tower_camera_y = max(0.0, min(float(TOWER_H - H), tower_camera_y))


def draw_tower_level(surface, mouse_pos):
    global tower_camera_y, tower_door_msg, tower_door_timer

    cam_y = int(tower_camera_y)

    # 1. Authentic Pagoda Mountain Background (Continuous vertical scroll matching player ascent)
    surface.blit(tower_bg, (0, -cam_y))

    # 2. Ambient Drifting Embers & Ash Particles
    for ap in tower_ambient_particles:
        sy = int(ap["y"]) - cam_y
        if 0 <= sy <= H:
            ember_col = (235, 125, 45, int(ap["alpha"]))
            e_surf = pygame.Surface((int(ap["size"] * 2), int(ap["size"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(e_surf, ember_col, (int(ap["size"]), int(ap["size"])), int(ap["size"]))
            surface.blit(e_surf, (int(ap["x"]), sy))

    # 3. Autumn Momiji (Red Maple Leaves) drifting down the gorge
    for leaf in tower_momiji_leaves:
        lsy = int(leaf["y"]) - cam_y
        if -30 <= lsy <= H + 30:
            lx = int(leaf["x"])
            sz = int(leaf["size"])
            pygame.draw.circle(surface, leaf["color"], (lx, lsy), sz // 2)
            pygame.draw.polygon(surface, leaf["color"], [
                (lx, lsy - sz),
                (lx + sz // 2 + 1, lsy + sz // 2),
                (lx - sz // 2 - 1, lsy + sz // 2)
            ])

    # 4. Wooden Ladders connecting cliff ledges (as depicted in the artwork)
    for lx, top_y, bot_y in tower_ladders:
        s_top = top_y - cam_y
        s_bot = bot_y - cam_y
        if s_bot < -50 or s_top > H + 50:
            continue
        # Wooden side rails
        pygame.draw.line(surface, (70, 44, 28), (lx - 12, s_top), (lx - 12, s_bot), 3)
        pygame.draw.line(surface, (70, 44, 28), (lx + 12, s_top), (lx + 12, s_bot), 3)
        # Rungs
        for ry in range(top_y, bot_y, 18):
            s_ry = ry - cam_y
            if -10 <= s_ry <= H + 10:
                pygame.draw.line(surface, (135, 88, 52), (lx - 12, s_ry), (lx + 12, s_ry), 2)

    # 5. Pagoda & Gorge Platforms (Structured to match artwork)
    for plat, p_type in tower_platforms:
        sy = plat.y - cam_y
        if sy + plat.height < -120 or sy > H + 60:
            continue

        p_rect = pygame.Rect(plat.x, sy, plat.width, plat.height)

        if p_type == "ground":
            pygame.draw.rect(surface, (26, 20, 20), p_rect)
            pygame.draw.line(surface, (130, 32, 28), (p_rect.left, p_rect.top), (p_rect.right, p_rect.top), 4)
            pygame.draw.line(surface, (212, 163, 75), (p_rect.left, p_rect.top + 4), (p_rect.right, p_rect.top + 4), 1)
            # Atmospheric stone lanterns flanking the trail
            for lx in [int(W * 0.08), int(W * 0.92)]:
                pygame.draw.rect(surface, (55, 48, 48), pygame.Rect(lx - 14, p_rect.top - 52, 28, 52))
                l_pulse = abs(math.sin(frame_count * 0.15 + lx))
                pygame.draw.rect(surface, (255, int(175 + 40 * l_pulse), 60), pygame.Rect(lx - 9, p_rect.top - 42, 18, 20))
                pygame.draw.polygon(surface, (35, 28, 28), [(lx - 20, p_rect.top - 52), (lx + 20, p_rect.top - 52), (lx, p_rect.top - 70)])

        elif p_type == "stone":
            # Ancient weathered stone arches & cliff shelves
            pygame.draw.rect(surface, (45, 42, 48), p_rect)
            pygame.draw.line(surface, (85, 80, 92), (p_rect.left, p_rect.top), (p_rect.right, p_rect.top), 2)
            for bx in range(p_rect.left, p_rect.right, 36):
                pygame.draw.line(surface, (30, 28, 32), (bx, p_rect.top), (bx, p_rect.bottom), 1)
            for sx in range(p_rect.left + 8, p_rect.right - 8, 28):
                pygame.draw.circle(surface, (165, 45, 35), (sx, p_rect.top + 3), 3)
            # Pillar arch supports beneath
            pygame.draw.rect(surface, (36, 33, 38), pygame.Rect(p_rect.left + 15, p_rect.bottom, 22, 36))
            pygame.draw.rect(surface, (36, 33, 38), pygame.Rect(p_rect.right - 37, p_rect.bottom, 22, 36))

        elif p_type == "bridge":
            # Wooden suspension rope bridge spanning the chasm
            pygame.draw.line(surface, (130, 85, 48), (p_rect.left, p_rect.top - 18), (p_rect.right, p_rect.top - 18), 3)
            pygame.draw.rect(surface, (72, 45, 28), p_rect)
            pygame.draw.line(surface, (110, 70, 40), (p_rect.left, p_rect.top), (p_rect.right, p_rect.top), 2)
            for plank_x in range(p_rect.left, p_rect.right, 14):
                pygame.draw.line(surface, (45, 26, 16), (plank_x, p_rect.top), (plank_x, p_rect.bottom), 1)
                if plank_x % 28 == 0:
                    pygame.draw.line(surface, (100, 65, 38), (plank_x, p_rect.top - 18), (plank_x, p_rect.top), 1)
            # Bridge support posts on both ends
            pygame.draw.rect(surface, (55, 32, 20), pygame.Rect(p_rect.left - 6, p_rect.top - 24, 10, 32))
            pygame.draw.rect(surface, (55, 32, 20), pygame.Rect(p_rect.right - 4, p_rect.top - 24, 10, 32))

        elif p_type == "torii_terrace":
            # Sacred Torii Terrace Platform with vermilion Torii Gate
            pygame.draw.rect(surface, (40, 36, 42), p_rect)
            pygame.draw.line(surface, (160, 42, 38), (p_rect.left, p_rect.top), (p_rect.right, p_rect.top), 3)
            pygame.draw.line(surface, (212, 163, 75), (p_rect.left, p_rect.top + 3), (p_rect.right, p_rect.top + 3), 1)
            # Torii Gate
            torii_cx = p_rect.left + int(p_rect.width * 0.38)
            torii_h = 110
            torii_w = 125
            torii_top_y = p_rect.top - torii_h
            col_w = 14
            p_left_x = torii_cx - torii_w // 2 + 15
            p_right_x = torii_cx + torii_w // 2 - 15 - col_w
            # Vermilion pillars
            pygame.draw.rect(surface, (185, 38, 32), pygame.Rect(p_left_x, torii_top_y + 12, col_w, torii_h - 12))
            pygame.draw.rect(surface, (185, 38, 32), pygame.Rect(p_right_x, torii_top_y + 12, col_w, torii_h - 12))
            # Black stone pillar bases (kamebara)
            pygame.draw.rect(surface, (25, 20, 22), pygame.Rect(p_left_x - 3, p_rect.top - 12, col_w + 6, 12))
            pygame.draw.rect(surface, (25, 20, 22), pygame.Rect(p_right_x - 3, p_rect.top - 12, col_w + 6, 12))
            # Top curved lintel (Kasagi & Shimaki)
            pygame.draw.rect(surface, (195, 42, 35), pygame.Rect(torii_cx - torii_w // 2, torii_top_y, torii_w, 14))
            pygame.draw.polygon(surface, (195, 42, 35), [(torii_cx - torii_w // 2, torii_top_y), (torii_cx - torii_w // 2 - 12, torii_top_y - 8), (torii_cx - torii_w // 2, torii_top_y + 14)])
            pygame.draw.polygon(surface, (195, 42, 35), [(torii_cx + torii_w // 2, torii_top_y), (torii_cx + torii_w // 2 + 12, torii_top_y - 8), (torii_cx + torii_w // 2, torii_top_y + 14)])
            # Tie beam (Nuki)
            pygame.draw.rect(surface, (170, 32, 28), pygame.Rect(p_left_x - 10, torii_top_y + 30, (p_right_x + col_w + 10) - (p_left_x - 10), 9))
            # Gold tablet (Gakuzuka)
            pygame.draw.rect(surface, (212, 163, 75), pygame.Rect(torii_cx - 8, torii_top_y + 14, 16, 16))
            # Shimenawa sacred rope
            pygame.draw.line(surface, (230, 205, 140), (p_left_x + col_w, torii_top_y + 38), (p_right_x, torii_top_y + 38), 2)

        elif p_type == "timber":
            pygame.draw.rect(surface, (36, 24, 20), p_rect)
            pygame.draw.rect(surface, (135, 34, 30), p_rect, 2)
            pygame.draw.rect(surface, (212, 163, 75), pygame.Rect(p_rect.left, p_rect.top, 14, p_rect.height))
            pygame.draw.rect(surface, (212, 163, 75), pygame.Rect(p_rect.right - 14, p_rect.top, 14, p_rect.height))

        elif p_type == "roof":
            pygame.draw.rect(surface, (24, 18, 24), p_rect)
            pygame.draw.line(surface, (140, 34, 30), (p_rect.left, p_rect.top), (p_rect.right, p_rect.top), 3)
            pygame.draw.polygon(surface, (212, 163, 75), [(p_rect.left, p_rect.top), (p_rect.left - 15, p_rect.top - 12), (p_rect.left + 8, p_rect.top)])
            pygame.draw.polygon(surface, (212, 163, 75), [(p_rect.right, p_rect.top), (p_rect.right + 15, p_rect.top - 12), (p_rect.right - 8, p_rect.top)])

        elif p_type == "summit":
            draw_feudal_panel(surface, p_rect, border_col=(212, 163, 75), bg_col=(32, 14, 14, 240), gold_corners=True)

    # 6. Summit Sanctum Gate
    gate_sy = tower_gate["y"] - cam_y
    if -200 <= gate_sy <= H + 100:
        gate_rect = pygame.Rect(tower_gate["x"], gate_sy, tower_gate["w"], tower_gate["h"])
        pygame.draw.rect(surface, (30, 10, 10), gate_rect)
        pygame.draw.rect(surface, (140, 32, 28), gate_rect, 4)
        pygame.draw.rect(surface, (160, 35, 30), pygame.Rect(gate_rect.left - 20, gate_rect.top - 18, gate_rect.width + 40, 22))
        pygame.draw.polygon(surface, (212, 163, 75), [(gate_rect.left - 24, gate_rect.top - 18), (gate_rect.left - 34, gate_rect.top - 30), (gate_rect.left - 6, gate_rect.top - 18)])
        pygame.draw.polygon(surface, (212, 163, 75), [(gate_rect.right + 24, gate_rect.top - 18), (gate_rect.right + 34, gate_rect.top - 30), (gate_rect.right + 6, gate_rect.top - 18)])

        # Feudal Gate Crest
        gc_x = gate_rect.centerx
        gc_y = gate_rect.centery
        pygame.draw.circle(surface, (20, 10, 10), (gc_x, gc_y), 22)
        pygame.draw.circle(surface, (212, 163, 75), (gc_x, gc_y), 22, 2)
        pygame.draw.circle(surface, (160, 32, 28), (gc_x, gc_y), 15, 2)
        pygame.draw.polygon(surface, (255, 220, 100), [(gc_x, gc_y - 9), (gc_x + 9, gc_y), (gc_x, gc_y + 9), (gc_x - 9, gc_y)])

        g_txt = "SUMMIT SANCTUM"
        g_surf = font_bar_val.render(g_txt, True, (240, 220, 190))
        surface.blit(g_surf, g_surf.get_rect(center=(gate_rect.centerx, gate_rect.top - 8)))

    # 7. Friendly NPC: Elder Shinobi Musashi (at the Sacred Torii Terrace)
    npc_sy = tower_npc["y"] - cam_y
    if -100 <= npc_sy <= H + 100:
        nx = tower_npc["x"]
        ny = npc_sy

        # Stone Pagoda Lantern beside NPC
        lx = nx + 48
        pygame.draw.rect(surface, (55, 48, 48), pygame.Rect(lx - 10, ny - 50, 20, 50))
        l_pulse = abs(math.sin(frame_count * 0.15))
        lantern_col = (255, int(170 + 40 * l_pulse), 50)
        pygame.draw.rect(surface, lantern_col, pygame.Rect(lx - 7, ny - 42, 14, 18))
        pygame.draw.polygon(surface, (35, 28, 28), [(lx - 15, ny - 50), (lx + 15, ny - 50), (lx, ny - 65)])
        halo_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(halo_surf, (255, 180, 60, int(35 + 20 * l_pulse)), (40, 40), 38)
        surface.blit(halo_surf, (lx - 40, ny - 70))

        # Elder Musashi Sprite
        pygame.draw.polygon(surface, (42, 45, 58), [(nx - 18, ny), (nx + 18, ny), (nx + 10, ny - 55), (nx - 10, ny - 55)])
        pygame.draw.line(surface, (212, 163, 75), (nx - 12, ny - 30), (nx + 12, ny - 30), 3)
        pygame.draw.circle(surface, (215, 185, 160), (nx, ny - 62), 11)
        pygame.draw.polygon(surface, (140, 110, 65), [(nx - 28, ny - 68), (nx + 28, ny - 68), (nx, ny - 84)])
        pygame.draw.line(surface, (90, 70, 40), (nx - 28, ny - 68), (nx + 28, ny - 68), 2)
        pygame.draw.line(surface, (135, 90, 50), (nx - 18, ny), (nx - 18, ny - 80), 3)
        pygame.draw.circle(surface, (212, 163, 75), (nx - 18, ny - 80), 5, 2)

        npc_lbl = font_hud_info.render("[ELDER MUSASHI â€” HOVER TO LISTEN]", True, (255, 225, 130))
        surface.blit(npc_lbl, npc_lbl.get_rect(center=(nx, ny - 98)))

    # 8. One-Shot Minions (Corrupted Ash Sentinels)
    for m in tower_minions:
        if m["alive"]:
            msy = m["y"] - cam_y
            if -80 <= msy <= H + 80:
                mx = int(m["x"])
                my = int(msy)
                facing = m["facing_right"]

                pygame.draw.polygon(surface, (22, 16, 20), [(mx - 14, my), (mx + 14, my), (mx + 8, my - 44), (mx - 8, my - 44)])
                scarf_dx = -16 if facing else 16
                pygame.draw.line(surface, (180, 28, 28), (mx, my - 38), (mx + scarf_dx, my - 42), 3)
                pygame.draw.line(surface, (180, 28, 28), (mx + scarf_dx, my - 42), (mx + scarf_dx * 1.4, my - 36), 2)
                pygame.draw.circle(surface, (30, 22, 26), (mx, my - 50), 10)
                eye_dx = 3 if facing else -3
                pygame.draw.circle(surface, (255, 35, 35), (mx + eye_dx, my - 51), 3)
                pygame.draw.circle(surface, (255, 220, 220), (mx + eye_dx, my - 51), 1)
                k_tip_x = mx + (22 if facing else -22)
                pygame.draw.line(surface, (200, 205, 210), (mx, my - 25), (k_tip_x, my - 28), 2)

    # 9. Render Projectiles in Tower (Scaled down for pagoda phase)
    for proj in projectiles:
        psy = int(proj["y"]) - cam_y
        if -50 <= psy <= H + 50:
            if proj["type"] == "kunai":
                k_img = tower_kunai_item_right if proj["facing_right"] else tower_kunai_item_left
                surface.blit(k_img, (int(proj["x"] - k_img.get_width() // 2), psy - k_img.get_height() // 2))

    # 10. Render Sparks in Tower
    for spk in sparks:
        col = spk.get("color", (255, 220, 100))
        if isinstance(col, (tuple, list)) and len(col) >= 3 and isinstance(col[0], (int, float)):
            safe_col = (max(0, min(255, int(col[0]))), max(0, min(255, int(col[1]))), max(0, min(255, int(col[2]))))
        else:
            safe_col = (255, 220, 100)
        sz = max(1, int(spk.get("size", 2)))
        spk_sy = int(spk["y"]) - cam_y
        if -10 <= spk_sy <= H + 10:
            pygame.draw.circle(surface, safe_col, (int(spk["x"]), spk_sy), sz)

    # 11. Render Player (General Zhao - Scaled down by 70% during Pagoda phase)
    p = player
    if p["state"] == "heal":
        p_sprite = tower_player_heal_frames[p["frame_idx"] % len(tower_player_heal_frames)]
        p_draw_x = int(p["x"] - tower_pheal_center_offset)
        p_draw_y = int(p["y"] - tower_pheal_feet_offset) - cam_y
    elif p["state"] == "idle":
        p_sprite = tower_idle_blink if p["is_blinking"] else tower_idle_open
        p_draw_x = int(p["x"] - tower_center_offset)
        p_draw_y = int(p["y"] - tower_feet_offset) - cam_y
    elif p["state"] == "walk":
        p_sprite = tower_walk_frames[p["frame_idx"]]
        p_draw_x = int(p["x"] - tower_center_offset)
        p_draw_y = int(p["y"] - tower_feet_offset) - cam_y
    elif p["state"] == "dodge":
        p_sprite = tower_dodge_frames[p["frame_idx"]]
        p_draw_x = int(p["x"] - tower_center_offset)
        p_draw_y = int(p["y"] - tower_feet_offset) - cam_y
    elif p["state"] == "slash":
        p_sprite = tower_slash_frames[p["frame_idx"]]
        p_draw_x = int(p["x"] - tower_center_offset)
        p_draw_y = int(p["y"] - tower_feet_offset) - cam_y
    elif p["state"] == "kunai":
        p_sprite = tower_player_kunai_frames[p["frame_idx"]]
        p_draw_x = int(p["x"] - tower_pk_center_offset)
        p_draw_y = int(p["y"] - tower_pk_feet_offset) - cam_y
    elif p["state"] == "parry":
        p_sprite = tower_parry_frames[p["frame_idx"]]
        p_draw_x = int(p["x"] - tower_center_offset)
        p_draw_y = int(p["y"] - tower_feet_offset) - cam_y
    else:
        p_sprite = tower_idle_open
        p_draw_x = int(p["x"] - tower_center_offset)
        p_draw_y = int(p["y"] - tower_feet_offset) - cam_y

    if not p["facing_right"]:
        p_sprite = pygame.transform.flip(p_sprite, True, False)

    if tower_damage_cooldown > 0 and (tower_damage_cooldown // 3) % 2 == 1:
        pass
    else:
        surface.blit(p_sprite, (p_draw_x, p_draw_y))

    # 13. Tower HUD (Health, Double Jump readiness, Keys, Current Tier)
    hud_y = int(H * 0.04)
    p_bar_w = int(W * 0.22)
    p_bar_h = int(H * 0.024)
    p_pct = max(0.0, min(1.0, p["hp"] / p["max_hp"]))
    draw_feudal_panel(surface, pygame.Rect(int(W * 0.05), hud_y, p_bar_w, p_bar_h), border_col=(120, 30, 25), bg_col=(18, 12, 10, 220))
    if p_pct > 0:
        pygame.draw.rect(surface, (190, 32, 28), pygame.Rect(int(W * 0.05) + 3, hud_y + 3, int((p_bar_w - 6) * p_pct), p_bar_h - 6))
    hp_txt = font_bar_val.render(f"ZHAO: {p['hp']}/{p['max_hp']} HP", True, (255, 245, 230))
    surface.blit(hp_txt, (int(W * 0.05) + 8, hud_y + (p_bar_h - hp_txt.get_height()) // 2))

    # Double Jump Readiness indicator
    dj_left = p.get("jumps_left", 2)
    dj_text = "DOUBLE JUMP: READY [W IN AIR]" if dj_left >= 2 else ("DOUBLE JUMP: AVAILABLE" if dj_left == 1 else "DOUBLE JUMP: USED")
    dj_col = (110, 240, 150) if dj_left >= 1 else (175, 160, 150)
    dj_surf = font_bar_val.render(dj_text, True, dj_col)
    surface.blit(dj_surf, (int(W * 0.05), hud_y + p_bar_h + 4))

    k_surf = font_tower_hud.render("PAGODA OF THE ASHEN PEAK  â€¢  ASCENT TO THE SUMMIT", True, (255, 220, 95))
    surface.blit(k_surf, k_surf.get_rect(center=(W // 2, hud_y + p_bar_h // 2)))

    if p["y"] > TOWER_H - 900:
        tier_str = "TIER I : LOWER GORGE & STONE ARCHES"
    elif p["y"] > TOWER_H - 1700:
        tier_str = "TIER II : TORII TERRACE & SHRINES"
    elif p["y"] > TOWER_H - 2500:
        tier_str = "TIER III : MAPLE CANOPY & ROOFTOPS"
    else:
        tier_str = "SUMMIT : PAGODA SANCTUM GATE"
    tier_surf = font_hud_info.render(tier_str, True, (212, 163, 75))
    surface.blit(tier_surf, (W - int(W * 0.05) - tier_surf.get_width(), hud_y + (p_bar_h - tier_surf.get_height()) // 2))

    # 13. Floating Door Banner Notification
    if tower_door_timer > 0 and tower_door_msg:
        box_w = int(W * 0.62)
        box_h = int(H * 0.048)
        b_rect = pygame.Rect((W - box_w) // 2, int(H * 0.12), box_w, box_h)
        draw_feudal_panel(surface, b_rect, border_col=(212, 163, 75), bg_col=(22, 12, 10, 240), gold_corners=True)
        m_surf = font_bar_val.render(tower_door_msg, True, (255, 235, 130))
        surface.blit(m_surf, m_surf.get_rect(center=b_rect.center))

    # 14. Friendly NPC Hover Dialogue Box (Lore between Zhao & Magistrate)
    npc_screen_x = tower_npc["x"]
    npc_screen_y = tower_npc["y"] - cam_y
    npc_rect = pygame.Rect(npc_screen_x - 45, npc_screen_y - 95, 90, 105)

    if npc_rect.collidepoint(mouse_pos) or (abs(p["x"] - npc_screen_x) < 70 and abs(p["y"] - tower_npc["y"]) < 60):
        diag_w = int(W * 0.76)
        diag_h = int(H * 0.30)
        d_rect = pygame.Rect((W - diag_w) // 2, int(H * 0.66), diag_w, diag_h)
        draw_feudal_panel(surface, d_rect, border_col=(212, 163, 75), bg_col=(18, 12, 12, 250), gold_corners=True)

        spk_surf = font_dialogue_name.render("ELDER SHINOBI MUSASHI  â€¢  KEEPER OF THE ASHEN RECORD", True, (255, 215, 80))
        surface.blit(spk_surf, (d_rect.x + 24, d_rect.y + 16))
        pygame.draw.line(surface, (140, 32, 28), (d_rect.x + 20, d_rect.y + 45), (d_rect.right - 20, d_rect.y + 45), 2)

        lore_lines = [
            "\"Ah, General Zhao... you have reached the Pagoda at last. Do you remember when you and the Magistrate trained",
            "together under the same moonlight as sworn brothers? Centuries ago, he was the greatest swordmaster of our realm.",
            "When war devastated the peak, he unearthed the cursed Ashen Blade beneath the mountain, seeking absolute power.",
            "The blade granted him titanic might, but hollowed his soul into an immortal monster. He no longer remembers his humanity.",
            "Only your blade can grant his tortured spirit eternal peace. Ascend through these mountain rafters to the",
            "Summit Sanctum, and finish what destiny began.\""
        ]
        curr_dy = d_rect.y + 55
        for ll in lore_lines:
            ll_surf = font_dialogue_body.render(ll, True, (240, 230, 210))
            surface.blit(ll_surf, (d_rect.x + 24, curr_dy))
            curr_dy += int(H * 0.026)

    # 15. Concept Explanation Modal (Shown at start until dismissed)
    if not tower_intro_dismissed:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((12, 8, 8, 225))
        surface.blit(overlay, (0, 0))

        modal_w = int(W * 0.68)
        modal_h = int(H * 0.66)
        m_rect = pygame.Rect((W - modal_w) // 2, (H - modal_h) // 2, modal_w, modal_h)
        draw_feudal_panel(surface, m_rect, border_col=(212, 163, 75), bg_col=(20, 14, 12, 250), gold_corners=True)

        t_title = font_tower_title.render("PAGODA OF THE ASHEN PEAK", True, (255, 220, 95))
        t_sub = font_sub.render("Prologue Ascent to The Hollow Magistrate", True, (212, 163, 75))
        surface.blit(t_title, t_title.get_rect(center=(W // 2, m_rect.y + int(H * 0.07))))
        surface.blit(t_sub, t_sub.get_rect(center=(W // 2, m_rect.y + int(H * 0.13))))
        pygame.draw.line(surface, (140, 32, 28), (m_rect.x + 40, m_rect.y + int(H * 0.17)), (m_rect.right - 40, m_rect.y + int(H * 0.17)), 2)

        instr = [
            ("1. Ascend the Mountain Pagoda", "Climb 3 vertical tiers across stone arches, rope bridges, and Torii terraces using [A]/[D] to run."),
            ("2. Ninja Double Jump", "Press [W] or [UP] to jump, and press [W] AGAIN in mid-air to DOUBLE JUMP! (Tower only)."),
            ("3. Slay Corrupted Ash Sentinels", "Guards patrol the platforms. 1 strike with Sword [Right Shift] or Kunai [Q] vanquishes them!"),
            ("4. Elder Musashi's Lore", "Visit Elder Musashi at the Torii Terrace on Tier II (hover with mouse) to discover the Magistrate's past."),
            ("5. Breach the Summit Sanctum", "Reach the moonlit peak to enter the gate and face the Hollow Magistrate!"),
        ]
        iy = m_rect.y + int(H * 0.20)
        for head, body in instr:
            h_s = font_bar_name.render(head, True, (255, 215, 80))
            b_s = font_guide_text.render(body, True, (230, 220, 205))
            surface.blit(h_s, (m_rect.x + 45, iy))
            surface.blit(b_s, (m_rect.x + 45, iy + int(H * 0.030)))
            iy += int(H * 0.072)

        start_btn = pygame.Rect(m_rect.centerx - int(W * 0.18), m_rect.bottom - int(H * 0.085), int(W * 0.36), int(H * 0.055))
        draw_button(surface, start_btn, "BEGIN ASCENT [PRESS SPACE]", start_btn.collidepoint(mouse_pos), primary_col=(140, 32, 28))


# ---------------------------------------------------------------------------
# Main Game Loop State
# ---------------------------------------------------------------------------
game_state = "MENU"   # "MENU", "CONTROLS", "TOWER", "PLAYING", "ROUND_WON", "BOUNCE_BACK", "FINAL_BOUNCE_BACK", "MATCH_VICTORY", "MATCH_DEFEAT"
previous_game_state = "PLAYING"
scroll_y = 0
frame_count = 0
running = True

btn_w = int(W * 0.34)
btn_h = int(H * 0.052)
btn_x = (W - btn_w) // 2

# Main Menu Buttons
btn_start_rect = pygame.Rect(btn_x, int(H * 0.48), btn_w, btn_h)
btn_boss_rect = pygame.Rect(btn_x, int(H * 0.55), btn_w, btn_h)
btn_guide_rect = pygame.Rect(btn_x, int(H * 0.62), btn_w, btn_h)
btn_exit_rect = pygame.Rect(btn_x, int(H * 0.69), btn_w, btn_h)

btn_back_rect = pygame.Rect(int(W * 0.05), int(H * 0.90), int(W * 0.16), int(H * 0.055))

# Round End & Pause Buttons
btn_continue_rect = pygame.Rect(btn_x, int(H * 0.48), btn_w, btn_h)
btn_restart_boss_rect = pygame.Rect(btn_x, int(H * 0.55), btn_w, btn_h)
btn_restart_game_rect = pygame.Rect(btn_x, int(H * 0.62), btn_w, btn_h)
btn_menu_rect = pygame.Rect(btn_x, int(H * 0.69), btn_w, btn_h)


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
                if game_state in ("TOWER", "PLAYING", "ROUND_WON", "BOUNCE_BACK", "FINAL_BOUNCE_BACK", "MATCH_VICTORY", "MATCH_DEFEAT"):
                    game_state = "MENU"
                elif game_state == "CONTROLS":
                    game_state = previous_game_state
                elif game_state == "MENU":
                    running = False

            if event.key == pygame.K_SPACE:
                if game_state == "PLAYING":
                    previous_game_state = "PLAYING"
                    game_state = "CONTROLS"
                elif game_state == "TOWER":
                    if not tower_intro_dismissed:
                        tower_intro_dismissed = True
                        play_sfx("slash_hit", 0.7)
                    else:
                        previous_game_state = "TOWER"
                        game_state = "CONTROLS"
                elif game_state == "CONTROLS":
                    game_state = previous_game_state
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
                if game_state in ("ROUND_WON", "BOUNCE_BACK", "FINAL_BOUNCE_BACK", "MATCH_VICTORY", "MATCH_DEFEAT", "CONTROLS"):
                    reset_full_match()

            if event.key == pygame.K_g:
                if game_state in ("ROUND_WON", "BOUNCE_BACK", "FINAL_BOUNCE_BACK", "MATCH_VICTORY", "MATCH_DEFEAT", "CONTROLS", "TOWER"):
                    reset_entire_game()

            # The ONLY remaining testing key: [T] Deletes 200 HP from the boss
            if game_state == "PLAYING":
                if event.key == pygame.K_t:
                    if boss["state"] in ("enrage_intro", "ascend", "airborne", "descend"):
                        play_sfx("block_wood", 0.8)
                    else:
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
        play_bgm("bgm_normal", vol=0.45)
        screen.blit(bg, (0, 0))

        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((14, 10, 8, 175))
        screen.blit(dim, (0, 0))

        # Title Emblem
        t_surf = font_title.render("SHINOBI : LEGEND OF ZHAO", True, (245, 225, 185))
        t_shadow = font_title.render("SHINOBI : LEGEND OF ZHAO", True, (20, 8, 8))
        t_rect = t_surf.get_rect(center=(W // 2, int(H * 0.22)))
        screen.blit(t_shadow, (t_rect.x + 3, t_rect.y + 3))
        screen.blit(t_surf, t_rect)

        sub_surf = font_sub.render("Pagoda Tower Descent  â€¢  Best of 5 Hollow Magistrate Encounter", True, (212, 163, 75))
        screen.blit(sub_surf, sub_surf.get_rect(center=(W // 2, int(H * 0.30))))

        draw_crossed_swords(screen, W // 2, int(H * 0.39), radius=int(H * 0.040))

        draw_button(screen, btn_start_rect, "ENTER PAGODA (START GAME)", btn_start_rect.collidepoint(mouse_pos), primary_col=(140, 32, 28))
        draw_button(screen, btn_boss_rect, "PRACTICE BOSS FIGHT (DIRECT)", btn_boss_rect.collidepoint(mouse_pos), primary_col=(115, 38, 25))
        draw_button(screen, btn_guide_rect, "COMBAT GUIDE & CONTROLS", btn_guide_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))
        draw_button(screen, btn_exit_rect, "EXIT TO DESKTOP", btn_exit_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        if mouse_clicked:
            if btn_start_rect.collidepoint(mouse_pos):
                reset_entire_game()
            elif btn_boss_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_guide_rect.collidepoint(mouse_pos):
                previous_game_state = "MENU"
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

        content_box = pygame.Rect(int(W * 0.08), int(H * 0.05), int(W * 0.84), int(H * 0.82))
        draw_feudal_panel(screen, content_box, border_col=(140, 32, 28), bg_col=(20, 14, 12, 240))

        g_title = font_guide_head.render("HAVEN HACKATHON â€” SHINOBI COMBAT MANUAL", True, (245, 225, 185))
        screen.blit(g_title, g_title.get_rect(center=(W // 2, int(H * 0.10))))
        pygame.draw.line(screen, (212, 163, 75), (int(W * 0.15), int(H * 0.14)), (int(W * 0.85), int(H * 0.14)), 2)

        clip_area = pygame.Rect(int(W * 0.10), int(H * 0.16), int(W * 0.80), int(H * 0.69))
        screen.set_clip(clip_area)

        curr_y = int(H * 0.17) + scroll_y
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

        # Bottom Action Bar in Controls
        ctrl_w = int(W * 0.20)
        ctrl_h = int(H * 0.052)
        btn_c_resume = pygame.Rect(int(W * 0.08), int(H * 0.89), ctrl_w, ctrl_h)
        btn_c_boss = pygame.Rect(int(W * 0.31), int(H * 0.89), ctrl_w, ctrl_h)
        btn_c_game = pygame.Rect(int(W * 0.54), int(H * 0.89), ctrl_w, ctrl_h)
        btn_c_menu = pygame.Rect(int(W * 0.77), int(H * 0.89), int(W * 0.15), ctrl_h)

        draw_button(screen, btn_c_resume, "< RESUME [SPACE]", btn_c_resume.collidepoint(mouse_pos), primary_col=(35, 120, 50))
        draw_button(screen, btn_c_boss, "RESTART BOSS [R]", btn_c_boss.collidepoint(mouse_pos), primary_col=(140, 32, 28))
        draw_button(screen, btn_c_game, "RESTART GAME [G]", btn_c_game.collidepoint(mouse_pos), primary_col=(95, 30, 26))
        draw_button(screen, btn_c_menu, "MENU [ESC]", btn_c_menu.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        if mouse_clicked:
            if btn_c_resume.collidepoint(mouse_pos):
                game_state = previous_game_state
            elif btn_c_boss.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_c_game.collidepoint(mouse_pos):
                reset_entire_game()
            elif btn_c_menu.collidepoint(mouse_pos):
                reset_entire_game()
                game_state = "MENU"

    # -----------------------------------------------------------------------
    # 2b. State: TOWER (Vertical Platformer Tower Level)
    # -----------------------------------------------------------------------
    elif game_state == "TOWER":
        keys = pygame.key.get_pressed()
        update_tower_level(keys, mouse_pos, mouse_clicked)
        draw_tower_level(screen, mouse_pos)

    # -----------------------------------------------------------------------
    # 3. State: PLAYING
    # -----------------------------------------------------------------------
    elif game_state == "PLAYING":
        p = player
        b = boss
        keys = pygame.key.get_pressed()

        # Phase Calculation
        is_enraged = (b["hp"] <= b["max_hp"] * 0.33)  # Phase 3 is Enraged Mode!
        if is_enraged:
            boss_phase = 3
        elif b["hp"] <= b["max_hp"] * 0.66:
            boss_phase = 2
        else:
            boss_phase = 1

        # Japanese Combat Music (Normal loop, intensified during Enraged mode / Phase 3)
        if is_enraged or boss_phase == 3:
            play_bgm("bgm_enraged", vol=0.75)
        else:
            play_bgm("bgm_normal", vol=0.65)

        # Enraged Mode Transition (5.5s dark roar sequence with 100% invulnerability)
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
                        # Boss Invulnerability during phase transitions & aerial slam
                        if b["state"] in ("enrage_intro", "ascend", "airborne", "descend"):
                            spawn_sparks(b["x"], b["y"] - boss_h * 0.5, count=6, is_golden=False)
                            play_sfx("block_wood", 0.7)
                        elif b["is_stunned"]:
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

        elif b["state"] == "ascend":
            # 1.5x Faster Ascent (40 ticks = ~0.67s) - boss is invulnerable!
            b["vx"] = 0.0
            b["slam_timer"] -= 1
            progress = (40 - b["slam_timer"]) / 40.0
            b["frame_idx"] = min(len(boss_ascent_frames) - 1, int(progress * len(boss_ascent_frames)))

            # Boss leaps upward into the heavens
            if progress > 0.35:
                b["y"] = GROUND_Y - int(((progress - 0.35) / 0.65) * (H * 0.85))

            if b["slam_timer"] <= 0:
                b["state"] = "airborne"
                b["slam_timer"] = 60  # 1.0 second in air (red indicator appears 1.0s before descent!)
                b["y"] = -400
                # Randomize landing location near player
                offset = random.choice([-1, 1]) * random.randint(30, int(W * 0.16))
                b["slam_target_x"] = max(int(W * 0.16), min(int(W * 0.86), p["x"] + offset))

        elif b["state"] == "airborne":
            b["vx"] = 0.0
            b["y"] = -400
            b["slam_timer"] -= 1
            if b["slam_timer"] <= 0:
                b["state"] = "descend"
                b["slam_timer"] = 40  # 1.5x Faster Descent (40 ticks = ~0.67s)
                b["frame_idx"] = 0
                b["x"] = b["slam_target_x"]
                b["y"] = GROUND_Y
                b["slam_hit"] = False
                b["facing_right"] = (p["x"] > b["x"])

        elif b["state"] == "descend":
            # 1.5x Faster Descent (40 ticks = ~0.67s) - boss is invulnerable!
            b["vx"] = 0.0
            b["y"] = GROUND_Y
            b["slam_timer"] -= 1
            progress = (40 - b["slam_timer"]) / 40.0
            b["frame_idx"] = min(len(boss_descent_frames) - 1, int(progress * len(boss_descent_frames)))

            # Descent crash impact happens around frame 17-20 (progress >= 0.58)
            if progress >= 0.58 and not b["slam_hit"]:
                b["slam_hit"] = True
                ground_shake_timer = 120
                ground_shake_intensity = 26.0
                play_sfx("ground_slam", 1.0)
                spawn_sparks(b["x"], GROUND_Y, count=35, is_golden=True)

                # AOE damage to player
                dist_to_player = abs(b["x"] - p["x"])
                if dist_to_player < int(W * 0.22):
                    if p["state"] == "dodge":
                        pass  # clean dodge through i-frames
                    elif p["state"] == "parry" and p["frame_idx"] <= 14:
                        # Perfect parry!
                        play_sfx("parry_metal", 1.0)
                        spawn_sparks(p["x"], p["y"] - player_h * 0.5, count=28, is_golden=True)
                        b["posture"] = min(b["max_posture"], b["posture"] + 30.0)
                        b["posture_decay_delay"] = 0
                    elif p["state"] == "parry":
                        # Block (60% damage mitigation)
                        play_sfx("block_wood", 0.9)
                        slam_dmg = 45 if boss_phase == 3 else (36 if boss_phase == 2 else 28)
                        p["hp"] = max(0, p["hp"] - int(slam_dmg * 0.40))
                        spawn_sparks(p["x"], p["y"] - player_h * 0.5, count=10, is_golden=False)
                    else:
                        # Direct crash impact!
                        slam_dmg = 45 if boss_phase == 3 else (36 if boss_phase == 2 else 28)
                        p["hp"] = max(0, p["hp"] - slam_dmg)
                        play_sfx("slash_hit", 1.0)

            if b["slam_timer"] <= 0:
                b["state"] = "idle"
                b["frame_idx"] = 0
                b["tick_count"] = 0
                b["y"] = GROUND_Y

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
                    # At range: Spear throw or Sky Leap (Aerial Slam)
                    chosen_atk = random.choices(["spear", "ascend"], weights=[0.65, 0.35])[0]
                    b["state"] = chosen_atk
                    b["frame_idx"] = 0
                    b["tick_count"] = 0
                    b["projectile_spawned"] = False
                    if chosen_atk == "ascend":
                        b["slam_timer"] = 40
                else:
                    # In melee: Greatsword Smash, Kunai, or Sky Leap (Aerial Slam)
                    chosen_atk = random.choices(["smash", "kunai", "ascend"], weights=[0.45, 0.25, 0.30])[0]
                    b["state"] = chosen_atk
                    b["frame_idx"] = 0
                    b["tick_count"] = 0
                    b["projectile_spawned"] = False
                    b["smash_hit"] = False
                    if chosen_atk == "ascend":
                        b["slam_timer"] = 40

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
                        # Boss Invulnerability during transitions and aerial slam
                        if b["state"] in ("enrage_intro", "ascend", "airborne", "descend"):
                            spawn_sparks(proj["x"], proj["y"], count=6, is_golden=False)
                            play_sfx("block_wood", 0.6)
                        else:
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
            stop_bgm(400)
            player_round_wins += 1
            if player_round_wins >= 3:
                game_state = "MATCH_VICTORY"
            else:
                game_state = "ROUND_WON"

        elif p["hp"] <= 0:
            stop_bgm(400)
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
        b_sprite = None
        if b["state"] == "enrage_intro":
            b_sprite = boss_enrage_frames[b["frame_idx"] % len(boss_enrage_frames)]
            b_draw_x = int(b["x"] - be_center) + shake_x
            b_draw_y = int(b["y"] - be_feet) + shake_y
        elif b["state"] == "walk":
            b_sprite = boss_walk_frames[b["frame_idx"] % len(boss_walk_frames)]
            b_draw_x = int(b["x"] - bw_center) + shake_x
            b_draw_y = int(b["y"] - bw_feet) + shake_y
        elif b["state"] in ("idle", "stunned"):
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
        elif b["state"] == "ascend":
            b_sprite = boss_ascent_frames[b["frame_idx"] % len(boss_ascent_frames)]
            b_draw_x = int(b["x"] - basc_center) + shake_x
            b_draw_y = int(b["y"] - basc_feet) + shake_y
        elif b["state"] == "airborne":
            b_sprite = None
        elif b["state"] == "descend":
            b_sprite = boss_descent_frames[b["frame_idx"] % len(boss_descent_frames)]
            b_draw_x = int(b["x"] - bdesc_center) + shake_x
            b_draw_y = int(b["y"] - bdesc_feet) + shake_y

        # Aerial Slam Red Light Indicator (Appears 1 second before descent and during descent)
        if (b["state"] == "airborne" and b["slam_timer"] <= 60) or (b["state"] == "descend"):
            ind_x = int(b["slam_target_x"]) + shake_x
            pulse = abs(math.sin(frame_count * 0.32))

            # 1. Vertical red light pillar from the heavens
            beam_w = int(24 + 18 * pulse)
            beam_surf = pygame.Surface((beam_w, H), pygame.SRCALPHA)
            for bi in range(beam_w // 2):
                alpha = int((65 + 75 * pulse) * (1.0 - (bi / (beam_w / 2.0))))
                pygame.draw.line(beam_surf, (255, 30, 30, alpha), (beam_w // 2 - bi, 0), (beam_w // 2 - bi, H))
                pygame.draw.line(beam_surf, (255, 30, 30, alpha), (beam_w // 2 + bi, 0), (beam_w // 2 + bi, H))
            # Bright inner ray
            pygame.draw.line(beam_surf, (255, 235, 235, 220), (beam_w // 2, 0), (beam_w // 2, H), 3)
            screen.blit(beam_surf, (ind_x - beam_w // 2, 0))

            # 2. Red Light Warning Indicator beacon at the top of the screen
            beacon_y = 4
            beacon_sz = int(18 + 7 * pulse)
            pts = [
                (ind_x - beacon_sz, beacon_y),
                (ind_x + beacon_sz, beacon_y),
                (ind_x, beacon_y + int(beacon_sz * 1.8))
            ]
            pygame.draw.polygon(screen, (255, 35, 35), pts)
            pygame.draw.polygon(screen, (255, 240, 200), pts, 2)
            pygame.draw.circle(screen, (255, 255, 255), (ind_x, beacon_y + int(beacon_sz * 0.65)), max(2, int(4 * pulse + 2)))

            # 3. Ground Impact Target Reticle
            ring_rad = int(W * 0.09)
            ring_surf = pygame.Surface((ring_rad * 2 + 10, int(ring_rad * 0.6) + 10), pygame.SRCALPHA)
            r_rect = pygame.Rect(5, 5, ring_rad * 2, int(ring_rad * 0.6))
            pygame.draw.ellipse(ring_surf, (255, 40, 40, int(110 + 90 * pulse)), r_rect, 3)
            pygame.draw.line(ring_surf, (255, 220, 220, int(130 + 80 * pulse)), (ring_rad + 5, 2), (ring_rad + 5, int(ring_rad * 0.6) + 8), 2)
            screen.blit(ring_surf, (ind_x - ring_rad - 5, GROUND_Y - int(ring_rad * 0.3) + shake_y))

        if b_sprite is not None:
            if not b["facing_right"]:
                b_sprite = pygame.transform.flip(b_sprite, True, False)

            if is_enraged and b["state"] not in ("enrage_intro", "ascend", "descend"):
                pulse = abs(math.sin(frame_count * 0.28))
                outline_alpha = int(140 + 115 * pulse)
                mask = pygame.mask.from_surface(b_sprite)
                outline_surf = mask.to_surface(setcolor=(255, 25, 25, outline_alpha), unsetcolor=(0, 0, 0, 0))
                for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)]:
                    screen.blit(outline_surf, (b_draw_x + ox, b_draw_y + oy))

            screen.blit(b_sprite, (b_draw_x, b_draw_y))

        if b["state"] == "enrage_intro":
            # Dark Roar Invincibility Barrier Aura & Banner
            e_pulse = abs(math.sin(frame_count * 0.35))
            barrier_rad = int(boss_h * 0.68 + 10 * e_pulse)
            b_surf = pygame.Surface((barrier_rad * 2 + 12, barrier_rad * 2 + 12), pygame.SRCALPHA)
            pygame.draw.circle(b_surf, (220, 25, 25, int(65 + 55 * e_pulse)), (barrier_rad + 6, barrier_rad + 6), barrier_rad, 4)
            pygame.draw.circle(b_surf, (255, 140, 140, int(45 + 45 * e_pulse)), (barrier_rad + 6, barrier_rad + 6), barrier_rad - 6, 2)
            screen.blit(b_surf, (int(b["x"] - barrier_rad - 6) + shake_x, int(b["y"] - be_feet * 0.6 - barrier_rad - 6) + shake_y))

            inv_txt = font_stun_banner.render("âš¡ MAGISTRATE ENRAGING â€” INVULNERABLE âš¡", True, (255, 70, 70))
            inv_shadow = font_stun_banner.render("âš¡ MAGISTRATE ENRAGING â€” INVULNERABLE âš¡", True, (20, 0, 0))
            inv_rect = inv_txt.get_rect(center=(int(b["x"]) + shake_x, int(b["y"] - boss_h * 1.15) + shake_y))
            screen.blit(inv_shadow, (inv_rect.x + 2, inv_rect.y + 2))
            screen.blit(inv_txt, inv_rect)

        if b["is_stunned"]:
            st_text = font_stun_banner.render("â˜… POSTURE BROKEN â€” CRITICAL STRIKE! â˜…", True, (255, 220, 60))
            st_shadow = font_stun_banner.render("â˜… POSTURE BROKEN â€” CRITICAL STRIKE! â˜…", True, (20, 10, 5))
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

        box = pygame.Rect((W - int(W * 0.68)) // 2, int(H * 0.12), int(W * 0.68), int(H * 0.76))
        draw_feudal_panel(screen, box, border_col=(212, 163, 75), bg_col=(20, 14, 10, 245), gold_corners=True)

        rw_title = font_end_title.render("ROUND WON", True, (255, 220, 95))
        rw_shadow = font_end_title.render("ROUND WON", True, (20, 10, 5))
        rw_rect = rw_title.get_rect(center=(W // 2, int(H * 0.20)))
        screen.blit(rw_shadow, (rw_rect.x + 3, rw_rect.y + 3))
        screen.blit(rw_title, rw_rect)

        sub_str = f"Great General Zhao claims Round {current_round}! The next round is starting..."
        rw_sub = font_end_sub.render(sub_str, True, (240, 230, 200))
        screen.blit(rw_sub, rw_sub.get_rect(center=(W // 2, int(H * 0.28))))

        score_info = f"Current Match Score: Zhao {player_round_wins} â€” {boss_round_wins} Hollow Magistrate"
        rw_score = font_bar_val.render(score_info, True, (215, 185, 110))
        screen.blit(rw_score, rw_score.get_rect(center=(W // 2, int(H * 0.34))))

        draw_crossed_swords(screen, W // 2, int(H * 0.40), radius=int(H * 0.032))

        draw_button(screen, btn_continue_rect, f"CONTINUE TO ROUND {current_round + 1}", btn_continue_rect.collidepoint(mouse_pos), primary_col=(35, 120, 50))
        draw_button(screen, btn_restart_boss_rect, "RESTART BOSS FIGHT", btn_restart_boss_rect.collidepoint(mouse_pos), primary_col=(140, 32, 28))
        draw_button(screen, btn_restart_game_rect, "RESTART ENTIRE GAME (PAGODA)", btn_restart_game_rect.collidepoint(mouse_pos), primary_col=(95, 30, 26))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        hint = font_bar_val.render("Press [ENTER] to Continue  |  [R] Restart Boss  |  [G] Restart Entire Game  |  [ESC] Menu", True, (200, 190, 160))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.77))))

        if mouse_clicked:
            if btn_continue_rect.collidepoint(mouse_pos):
                start_next_round()
            elif btn_restart_boss_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_restart_game_rect.collidepoint(mouse_pos):
                reset_entire_game()
            elif btn_menu_rect.collidepoint(mouse_pos):
                reset_entire_game()
                game_state = "MENU"

    # -----------------------------------------------------------------------
    # 5. State: BOUNCE_BACK (Player 1st Loss: Big letters + HP Buff)
    # -----------------------------------------------------------------------
    elif game_state == "BOUNCE_BACK":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((25, 6, 6, 225))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((W - int(W * 0.68)) // 2, int(H * 0.12), int(W * 0.68), int(H * 0.76))
        draw_feudal_panel(screen, box, border_col=(212, 163, 75), bg_col=(22, 10, 10, 245), gold_corners=True)

        bb_title = font_bounce_back.render("BOUNCE BACK", True, (255, 215, 80))
        bb_shadow = font_bounce_back.render("BOUNCE BACK", True, (30, 0, 0))
        bb_rect = bb_title.get_rect(center=(W // 2, int(H * 0.20)))
        screen.blit(bb_shadow, (bb_rect.x + 4, bb_rect.y + 4))
        screen.blit(bb_title, bb_rect)

        bb_sub = font_end_sub.render(f"General Zhao fell in Round {current_round}! Play again to receive an HP Buff (+30 Max HP)!", True, (240, 225, 200))
        screen.blit(bb_sub, bb_sub.get_rect(center=(W // 2, int(H * 0.28))))

        perk_msg = f"Perk Granted: Max HP boosted from 100 to 130 for Round {current_round + 1}!"
        bb_perk = font_bar_val.render(perk_msg, True, (110, 245, 130))
        screen.blit(bb_perk, bb_perk.get_rect(center=(W // 2, int(H * 0.34))))

        draw_crossed_swords(screen, W // 2, int(H * 0.40), radius=int(H * 0.032))

        draw_button(screen, btn_continue_rect, f"PLAY AGAIN WITH BUFF (ROUND {current_round + 1})", btn_continue_rect.collidepoint(mouse_pos), primary_col=(160, 30, 26))
        draw_button(screen, btn_restart_boss_rect, "RESTART BOSS FIGHT", btn_restart_boss_rect.collidepoint(mouse_pos), primary_col=(140, 32, 28))
        draw_button(screen, btn_restart_game_rect, "RESTART ENTIRE GAME (PAGODA)", btn_restart_game_rect.collidepoint(mouse_pos), primary_col=(95, 30, 26))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        hint = font_bar_val.render("Press [ENTER] to Play Again  |  [R] Restart Boss  |  [G] Restart Entire Game  |  [ESC] Menu", True, (210, 180, 180))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.77))))

        if mouse_clicked:
            if btn_continue_rect.collidepoint(mouse_pos):
                start_next_round()
            elif btn_restart_boss_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_restart_game_rect.collidepoint(mouse_pos):
                reset_entire_game()
            elif btn_menu_rect.collidepoint(mouse_pos):
                reset_entire_game()
                game_state = "MENU"

    # -----------------------------------------------------------------------
    # 6. State: FINAL_BOUNCE_BACK (Player 2nd Loss: Movement & Atk Speed Buff)
    # -----------------------------------------------------------------------
    elif game_state == "FINAL_BOUNCE_BACK":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((30, 4, 4, 230))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((W - int(W * 0.68)) // 2, int(H * 0.12), int(W * 0.68), int(H * 0.76))
        draw_feudal_panel(screen, box, border_col=(255, 60, 60), bg_col=(24, 8, 8, 245), gold_corners=True)

        fbb_title = font_bounce_back.render("FINAL BOUNCE BACK", True, (255, 80, 60))
        fbb_shadow = font_bounce_back.render("FINAL BOUNCE BACK", True, (20, 0, 0))
        fbb_rect = fbb_title.get_rect(center=(W // 2, int(H * 0.20)))
        screen.blit(fbb_shadow, (fbb_rect.x + 4, fbb_rect.y + 4))
        screen.blit(fbb_title, fbb_rect)

        fbb_sub = font_end_sub.render(f"On the brink! Play again to receive Movement Speed & Attack Speed Buffs!", True, (255, 220, 200))
        screen.blit(fbb_sub, fbb_sub.get_rect(center=(W // 2, int(H * 0.28))))

        perk_msg = f"Perks Active: +30 Max HP  â€¢  +25% Movement Speed  â€¢  +25% Attack Speed!"
        fbb_perk = font_bar_val.render(perk_msg, True, (100, 240, 255))
        screen.blit(fbb_perk, fbb_perk.get_rect(center=(W // 2, int(H * 0.34))))

        draw_crossed_swords(screen, W // 2, int(H * 0.40), radius=int(H * 0.032))

        draw_button(screen, btn_continue_rect, f"PLAY AGAIN WITH BUFFS (ROUND {current_round + 1})", btn_continue_rect.collidepoint(mouse_pos), primary_col=(175, 30, 26))
        draw_button(screen, btn_restart_boss_rect, "RESTART BOSS FIGHT", btn_restart_boss_rect.collidepoint(mouse_pos), primary_col=(140, 32, 28))
        draw_button(screen, btn_restart_game_rect, "RESTART ENTIRE GAME (PAGODA)", btn_restart_game_rect.collidepoint(mouse_pos), primary_col=(95, 30, 26))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        hint = font_bar_val.render("Press [ENTER] to Play Again  |  [R] Restart Boss  |  [G] Restart Entire Game  |  [ESC] Menu", True, (220, 180, 180))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.77))))

        if mouse_clicked:
            if btn_continue_rect.collidepoint(mouse_pos):
                start_next_round()
            elif btn_restart_boss_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_restart_game_rect.collidepoint(mouse_pos):
                reset_entire_game()
            elif btn_menu_rect.collidepoint(mouse_pos):
                reset_entire_game()
                game_state = "MENU"

    # -----------------------------------------------------------------------
    # 7. State: MATCH_DEFEAT (Player loses 3 rounds -> Magistrate Wins)
    # -----------------------------------------------------------------------
    elif game_state == "MATCH_DEFEAT":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((30, 5, 5, 235))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((W - int(W * 0.68)) // 2, int(H * 0.12), int(W * 0.68), int(H * 0.76))
        draw_feudal_panel(screen, box, border_col=(180, 32, 28), bg_col=(24, 8, 8, 250), gold_corners=True)

        d_title = font_end_title.render("THE MAGISTRATE WINS", True, (245, 45, 45))
        d_shadow = font_end_title.render("THE MAGISTRATE WINS", True, (15, 0, 0))
        d_rect = d_title.get_rect(center=(W // 2, int(H * 0.20)))
        screen.blit(d_shadow, (d_rect.x + 4, d_rect.y + 4))
        screen.blit(d_title, d_rect)

        d_sub = font_end_sub.render(f"The Hollow Magistrate has claimed 3 rounds to conquer the match! Will you try again?", True, (235, 200, 200))
        screen.blit(d_sub, d_sub.get_rect(center=(W // 2, int(H * 0.28))))

        score_info = f"Final Score: Hollow Magistrate {boss_round_wins} â€” {player_round_wins} Great General Zhao"
        d_score = font_bar_val.render(score_info, True, (215, 120, 110))
        screen.blit(d_score, d_score.get_rect(center=(W // 2, int(H * 0.34))))

        draw_crossed_swords(screen, W // 2, int(H * 0.40), radius=int(H * 0.032))

        draw_button(screen, btn_continue_rect, "TRY AGAIN (NEW MATCH)", btn_continue_rect.collidepoint(mouse_pos), primary_col=(175, 30, 26))
        draw_button(screen, btn_restart_boss_rect, "RESTART BOSS FIGHT", btn_restart_boss_rect.collidepoint(mouse_pos), primary_col=(140, 32, 28))
        draw_button(screen, btn_restart_game_rect, "RESTART ENTIRE GAME (PAGODA)", btn_restart_game_rect.collidepoint(mouse_pos), primary_col=(95, 30, 26))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        hint = font_bar_val.render("Press [ENTER] to Try Again  |  [R] Restart Boss  |  [G] Restart Entire Game  |  [ESC] Menu", True, (200, 160, 160))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.77))))

        if mouse_clicked:
            if btn_continue_rect.collidepoint(mouse_pos) or btn_restart_boss_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_restart_game_rect.collidepoint(mouse_pos):
                reset_entire_game()
            elif btn_menu_rect.collidepoint(mouse_pos):
                reset_entire_game()
                game_state = "MENU"

    # -----------------------------------------------------------------------
    # 8. State: MATCH_VICTORY (Player wins 3 rounds -> Zhao claims triumph)
    # -----------------------------------------------------------------------
    elif game_state == "MATCH_VICTORY":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((14, 10, 6, 220))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((W - int(W * 0.68)) // 2, int(H * 0.12), int(W * 0.68), int(H * 0.76))
        draw_feudal_panel(screen, box, border_col=(212, 163, 75), bg_col=(20, 14, 10, 250), gold_corners=True)

        v_title = font_end_title.render("MATCH VICTORY", True, (255, 220, 95))
        v_shadow = font_end_title.render("MATCH VICTORY", True, (20, 10, 5))
        v_rect = v_title.get_rect(center=(W // 2, int(H * 0.20)))
        screen.blit(v_shadow, (v_rect.x + 3, v_rect.y + 3))
        screen.blit(v_title, v_rect)

        v_sub = font_end_sub.render(f"Great General Zhao claims match triumph ({player_round_wins} - {boss_round_wins})! The Magistrate is vanquished!", True, (240, 230, 200))
        screen.blit(v_sub, v_sub.get_rect(center=(W // 2, int(H * 0.28))))

        score_info = f"Final Score: Great General Zhao {player_round_wins} â€” {boss_round_wins} The Hollow Magistrate"
        v_score = font_bar_val.render(score_info, True, (212, 185, 90))
        screen.blit(v_score, v_score.get_rect(center=(W // 2, int(H * 0.34))))

        draw_crossed_swords(screen, W // 2, int(H * 0.40), radius=int(H * 0.032))

        draw_button(screen, btn_continue_rect, "PLAY AGAIN (NEW MATCH)", btn_continue_rect.collidepoint(mouse_pos), primary_col=(35, 125, 55))
        draw_button(screen, btn_restart_boss_rect, "RESTART BOSS FIGHT", btn_restart_boss_rect.collidepoint(mouse_pos), primary_col=(140, 32, 28))
        draw_button(screen, btn_restart_game_rect, "RESTART ENTIRE GAME (PAGODA)", btn_restart_game_rect.collidepoint(mouse_pos), primary_col=(95, 30, 26))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(35, 30, 28))

        hint = font_bar_val.render("Press [ENTER] to Play Again  |  [R] Restart Boss  |  [G] Restart Entire Game  |  [ESC] Menu", True, (200, 190, 160))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.77))))

        if mouse_clicked:
            if btn_continue_rect.collidepoint(mouse_pos) or btn_restart_boss_rect.collidepoint(mouse_pos):
                reset_full_match()
            elif btn_restart_game_rect.collidepoint(mouse_pos):
                reset_entire_game()
            elif btn_menu_rect.collidepoint(mouse_pos):
                reset_entire_game()
                game_state = "MENU"

    # Display Flip & Tick
    pygame.display.flip()
    clock.tick(60)

pygame.quit()

