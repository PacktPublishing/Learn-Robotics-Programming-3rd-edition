import mqtt from "./libs/mqtt.js";

// Load environment configuration from .env.json
const response = await fetch('/.env.json?t=' + new Date().getTime());
let env = await response.json();

export function connect() {
    let client = mqtt.connect(`ws://${env.PI_HOSTNAME}:9001`, {
        username: env.MQTT_USERNAME,
        password: env.MQTT_PASSWORD,
    });

    client.on("connect", () => {
        console.log("Connected to MQTT broker");
    });

    client.on("error", (err) => {
        console.log("Error connecting to MQTT broker");
        console.log(err);
    });
    return client;
}

export function publish_when_clicked(client, element_id,topic, data) {
    document.getElementById(element_id).addEventListener("click", () => {
        client.publish(topic, data);
    });
}
