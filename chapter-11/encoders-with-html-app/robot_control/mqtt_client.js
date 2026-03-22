import { env } from "./.env.js";
import mqtt from "./libs/mqtt.js";

export function connect(on_connect = () => console.log("Connected to MQTT broker"))
{
    let client = mqtt.connect(`ws://${env.PI_HOSTNAME}:9001`, {
        username: env.MQTT_USERNAME,
        password: env.MQTT_PASSWORD,
    });

    client.on("connect", on_connect);

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
