class Building:
    def __init__(self, world, x, y):
        self.world = world
        self.x = x
        self.y = y
        world.tiles[x][y].building = self
    def update(self, world):
        pass
