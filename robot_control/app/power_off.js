import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { connect } from '../lib/connection'
import { styles } from '../styles';
import { TitleBar } from '../components/title_bar';

export default function Page() {
    mqttClient = connect({
        onConnectionMade: (client) => {
            client.publish("launcher/poweroff", "");
        },
    });

    return (
        <View style={styles.container}>
            <TitleBar title="Power off" />
            <StatusBar style="auto" />
        </View>
    );
}
