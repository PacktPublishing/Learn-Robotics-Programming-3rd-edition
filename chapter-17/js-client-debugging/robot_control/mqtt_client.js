import { env } from "./.env.js";
import mqtt from "./libs/mqtt.js";

console.log("Mqtt library imported")
export function connect() {
    console.log("Connecting to MQTT broker...")
    try {
        let client = mqtt.connect(`ws://${env.PI_HOSTNAME}:9001`, {
            username: env.MQTT_USERNAME,
            password: env.MQTT_PASSWORD,
        });
        console.log("MQTT client created.");

        client.on("connect", () => {
            console.log("Connected to MQTT broker");
        });

        client.on("error", (err) => {
            console.error("Error connecting to MQTT broker", err);
        });

        let original_publish = client.publish;
        client.publish = (topic, message, options, callback) => {
            console.log(`Publishing message to topic ${topic}:`, message);
            original_publish.call(client, topic, message, options, (err, packet) => {
                if (err) {
                    console.error("Error publishing message", err);
                    if (callback) callback(err, packet);
                    return;
                }
                console.log(`Message published to topic ${topic}:`, message);
                if (callback) callback(err, packet);
            });
        };

        let original_subscribe = client.subscribe;
        client.subscribe = (topic, options, callback) => {
            console.log(`Subscribing to topic ${topic}`);
            original_subscribe.call(client, topic, options, () => {});
        };

        return client;
    } catch (error) {
        console.error("Error connecting to MQTT broker", error);
    }
}

export function publish_when_clicked(client, element_id, topic, data) {
    console.log("Publishing when clicked");
    document.getElementById(element_id).addEventListener("click", () => {
        client.publish(topic, data);
    });
}
