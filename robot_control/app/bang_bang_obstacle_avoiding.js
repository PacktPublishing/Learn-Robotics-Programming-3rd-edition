import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { useNavigation } from 'expo-router';
import { styles, BackButton } from '../lib/styles';
import { env } from '../lib/connection'
import { WebView } from 'react-native-webview';

export default function Page() {
    const [distanceLogs, setDistanceLogs] = useState({});
    useNavigation().addListener('beforeRemove', (e) => {
        global.mqttClient.unsubscribe("log/obstacle_avoider");
    });

    useNavigation().addListener('focus', () => {
        global.mqttClient.subscribe("log/obstacle_avoider");
        global.mqttClient.onMessageArrived = (message) => {
            const logData = JSON.parse(message.payloadString);
            setDistanceLogs(logData);
        }    
    });
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Bang Bang Obstacle Avoiding</Text>
            <BackButton/>
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
