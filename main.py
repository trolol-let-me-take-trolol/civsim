import pygame as pg
import os
from settings import *
from core.worldgen import World, Tile
from core.unitsys import Unit
from core.buildsys import Building
from importlib import import_module

def load_texture(name):
    path = os.path.join('textures', f"{name}.png")
    if os.path.isfile(path):
        surf = pg.image.load(path).convert_alpha()
        w, h = surf.get_size()
        corners = [surf.get_at((0, 0)), surf.get_at((w - 1, 0)),
                   surf.get_at((0, h - 1)), surf.get_at((w - 1, h - 1))]
        if all(c[3] == 0 for c in corners):
            has_black_opaque = False
            for x in range(w):
                for y in range(h):
                    c = surf.get_at((x, y))
                    if c[3] != 0 and c[:3] == (0, 0, 0):
                        has_black_opaque = True
                        break
                if has_black_opaque:
                    break
            if has_black_opaque:
                surf.set_colorkey((0, 0, 0))
        return surf
    surf = pg.Surface((CELL_SIZE, CELL_SIZE))
    surf.fill((255, 0, 255))
    return surf

def get_object_texture(obj):
    if isinstance(obj, Tile):
        texture = pg.Surface((CELL_SIZE, CELL_SIZE))
        texture.blit(tile_textures[obj.type], (0, 0))
        if obj.overlay:
            texture.blit(overlay_textures[obj.overlay], (0, 0))
        if obj.building:
            texture.blit(buildings[obj.building.id]["texture"], (0, 0))
    elif isinstance(obj, Unit):
        texture = units[obj.id]["texture"]
    else:
        raise TypeError(type(obj))
    return texture

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.zoom = DEFAULT_ZOOM

    def handle_zoom(self, mouse_pos, direction, renderer):
        mx, my = mouse_pos
        wx, wy = (mx - self.x) / self.zoom, (my - self.y) / self.zoom
        old_zoom = self.zoom
        if direction == "in":
            self.zoom = min(MAX_ZOOM, self.zoom + ZOOM_STEP)
        else:
            self.zoom = max(MIN_ZOOM, self.zoom - ZOOM_STEP)

        if old_zoom != self.zoom:
            new_surf = renderer.update_view(self.zoom)
            self.x = mx - wx * self.zoom
            self.y = my - wy * self.zoom
            return new_surf
        return None

    def handle_move(self, rel):
        self.x += rel[0]
        self.y += rel[1]

    def apply_limits(self, view_surf, screen_width, screen_height):
        vw, vh = view_surf.get_size()
        if vw > screen_width:
            self.x = min(0, max(self.x, screen_width - vw))
        else:
            self.x = (screen_width - vw) // 2
        if vh > screen_height:
            self.y = min(0, max(self.y, screen_height - vh))
        else:
            self.y = (screen_height - vh) // 2

    def screen_to_world(self, mouse_pos):
        mx, my = mouse_pos
        tx = int((mx - self.x) / (CELL_SIZE * self.zoom))
        ty = int((my - self.y) / (CELL_SIZE * self.zoom))
        return tx, ty


class WorldRenderer:
    def __init__(self, world):
        self.world = world
        self.full_surf = pg.Surface((world.w * CELL_SIZE, world.h * CELL_SIZE))
        self.render_all()

    def render_all(self):
        for y in range(self.world.h):
            for x in range(self.world.w):
                t = self.world.tiles[x][y]
                tile_texture = get_object_texture(t)
                pos = (x * CELL_SIZE, y * CELL_SIZE)
                self.full_surf.blit(tile_texture, pos)

    def update_view(self, zoom):
        size = (int(self.world.w * CELL_SIZE * zoom),
                int(self.world.h * CELL_SIZE * zoom))
        return pg.transform.smoothscale(self.full_surf, size)

    def draw_units(self, screen, camera):
        for group in self.world.active_groups:
            x, y = group.x, group.y
            # Рисуем юнитов с учетом зума и смещения камеры
            ux = x * CELL_SIZE * camera.zoom + camera.x
            uy = y * CELL_SIZE * camera.zoom + camera.y
            u_size = int(CELL_SIZE * camera.zoom)
            img = pg.transform.scale(
                get_object_texture(group.main_unit),
                (u_size, u_size)
            )
            screen.blit(img, (ux, uy))

    def draw_ui(self, screen, camera, world):
        tx, ty = camera.screen_to_world(pg.mouse.get_pos())
        tile = world.get_tile(tx, ty)
        if tile:
            rect = (tx * CELL_SIZE * camera.zoom + camera.x,
                    ty * CELL_SIZE * camera.zoom + camera.y,
                    CELL_SIZE * camera.zoom, CELL_SIZE * camera.zoom)
            pg.draw.rect(screen, SELECT_COLOR, rect, 2)
            f, p, g = tile.get_resources()
            info = f"Coord: {tx},{ty} | {TILE_NAMES[tile.type]} " \
                   f"{OVERLAY_NAMES[tile.overlay]} | F:{f} P:{p} G:{g}"
            pg.display.set_caption(info)

def init():
    global units, tile_textures, overlay_textures, building_textures, buildings
    units = {}
    buildings = {}
    for file in os.listdir('units'):
        if not os.path.isfile(os.path.join('units', file)):
            continue
        fname=file.split('.')[0]
        if not fname.isalnum():
            continue
        unit_cls = import_module(f'units.{fname}').register_unit()
        if not issubclass(unit_cls, Unit):
            continue
        units[unit_cls.id] = {
            "name": unit_cls.name,
            "class": unit_cls,
            "texture": load_texture(f'units/{unit_cls.texture}')
            }
    for file in os.listdir('buildings'):
        if not os.path.isfile(os.path.join('buildings', file)):
            continue
        fname=file.split('.')[0]
        if not fname.isalnum():
            continue
        build_cls = import_module(f'buildings.{fname}').register_building()
        if not issubclass(build_cls, Building):
            continue
        buildings[build_cls.id] = {
            "name": build_cls.name,
            "class": build_cls,
            "texture": load_texture(f'buildings/{build_cls.texture}')
            }
    
    tile_textures = [
        load_texture("tiles/plain"),
        load_texture("tiles/forest"),
        load_texture("tiles/mountain")
    ]
    overlay_textures = [
        pg.Surface((0, 0), pg.SRCALPHA),
        load_texture("overlays/iron")
    ]
    

def main():
    pg.init()
    screen_width, screen_height = 640, 640
    screen = pg.display.set_mode((screen_width, screen_height), pg.RESIZABLE)
    init()
    clock = pg.time.Clock()
    world = World(W_TILES, H_TILES, units, buildings)
    renderer = WorldRenderer(world)
    camera = Camera()
    dragging = False
    view_surf = renderer.update_view(camera.zoom)

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return
            elif event.type == pg.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                screen = pg.display.set_mode((screen_width, screen_height), pg.RESIZABLE)
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 3:
                    dragging = True
                elif event.button == 4:
                    res = camera.handle_zoom(event.pos, "in", renderer)
                    if res:
                        view_surf = res
                elif event.button == 5:
                    res = camera.handle_zoom(event.pos, "out", renderer)
                    if res:
                        view_surf = res
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 3:
                    dragging = False
            elif event.type == pg.MOUSEMOTION and dragging:
                camera.handle_move(event.rel)

        camera.apply_limits(view_surf, screen_width, screen_height)
        screen.fill((30, 30, 30))

        # Сначала рисуем саму карту
        screen.blit(view_surf, (camera.x, camera.y))
        # Затем рисуем юнитов поверх неё
        renderer.draw_units(screen, camera)
        # И в конце UI
        renderer.draw_ui(screen, camera, world)

        pg.display.flip()
        clock.tick(FPS)
        world.update()

if __name__ == "__main__":
    main()
