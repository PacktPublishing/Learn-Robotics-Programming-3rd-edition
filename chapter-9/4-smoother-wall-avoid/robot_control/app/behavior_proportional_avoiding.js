import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { Link, useNavigation } from 'expo-router';
import { styles } from '../styles';
import { env } from '../lib/connection'
import { WebView } from 'react-native-webview';

export default function Page({ navigation }) {
    const [distanceLogs, setDistanceLogs] = useState({});
    global.mqttClient.subscribe("log/obstacle_avoiding/proportional");
    global.mqttClient.onMessageArrived = (message) => {
        const logData = JSON.parse(message.payloadString);
        setDistanceLogs(logData);
    }

    useNavigation().addListener('beforeRemove', (e) => {
        global.mqttClient.unsubscribe("log/obstacle_avoiding/proportional");
    });

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Proportional Wall Avoiding Behavior</Text>
            <Link href="/">Back</Link>
            <Button title="Start" onPress={() => global.mqttClient.publish("launcher/start", "behavior_proportional_avoiding")} />
            <Button title="Stop" onPress={() => global.mqttClient.publish("launcher/stop", "behavior_proportional_avoiding")} />
            <View>
                <Text>Left Distance: {distanceLogs[0]}, Motor: {distanceLogs[2]}</Text>
                <Text>Right Distance: {distanceLogs[1]}, Motor: {distanceLogs[3]}</Text>
            </View>
            <WebView style={styles.container}
                source={{ html: '<img src="http://' + env.MQTT_HOSTNAME + ':5000/display"></img>'}}
                cacheEnabled={false}
                cacheMode='LOAD_NO_CACHE'
                />
            <StatusBar style="auto" />
        </View>
    );
}
