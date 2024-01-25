import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { Link } from 'expo-router';
import { styles } from '../styles';
import { connect } from '../lib/connection'

mqttClient = connect();

export default function Page() {
    const [distanceLeft, setDistanceLeft] = useState(0);
    const [distanceRight, setDistanceRight] = useState(0);
    const [motorLeft, setMotorLeft] = useState(0);
    const [motorRight, setMotorRight] = useState(0);

    mqttClient.subscribe("log/obstacle_avoiding/distances");
    mqttClient.onMessageArrived = (message) => {
        // console.log(message.payloadString);
        const logData = JSON.parse(message.payloadString);
        setDistanceLeft(logData[0]);
        setDistanceRight(logData[1]);
        setMotorLeft(logData[2]);
        setMotorRight(logData[3]);
    }

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Simple Wall Avoiding Behavior</Text>
            <Link href="/">Back</Link>
            <Button title="Start" onPress={() => mqttClient.publish("launcher/start", "behavior_simple_obstacle_avoiding")} />
            <Button title="Stop" onPress={() => mqttClient.publish("launcher/stop", "behavior_simple_obstacle_avoiding")} />
            <Text>Left Distance: {distanceLeft}, Motor: {motorLeft}</Text>
            <Text>Right Distance: {distanceRight}, Motor: {motorRight}</Text>
            <StatusBar style="auto" />
        </View>
    );
}
