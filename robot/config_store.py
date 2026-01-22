import ujson as json
import dbm.dumb
from common.mqtt_behavior import connect, publish_json


class RobotConfigStore:
    def __init__(self):
        self.db = dbm.dumb.open("robot_config.db", 'c')

    def on_set(self, client, userdata, message):
        key, value = json.loads(message.payload)
        print(f"Setting {key} to {value}")
        self.db[key] = json.dumps(value)
        self.db.sync()
        publish_json(client, "config/updated", {key: value})

    def on_get(self, client, userdata, message):
        data = json.loads(message.payload)
        response = {key: json.loads(self.db[key]) for key in data if key in self.db}
        publish_json(client, "config/updated", response)

    def on_list(self, client, userdata, message):
        """List all configuration keys and values."""
        all_config = {}
        for key in self.db.keys():
            # Keys are bytes in dbm, decode them
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            all_config[key_str] = json.loads(self.db[key])
        print(f"Current config store: {all_config}")
        publish_json(client, "config/list", all_config)

    def start(self):
        client = connect(start_loop=False)
        client.subscribe("config/set")
        client.message_callback_add("config/set", self.on_set)
        client.subscribe("config/get")
        client.message_callback_add("config/get", self.on_get)
        client.subscribe("config/list/get")
        client.message_callback_add("config/list/get", self.on_list)
        client.loop_forever()

config_store = RobotConfigStore()
config_store.start()
