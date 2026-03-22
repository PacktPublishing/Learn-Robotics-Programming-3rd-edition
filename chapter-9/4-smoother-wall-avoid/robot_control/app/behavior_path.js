import { StatusBar } from 'expo-status-bar';
import { View , Text } from 'react-native';
import { Link } from 'expo-router';
import { styles } from '../styles';

export default function Page() {
    global.mqttClient.publish("launcher/start", "behavior_path.service");
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Drive path</Text>
            <Link href="/">Back</Link>
            <StatusBar style="auto" />
        </View>
    );
}
