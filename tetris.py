"""Fullscreen pygame Tetris with color bonuses and simple generated sounds."""
from __future__ import annotations

import math
import random
import sys
from dataclasses import dataclass

import pygame

import numpy as np

GRID_WIDTH = 10
GRID_HEIGHT = 20
BLOCK_SIZE = 34
SIDE_PANEL = 300
FPS = 60
DROP_START_MS = 800
DROP_MIN_MS = 90
DROP_SPEEDUP = 18
END_SCORE = 50

BLACK = (8, 10, 18)
GRID_BG = (18, 22, 34)
GRID_LINE = (35, 42, 58)
WHITE = (238, 240, 246)
GRAY = (150, 155, 170)
RED = (238, 83, 80)
GREEN = (102, 187, 106)
BLUE = (66, 165, 245)
YELLOW = (255, 213, 79)
PURPLE = (171, 71, 188)

COLORS = [RED, GREEN, BLUE, YELLOW, PURPLE]
SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "U": [[1, 0, 1], [1, 1, 1]],
    "P": [[1, 1], [1, 1], [1, 0]],
    "X": [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
    "V": [[1, 0, 0], [1, 0, 0], [1, 1, 1]],
    "W": [[1, 0, 0], [1, 1, 0], [0, 1, 1]],
}


@dataclass
class Piece:
    shape: list[list[int]]
    color: tuple[int, int, int]
    x: int
    y: int

    def rotate(self) -> list[list[int]]:
        return [list(row) for row in zip(*self.shape[::-1])]


def make_piece() -> Piece:
    shape = [row[:] for row in random.choice(list(SHAPES.values()))]
    return Piece(shape=shape, color=random.choice(COLORS), x=GRID_WIDTH // 2 - len(shape[0]) // 2, y=0)


def collides(grid: list[list[tuple[int, int, int] | None]], piece: Piece, dx: int = 0, dy: int = 0, shape=None) -> bool:
    shape = shape or piece.shape
    for row_idx, row in enumerate(shape):
        for col_idx, cell in enumerate(row):
            if not cell:
                continue
            x = piece.x + col_idx + dx
            y = piece.y + row_idx + dy
            if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT:
                return True
            if y >= 0 and grid[y][x] is not None:
                return True
    return False


def lock_piece(grid: list[list[tuple[int, int, int] | None]], piece: Piece) -> None:
    for row_idx, row in enumerate(piece.shape):
        for col_idx, cell in enumerate(row):
            if cell and piece.y + row_idx >= 0:
                grid[piece.y + row_idx][piece.x + col_idx] = piece.color


def clear_lines(grid: list[list[tuple[int, int, int] | None]]) -> tuple[int, int, int]:
    remaining = []
    cleared = 0
    same_color = 0
    for row in grid:
        if all(cell is not None for cell in row):
            cleared += 1
            if len(set(row)) == 1:
                same_color += 1
        else:
            remaining.append(row)
    for _ in range(cleared):
        remaining.insert(0, [None for _ in range(GRID_WIDTH)])
    grid[:] = remaining

    line_points = 2 ** cleared if cleared > 1 else cleared
    color_bonus = same_color * 5
    return cleared, line_points + color_bonus, same_color


def make_sound(frequency: float, duration: float, volume: float = 0.35):
    if not pygame.mixer.get_init():
        return None
    sample_rate = pygame.mixer.get_init()[0]
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples, False)
    wave = np.sin(frequency * t * 2 * math.pi) * volume
    fade = np.linspace(1, 0, samples)
    audio = (wave * fade * 32767).astype(np.int16)
    stereo = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo.copy())


def start_music() -> None:
    if not pygame.mixer.get_init():
        return
    sample_rate = pygame.mixer.get_init()[0]
    melody = [196, 247, 294, 330, 294, 247, 220, 247]
    chunks = []
    for note in melody:
        duration = 0.22
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        tone = 0.13 * np.sin(2 * math.pi * note * t) + 0.05 * np.sin(2 * math.pi * note * 2 * t)
        chunks.append((tone * 32767).astype(np.int16))
    audio = np.concatenate(chunks)
    stereo = np.column_stack((audio, audio))
    pygame.sndarray.make_sound(stereo.copy()).play(loops=-1)


def draw_text(surface, font, text, color, x, y, center=False):
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(image, rect)


def draw(surface, grid, piece, next_piece, score, lines, same_color_lines, fonts, game_over=False, won=False):
    surface.fill(BLACK)
    screen_w, screen_h = surface.get_size()
    board_w = GRID_WIDTH * BLOCK_SIZE
    board_h = GRID_HEIGHT * BLOCK_SIZE
    board_x = (screen_w - board_w - SIDE_PANEL) // 2
    board_y = (screen_h - board_h) // 2

    pygame.draw.rect(surface, GRID_BG, (board_x, board_y, board_w, board_h), border_radius=8)
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(board_x + x * BLOCK_SIZE, board_y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surface, GRID_LINE, rect, 1)
            color = grid[y][x]
            if color:
                pygame.draw.rect(surface, color, rect.inflate(-4, -4), border_radius=5)

    if not game_over:
        for row_idx, row in enumerate(piece.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    rect = pygame.Rect(board_x + (piece.x + col_idx) * BLOCK_SIZE, board_y + (piece.y + row_idx) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                    pygame.draw.rect(surface, piece.color, rect.inflate(-4, -4), border_radius=5)

    panel_x = board_x + board_w + 40
    draw_text(surface, fonts["title"], "TETRIS", WHITE, panel_x, board_y)
    draw_text(surface, fonts["normal"], f"Punkte: {score}", WHITE, panel_x, board_y + 80)
    draw_text(surface, fonts["normal"], f"Zeilen: {lines}", WHITE, panel_x, board_y + 120)
    draw_text(surface, fonts["small"], f"Farbzeilen: {same_color_lines}", GRAY, panel_x, board_y + 160)
    draw_text(surface, fonts["small"], f"Ziel: {END_SCORE} Punkte", GRAY, panel_x, board_y + 190)
    draw_text(surface, fonts["normal"], "Naechster Block:", WHITE, panel_x, board_y + 220)
    for row_idx, row in enumerate(next_piece.shape):
        for col_idx, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(panel_x + col_idx * BLOCK_SIZE, board_y + 270 + row_idx * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(surface, next_piece.color, rect.inflate(-4, -4), border_radius=5)

    help_lines = ["Steuerung:", "←/→ bewegen", "↑ drehen", "↓ schneller", "Leertaste fallen"]
    for idx, line in enumerate(help_lines):
        draw_text(surface, fonts["small"], line, GRAY if idx else WHITE, panel_x, board_y + 430 + idx * 34)

    if game_over or won:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        headline = "ZIEL ERREICHT!" if won else "SPIEL VORBEI"
        detail = f"Endstand: {score} Punkte"
        draw_text(surface, fonts["title"], headline, WHITE, screen_w // 2, screen_h // 2 - 70, True)
        draw_text(surface, fonts["normal"], detail, YELLOW, screen_w // 2, screen_h // 2, True)
        draw_text(surface, fonts["small"], "ESC zum Beenden", GRAY, screen_w // 2, screen_h // 2 + 60, True)

    pygame.display.flip()


def main() -> int:
    pygame.init()
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
    except pygame.error:
        pass

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    fonts = {
        "title": pygame.font.SysFont("arial", 56, bold=True),
        "normal": pygame.font.SysFont("arial", 34),
        "small": pygame.font.SysFont("arial", 24),
    }

    start_music()
    zap_sound = make_sound(880, 0.18, 0.55)
    grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    piece = make_piece()
    next_piece = make_piece()
    score = 0
    lines = 0
    same_color_lines = 0
    drop_ms = DROP_START_MS
    last_drop = pygame.time.get_ticks()
    game_over = False
    won = False

    while True:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 0
                if game_over or won:
                    continue
                if event.key == pygame.K_LEFT and not collides(grid, piece, dx=-1):
                    piece.x -= 1
                elif event.key == pygame.K_RIGHT and not collides(grid, piece, dx=1):
                    piece.x += 1
                elif event.key == pygame.K_DOWN and not collides(grid, piece, dy=1):
                    piece.y += 1
                elif event.key == pygame.K_UP:
                    rotated = piece.rotate()
                    if not collides(grid, piece, shape=rotated):
                        piece.shape = rotated
                elif event.key == pygame.K_SPACE:
                    while not collides(grid, piece, dy=1):
                        piece.y += 1
                    last_drop = 0

        if not game_over and not won and now - last_drop >= drop_ms:
            if collides(grid, piece, dy=1):
                lock_piece(grid, piece)
                cleared, points, color_count = clear_lines(grid)
                if cleared:
                    score += points
                    lines += cleared
                    same_color_lines += color_count
                    drop_ms = max(DROP_MIN_MS, DROP_START_MS - lines * DROP_SPEEDUP)
                    if zap_sound:
                        zap_sound.play()
                    if score >= END_SCORE:
                        won = True
                        pygame.mixer.stop()
                piece = next_piece
                next_piece = make_piece()
                if collides(grid, piece):
                    game_over = True
                    pygame.mixer.stop()
            else:
                piece.y += 1
            last_drop = now

        draw(screen, grid, piece, next_piece, score, lines, same_color_lines, fonts, game_over, won)
        clock.tick(FPS)


if __name__ == "__main__":
    sys.exit(main())
