import pygame as pg
import random
import hashlib



def load_texture(name):
    return pg.image.load(f"textures/{name}.png")



PLAIN = 0
FOREST = 1
MOUNTAIN = 2

OVERLAY_NONE = 0
OVERLAY_IRON = 1

textures = [
    load_texture("tiles/plain"),
    load_texture("tiles/forest"),
    load_texture("tiles/mountain")
]

overlay_textures = [
    pg.Surface((16, 16), pg.SRCALPHA),
    load_texture("overlays/iron")
]

CELL_SIZE = 16
NEIGHS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

screen = pg.display.set_mode((800, 800))
pg.display.set_caption("Цивилизация")



class Tile:
    def __init__(self, tile_type=PLAIN, overlay=OVERLAY_NONE):
        self.type = tile_type
        self.overlay = overlay



class World:
    def __init__(self, w, h, seed=None):
        self.w = w
        self.h = h
        if seed is None:
            self.seed = random.randint(0, 10**10)
        else:
            self.seed = seed
        self.tiles = [[Tile() for _ in range(h)] for _ in range(w)]
        self.generate()

    def get_tile(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.tiles[x][y]
        return None

    def hash_coords(self, x, y, extra=""):
        input_data = f"{x},{y},{self.seed},{extra}".encode()
        hash_value = int(hashlib.md5(input_data).hexdigest(), 16)
        return hash_value

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
                hash_val = self.hash_coords(x, y, f"neighbor_{dx}_{dy}")
                probability = (hash_val % 1000) / 1000
                if probability < 0.7 and steps < size:
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in visited:
                        queue.append((nx, ny))
            if steps >= size:
                break

    def fix_clusters(self, tile_type, iters=2):
        print(f"Фикс кластеров")
        for _ in range(iters):
            to_fill = []
            to_erase = []

            for x in range(self.w):
                for y in range(self.h):
                    tile = self.get_tile(x, y)
                    if tile.type not in [PLAIN, tile_type]:
                        continue
                    same = 0
                    for dx, dy in NEIGHS:
                        neigh = self.get_tile(x + dx, y + dy)
                        if neigh and neigh.type == tile_type:
                            same += 1
                    if same >= 3 and tile.type == PLAIN:
                        to_fill.append((x, y))
                    elif same <= 1 and tile.type == tile_type:
                        to_erase.append((x, y))

            for x, y in to_fill:
                self.get_tile(x, y).type = tile_type
            for x, y in to_erase:
                self.get_tile(x, y).type = PLAIN

    def generate(self):
        print(f"Генерация карты с сидом: {self.seed}")
        self.generate_forests()
        self.generate_mountains()
        self.fix_clusters(FOREST)
        self.fix_clusters(MOUNTAIN)
        self.place_iron()

    def generate_forests(self):
        forest_count = (self.hash_coords(0, 0, "forest_count") % 3) + 3
        for i in range(forest_count):
            hash_x = self.hash_coords(i, 0, "forest_x")
            hash_y = self.hash_coords(0, i, "forest_y")
            start_x = hash_x % self.w
            start_y = hash_y % self.h
            self.generate_cluster(start_x, start_y, FOREST, 50)

    def generate_mountains(self):
        mountain_count = (self.hash_coords(1, 1, "mountain_count") % 2) + 2
        for i in range(mountain_count):
            hash_x = self.hash_coords(i, i, "mountain_x")
            hash_y = self.hash_coords(i * 2, i, "mountain_y")
            start_x = hash_x % self.w
            start_y = hash_y % self.h
            self.generate_cluster(start_x, start_y, MOUNTAIN, 50)

    def place_iron(self):
        for x in range(self.w):
            for y in range(self.h):
                tile = self.get_tile(x, y)
                if tile.type == MOUNTAIN:
                    ok = True
                    for dx, dy in NEIGHS:
                        neigh = self.get_tile(x + dx, y + dy)
                        if not neigh or neigh.type != MOUNTAIN:
                            ok = False
                    hash_prob = self.hash_coords(x, y, "iron_prob")
                    probability = (hash_prob % 100) / 100
                    if ok and probability < 0.1:
                        tile.overlay = OVERLAY_IRON

    def draw(self, screen):
        for y in range(self.h):
            for x in range(self.w):
                tile_type = self.get_tile(x, y).type
                tile_overlay = self.get_tile(x, y).overlay
                screen.blit(textures[tile_type], (x * 16, y * 16))
                screen.blit(overlay_textures[tile_overlay], (x * 16, y * 16))



w, h = 50, 50
world = World(w, h)

world.draw(screen)
pg.display.update()

run = True
while run:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_r:
                world = World(w, h)
                world.draw(screen)
                pg.display.update()
            elif event.key == pg.K_s:
                with open("last_seed.txt", "w") as f:
                    f.write(str(world.seed))
                print(f"Текущий сид сохранён: {world.seed}")

pg.quit()
