import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { styles, BackButton } from '../lib/styles';
import { env } from '../lib/connection'
import { WebView } from 'react-native-webview';


export default function Page() {
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Distance Sensor</Text>
            <BackButton/>
            <Button title="Start" onPress={() => global.mqttClient.publish("sensors/distance/control", "start_ranging")} />
            <Button title="Stop" onPress={() => global.mqttClient.publish("sensors/distance/control", "stop_ranging")} />
            <WebView style={styles.container}
                source={{uri: "http://" + env.PI_HOSTNAME + ":5000/"}}
                />
            <StatusBar style="auto" />
        </View>
    );
}
