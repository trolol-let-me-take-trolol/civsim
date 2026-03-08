# --- Экран и FPS ---
SCREEN_SIZE = 800
FPS = 60

# --- Мир ---
W_TILES = 100
H_TILES = 100
CELL_SIZE = 16

# --- Камера ---
DEFAULT_ZOOM = 1.0
MIN_ZOOM = 0.5
MAX_ZOOM = 3.0
ZOOM_STEP = 0.1

# --- Генерация ---
FOREST_CLUSTERS = 20
FOREST_SIZE = 60
MOUNTAIN_CLUSTERS = 10
MOUNTAIN_SIZE = 40
CLUSTER_PROBABILITY = 0.7
IRON_PROBABILITY = 10

# --- Типы тайлов ---
TILE_PLAIN = 0
TILE_FOREST = 1
TILE_MOUNTAIN = 2
OVERLAY_NONE = 0
OVERLAY_IRON = 1

# --- Экономика (Food, Prod, Gold) ---
TILE_STATS = {
    TILE_PLAIN: (2, 1, 1),
    TILE_FOREST: (1, 2, 0),
    TILE_MOUNTAIN: (0, 1, 0)
}

OVERLAY_STATS = {
    OVERLAY_NONE: (0, 0, 0),
    OVERLAY_IRON: (0, 3, 0)
}

# --- Интерфейс ---
TILE_NAMES = {
    TILE_PLAIN: "Plain",
    TILE_FOREST: "Forest",
    TILE_MOUNTAIN: "Mountain"
}
OVERLAY_NAMES = {
    OVERLAY_NONE: "",
    OVERLAY_IRON: "Iron"
}
SELECT_COLOR = (255, 255, 255)
