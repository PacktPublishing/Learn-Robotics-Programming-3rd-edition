import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { WebView } from 'react-native-webview';

import { styles, BackButton } from '../lib/styles';
import { env } from '../lib/connection'
import { useMQTTData } from '../lib/mqtt_hook';

const DistanceLogs = () => {
    const distanceLogs = useMQTTData("log/obstacle_avoider", {});
    return (
        <>
            <Text>Left Distance: {distanceLogs.left_distance}, Motor: {distanceLogs.left_motor_speed}</Text>
            <Text>Right Distance: {distanceLogs.right_distance}, Motor: {distanceLogs.right_motor_speed}</Text>
        </>
    );
}

export default function Page() {
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Bang Bang Obstacle Avoiding</Text>
            <BackButton/>
            <Button title="Start" onPress={() => global.mqttClient.publish("launcher/start", "bang_bang_obstacle_avoiding")} />
            <Button title="Stop" onPress={() => global.mqttClient.publish("launcher/stop", "bang_bang_obstacle_avoiding")} />
            <DistanceLogs/>
            <WebView style={styles.container}
                source={{uri: "http://" + env.PI_HOSTNAME + ":5000/"}}
                />
            <StatusBar style="auto" />
        </View>
    );
}
