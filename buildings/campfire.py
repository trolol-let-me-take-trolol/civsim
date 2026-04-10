from core.buildsys import Building

class CampfireBuild(Building):
    name = "Костёр"
    id = 0
    texture = "campfire"

def register_building():
    return CampfireBuild
