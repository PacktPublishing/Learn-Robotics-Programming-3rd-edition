import numpy as np
from common.mqtt_behavior import publish_json

left = 0
bottom = 0
right = 1500
top = 1500
cutout_left = 1000
cutout_top = 500
walls = [
    (left, top),
    (right, top),
    (right, cutout_top),
    (cutout_left, cutout_top),
    (cutout_left, bottom),
    (left, bottom)
]

def publish_map(client):
    publish_json(client, "localisation/map", {
        "walls": walls
    })

class MapFrame:
    def __init__(self, margin: int):
        """Mapped coordinates represents a margin around the world coordinates.
        The extents of this should be
        """
        self.w_left = -margin
        self.w_right = right + margin
        self.w_bottom = -margin
        self.w_top = top + margin
        self.margin = margin

    @property
    def width(self) -> int:
        return self.w_right - self.w_left

    @property
    def height(self) -> int:
        return self.w_top - self.w_bottom

    def world_to_map(self, world_coordinates: np.ndarray) -> np.ndarray:
        return world_coordinates + np.array([self.margin, self.margin])

    def map_to_world(self, map_coordinates: np.ndarray) -> np.ndarray:
        return map_coordinates - np.array([self.margin, self.margin])
