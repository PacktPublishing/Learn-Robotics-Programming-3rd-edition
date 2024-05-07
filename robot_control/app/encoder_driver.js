import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { useNavigation } from 'expo-router';
import { BehaviorSetting } from '../lib/behavior_setting';

import { styles, BackButton } from '../lib/styles';
import { env, publish_json } from '../lib/connection'
import { WebView } from 'react-native-webview';

import { useMQTTData } from '../lib/mqtt_hook';


export const LogDisplay = () => {
    const logData = useMQTTData("behaviour/log");
    return (
        <>
        {Object.entries(logData).map((item, key) => <Text>{key}: {item}</Text>)}
        </>
    );
};


const MqttButton = ({title, topic, message={}}) => {
    return (
        <Button title={title} onPress={() => publish_json(topic, message)} />
    );
}

const DelayedWebView = ({uri}) => {
    const graphView = <WebView style={styles.container} startInLoadingState={true} source={{html:"loading"}} 
        ref={(ref) => {
            setTimeout(() => {
                if (!ref) return;
                ref.source = {uri: uri};
                ref.reload();
            }, 1000);
        
        }}
    />;
    return graphView;
}

export default function Page() {
    useNavigation().addListener('beforeRemove', (e) => {
        global.mqttClient.publish("launcher/stop", "encoder_driver");
    });

    useNavigation().addListener('focus', () => {
        global.mqttClient.publish("launcher/start", "encoder_driver");
    });

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Encoder driver</Text>
            <BackButton/>
            <MqttButton title="Drive" topic="drive/start"/>
            <MqttButton title="Stop" topic="drive/stop"/>
            <StatusBar style="auto" />
            <LogDisplay/>
            <DelayedWebView uri={"http://" + env.PI_HOSTNAME + ":5002/"}/>
            <BehaviorSetting title="Speed" name="speed" minimum={0} maximum={10} step={0.5} start_value={6} />
            <BehaviorSetting title="Diff Proportion" name="diff_proportion" minimum={0} maximum={3} step={0.1} start_value={1} />
            <BehaviorSetting title="Diff Integral" name="diff_integral" minimum={0} maximum={2} step={0.1} start_value={0.3} />
            <BehaviorSetting title="Motor Proportion" name="motor_proportion" minimum={0} maximum={3} step={0.1} start_value={1} />
            <BehaviorSetting title="Motor Integral" name="motor_integral" minimum={0} maximum={2} step={0.1} start_value={0.3} />
        </View>
    );
}
