import { StatusBar } from 'expo-status-bar';
import { Text, View } from 'react-native';
import { styles } from '../styles';

export default function Page() {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Manual drive</Text>
        <StatusBar style="auto" />
      </View>
    );
  }
