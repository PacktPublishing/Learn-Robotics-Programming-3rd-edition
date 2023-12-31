import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View } from 'react-native';

export default function Page() {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Manual drive</Text>
        <StatusBar style="auto" />
      </View>
    );
  }

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
        alignItems: 'stretch',
        justifyContent: 'center',
        marginTop: StatusBar.currentHeight || 60,
    },
    title: {
        alignSelf: 'center',
        marginBottom: 20,
    }
}
);