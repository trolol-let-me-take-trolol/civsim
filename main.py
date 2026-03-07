import pygame as pg
import random
import hashlib
import os
from settings import *

def load_texture(name):
    path = f"textures/{name}.png"
    if os.path.isfile(path):
        return pg.image.load(path).convert_alpha()
    surf = pg.Surface((CELL_SIZE, CELL_SIZE))
    surf.fill((255, 0, 255))
    return surf

class Tile:
    __slots__ = ('type', 'overlay')
    def __init__(self, t_type=TILE_PLAIN, overlay=OVERLAY_NONE):
        self.type = t_type
        self.overlay = overlay

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = DEFAULT_ZOOM

    def handle_zoom(self, mouse_pos, direction, world):
        mx, my = mouse_pos
        wx, wy = (mx - self.x) / self.zoom, (my - self.y) / self.zoom
        old_zoom = self.zoom
        if direction == "in":
            self.zoom = min(MAX_ZOOM, self.zoom + ZOOM_STEP)
        else:
            self.zoom = max(MIN_ZOOM, self.zoom - ZOOM_STEP)
        
        if old_zoom != self.zoom:
            new_surf = world.update_view(self.zoom)
            self.x = mx - wx * self.zoom
            self.y = my - wy * self.zoom
            return new_surf
        return None

    def handle_move(self, rel):
        self.x += rel[0]
        self.y += rel[1]

    def apply_limits(self, view_surf):
        vw, vh = view_surf.get_size()
        if vw > SCREEN_SIZE:
            self.x = min(0, max(self.x, SCREEN_SIZE - vw))
        else:
            self.x = (SCREEN_SIZE - vw) // 2
        if vh > SCREEN_SIZE:
            self.y = min(0, max(self.y, SCREEN_SIZE - vh))
        else:
            self.y = (SCREEN_SIZE - vh) // 2

class World:
    def __init__(self, w, h, seed=None):
        self.w, self.h = w, h
        self.seed = seed if seed is not None else random.randint(0, 10**10)
        self.tiles = [[Tile() for _ in range(h)] for _ in range(w)]
        self.full_surf = pg.Surface((w * CELL_SIZE, h * CELL_SIZE))
        self.textures = [load_texture("tiles/plain"), 
                         load_texture("tiles/forest"), 
                         load_texture("tiles/mountain")]
        self.overlays = [pg.Surface((0, 0), pg.SRCALPHA), 
                         load_texture("overlays/iron")]
        self.generate()
        self.render_all()

    def get_tile(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.tiles[x][y]
        return None

    def hash_coords(self, x, y, extra=""):
        data = f"{x},{y},{self.seed},{extra}".encode()
        return int(hashlib.md5(data).hexdigest(), 16)

    def cluster(self, sx, sy, t_type, size):
        queue, visited, steps = [(sx, sy)], set(), 0
        neighs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        while queue and steps < size:
            x, y = queue.pop(0)
            if (x, y) in visited or x < 0 or x >= self.w or y < 0 or y >= self.h:
                continue
            visited.add((x, y))
            if self.tiles[x][y].type != TILE_PLAIN: continue
            self.tiles[x][y].type, steps = t_type, steps + 1
            for dx, dy in neighs:
                if (self.hash_coords(x, y, f"{dx}{dy}") % 1000) / 1000 < CLUSTER_PROBABILITY:
                    queue.append((x + dx, y + dy))

    def fix_clusters(self, tile_type):
        for _ in range(2):
            to_change = []
            for x in range(self.w):
                for y in range(self.h):
                    tile = self.tiles[x][y]
                    same = sum(1 for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)] 
                               if (n := self.get_tile(x+dx, y+dy)) and n.type == tile_type)
                    if same >= 3 and tile.type == TILE_PLAIN:
                        to_change.append((x, y, tile_type))
                    elif same <= 1 and tile.type == tile_type:
                        to_change.append((x, y, TILE_PLAIN))
            for x, y, new_type in to_change:
                self.tiles[x][y].type = new_type

    def place_iron(self):
        for x in range(self.w):
            for y in range(self.h):
                if self.tiles[x][y].type == TILE_MOUNTAIN:
                    if (self.hash_coords(x, y, "iron") % 100) < IRON_PROBABILITY:
                        self.tiles[x][y].overlay = OVERLAY_IRON

    def generate(self):
        for i in range(FOREST_CLUSTERS):
            sx, sy = self.hash_coords(i, 0) % self.w, self.hash_coords(0, i) % self.h
            self.cluster(sx, sy, TILE_FOREST, FOREST_SIZE)
        for i in range(MOUNTAIN_CLUSTERS):
            sx, sy = self.hash_coords(i, i) % self.w, self.hash_coords(i, i*2) % self.h
            self.cluster(sx, sy, TILE_MOUNTAIN, MOUNTAIN_SIZE)
        self.fix_clusters(TILE_FOREST)
        self.fix_clusters(TILE_MOUNTAIN)
        self.place_iron()

    def render_all(self):
        for y in range(self.h):
            for x in range(self.w):
                t = self.tiles[x][y]
                pos = (x * CELL_SIZE, y * CELL_SIZE)
                self.full_surf.blit(self.textures[t.type], pos)
                if t.overlay: self.full_surf.blit(self.overlays[t.overlay], pos)

    def update_view(self, zoom):
        return pg.transform.smoothscale(self.full_surf, (int(self.w * CELL_SIZE * zoom), int(self.h * CELL_SIZE * zoom)))

def main():
    pg.init()
    screen = pg.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    clock = pg.time.Clock()
    world = World(W_TILES, H_TILES)
    camera = Camera()
    dragging = False
    view_surf = world.update_view(camera.zoom)
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT: pg.quit(); return
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 3: dragging = True
                elif event.button == 4:
                    res = camera.handle_zoom(event.pos, "in", world)
                    if res: view_surf = res
                elif event.button == 5:
                    res = camera.handle_zoom(event.pos, "out", world)
                    if res: view_surf = res
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 3: dragging = False
            elif event.type == pg.MOUSEMOTION and dragging:
                camera.handle_move(event.rel)
        camera.apply_limits(view_surf)
        screen.fill((30, 30, 30))
        screen.blit(view_surf, (camera.x, camera.y))
        pg.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
