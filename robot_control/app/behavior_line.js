import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View , Text } from 'react-native';
import { Link, useNavigation } from 'expo-router';
import { styles, BackButton } from '../lib/styles';

export default function Page({ navigation }) {
    const [encoderData, setEncoderData] = useState({left_radians: 0.0, right_radians: 0.0});
    global.mqttClient.subscribe("sensors/encoders/data");
    global.mqttClient.onMessageArrived = (message) => {
        const logData = JSON.parse(message.payloadString);
        setEncoderData(logData);
    }

    useNavigation().addListener('beforeRemove', (e) => {
        global.mqttClient.unsubscribe("sensors/encoders/data");
    });


    global.mqttClient.publish("launcher/start", "behavior_line.service");
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Drive line</Text>
            <BackButton/>
            <StatusBar style="auto" />
            <Text>Left Encoder: {encoderData.left_radians}</Text>
            <Text>Right Encoder: {encoderData.right_radians}</Text>
        </View>
    );
}
