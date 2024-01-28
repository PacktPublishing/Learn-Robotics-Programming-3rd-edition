import { StatusBar } from 'expo-status-bar';
import { View , Text } from 'react-native';
import { Link } from 'expo-router';
import { styles } from '../styles';
import { connect } from '../lib/connection'

export default function Page() {
    const mqttClient = connect({
        onConnectionMade: (client) => {
            client.publish("launcher/start", "behavior_path.service");
        },
    });

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Drive path</Text>
            <Link href="/">Back</Link>
            <StatusBar style="auto" />
        </View>
    );
}
