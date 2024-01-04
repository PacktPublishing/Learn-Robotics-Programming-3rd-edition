import { StatusBar } from 'expo-status-bar';
import { View } from 'react-native';
import { connect } from '../lib/connection'
import { styles } from '../styles';
import { TitleBar } from '../components/title_bar';

export default function Page() {
    mqttClient = connect({
        onConnectionMade: (client) => {
            client.publish("launcher/start", "behavior_path.service");
        },
    });

    return (
        <View style={styles.container}>
            <TitleBar title="Drive path" />
            <StatusBar style="auto" />
        </View>        
    );
}
