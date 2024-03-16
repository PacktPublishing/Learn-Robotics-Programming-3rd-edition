import { StatusBar } from 'expo-status-bar';
import { View , Text } from 'react-native';
import { Link } from 'expo-router';
import { styles, BackButton } from '../lib/styles';

export default function Page() {
    global.mqttClient.publish("launcher/start", "behavior_path.service");
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Drive path</Text>
            <BackButton/>
            <StatusBar style="auto" />
        </View>
    );
}
