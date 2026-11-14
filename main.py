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
            frame = sheet.subsurface(rect).copy()
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
# Player Sprites & Animations
# ---------------------------------------------------------------------------
PLAYER_SCALE = FLAG_SCALE * 1.10
player_h = int(H * PLAYER_SCALE)

# 1. 30-frame sheets (Walking, Rolling/Dodge, Slash, Parry)
raw_walk_frames = extract_grid_frames("walking_30_frames.png", 5, 6)
raw_dodge_frames = extract_grid_frames("rolling_30_frames.png", 5, 6)
raw_slash_frames = extract_grid_frames("basic_slash_30_frames.png", 5, 6)
raw_parry_frames = extract_grid_frames("perfect_parry_30_frames.png", 5, 6)

sheet_scale = player_h / 270.0
frame_w = int(360 * sheet_scale)
frame_h = int(360 * sheet_scale)
feet_offset = int(337 * sheet_scale)
center_offset = frame_w // 2

walk_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_walk_frames]
dodge_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_dodge_frames]
slash_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_slash_frames]
parry_frames = [pygame.transform.smoothscale(f, (frame_w, frame_h)) for f in raw_parry_frames]

# 2. Idle Animation: Blink style
raw_idle_open = raw_slash_frames[0].copy()
raw_idle_blink = raw_slash_frames[0].copy()
eyelid_color = (48, 38, 38, 255)
for ex in range(186, 194):
    for ey in range(101, 104):
        raw_idle_blink.set_at((ex, ey), eyelid_color)

idle_open = pygame.transform.smoothscale(raw_idle_open, (frame_w, frame_h))
idle_blink = pygame.transform.smoothscale(raw_idle_blink, (frame_w, frame_h))

# 3. Kunai Throw
raw_kunai_frames = extract_grid_frames("player_kunai.png", 3, 7)
kunai_scale = player_h / 128.0
kunai_w = int(146 * kunai_scale)
kunai_h = int(146 * kunai_scale)
kunai_feet_offset = int(140 * kunai_scale)
kunai_center_offset = kunai_w // 2
kunai_frames = [pygame.transform.smoothscale(f, (kunai_w, kunai_h)) for f in raw_kunai_frames]

# ---------------------------------------------------------------------------
# Entities (Player & Boss)
# ---------------------------------------------------------------------------
GROUND_Y = flag1_bottom[1]
GRAVITY = 0.65
JUMP_FORCE = -14
WALK_SPEED = 5
DODGE_SPEED = 9

player = {
    "x": int(W * 0.05),
    "y": GROUND_Y,
    "vy": 0,
    "on_ground": True,
    "facing_right": True,
    "state": "idle",
    "frame_idx": 0,
    "tick_count": 0,
    "blink_timer": random.randint(120, 180),
    "is_blinking": False,
    # Health & Combat stats
    "hp": 100,
    "max_hp": 100,
    "displayed_hp": 100.0,
}

boss = {
    "name": "Titan",
    "hp": 1000,
    "max_hp": 1000,
    "displayed_hp": 1000.0,
    "phase": "Normal",
    "enrage_timer": 30.0,
}


def reset_battle():
    """Resets both player and boss to initial state for a fresh battle."""
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

    boss["hp"] = boss["max_hp"]
    boss["displayed_hp"] = float(boss["max_hp"])
    boss["phase"] = "Normal"
    boss["enrage_timer"] = 30.0


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
            "  [ Left Shift ] : Dodge (Forward evasive roll)",
            "  [ Right Shift ]: Sword Slash (High-impact combo)",
            "  [ Q ]          : Throw Kunai (Ranged energy projectile)",
            "  [ F ]          : Parry (Defensive counter-stance)",
            "  [ G ]          : Ultimate Ability",
            "  [ Spacebar ]   : Pause Menu (Time Rewind 10s, Reset, Keybinds)",
            "  [ K ]          : Self-Damage Test (-25 HP to test Defeat screen)",
            "  [ T ]          : Strike Titan Test (-200 HP to test Victory screen)",
            "  [ Esc ]        : Return to Menu / Exit Game",
        ]
    },
    {
        "title": "COMBAT RULES & MECHANICS",
        "color": (255, 140, 140),
        "lines": [
            "  • Parry Risk/Reward : Precise parry reflects attacks safely.",
            "                        MISSING parry timing inflicts HIGHER damage penalty than not parrying!",
            "  • Attack & Movement: Walking utilizes fluid movement cycles without triggering attack animations.",
            "  • UI Displays       : Live Player Health Bar, Boss Health Bar, Ability Cooldowns, and Health Flasks.",
        ]
    },
    {
        "title": "BOSS: TITAN",
        "color": (255, 180, 80),
        "lines": [
            "  • Long-Range Spear Throw : Piercing high-velocity ranged strike.",
            "  • Damage Sphere Boost    : Prior to last 10% HP, Titan deals increased damage the closer you get.",
            "  • Area Ripple Shockwave  : Ground wave that sweeps across the arena.",
            "  • Last 10% Enrage Phase  : At <= 10% HP, Titan transitions to brutal close-range strikes with a",
            "                             30-SECOND TIMER to defeat him or trigger INSTANT DEATH!",
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

    # Background
    pygame.draw.rect(surface, btn_col, rect, border_radius=6)

    # Inner glass highlight on top half
    top_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 2)
    glass = pygame.Surface((top_rect.width, top_rect.height), pygame.SRCALPHA)
    glass.fill((255, 255, 255, 30 if not is_hover else 50))
    surface.blit(glass, top_rect)

    # Border
    pygame.draw.rect(surface, border_c, rect, width=2, border_radius=6)

    # Text
    txt_surf = font_btn.render(text, True, (255, 255, 255) if not is_hover else (255, 240, 190))
    txt_rect = txt_surf.get_rect(center=rect.center)
    surface.blit(txt_surf, txt_rect)


def draw_health_bars(surface, p, b):
    """Draws the player's red health bar on the left and the boss's bar on the right."""
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

    # ── Boss Health Bar (Right) ───────────────────────────────────────────
    bx = W - int(W * 0.04) - bar_w
    b_title = "Titan" if b["hp"] > 100 else "Titan [ENRAGED]"
    b_name = font_bar_name.render(b_title, True, (255, 80, 80) if b["hp"] <= 100 else (240, 220, 170))
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
        b_color = (235, 40, 40) if b["hp"] <= 100 else (180, 35, 55)
        b_fill_rect = pygame.Rect(bx, top_y, int(bar_w * b_pct), bar_h)
        pygame.draw.rect(surface, b_color, b_fill_rect, border_radius=4)
        highlight_rect = pygame.Rect(bx, top_y, int(bar_w * b_pct), bar_h // 2)
        hl = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
        hl.fill((255, 255, 255, 45))
        surface.blit(hl, highlight_rect)

    pygame.draw.rect(surface, (215, 140, 70) if b["hp"] > 100 else (255, 60, 60), b_bg_rect, width=2, border_radius=4)

    b_val_surf = font_bar_val.render(f"{int(b['hp'])} / {b['max_hp']} HP", True, (255, 245, 225))
    b_val_rect = b_val_surf.get_rect(topright=(bx + bar_w - 8, top_y + 4))
    surface.blit(b_val_surf, b_val_rect)


# ---------------------------------------------------------------------------
# Game States: "MENU", "CONTROLS", "PLAYING", "VICTORY", "DEFEAT"
# ---------------------------------------------------------------------------
game_state = "MENU"
controls_scroll_y = 0
max_scroll_y = 0

# Button Rects on Main Menu
btn_w = int(W * 0.28)
btn_h = int(H * 0.065)
btn_start_rect = pygame.Rect((W - btn_w) // 2, int(H * 0.50), btn_w, btn_h)
btn_ctrls_rect = pygame.Rect((W - btn_w) // 2, int(H * 0.60), btn_w, btn_h)
btn_exit_rect = pygame.Rect((W - btn_w) // 2, int(H * 0.70), btn_w, btn_h)

# Button Rect on Controls Screen
btn_back_rect = pygame.Rect(int(W * 0.08), int(H * 0.88), int(W * 0.16), int(H * 0.055))

# Button Rects on Victory & Defeat Screens
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

            # Menu navigation keys
            if game_state == "MENU":
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    reset_battle()
                    game_state = "PLAYING"
                elif event.key == pygame.K_c:
                    game_state = "CONTROLS"

            elif game_state == "CONTROLS":
                if event.key in (pygame.K_BACKSPACE, pygame.K_RETURN):
                    game_state = "MENU"

            # Victory / Defeat navigation keys
            elif game_state in ("VICTORY", "DEFEAT"):
                if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                    reset_battle()
                    game_state = "PLAYING"
                elif event.key == pygame.K_m:
                    reset_battle()
                    game_state = "MENU"

            # In-game quick testing hotkeys
            elif game_state == "PLAYING":
                if event.key == pygame.K_k:
                    # Test player taking damage
                    player["hp"] = max(0, player["hp"] - 25)
                elif event.key == pygame.K_t:
                    # Test striking Titan with heavy damage
                    boss["hp"] = max(0, boss["hp"] - 200)

        # Mouse clicks
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

        # Mouse wheel for Controls scroll
        if event.type == pygame.MOUSEWHEEL and game_state == "CONTROLS":
            controls_scroll_y = max(0, min(max_scroll_y, controls_scroll_y - event.y * 30))

    # ══════════════════════════════════════════════════════════════════════
    # BACKGROUND SIMULATION (Active across all screens)
    # ══════════════════════════════════════════════════════════════════════
    screen.blit(background, (0, 0))

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
        screen.blit(img, (int(c["x"]), c["y"]))
        if c["x"] > W + 50:
            c["x"] = -img.get_width() - random.randint(0, W // 4)
            c["y"] = random.randint(0, int(H * 0.12))

    # Flags
    flag_frame_idx = (frame_count // FLAG_ANIM_SPEED) % 2
    sway = math.sin(frame_count * 0.04) * 3

    f1 = flag1_frames[flag_frame_idx]
    f1_y = flag1_bottom[1] - f1.get_height()
    screen.blit(f1, (flag1_bottom[0] + int(sway), f1_y))

    f2 = flag2_frames[flag_frame_idx]
    f2_y = flag2_bottom[1] - f2.get_height()
    screen.blit(f2, (flag2_bottom[0] - int(sway), f2_y))

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
        screen.blit(img, (int(s["x"]), int(s["y"])))

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

        # ── Check Victory / Defeat Transitions ────────────────────────────
        if b["hp"] <= 0:
            b["hp"] = 0
            game_state = "VICTORY"
        elif p["hp"] <= 0:
            p["hp"] = 0
            game_state = "DEFEAT"

        # ── Player State Machine & Actions ────────────────────────────────
        if p["state"] in ("dodge", "slash", "parry", "kunai"):
            p["tick_count"] += 1

            if p["state"] == "dodge":
                dx = DODGE_SPEED if p["facing_right"] else -DODGE_SPEED
                p["x"] += dx
                p["frame_idx"] += 1
                if p["frame_idx"] >= len(dodge_frames):
                    p["state"] = "idle"
                    p["frame_idx"] = 0
                    p["tick_count"] = 0

            elif p["state"] == "slash":
                p["frame_idx"] += 1
                # When sword strike connects (~frame 12), damage Titan!
                if p["frame_idx"] == 12:
                    b["hp"] = max(0, b["hp"] - 25)
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
                if p["tick_count"] >= 2:
                    p["tick_count"] = 0
                    p["frame_idx"] += 1
                    # Kunai hits Titan at frame 10
                    if p["frame_idx"] == 10:
                        b["hp"] = max(0, b["hp"] - 15)
                    if p["frame_idx"] >= len(kunai_frames):
                        p["state"] = "idle"
                        p["frame_idx"] = 0

        else:
            # ── Check Action Key Triggers ─────────────────────────────────
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
                    # ── Idle (Blink Style) ────────────────────────────────
                    p["state"] = "idle"
                    p["blink_timer"] -= 1
                    if p["blink_timer"] <= 0:
                        if not p["is_blinking"]:
                            p["is_blinking"] = True
                            p["blink_timer"] = 6
                        else:
                            p["is_blinking"] = False
                            p["blink_timer"] = random.randint(120, 200)

            # ── Jump (W) ──────────────────────────────────────────────────
            if keys[pygame.K_w] and p["on_ground"]:
                p["vy"] = JUMP_FORCE
                p["on_ground"] = False

        # ── Gravity ───────────────────────────────────────────────────────
        if not p["on_ground"]:
            p["vy"] += GRAVITY
            p["y"] += p["vy"]
            if p["y"] >= GROUND_Y:
                p["y"] = GROUND_Y
                p["vy"] = 0
                p["on_ground"] = True

        # Clamp inside screen
        p["x"] = max(center_offset, min(p["x"], W - center_offset))

        # ── Render Player ─────────────────────────────────────────────────
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

        # ── Render Health Bars at Top ─────────────────────────────────────
        draw_health_bars(screen, p, b)

    elif game_state == "VICTORY":
        # Golden celebratory overlay
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((15, 12, 5, 190))
        screen.blit(overlay, (0, 0))

        # Title: VICTORY ACHIEVED
        v_title = font_end_title.render("VICTORY ACHIEVED", True, (255, 220, 90))
        v_shadow = font_end_title.render("VICTORY ACHIEVED", True, (20, 15, 5))
        v_rect = v_title.get_rect(center=(W // 2, int(H * 0.28)))
        screen.blit(v_shadow, (v_rect.x + 3, v_rect.y + 3))
        screen.blit(v_title, v_rect)

        # Subtitle
        v_sub = font_end_sub.render("Titan has fallen before Great General Zhao!", True, (240, 230, 200))
        vs_rect = v_sub.get_rect(center=(W // 2, int(H * 0.38)))
        screen.blit(v_sub, vs_rect)

        # Gold separator line
        pygame.draw.line(screen, (220, 185, 90), (W // 2 - int(W * 0.25), int(H * 0.44)), (W // 2 + int(W * 0.25), int(H * 0.44)), 2)

        # Buttons
        draw_button(screen, btn_reset_rect, "PLAY AGAIN (RESET)", btn_reset_rect.collidepoint(mouse_pos), primary_col=(35, 130, 60))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(50, 45, 50))

        # Hint text
        hint = font_bar_val.render("Press [R] or [ENTER] to Play Again  |  Press [ESC] for Main Menu", True, (200, 190, 160))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.74))))

    elif game_state == "DEFEAT":
        # Dark crimson / blood-red overlay
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((30, 5, 5, 205))
        screen.blit(overlay, (0, 0))

        # Title: YOU DIED
        d_title = font_end_title.render("YOU DIED", True, (230, 40, 40))
        d_shadow = font_end_title.render("YOU DIED", True, (10, 0, 0))
        d_rect = d_title.get_rect(center=(W // 2, int(H * 0.28)))
        screen.blit(d_shadow, (d_rect.x + 4, d_rect.y + 4))
        screen.blit(d_title, d_rect)

        # Subtitle
        d_sub = font_end_sub.render("Great General Zhao has perished in battle against Titan...", True, (230, 190, 190))
        ds_rect = d_sub.get_rect(center=(W // 2, int(H * 0.38)))
        screen.blit(d_sub, ds_rect)

        # Crimson separator line
        pygame.draw.line(screen, (200, 50, 50), (W // 2 - int(W * 0.25), int(H * 0.44)), (W // 2 + int(W * 0.25), int(H * 0.44)), 2)

        # Buttons
        draw_button(screen, btn_reset_rect, "TRY AGAIN (RESET)", btn_reset_rect.collidepoint(mouse_pos), primary_col=(180, 35, 35))
        draw_button(screen, btn_menu_rect, "MAIN MENU", btn_menu_rect.collidepoint(mouse_pos), primary_col=(50, 45, 50))

        # Hint text
        hint = font_bar_val.render("Press [R] or [ENTER] to Try Again  |  Press [ESC] for Main Menu", True, (190, 150, 150))
        screen.blit(hint, hint.get_rect(center=(W // 2, int(H * 0.74))))

    # ── Display Flip & Clock ──────────────────────────────────────────────
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
