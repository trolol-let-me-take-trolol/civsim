import pygame as pg
import os
from settings import *
from worldgen import World


def load_texture(name):
    path = f"textures/{name}.png"
    if os.path.isfile(path):
        return pg.image.load(path).convert_alpha()
    surf = pg.Surface((CELL_SIZE, CELL_SIZE))
    surf.fill((255, 0, 255))
    return surf


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

    def screen_to_world(self, mouse_pos):
        mx, my = mouse_pos
        tx = int((mx - self.x) / (CELL_SIZE * self.zoom))
        ty = int((my - self.y) / (CELL_SIZE * self.zoom))
        return tx, ty


class WorldRenderer:
    def __init__(self, world):
        self.world = world
        self.full_surf = pg.Surface((world.w * CELL_SIZE, world.h * CELL_SIZE))
        self.textures = [
            load_texture("tiles/plain"),
            load_texture("tiles/forest"),
            load_texture("tiles/mountain")
        ]
        self.overlays = [
            pg.Surface((0, 0), pg.SRCALPHA),
            load_texture("overlays/iron")
        ]
        self.unit_textures = [load_texture("units/test")]
        self.render_all()

    def render_all(self):
        for y in range(self.world.h):
            for x in range(self.world.w):
                t = self.world.tiles[x][y]
                pos = (x * CELL_SIZE, y * CELL_SIZE)
                self.full_surf.blit(self.textures[t.type], pos)
                if t.overlay:
                    self.full_surf.blit(self.overlays[t.overlay], pos)

    def update_view(self, zoom):
        size = (int(self.world.w * CELL_SIZE * zoom),
                int(self.world.h * CELL_SIZE * zoom))
        return pg.transform.smoothscale(self.full_surf, size)

    def draw_units(self, screen, camera):
        for y in range(self.world.h):
            for x in range(self.world.w):
                group = self.world.unit_groups[x][y]
                if group:
                    # Рисуем юнитов с учетом зума и смещения камеры
                    ux = x * CELL_SIZE * camera.zoom + camera.x
                    uy = y * CELL_SIZE * camera.zoom + camera.y
                    u_size = int(CELL_SIZE * camera.zoom)
                    img = pg.transform.scale(
                        self.unit_textures[group.main_unit.type],
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


def main():
    pg.init()
    screen = pg.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
    clock = pg.time.Clock()
    world = World(W_TILES, H_TILES)
    renderer = WorldRenderer(world)
    camera = Camera()
    dragging = False
    view_surf = renderer.update_view(camera.zoom)

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return
            if event.type == pg.MOUSEBUTTONDOWN:
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

        camera.apply_limits(view_surf)
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
