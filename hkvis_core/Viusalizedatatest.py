import math
import pygame
import sys
import colorsys

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
BASE_TIME_SCALE = 25.0  # updated start speed per your request

# saturation controls (replace previous brightness options)
TOP_SATURATION_BIAS = 0.30      # how much to boost saturation toward the top (0..1)
BOTTOM_SATURATION_BOOST = 0.25  # how much to boost saturation toward the bottom (0..1)

# --- pattern generation (same algorithm, returns (char, norm) per cell) ---
def generate_fluid_pattern(data, global_time, cols=COLS, rows=ROWS, speed_factor=SPEED_FACTOR, base_scale=BASE_TIME_SCALE):
    max_val = max(data) if data else 1.0
    grid = []
    for y in range(rows):
        row_chars = []
        for x in range(cols):
            data_index = int((x / cols) * len(data))
            intensity = data[data_index] / max_val

            time_scale = base_scale + intensity * speed_factor
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

def row_base_color(row_idx, total_rows, top_saturation_bias=TOP_SATURATION_BIAS, bottom_boost=BOTTOM_SATURATION_BOOST):
    t = row_idx / max(1, total_rows - 1)
    t_top_biased = max(0.0, t - (1.0 - t) * top_saturation_bias * 0.2)
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
    return lerp_color(c1, c2, frac)

def increase_saturation(rgb, factor):
    r, g, b = rgb
    r_f, g_f, b_f = r/255.0, g/255.0, b/255.0
    h, l, s = colorsys.rgb_to_hls(r_f, g_f, b_f)
    s_new = max(0.0, min(1.0, s * factor))
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s_new)
    return (int(r2*255), int(g2*255), int(b2*255))

def apply_density_tint(base_color, norm):
    bright = (230, 255, 255)
    t1 = norm
    c_mid = lerp_color(base_color, bright, t1 * 0.95)
    r, g, b = c_mid
    g = min(255, int(g + 35 * norm))
    b = min(255, int(b + 70 * norm))
    return (r, g, b)

def final_cell_color(base, norm, row_idx, total_rows, top_sat_bias, bottom_sat_boost, time_mod=0.0):
    t = row_idx / max(1, total_rows - 1)
    top_contrib = max(0.0, 1.0 - t) * top_sat_bias
    bottom_contrib = 0.0
    if t > 0.6:
        bottom_factor = (t - 0.6) / 0.4
        bottom_contrib = bottom_factor * bottom_sat_boost
    sat_factor = 1.0 + top_contrib + bottom_contrib
    sat_factor *= (1.0 + time_mod * 0.06)
    saturated = increase_saturation(base, sat_factor)
    return apply_density_tint(saturated, norm)

def main():
    pygame.init()
    monos = pygame.font.match_font('consolas, courier, monospace')
    if monos:
        font = pygame.font.Font(monos, FONT_SIZE)
    else:
        font = pygame.font.SysFont('couriernew', FONT_SIZE)
    sample_surf = font.render('M', True, (255,255,255))
    char_w, char_h = sample_surf.get_size()
    window_width = char_w * COLS + PADDING * 2
    window_height = char_h * ROWS + PADDING * 2
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption('Rain Art - Blue (Saturation Controls)')
    clock = pygame.time.Clock()
    frame_time = 0.0
    running = True
    global SPEED_FACTOR, BASE_TIME_SCALE, TOP_SATURATION_BIAS, BOTTOM_SATURATION_BOOST
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_UP:
                    SPEED_FACTOR *= 1.2
                    print("SPEED_FACTOR:", round(SPEED_FACTOR, 2))
                if event.key == pygame.K_DOWN:
                    SPEED_FACTOR *= 0.8
                    print("SPEED_FACTOR:", round(SPEED_FACTOR, 2))
                if event.key == pygame.K_RIGHT:
                    BASE_TIME_SCALE *= 1.2
                    print("BASE_TIME_SCALE:", round(BASE_TIME_SCALE, 2))
                if event.key == pygame.K_LEFT:
                    BASE_TIME_SCALE *= 0.8
                    print("BASE_TIME_SCALE:", round(BASE_TIME_SCALE, 2))
                if event.key == pygame.K_w:
                    TOP_SATURATION_BIAS = min(2.5, TOP_SATURATION_BIAS + 0.05)
                    print("TOP_SATURATION_BIAS:", round(TOP_SATURATION_BIAS, 3))
                if event.key == pygame.K_s:
                    TOP_SATURATION_BIAS = max(0.0, TOP_SATURATION_BIAS - 0.05)
                    print("TOP_SATURATION_BIAS:", round(TOP_SATURATION_BIAS, 3))
                if event.key == pygame.K_e:
                    BOTTOM_SATURATION_BOOST = min(2.5, BOTTOM_SATURATION_BOOST + 0.05)
                    print("BOTTOM_SATURATION_BOOST:", round(BOTTOM_SATURATION_BOOST, 3))
                if event.key == pygame.K_d:
                    BOTTOM_SATURATION_BOOST = max(0.0, BOTTOM_SATURATION_BOOST - 0.05)
                    print("BOTTOM_SATURATION_BOOST:", round(BOTTOM_SATURATION_BOOST, 3))
        dt = clock.tick(FPS) / 1000.0
        frame_time += dt
        grid = generate_fluid_pattern(RAIN_DATA, frame_time, cols=COLS, rows=ROWS, speed_factor=SPEED_FACTOR, base_scale=BASE_TIME_SCALE)
        screen.fill(BG_COLOR)
        for row_idx, row in enumerate(grid):
            y = PADDING + row_idx * char_h
            base = row_base_color(row_idx, ROWS)
            for col_idx, (ch, norm) in enumerate(row):
                col_mod = (math.sin((frame_time * 1.2) + col_idx * 0.12) + 1) / 2
                color = final_cell_color(base, norm, row_idx, ROWS, TOP_SATURATION_BIAS, BOTTOM_SATURATION_BOOST, time_mod=col_mod)
                surf = font.render(ch, True, color)
                x = PADDING + col_idx * char_w
                screen.blit(surf, (x, y))
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
