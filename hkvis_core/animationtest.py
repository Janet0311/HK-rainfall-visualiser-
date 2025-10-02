import math
import sys

try:
    import pygame
except ImportError:
    print("Error: pygame is not installed. Please install it with: pip install pygame")
    sys.exit(1)

# --- CONFIG ---
RAIN_DATA = [15.2, 8.7, 45.3, 78.9, 156.4, 234.7, 298.5, 267.3, 189.6, 67.8, 23.4, 12.1]

COLS = 100
ROWS = 36
FONT_SIZE = 14
PADDING = 8
FPS = 60

ASCII_CHARS = "@%#*+=-:. "  # from dense to sparse

# vivid cyan/blue palette (top -> bottom)
BLUE_PALETTE = [
    (20, 100, 255),
    (10, 150, 255),
    (0, 200, 255),
    (0, 230, 220),
    (60, 230, 220),
    (190, 245, 250)
]

# black background
BG_COLOR = (0, 0, 0)

# speed params
SPEED_FACTOR = 6.0
BASE_TIME_SCALE = 20.0  # base time scale; effective speed will be derived from data
# Global multiplier to amplify how strongly yearly rain affects animation speed.
# Increase to make differences between years more obvious (1.0 = original behavior)
SPEED_MULTIPLIER = 3.5
# cap for normalizing mean rainfall into 0..1. Set to a reasonable high monthly mean (mm)
GLOBAL_MEAN_CAP = 300.0

# whiten controls (replace saturation controls)
TOP_WHITEN_BIAS = 0.30      # how much to move top rows toward white (0..1)
BOTTOM_WHITEN_BOOST = 0.25  # how much to move bottom rows toward white (0..1)

# --- pattern generation (returns (char, norm) per cell) ---
def generate_fluid_pattern(data, global_time, cols=COLS, rows=ROWS, speed_factor=SPEED_FACTOR, base_scale=BASE_TIME_SCALE):
    if not data or len(data) == 0:
        data = [0.0] * 12  # Default to 12 months of zero rainfall
    
    # Ensure all data values are numeric and non-negative
    data = [max(0.0, float(x) if x is not None else 0.0) for x in data]
    
    if data:
        max_val = max(data)
        mean_val = sum(data) / len(data)
        max_val = max(max_val, 1.0)
        mean_intensity = min(1.0, mean_val / GLOBAL_MEAN_CAP)
    else:
        max_val = 1.0
        mean_intensity = 0.0
    data_speed_multiplier = 0.3 + (mean_intensity ** 0.7) * 2.0
    effective_speed_factor = speed_factor * data_speed_multiplier * SPEED_MULTIPLIER
    grid = []
    for y in range(rows):
        row_chars = []
        for x in range(cols):
            data_index = min(int((x / cols) * len(data)), len(data) - 1)
            intensity = data[data_index] / max_val if max_val > 0 else 0.0
            time_scale = base_scale + intensity * effective_speed_factor
            t = global_time * time_scale
            flowX = x + (t * 0.2)
            flowY = y - (t * 0.8)
            wave1 = math.sin((x * 0.18) + (flowY * 0.12) + (t * 0.05)) * 0.5 + 0.5
            wave2 = math.sin((x * 0.08) + (flowY * 0.22) + (t * 0.08)) * 0.4 + 0.6
            wave3 = math.cos((x * 0.25) + (flowY * 0.08) - (t * 0.06)) * 0.5 + 0.5
            wave4 = math.sin((flowX * 0.15) + (flowY * 0.35) + (t * 0.1)) * 0.3 + 0.7
            horizontalFlow = math.sin((x * 0.15) + (t * 0.12)) * 0.3
            diagonalFlow = math.cos((x * 0.08) + (y * 0.08) + (t * 0.09)) * 0.25
            combined = (wave1 + wave2 + wave3 + wave4) / 4.0 + horizontalFlow + diagonalFlow
            modulated = combined * intensity
            noise1 = math.sin(x * 0.5 + flowY * 0.4 + t * 0.15) * 0.2
            noise2 = math.cos(x * 0.7 + y * 0.3 + t * 0.12) * 0.15
            randomness = math.sin(x * 1.2 + y * 0.8 + t * 0.18) * math.cos(x * 0.6 + y * 1.1) * 0.25
            final = modulated + noise1 + noise2 + randomness
            charRandom = math.sin(x * 0.3 + y * 0.5 + t * 0.1) * 0.1
            adjustedFinal = final + charRandom
            norm = (math.tanh(adjustedFinal) + 1.0) / 2.0
            idx = int(norm * (len(ASCII_CHARS) - 1))
            ch = ASCII_CHARS[max(0, min(len(ASCII_CHARS) - 1, idx))]
            row_chars.append((ch, norm))
        grid.append(row_chars)
    return grid

def lerp_color(a, b, t):
    return (int(a[0] + (b[0]-a[0]) * t),
            int(a[1] + (b[1]-a[1]) * t),
            int(a[2] + (b[2]-a[2]) * t))

def row_base_color(row_idx, total_rows, top_whiten=TOP_WHITEN_BIAS, bottom_boost=BOTTOM_WHITEN_BOOST):
    t = row_idx / max(1, total_rows - 1)
    t_top_biased = max(0.0, t - (1.0 - t) * (top_whiten * 0.15))
    if t > 0.6:
        bottom_factor = (t - 0.6) / 0.4
        t_bottom_biased = t_top_biased + (1.0 - t_top_biased) * (bottom_factor * bottom_boost)
        t_final = min(1.0, t_bottom_biased)
    else:
        t_final = t_top_biased
    segs = len(BLUE_PALETTE) - 1
    seg_pos = t_final * segs
    i = int(seg_pos)
    frac = seg_pos - i
    c1 = BLUE_PALETTE[i]
    c2 = BLUE_PALETTE[min(i+1, segs)]
    base = lerp_color(c1, c2, frac)
    top_influence = max(0.0, 1.0 - t) * top_whiten
    bottom_influence = 0.0
    if t > 0.6:
        bottom_factor = (t - 0.6) / 0.4
        bottom_influence = bottom_factor * bottom_boost
    whiten_amount = min(1.0, top_influence + bottom_influence)
    if whiten_amount > 0:
        white = (255, 255, 255)
        base = lerp_color(base, white, whiten_amount * 0.9)
    return base

def apply_density_tint(base_color, norm):
    bright = (230, 255, 255)
    t1 = norm
    c_mid = lerp_color(base_color, bright, t1 * 0.95)
    r, g, b = c_mid
    g = min(255, int(g + 35 * norm))
    b = min(255, int(b + 70 * norm))
    return (r, g, b)

def final_cell_color(base, norm, row_idx, total_rows, time_mod=0.0, white_factor=0.0):
    mod = 1.0 + (time_mod - 0.5) * 0.08
    r, g, b = apply_density_tint(base, norm)
    r = int(max(0, min(255, r * mod)))
    g = int(max(0, min(255, g * mod)))
    b = int(max(0, min(255, b * mod)))
    if white_factor and white_factor > 0:
        wr = int(255 * white_factor + r * (1 - white_factor))
        wg = int(255 * white_factor + g * (1 - white_factor))
        wb = int(255 * white_factor + b * (1 - white_factor))
        return (wr, wg, wb)
    return (r, g, b)

def main():
    pygame.init()
    
    # Set up the display
    monos = pygame.font.match_font('consolas, courier, monospace')
    if monos:
        anim_font = pygame.font.Font(monos, FONT_SIZE)
    else:
        anim_font = pygame.font.SysFont('couriernew', FONT_SIZE)
    
    sample = anim_font.render('M', True, (255,255,255))
    anim_char_w, anim_char_h = sample.get_size()
    
    # Calculate window size
    window_width = anim_char_w * COLS + PADDING * 2
    window_height = anim_char_h * ROWS + PADDING * 2
    
    # Create the main display window
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Hong Kong Rainfall Visualization")
    
    anim_surface = pygame.Surface((window_width, window_height))
    clock = pygame.time.Clock()
    frame_time = 0.0
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        dt = clock.tick(FPS) / 1000.0
        frame_time += dt
        grid = generate_fluid_pattern(RAIN_DATA, frame_time, cols=COLS, rows=ROWS, speed_factor=SPEED_FACTOR, base_scale=BASE_TIME_SCALE)
        anim_surface.fill(BG_COLOR)
        if grid:
            for row_idx, row in enumerate(grid):
                y = PADDING + row_idx * anim_char_h
                base = row_base_color(row_idx, ROWS, top_whiten=TOP_WHITEN_BIAS, bottom_boost=BOTTOM_WHITEN_BOOST)
                for col_idx, (ch, norm) in enumerate(row):
                    col_mod = (math.sin((frame_time * 1.2) + col_idx * 0.12) + 1) / 2
                    seed = (row_idx * 1315423911) ^ (col_idx * 2654435761)
                    phase = (seed % 1000) / 1000.0
                    white_osc = (math.sin(frame_time * 1.5 + phase * 6.28318) + 1) / 2
                    white_factor = (white_osc ** 3) * 0.9
                    sparsity = ((seed >> 3) & 31) / 31.0
                    white_factor = white_factor * (sparsity * 0.8)
                    color = final_cell_color(base, norm, row_idx, ROWS, time_mod=col_mod, white_factor=white_factor)
                    surf = anim_font.render(ch, True, color)
                    x = PADDING + col_idx * anim_char_w
                    anim_surface.blit(surf, (x, y))
        
        # Blit the animation surface to the main screen
        screen.blit(anim_surface, (0, 0))
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
