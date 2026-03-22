import { useState, useEffect } from 'react';

export const useMQTTData = (topic, initial_state={}) => {
    const [data, setData] = useState(initial_state);

    useEffect(() => {
        const handleMessage = (message) => {
            // Assuming a condition to check the topic
            if (message.topic === topic) {
                const newData = JSON.parse(message.payloadString);
                setData(newData);
            }
        };

        global.mqttClient.subscribe(topic);
        global.mqttClient.onMessageArrived = handleMessage;

        return () => {
            global.mqttClient.unsubscribe(topic);
        };
    }, [topic]);

    return data;
};
