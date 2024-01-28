import { StatusBar } from 'expo-status-bar';
import { View , Text, Button } from 'react-native';
import { Link } from 'expo-router';
import { styles } from '../styles';
import { connect, env } from '../lib/connection'
import { WebView } from 'react-native-webview';


export default function Page() {
    const mqttClient = connect();
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Distance Sensor</Text>
            <Link href="/">Back</Link>
            <Button title="Start" onPress={() => mqttClient.publish("sensors/distance/control/start_ranging", "{}")} />
            <Button title="Stop" onPress={() => mqttClient.publish("sensors/distance/control/stop_ranging", "{}")} />
            <Button title="Resolution:64" onPress={() => mqttClient.publish("sensors/distance/control/set_resolution", '64')} />
            <Button title="Resolution:16" onPress={() => mqttClient.publish("sensors/distance/control/set_resolution", '16')} />
            <WebView style={styles.container}
                source={{ html: '<img src="http://' + env.PI_HOSTNAME + ':5000/display"></img>'}}
                cacheEnabled={false}
                cacheMode='LOAD_NO_CACHE'
                />
            <StatusBar style="auto" />
        </View>
    );
}
