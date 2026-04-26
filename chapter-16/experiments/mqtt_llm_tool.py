import json

import requests

from common.mqtt_behavior import connect, publish_json

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"

# MQTT client
client = connect()

latest = {}  # simple snapshot store

def on_message(_c, _u, msg):
    latest[msg.topic] = msg.payload.decode("utf-8")
client.on_message = on_message
client.subscribe("robot/status/#")
client.loop_start()

tools = [
  {
    "type": "function",
    "function": {
      "name": "publish_mqtt",
      "description": "Publish a JSON payload to an MQTT topic.",
      "parameters": {
        "type":"object",
        "properties":{
          "topic":{"type":"string"},
          "payload":{"type":"object"}
        },
        "required":["topic","payload"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "read_mqtt",
      "description": "Return last seen message on topic.",
      "parameters":{
        "type":"object",
        "properties":{"topic":{"type":"string"}},
        "required":["topic"]
      }
    }
  }
]

def chat(user_text):
    messages = [{"role":"system","content":"You are RobotIntent."},
                {"role":"user","content": user_text}]
    r = requests.post(OLLAMA_URL, json={
        "model":"robot-intent-1b",
        "messages": messages,
        "tools": tools
    })
    resp = r.json()["choices"][0]["message"]

    # If the model called a tool, execute it:
    for call in resp.get("tool_calls", []):
        fn = call["function"]["name"]
        args = json.loads(call["function"]["arguments"])
        if fn == "publish_mqtt":
            client.publish(args["topic"], json.dumps(args["payload"]))
            tool_result = {"ok": True}
        elif fn == "read_mqtt":
            tool_result = {"value": latest.get(args["topic"], None)}
        else:
            tool_result = {"error": "unknown tool"}

        # Send result back so the model can finalize
        messages += [resp,
                     {"role":"tool","tool_call_id": call["id"],
                      "name": fn, "content": json.dumps(tool_result)}]
        r = requests.post(OLLAMA_URL, json={
            "model":"robot-intent-1b",
            "messages": messages
        })
        resp = r.json()["choices"][0]["message"]

    return resp["content"]

print(chat("drive ahead for a bit"))
print(chat("what's the battery level?"))
