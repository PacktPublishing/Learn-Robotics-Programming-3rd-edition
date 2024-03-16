import { StatusBar } from 'expo-status-bar';
import { View , Text } from 'react-native';
import { useNavigation } from 'expo-router';
import { styles, BackButton } from '../lib/styles';

export default function Page() {
    useNavigation().addListener('focus', () => {
        global.mqttClient.publish("launcher/poweroff", "");
    });
    return (
        <View style={styles.container}>
            <Text style={styles.title}>Power off</Text>
            <BackButton/>
            <StatusBar style="auto" />
        </View>
    );
}
