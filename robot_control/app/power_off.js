import { StatusBar } from 'expo-status-bar';
import { View , Text } from 'react-native';
import { Link } from 'expo-router';
import { connect } from '../lib/connection'
import { styles } from '../styles';

export default function Page() {
    mqttClient = connect({
        onConnectionMade: (client) => {
            client.publish("launcher/poweroff", "");
        },
    });

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Power off</Text>
            <Link href="/">Back</Link>
            <StatusBar style="auto" />
        </View>
    );
}
