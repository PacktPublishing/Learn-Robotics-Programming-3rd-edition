import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { useNavigation } from 'expo-router';
import { BehaviorSetting } from '../lib/behavior_setting';

import { styles, BackButton } from '../lib/styles';
import { env, publish_json } from '../lib/connection'
import { WebView } from 'react-native-webview';

import { useMQTTData } from '../lib/mqtt_hook';


export const EncoderDisplay = () => {
    const encoderData = useMQTTData("sensors/encoders/data", { left_radians: 0, right_radians: 0 });

    return (
        <>
            <Text>Left Encoder: {encoderData.left_radians}</Text>
            <Text>Right Encoder: {encoderData.right_radians}</Text>
        </>
    );
};

export default function Page() {
    useNavigation().addListener('beforeRemove', (e) => {
        global.mqttClient.publish("launcher/stop", "line_with_correction");
    });

    useNavigation().addListener('focus', () => {
        global.mqttClient.publish("launcher/start", "line_with_correction");
    });
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Line with correction</Text>
            <BackButton/>
            <Button title="Start" onPress={() => publish_json("behavior/settings", {"running": true})} />
            <Button title="Stop" onPress={() => publish_json("behavior/settings", {"running": false})} />
            <StatusBar style="auto" />
            <EncoderDisplay/>
            <WebView style={styles.container}
                source={{uri: "http://" + env.PI_HOSTNAME + ":5001/"}}
                />
            <BehaviorSetting title="Speed" name="speed" minimum={0} maximum={1} step={0.1} start_value={0.6} />
            <BehaviorSetting title="Veer Proportion" name="veer_proportion" minimum={0} maximum={10} step={1} start_value={0.2} />
            <BehaviorSetting title="Veer Integral" name="veer_integral" minimum={0} maximum={2} step={0.1} start_value={0.3} />
        </View>
    );
}

