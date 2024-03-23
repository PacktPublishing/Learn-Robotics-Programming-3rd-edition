import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { WebView } from 'react-native-webview';

import { styles, BackButton } from '../lib/styles';
import { env } from '../lib/connection'
import { BehaviorSetting } from '../lib/behavior_setting';

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
            <Text style={styles.title}>Proportional Obstacle Avoiding Behavior</Text>
            <BackButton/>
            <Button title="Start" onPress={() => global.mqttClient.publish("launcher/start", "proportional_obstacle_avoiding")} />
            <Button title="Stop" onPress={() => global.mqttClient.publish("launcher/stop", "proportional_obstacle_avoiding")} />
            <DistanceLogs/>
            <WebView style={styles.container}
                source={{uri: "http://" + env.PI_HOSTNAME + ":5000/"}}
                />
            <BehaviorSetting title="Speed" name="speed" minimum={0} maximum={1} step={0.1} start_value={0.6} />
            <BehaviorSetting title="Curve Proportion" name="curve_proportion" minimum={1} maximum={200} step={1} start_value={140} />
            <StatusBar style="auto" />
        </View>
    );
}
