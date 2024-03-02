import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { Link, useNavigation } from 'expo-router';
import { styles } from '../styles';
import { env } from '../lib/connection'
import { WebView } from 'react-native-webview';

export default function Page({ navigation }) {
    const [distanceLogs, setDistanceLogs] = useState({});
    global.mqttClient.subscribe("log");
    global.mqttClient.onMessageArrived = (message) => {
        const logData = JSON.parse(message.payloadString);
        setDistanceLogs(logData);
    }

    useNavigation().addListener('beforeRemove', (e) => {
        global.mqttClient.unsubscribe("log");
    });

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Bang Bang Avoiding Behavior</Text>
            <Link href="/">Back</Link>
            <Button title="Start" onPress={() => global.mqttClient.publish("launcher/start", "bang_bang_obstacle_avoiding")} />
            <Button title="Stop" onPress={() => global.mqttClient.publish("launcher/stop", "bang_bang_obstacle_avoiding")} />
            <Text>Left Distance: {distanceLogs.left_distance}, Motor: {distanceLogs.left_motor_speed}</Text>
            <Text>Right Distance: {distanceLogs.right_distance}, Motor: {distanceLogs.right_motor_speed}</Text>
            <WebView style={styles.container}
                source={{uri: "http://" + env.PI_HOSTNAME + ":5000/"}}
                />
            <StatusBar style="auto" />
        </View>
    );
}
