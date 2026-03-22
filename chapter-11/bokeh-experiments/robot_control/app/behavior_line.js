import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View , Text } from 'react-native';
import { useNavigation } from 'expo-router';
import { styles, BackButton } from '../lib/styles';
import { env } from '../lib/connection'
import { WebView } from 'react-native-webview';

export default function Page() {
    const [encoderData, setEncoderData] = useState({left_radians: 0.0, right_radians: 0.0});

    useNavigation().addListener('beforeRemove', (e) => {
        global.mqttClient.unsubscribe("sensors/encoders/data");
    });

    useNavigation().addListener('focus', () => {
        global.mqttClient.publish("launcher/start", "behavior_line.service");
        global.mqttClient.subscribe("sensors/encoders/data");
        global.mqttClient.onMessageArrived = (message) => {
            const logData = JSON.parse(message.payloadString);
            setEncoderData(logData);
        }
    
    });
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Drive line</Text>
            <BackButton/>
            <StatusBar style="auto" />
            <Text>Left Encoder: {encoderData.left_radians}</Text>
            <Text>Right Encoder: {encoderData.right_radians}</Text>
            <WebView style={styles.container}
                source={{uri: "http://" + env.PI_HOSTNAME + ":5001/"}}
                />
        </View>
    );
}
