import Paho from "paho-mqtt";

export function connect(options) {
    const env = {
        PI_HOSTNAME: "learnrob3.local",
        MQTT_USERNAME: "robot",
        MQTT_PASSWORD: "robot",
    };

    const mqttClient = new Paho.Client(
        env.PI_HOSTNAME,
        9001,
        "robot_control"
    );

    mqttClient.onConnectionLost = (err) => {
        console.log("Connected to MQTT broker lost");
        console.log(err);
    };

    console.log("Attempting to connect to " + env.PI_HOSTNAME);
    mqttClient.connect({
        userName: env.MQTT_USERNAME,
        password: env.MQTT_PASSWORD,
        onSuccess: () => {
            console.log("Connected");
            if (options.onConnectionMade !== undefined) {
                options.onConnectionMade(mqttClient);
            }
        },
        onFailure: (err) => {
            console.log('Connection failed');
            console.log(err)
        },
    });

    return mqttClient;
}
