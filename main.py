import pygame as pg
import random
import hashlib
import os

PLAIN = 0
FOREST = 1
MOUNTAIN = 2
OVERLAY_NONE = 0
OVERLAY_IRON = 1
CELL_SIZE = 16
W_TILES = 50
H_TILES = 50
SCREEN_SIZE = 800
NEIGHS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def load_texture(name):
    filepath = f"textures/{name}.png"
    if not os.path.isfile(filepath):
        surface = pg.Surface((CELL_SIZE, CELL_SIZE))
        surface.fill((255, 0, 255))
        return surface.convert_alpha()
    return pg.image.load(filepath).convert_alpha()


class Tile:
    __slots__ = ('type', 'overlay')

    def __init__(self, tile_type=PLAIN, overlay=OVERLAY_NONE):
        self.type = tile_type
        self.overlay = overlay


class World:
    def __init__(self, w, h, seed=None):
        self.w = w
        self.h = h
        self.seed = seed if seed is not None else random.randint(0, 10**10)
        self.tiles = [[Tile() for _ in range(h)] for _ in range(w)]
        self.surface = pg.Surface((w * CELL_SIZE, h * CELL_SIZE))
        self.textures = [
            load_texture("tiles/plain"),
            load_texture("tiles/forest"),
            load_texture("tiles/mountain")
        ]
        self.overlay_textures = [
            pg.Surface((CELL_SIZE, CELL_SIZE), pg.SRCALPHA),
            load_texture("overlays/iron")
        ]
        self.generate()
        self.render_to_surface()

    def get_tile(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.tiles[x][y]
        return None

    def hash_coords(self, x, y, extra=""):
        input_data = f"{x},{y},{self.seed},{extra}".encode()
        return int(hashlib.md5(input_data).hexdigest(), 16)

    def generate_cluster(self, start_x, start_y, tile_type, size):
        queue = [(start_x, start_y)]
        visited = set()
        steps = 0
        while queue:
            x, y = queue.pop(0)
            if (x, y) in visited:
                continue
            visited.add((x, y))
            tile = self.get_tile(x, y)
            if not tile or tile.type != PLAIN:
                continue
            tile.type = tile_type
            steps += 1
            for dx, dy in NEIGHS:
                hash_val = self.hash_coords(x, y, f"n_{dx}_{dy}")
                if (hash_val % 1000) / 1000 < 0.7 and steps < size:
                    queue.append((x + dx, y + dy))
            if steps >= size:
                break

    def fix_clusters(self, tile_type, iters=2):
        for _ in range(iters):
            to_change = []
            for x in range(self.w):
                for y in range(self.h):
                    tile = self.tiles[x][y]
                    if tile.type not in [PLAIN, tile_type]:
                        continue
                    same = 0
                    for dx, dy in NEIGHS:
                        neigh = self.get_tile(x + dx, y + dy)
                        if neigh and neigh.type == tile_type:
                            same += 1
                    if same >= 3 and tile.type == PLAIN:
                        to_change.append((x, y, tile_type))
                    elif same <= 1 and tile.type == tile_type:
                        to_change.append((x, y, PLAIN))
            for x, y, new_type in to_change:
                self.tiles[x][y].type = new_type

    def generate(self):
        self.generate_forests()
        self.generate_mountains()
        self.fix_clusters(FOREST)
        self.fix_clusters(MOUNTAIN)
        self.place_iron()

    def generate_forests(self):
        count = (self.hash_coords(0, 0, "f_c") % 3) + 3
        for i in range(count):
            sx = self.hash_coords(i, 0, "f_x") % self.w
            sy = self.hash_coords(0, i, "f_y") % self.h
            self.generate_cluster(sx, sy, FOREST, 50)

    def generate_mountains(self):
        count = (self.hash_coords(1, 1, "m_c") % 2) + 2
        for i in range(count):
            sx = self.hash_coords(i, i, "m_x") % self.w
            sy = self.hash_coords(i * 2, i, "m_y") % self.h
            self.generate_cluster(sx, sy, MOUNTAIN, 50)

    def place_iron(self):
        for x in range(self.w):
            for y in range(self.h):
                tile = self.tiles[x][y]
                if tile.type == MOUNTAIN:
                    is_inner = True
                    for dx, dy in NEIGHS:
                        n = self.get_tile(x + dx, y + dy)
                        if not n or n.type != MOUNTAIN:
                            is_inner = False
                            break
                    prob = (self.hash_coords(x, y, "iron") % 100) / 100
                    if is_inner and prob < 0.1:
                        tile.overlay = OVERLAY_IRON

    def render_to_surface(self):
        for y in range(self.h):
            for x in range(self.w):
                tile = self.tiles[x][y]
                self.surface.blit(self.textures[tile.type],
                                  (x * CELL_SIZE, y * CELL_SIZE))
                if tile.overlay != OVERLAY_NONE:
                    self.surface.blit(self.overlay_textures[tile.overlay],
                                      (x * CELL_SIZE, y * CELL_SIZE))

    def draw(self, target_screen):
        target_screen.blit(self.surface, (0, 0))


def main():
    pg.init()
    screen = pg.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    pg.display.set_caption("Civilization")
    clock = pg.time.Clock()
    world = World(W_TILES, H_TILES)
    run = True
    while run:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                run = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_r:
                    world = World(W_TILES, H_TILES)
                elif event.key == pg.K_s:
                    with open("last_seed.txt", "w") as f:
                        f.write(str(world.seed))
        screen.fill((0, 0, 0))
        world.draw(screen)
        pg.display.flip()
        clock.tick(60)
    pg.quit()


if __name__ == "__main__":
    main()
