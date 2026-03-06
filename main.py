import pygame as pg
import random
import hashlib
import os

PLAIN, FOREST, MOUNTAIN = 0, 1, 2
OVERLAY_NONE, OVERLAY_IRON = 0, 1
CELL_SIZE = 16
W_TILES, H_TILES = 100, 100
SCREEN_SIZE = 800
NEIGHS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def load_texture(name):
    path = f"textures/{name}.png"
    if os.path.exists(path):
        return pg.image.load(path).convert_alpha()
    surf = pg.Surface((CELL_SIZE, CELL_SIZE))
    surf.fill((255, 0, 255))
    return surf


class Tile:
    __slots__ = ('type', 'overlay')

    def __init__(self, t_type=PLAIN, overlay=OVERLAY_NONE):
        self.type = t_type
        self.overlay = overlay


class World:
    def __init__(self, w, h, seed=None):
        self.w, self.h = w, h
        self.seed = seed if seed is not None else random.randint(0, 10**10)
        self.tiles = [[Tile() for _ in range(h)] for _ in range(w)]
        self.full_surf = pg.Surface((w * CELL_SIZE, h * CELL_SIZE))
        
        self.textures = [load_texture("tiles/plain"), 
                         load_texture("tiles/forest"), 
                         load_texture("tiles/mountain")]
        self.overlays = [pg.Surface((0, 0)), load_texture("overlays/iron")]
        
        self.generate()
        self.render_all()

    def hash_coords(self, x, y, extra=""):
        data = f"{x},{y},{self.seed},{extra}".encode()
        return int(hashlib.md5(data).hexdigest(), 16)

    def generate(self):
        for i in range(20):
            sx, sy = self.hash_coords(i, 0) % self.w, self.hash_coords(0, i) % self.h
            self.cluster(sx, sy, FOREST, 60)
        for i in range(10):
            sx, sy = self.hash_coords(i, i) % self.w, self.hash_coords(i, i*2) % self.h
            self.cluster(sx, sy, MOUNTAIN, 40)

    def cluster(self, sx, sy, t_type, size):
        q, v, steps = [(sx, sy)], set(), 0
        while q and steps < size:
            x, y = q.pop(0)
            if (x, y) in v or x < 0 or x >= self.w or y < 0 or y >= self.h:
                continue
            v.add((x, y))
            if self.tiles[x][y].type != PLAIN: continue
            self.tiles[x][y].type, steps = t_type, steps + 1
            for dx, dy in NEIGHS:
                if (self.hash_coords(x, y, f"{dx}{dy}") % 1000) / 1000 < 0.7:
                    q.append((x + dx, y + dy))

    def render_all(self):
        for y in range(self.h):
            for x in range(self.w):
                t = self.tiles[x][y]
                self.full_surf.blit(self.textures[t.type], (x*CELL_SIZE, y*CELL_SIZE))
                if t.overlay:
                    self.full_surf.blit(self.overlays[t.overlay], (x*CELL_SIZE, y*CELL_SIZE))

    def get_view(self, zoom):
        new_size = (int(self.w * CELL_SIZE * zoom), int(self.h * CELL_SIZE * zoom))
        return pg.transform.smoothscale(self.full_surf, new_size)


def main():
    pg.init()
    screen = pg.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    clock = pg.time.Clock()
    world = World(W_TILES, H_TILES)
    
    cam_x, cam_y = 0, 0
    zoom = 1.0
    dragging = False
    
    view_surf = world.get_view(zoom)

    run = True
    while run:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
            
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 3: dragging = True
                if event.button == 4: # Zoom in
                    zoom = min(zoom + 0.1, 3.0)
                    view_surf = world.get_view(zoom)
                if event.button == 5: # Zoom out
                    zoom = max(zoom - 0.1, 0.5)
                    view_surf = world.get_view(zoom)
            
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 3: dragging = False
            
            elif event.type == pg.MOUSEMOTION and dragging:
                cam_x += event.rel[0]
                cam_y += event.rel[1]

        # Ограничение камеры
        w_limit = SCREEN_SIZE - view_surf.get_width()
        h_limit = SCREEN_SIZE - view_surf.get_height()
        cam_x = min(0, max(cam_x, w_limit)) if w_limit < 0 else 0
        cam_y = min(0, max(cam_y, h_limit)) if h_limit < 0 else 0

        screen.fill((30, 30, 30))
        screen.blit(view_surf, (cam_x, cam_y))
        pg.display.flip()
        clock.tick(60)

    pg.quit()

if __name__ == "__main__":
    main()
