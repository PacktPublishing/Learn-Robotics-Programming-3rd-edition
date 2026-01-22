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
                mqtt_client.publish('config/set',
                    JSON.stringify([key, value]));
            };
            container.appendChild(input);
            keys[key] = input;
        },
        start: () => {
            mqtt_client.publish('config/get',
                JSON.stringify(Object.keys(keys)));
        }
    }
}

export function await_config(
    mqttClient,
    configKeys,
    controlDiv,
    onLoaded
) {
    controlDiv.innerHTML = '<p>Loading configuration...</p>';

    mqttClient.subscribe('config/updated');

    const messageHandler = (topic, message) => {
        if (topic !== 'config/updated') return;

        const config = JSON.parse(message.toString());
        const missing = configKeys.filter(
            key => config[key] === undefined
        );

        if (missing.length === 0) {
            mqttClient.unsubscribe('config/updated');
            mqttClient.off('message', messageHandler);
            onLoaded();
        } else {
            showMissingConfig(controlDiv, missing);
        }
    };

    mqttClient.on('message', messageHandler);
    mqttClient.publish('config/get', JSON.stringify(configKeys));
}

function showMissingConfig(controlDiv, missingKeys) {
    const exampleKey = missingKeys[0];
    const keyList = missingKeys.map(k => `<li>${k}</li>`).join('');

    controlDiv.innerHTML = `
        <div style="
            background-color: #660000;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        ">
            <h3 style="margin-top: 0;">
                ⚠️ Configuration Required
            </h3>
            <p>The following configuration values are missing:</p>
            <ul>${keyList}</ul>
            <p><strong>Set them using:</strong></p>
            <code style="
                display: block;
                background: #000;
                padding: 10px;
                margin: 10px 0;
            ">
                mosquitto_pub -h localhost -t config/set
                -m '["${exampleKey}", value]'
            </code>
            <p style="font-size: 0.9em; color: #aaa;">
                Replace "value" with your measurement.
            </p>
        </div>
    `;
}
