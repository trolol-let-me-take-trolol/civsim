import random


class UnitGroup:
    def __init__(self, units, x, y, world):
        self.x = x
        self.y = y
        self.world = world

        for unit in units:
            if not self._is_valid_unit(unit):
                raise ValueError("Invalid unit")

        if not units:
            raise ValueError("Group can't be empty")

        self.units = units[:]
        self.main_unit = units[0]

        for unit in units:
            unit.group = self

    def _is_valid_unit(self, unit):
        if unit.x != self.x or unit.y != self.y or unit.group is not None:
            return False
        return True

    def update(self, world):
        for unit in self.units[:]:
            unit.update(world)

    def add_unit(self, unit):
        if not self._is_valid_unit(unit):
            raise ValueError("Invalid unit")
        self.units.append(unit)
        unit.group = self

    def remove_unit(self, unit):
        if unit in self.units:
            self.units.remove(unit)
            unit.group = None
        if not self.units:
            self.world.unit_groups[self.x][self.y] = None
            return
        if unit is self.main_unit:
            self.main_unit = self.units[0]


class Unit:
    def __init__(self, unit_type, world, x, y):
        self.type = unit_type
        self.world = world
        self.x = x
        self.y = y
        self.group = None

    def update(self, world):
        if random.random() < 0.05:
            self.move(random.randint(-1, 1), random.randint(-1, 1))

    def move(self, dx, dy):
        new_x = max(0, min(self.world.w - 1, self.x + dx))
        new_y = max(0, min(self.world.h - 1, self.y + dy))

        if new_x == self.x and new_y == self.y:
            return

        old_group = self.group
        old_group.remove_unit(self)

        self.x, self.y = new_x, new_y
        target_group = self.world.unit_groups[self.x][self.y]

        if target_group:
            target_group.add_unit(self)
        else:
            new_group = UnitGroup([self], self.x, self.y, self.world)
            self.world.unit_groups[self.x][self.y] = new_group
