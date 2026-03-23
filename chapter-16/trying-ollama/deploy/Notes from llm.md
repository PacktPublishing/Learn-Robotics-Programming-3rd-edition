# Notes from voice

Interacting when ssh'd in:

```shell
danny@learnrob3:~ $ ollama list
NAME                      ID              SIZE      MODIFIED
llama3.2:1b               baf6a787fdff    1.3 GB    About a minute ago
robot-intent-1b:latest    d184b29db821    1.3 GB    About a minute ago
danny@learnrob3:~ $ ollama run robot-intent-1b
```
This takes a while (2 minutes)
```shell
>>> drive forward
Publishing "go forward" to topic: wheel_control/wheel_speed_mm with json payload "[40, 40]".

Confirmed action: Driven forward.
>>> say hello
Publishing "look at faces" to topic: launcher/start with json payload "face_detector", then publish
to topic: launcher/start with json payload "look_at_face".
```

Note it's quicker after the first chat.
```shell
>>> stop
Publishing "all/stop" to topic: all/stop with no payload.

>>> follow that line
Publishing "start following lines" to topic: launcher/start with json payload "line_detector", then
publish to topic: launcher/start with json payload "line_follower".

>>> stop
Publishing "all/stop" to topic: all/stop with no payload.
```

This is not quick... I don't know if that's yet viable. It is sticking to the script though.
```shell
>>> what are your capabilities?
My capabilities include:

* Publishing MQTT commands (tool calls) to specific topics
* Reading MQTT messages from a specified topic
* Confirming actions after each tool call

I can help you manage and control various aspects of your robot, such as navigation, object
tracking, and more. Let me know how I can assist!


```

## Tooling
https://platform.openai.com/docs/guides/function-calling?api-mode=chat

## Chatting with qwen 2.5

```shell
>>> chat("Can you drive forward?")
Content:
Tool calls: [ToolCall(function=Function(name='forward', arguments={}))]
>>> chat("stop")
Content: I'm sorry, but the tool 'stop_tracking_faces' is not available. It's possible that you're trying to stop tracking faces, which would require a different function call or interaction with your robot system. Could you please clarify what action you want to take? If you have any specific instructions or commands for stopping the robot, I'd be happy to assist further.
Tool calls: None
>>> chat("Can you track faces")
Content: Sure, I can start tracking faces. Please tell me the desired speed for the tracking.
Tool calls: None
>>>
```

It's getting there. Qwen is notably faster for this than llama.

At 23:05, august 20th;
```
danny@learnrob3:~/robot $ ollama list
NAME                      ID              SIZE      MODIFIED
robot-intent-1b:latest    476a337ecee0    397 MB    14 minutes ago
qwen2.5:0.5b              a8b0c5157701    397 MB    16 minutes ago
qwen3:0.6b                7df6b6e09427    522 MB    21 minutes ago
gemma3:270m               e7d36fb2c3b3    291 MB    24 minutes ago
llama3.2:1b               baf6a787fdff    1.3 GB    About an hour ago
```
Maybe I should delete the less useful ones...

