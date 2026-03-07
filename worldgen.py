import random
import hashlib
from settings import *

class Tile:
    __slots__ = ('type', 'overlay')
    def __init__(self, t_type=TILE_PLAIN, overlay=OVERLAY_NONE):
        self.type = t_type
        self.overlay = overlay

class World:
    def __init__(self, w, h, seed=None):
        self.w, self.h = w, h
        self.seed = seed if seed is not None else random.randint(0, 10**10)
        self.tiles = [[Tile() for _ in range(h)] for _ in range(w)]
        self.generate()

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
