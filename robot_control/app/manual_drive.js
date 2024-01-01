import { StatusBar } from 'expo-status-bar';
import { Text, View } from 'react-native';
import { Link } from 'expo-router';
import { styles } from '../styles';

export default function Page() {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Manual drive</Text>
        <Link href="/">Back</Link>
        <StatusBar style="auto" />
      </View>
    );
  }
