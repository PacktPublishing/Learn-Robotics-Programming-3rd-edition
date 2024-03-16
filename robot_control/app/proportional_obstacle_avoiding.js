import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { Link, useNavigation } from 'expo-router';
import { styles, BackButton } from '../lib/styles';
import { env } from '../lib/connection'
import { WebView } from 'react-native-webview';
import Slider from '@react-native-community/slider';

// npx expo install @react-native-community/slider

function BehaviorWidget({title, name, minimum, maximum, step, start_value}) {
    const [value, setValue] = useState(start_value);
    const change_value = (value) => {
        settings = {}
        settings[name] = value;
        setValue(value);
        global.mqttClient.publish("behavior/settings", 
            JSON.stringify(settings)
        );
    }
    return (
        <View>
            <Text>{title}</Text>
            <Text style={{textAlign: "center"}}>{value}</Text>
            <Slider
                style={{width: "80%", marginLeft: "10%"}}
                minimumValue={minimum}
                maximumValue={maximum}
                value = {value}
                step={step}
                onValueChange={change_value}
            />
        </View>
    );
}


export default function Page({ navigation }) {
    const [distanceLogs, setDistanceLogs] = useState({});
    global.mqttClient.subscribe("log/obstacle_avoider");
    global.mqttClient.onMessageArrived = (message) => {
        const logData = JSON.parse(message.payloadString);
        setDistanceLogs(logData);
    }

    useNavigation().addListener('beforeRemove', (e) => {
        global.mqttClient.unsubscribe("log/obstacle_avoider");
    });

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Proportional Obstacle Avoiding Behavior</Text>
            <BackButton/>
            <Button title="Start" onPress={() => global.mqttClient.publish("launcher/start", "proportional_obstacle_avoiding")} />
            <Button title="Stop" onPress={() => global.mqttClient.publish("launcher/stop", "proportional_obstacle_avoiding")} />
            <Text>Left Distance: {distanceLogs.left_distance}, Motor: {distanceLogs.left_motor_speed}</Text>
            <Text>Right Distance: {distanceLogs.right_distance}, Motor: {distanceLogs.right_motor_speed}</Text>
            <WebView style={styles.container}
                source={{uri: "http://" + env.PI_HOSTNAME + ":5000/"}}
                />
            <BehaviorWidget title="Speed" name="speed" minimum={0} maximum={1} step={0.1} start_value={0.6} />
            <BehaviorWidget title="Curve Proportion" name="curve_proportion" minimum={1} maximum={200} step={1} start_value={140} />
            <StatusBar style="auto" />
        </View>
    );
}
