export function config_store_client(mqtt_client) {
    const keys = {};

    mqtt_client.subscribe('config/updated');
    mqtt_client.on('message', (topic, message) => {
        if (topic === 'config/updated') {
            console.log("Received config update");
            const data = JSON.parse(message.toString());
            for (const key in data) {
                if (keys[key] !== undefined) {
                    keys[key].value = data[key].toString();
                }
            }
        }
    });

    return {
        add_input: (key, label, container_id, starting_value) => {
            const container = document.getElementById(container_id);
            const label_element = document.createElement('label');
            label_element.textContent = label;
            container.appendChild(label_element);
            const input = document.createElement('input');
            input.type = 'text';
            input.value = starting_value.toString();
            input.onblur = () => {
                const value = parseFloat(input.value);
                mqtt_client.publish('config/set', JSON.stringify([key, value]));
            };
            container.appendChild(input);
            keys[key] = input;
        },
        start: () => {
            mqtt_client.publish('config/get', JSON.stringify(Object.keys(keys)));
        }
    }
}
