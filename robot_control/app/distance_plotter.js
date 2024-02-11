import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { Link } from 'expo-router';
import { styles } from '../styles';
import { env } from '../lib/connection'
import { WebView } from 'react-native-webview';


export default function Page() {
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Distance Sensor</Text>
            <Link href="/">Back</Link>
            <Button title="Start" onPress={() => global.mqttClient.publish("sensors/distance/control/start_ranging", "{}")} />
            <Button title="Stop" onPress={() => global.mqttClient.publish("sensors/distance/control/stop_ranging", "{}")} />
            <WebView style={styles.container}
                source={{ html: '<img src="http://' + env.PI_HOSTNAME + ':5000/display"></img>'}}
                cacheEnabled={false}
                cacheMode='LOAD_NO_CACHE'
                />
            <StatusBar style="auto" />
        </View>
    );
}
