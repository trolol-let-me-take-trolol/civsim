TASK_GOTO_TILE = 0

class AITask:
    def __init__(self, task_type, details):
        self.task_type = task_type
        self.details = details
    def apply(self, unit):
        if self.task_type == TASK_GOTO_TILE:
            tile_type = self.details["tile_type"]
            ux, uy = unit.x, unit.y
            cur_x = None
            cur_y = None
            cur_dist = float('inf')
            if unit.world.get_tile(ux, uy).type == tile_type:
                return
            for dx in range(-8, 9):
                max_dy = 8 - abs(dx)
                for dy in range(-max_dy, max_dy + 1):
                    if unit.world.get_tile(ux + dx, uy + dy).type == tile_type:
                        if abs(dx) + abs(dy) < cur_dist:
                            cur_x, cur_y = ux + dx, uy + dy
                            cur_dist = abs(dx) + abs(dy)
            if cur_x is None or cur_y is None:
                return
            dx, dy = abs(ux - cur_x), abs(uy - cur_y)
            if dx > dy:
                unit.move(1 if cur_x > ux else -1, 0)
            else:
                unit.move(0, 1 if cur_y > uy else -1)
