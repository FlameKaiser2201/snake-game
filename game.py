"""Smooth grid Snake built with pygame.

Logic stays on a grid for fair collisions. Drawing interpolates between
cells so the snake glides instead of jumping once per tick.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pygame

CELL = 28
COLS = 24
ROWS = 18
HUD = 72
WIDTH = CELL * COLS
HEIGHT = CELL * ROWS + HUD
BASE_STEP = 0.145
MIN_STEP = 0.062
SCORE_FILE = Path(__file__).with_name("highscore.txt")

BG = (10, 16, 28)
BOARD = (16, 24, 42)
GRID = (24, 36, 58)
HUD_BG = (8, 12, 22)
SNAKE_HEAD = (92, 230, 164)
SNAKE_BODY = (46, 196, 140)
SNAKE_DARK = (22, 120, 92)
FOOD = (255, 92, 120)
FOOD_GLOW = (255, 150, 170)
TEXT = (230, 236, 248)
MUTED = (140, 156, 184)
GOLD = (255, 208, 96)
WHITE = (255, 255, 255)

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}


def load_high_score() -> int:
    try:
        return int(SCORE_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0


def save_high_score(score: int) -> None:
    try:
        SCORE_FILE.write_text(str(score), encoding="utf-8")
    except OSError:
        pass


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class Particle:
    def __init__(self, x: float, y: float) -> None:
        angle = random.uniform(0, math.tau)
        speed = random.uniform(40, 160)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.28, 0.55)
        self.age = 0.0
        self.size = random.uniform(2.5, 5.5)
        self.color = random.choice([FOOD, FOOD_GLOW, GOLD, WHITE])

    def update(self, dt: float) -> bool:
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 90 * dt
        return self.age < self.life

    def draw(self, surface: pygame.Surface) -> None:
        t = 1.0 - self.age / self.life
        radius = max(1, int(self.size * t))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), radius)


class SnakeGame:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Smooth Snake")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 26)
        self.small = pygame.font.SysFont("segoeui", 18)
        self.big = pygame.font.SysFont("segoeui", 48, bold=True)
        self.high_score = load_high_score()
        self.particles: list[Particle] = []
        self.reset()

    def reset(self) -> None:
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx - 2, cy), (cx - 1, cy), (cx, cy)]
        self.prev_snake = list(self.snake)
        self.direction = RIGHT
        self.queued: list[tuple[int, int]] = []
        self.spawn_food()
        self.score = 0
        self.alive = True
        self.paused = False
        self.accumulator = 0.0
        self.eat_flash = 0.0
        self.shake = 0.0
        self.started = False

    def spawn_food(self) -> None:
        occupied = set(self.snake)
        free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in occupied]
        self.food = random.choice(free) if free else None

    def step_interval(self) -> float:
        return max(MIN_STEP, BASE_STEP - self.score * 0.0032)

    def queue_direction(self, direction: tuple[int, int]) -> None:
        if not self.alive:
            return
        last = self.queued[-1] if self.queued else self.direction
        if direction == last or direction == OPPOSITE[last]:
            return
        if len(self.queued) < 2:
            self.queued.append(direction)
            self.started = True

    def advance(self) -> None:
        if self.queued:
            self.direction = self.queued.pop(0)
        self.prev_snake = list(self.snake)
        hx, hy = self.snake[-1]
        nx, ny = hx + self.direction[0], hy + self.direction[1]
        if nx < 0 or ny < 0 or nx >= COLS or ny >= ROWS or (nx, ny) in self.snake:
            self.alive = False
            self.shake = 0.35
            if self.score > self.high_score:
                self.high_score = self.score
                save_high_score(self.high_score)
            return
        self.snake.append((nx, ny))
        if self.food and (nx, ny) == self.food:
            self.score += 1
            self.eat_flash = 0.22
            fx, fy = self.cell_center(self.food)
            for _ in range(18):
                self.particles.append(Particle(fx, fy))
            self.spawn_food()
            self.prev_snake = [self.prev_snake[0]] + self.prev_snake
        else:
            self.snake.pop(0)

    def cell_center(self, cell: tuple[int, int]) -> tuple[float, float]:
        return cell[0] * CELL + CELL / 2, HUD + cell[1] * CELL + CELL / 2

    def interpolated_points(self) -> list[tuple[float, float]]:
        t = ease(self.accumulator / self.step_interval()) if self.alive and self.started else 0.0
        prev = self.prev_snake
        curr = self.snake
        n = max(len(prev), len(curr))
        points = []
        for i in range(n):
            c = curr[min(i, len(curr) - 1)]
            p = prev[min(i, len(prev) - 1)]
            x = lerp(p[0], c[0], t) * CELL + CELL / 2
            y = lerp(p[1], c[1], t) * CELL + CELL / 2 + HUD
            points.append((x, y))
        return points

    def update(self, dt: float) -> None:
        self.eat_flash = max(0.0, self.eat_flash - dt)
        self.shake = max(0.0, self.shake - dt)
        self.particles = [p for p in self.particles if p.update(dt)]
        if not self.alive or self.paused or not self.started:
            return
        self.accumulator += dt
        interval = self.step_interval()
        while self.accumulator >= interval and self.alive:
            self.accumulator -= interval
            self.advance()

    def draw_board(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, BOARD, (0, HUD, WIDTH, HEIGHT - HUD), border_radius=0)
        for x in range(COLS):
            for y in range(ROWS):
                if (x + y) % 2 == 0:
                    rect = pygame.Rect(x * CELL, HUD + y * CELL, CELL, CELL)
                    pygame.draw.rect(surface, GRID, rect)

    def draw_food(self, surface: pygame.Surface, time_s: float) -> None:
        if not self.food:
            return
        cx, cy = self.cell_center(self.food)
        pulse = 1.0 + 0.12 * math.sin(time_s * 6.0)
        radius = int((CELL * 0.32) * pulse)
        glow = pygame.Surface((CELL * 2, CELL * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*FOOD, 55), (CELL, CELL), radius + 10)
        surface.blit(glow, (cx - CELL, cy - CELL))
        pygame.draw.circle(surface, FOOD, (int(cx), int(cy)), radius)
        pygame.draw.circle(surface, WHITE, (int(cx - 3), int(cy - 3)), max(2, radius // 4))

    def draw_snake(self, surface: pygame.Surface) -> None:
        points = self.interpolated_points()
        n = len(points)
        for i, (x, y) in enumerate(points):
            k = i / max(1, n - 1)
            color = (
                int(lerp(SNAKE_DARK[0], SNAKE_HEAD[0], k)),
                int(lerp(SNAKE_DARK[1], SNAKE_HEAD[1], k)),
                int(lerp(SNAKE_DARK[2], SNAKE_HEAD[2], k)),
            )
            radius = int(lerp(CELL * 0.30, CELL * 0.42, k))
            pygame.draw.circle(surface, color, (int(x), int(y)), radius)
        if len(points) >= 2:
            hx, hy = points[-1]
            dx = self.direction[0]
            dy = self.direction[1]
            eye_off = CELL * 0.14
            for side in (-1, 1):
                ex = hx + dx * 4 + (-dy) * side * eye_off
                ey = hy + dy * 4 + dx * side * eye_off
                pygame.draw.circle(surface, WHITE, (int(ex), int(ey)), 4)
                pygame.draw.circle(surface, BG, (int(ex + dx * 1.4), int(ey + dy * 1.4)), 2)

    def draw_hud(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, HUD_BG, (0, 0, WIDTH, HUD))
        title = self.font.render("SMOOTH SNAKE", True, SNAKE_HEAD)
        score = self.font.render(f"Score  {self.score}", True, TEXT)
        best = self.font.render(f"Best  {self.high_score}", True, GOLD)
        surface.blit(title, (18, 20))
        surface.blit(score, (WIDTH - 320, 20))
        surface.blit(best, (WIDTH - 150, 20))
        hint = self.small.render("Arrows / WASD   ·   Space pause   ·   R restart   ·   Esc quit", True, MUTED)
        surface.blit(hint, (18, 48))

    def draw_overlay(self, surface: pygame.Surface) -> None:
        if self.alive and not self.paused and self.started:
            return
        veil = pygame.Surface((WIDTH, HEIGHT - HUD), pygame.SRCALPHA)
        veil.fill((6, 10, 18, 160))
        surface.blit(veil, (0, HUD))
        if not self.alive:
            msg = "GAME OVER"
            sub = "Press R to play again"
        elif self.paused:
            msg = "PAUSED"
            sub = "Press Space to continue"
        else:
            msg = "READY"
            sub = "Press an arrow key or WASD to start"
        label = self.big.render(msg, True, WHITE)
        detail = self.small.render(sub, True, MUTED)
        rect = label.get_rect(center=(WIDTH / 2, HUD + (HEIGHT - HUD) / 2 - 12))
        drect = detail.get_rect(center=(WIDTH / 2, rect.bottom + 28))
        surface.blit(label, rect)
        surface.blit(detail, drect)

    def handle_input(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type != pygame.KEYDOWN:
            return True
        mapping = {
            pygame.K_UP: UP,
            pygame.K_w: UP,
            pygame.K_DOWN: DOWN,
            pygame.K_s: DOWN,
            pygame.K_LEFT: LEFT,
            pygame.K_a: LEFT,
            pygame.K_RIGHT: RIGHT,
            pygame.K_d: RIGHT,
        }
        if event.key in mapping:
            self.queue_direction(mapping[event.key])
        elif event.key == pygame.K_SPACE and self.alive:
            self.paused = not self.paused
        elif event.key == pygame.K_r:
            self.reset()
        elif event.key == pygame.K_ESCAPE:
            return False
        return True

    def run(self) -> None:
        running = True
        while running:
            dt = min(self.clock.tick(120) / 1000.0, 0.05)
            for event in pygame.event.get():
                running = self.handle_input(event)
                if not running:
                    break
            self.update(dt)
            ox = oy = 0
            if self.shake > 0:
                mag = 6 * (self.shake / 0.35)
                ox = int(random.uniform(-mag, mag))
                oy = int(random.uniform(-mag, mag))
            frame = pygame.Surface((WIDTH, HEIGHT))
            flash = min(1.0, self.eat_flash / 0.22)
            bg = (
                int(lerp(BG[0], 40, flash)),
                int(lerp(BG[1], 28, flash)),
                int(lerp(BG[2], 36, flash)),
            )
            frame.fill(bg)
            self.draw_board(frame)
            self.draw_food(frame, pygame.time.get_ticks() / 1000.0)
            self.draw_snake(frame)
            for particle in self.particles:
                particle.draw(frame)
            self.draw_hud(frame)
            self.draw_overlay(frame)
            self.screen.fill(BG)
            self.screen.blit(frame, (ox, oy))
            pygame.display.flip()
        pygame.quit()


def main() -> None:
    try:
        SnakeGame().run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
