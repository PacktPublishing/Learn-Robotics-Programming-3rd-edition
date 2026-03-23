from pyexpat.errors import messages
import ollama

from common.mqtt_behavior import connect, publish_json


# https://github.com/ollama/ollama/blob/main/docs/api.md#chat-request-with-history-with-tools
# https://github.com/ollama/ollama-python
# https://projects.raspberrypi.org/en/projects/llm-rpi/0

# You are RobotIntent, running on a mobile robot. You translate natural language into tool calls over MQTT.

# Capabilities:
# - publish_mqtt(topic, payload) to send a command
# - read_mqtt(topic) to snapshot the latest message

# Command map & synonyms (examples, not exhaustive):
# - "go forward", "drive ahead", "move straight" -> publish to topic: wheel_control/wheel_speed_mm with json payload "[40, 40]"
# - "turn left", "rotate left" -> publish to topic: wheel_control/wheel_speed_mm with json payload "[-40, 40]"
# - "turn right", "rotate right" -> publish to topic: wheel_control/wheel_speed_mm with json payload "[40, -40]"
# - "stop", "halt", "freeze" -> publish to topic: all/stop with no payload
# - "look at faces", "follow face", "track face" -> publish to topic: launcher/start with json payload "face_detector", then publish to topic: launcher/start with json payload "look_at_face"
# - "stop looking at faces", "stop tracking faces" -> publish to topic: launcher/stop with json payload "face_detector", then publish to topic: launcher/stop with json payload "look_at_face"
# - "start following lines" -> publish to topic: launcher/start with json payload "line_detector", then publish to topic: launcher/start with json payload "line_follower"
# - "stop following lines" -> publish to topic: launcher/stop with json payload "line_detector", then publish to topic: launcher/stop with json payload "line_follower"
# - "start following objects" -> publish to topic: launcher/start with json payload "colored_object_detector", then publish to topic: launcher/start with json payload "object_follower"
# - "stop following objects" -> publish to topic: launcher/stop with json payload "colored_object_detector", then publish to topic: launcher/stop with json payload "object_follower"
# - "Get distance in front"  -> publish to topic: sensors/distance/control/start_ranging with no payload, then listen to topic: "sensors/distance_mm", then publish to topic: sensors/distance/control/stop_ranging with no payload
# """

client = connect()

def forward(speed):
    publish_json(client, "wheel_control/wheel_speed_mm", [speed, speed])

def backward(speed):
    publish_json(client, "wheel_control/wheel_speed_mm", [-speed, -speed])

def turn_left(speed):
    publish_json(client, "wheel_control/wheel_speed_mm", [-speed, speed])

def turn_right(speed):
    publish_json(client, "wheel_control/wheel_speed_mm", [speed, -speed])

def all_stop():
    publish_json(client, "all/stop", "")

def track_faces():
    publish_json(client, "launcher/start", "face_detector")
    publish_json(client, "launcher/start", "look_at_face")

def stop_tracking_faces():
    publish_json(client, "launcher/stop", "face_detector")
    publish_json(client, "launcher/stop", "look_at_face")


tools=[
    {
        "type": "function",
        "function": {
            "name": "track_faces",
            "description": "Start tracking faces",
            "parameters": {}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_tracking_faces",
            "description": "Stop tracking faces",
            "parameters": {}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forward",
            "description": "Drive the robot forward",
            "parameters": {
                'type': 'object',
                'properties': {
                    "speed": {
                        "type": "integer",
                        "description": "Wheel speed in mm, range 0 to 180"
                    }
                },
            }
        }
    },
    # backward
    {
        "type": "function",
        "function": {
            "name": "backward",
            "description": "Drive the robot backward",
            "parameters": {
                'type': 'object',
                'properties': {
                    "speed": {
                        "type": "integer",
                        "description": "Wheel speed in mm, range 0 to 180"
                    }
                },
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "turn_left",
            "description": "Turn the robot left",
            "parameters": {
                'type': 'object',
                'properties': {
                    "speed": {
                        "type": "integer",
                        "description": "Wheel speed in mm, range 0 to 180"
                    }
                },
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "turn_right",
            "description": "Turn the robot right",
            "parameters": {
                'type': 'object',
                'properties': {
                    "speed": {
                        "type": "integer",
                        "description": "Wheel speed in mm, range 0 to 180"
                    }
                },
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop",
            "description": "Stop the robot",
            "parameters": {}
        }
    }
]

if __name__ == "__main__":
    response = ollama.chat(
        model="robot-intent-1b",
        messages=[
            {"role": "user", "content": "Go forward"}
        ],
        tools=tools,

    )

    print("Content:", response['message']['content'])
    print("Tool calls:", response['message'].get('tool_calls', "No tool calls"))



def chat(message):
    response = ollama.chat(
        model="robot-intent-1b",
        messages=[
            {"role": "user", "content": message}
        ],
        tools=tools,
    )
    print("Content:", response['message']['content'])
    print("Tool calls:", response['message'].get('tool_calls', "No tool calls"))

# cd robot
# robotpython
# >>> from model_chat import chat
