import Paho from "paho-mqtt";

export const env = {
    PI_HOSTNAME: "learnrob3.local",
    MQTT_USERNAME: "robot",
    MQTT_PASSWORD: "robot",
};

export function connect(options={}) {
    const mqttClient = new Paho.Client(
        env.PI_HOSTNAME,
        9001,
        "robot_control"
    );

    mqttClient.onConnectionLost = (err) => {
        console.log("Connected to MQTT broker lost");
        console.log(err);
    };

    mqttClient.onConnected = (reconnect, uri) => {
        console.log("Connected to " + uri + " via MQTT broker");
        if (options.onConnectionMade !== undefined) {
            options.onConnectionMade(mqttClient);
        }
    };

    console.log("Attempting to connect to " + env.PI_HOSTNAME);
    mqttClient.connect({
        userName: env.MQTT_USERNAME,
        password: env.MQTT_PASSWORD,
        onFailure: (err) => {
            console.log('Connection failed');
            console.log(err)
        },
    });

    return mqttClient;
}
