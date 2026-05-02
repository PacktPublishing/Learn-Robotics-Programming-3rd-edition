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
