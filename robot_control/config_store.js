export function config_store_client(mqtt_client) {
    mqtt_client.subscribe('config/updated');
    const update_handlers = {};
    // Does this clobber out the previous handler?
    mqtt_client.on('message', (topic, message) => {
        if (topic === 'config/updated') {
            console.log("Received config update");
            const data = JSON.parse(message.toString());
            for (const key in data) {
                if (update_handlers[key]) {
                    update_handlers[key](data[key]);
                }
            }
        }
    });

    return {
        set: (key, value) => {
            mqtt_client.publish('config/set', JSON.stringify([key, value]));
        },
        get: (key) => {
            mqtt_client.publish('config/get', JSON.stringify([key]));
        },
        on: (key, callback) => {
            update_handlers[key] = callback;
        }
    }
}


export function create_numeric_input(config_client, key, label, container_id, starting_value) {
    const container = document.getElementById(container_id);
    const label_element = document.createElement('label');
    label_element.textContent = label;
    container.appendChild(label_element);
    const input = document.createElement('input');
    input.type = 'text';
    input.value = starting_value.toString();
    input.onblur = () => {
        config_client.set(key, parseFloat(input.value));
    };
    config_client.on(key, (value) => {
        input.value = value.toString();
    });
    config_client.get(key);
    container.appendChild(input);
}
