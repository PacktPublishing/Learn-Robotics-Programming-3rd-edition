import Paho from "paho-mqtt";

export const env = {
    MQTT_HOSTNAME: "learnrob3.local",
    MQTT_USERNAME: "robot",
    MQTT_PASSWORD: "robot",
};

export function connect() {
    const mqttClient = new Paho.Client(
        env.MQTT_HOSTNAME,
        9001,
        "robot_control"
    );

    mqttClient.onConnectionLost = (err) => {
        console.log("Connected to MQTT broker lost");
        console.log(err);
    };

    mqttClient.onConnected = (reconnect, uri) => {
        console.log("Connected to " + uri + " via MQTT broker");
    };

    console.log("Attempting to connect to " + env.MQTT_HOSTNAME);
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
