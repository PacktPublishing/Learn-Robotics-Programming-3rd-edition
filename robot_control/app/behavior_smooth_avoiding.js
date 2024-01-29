import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { Link } from 'expo-router';
import { styles } from '../styles';
import { useNavigation } from 'expo-router';

export default function Page({ navigation }) {
    const [distanceLeft, setDistanceLeft] = useState(0);
    const [distanceRight, setDistanceRight] = useState(0);
    const [motorLeft, setMotorLeft] = useState(0);
    const [motorRight, setMotorRight] = useState(0);
    global.mqttClient.subscribe("log/obstacle_avoiding/smooth");
    global.mqttClient.onMessageArrived = (message) => {
        const logData = JSON.parse(message.payloadString);
        setDistanceLeft(logData[0]);
        setDistanceRight(logData[1]);
        setMotorLeft(logData[2]);
        setMotorRight(logData[3]);
    }

    useNavigation().addListener('beforeRemove', (e) => {
        global.mqttClient.unsubscribe("log/obstacle_avoiding/smooth");
    });

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Smooth Wall Avoiding Behavior</Text>
            <Link href="/">Back</Link>
            <Button title="Start" onPress={() => global.mqttClient.publish("launcher/start", "behavior_smooth_obstacle_avoiding")} />
            <Button title="Stop" onPress={() => global.mqttClient.publish("launcher/stop", "behavior_smooth_obstacle_avoiding")} />
            <View>
                <Text>Left Distance: {distanceLeft}, Motor: {motorLeft}</Text>
                <Text>Right Distance: {distanceRight}, Motor: {motorRight}</Text>
            </View>
            <StatusBar style="auto" />
        </View>
    );
}
