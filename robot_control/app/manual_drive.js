import { StatusBar } from 'expo-status-bar';
import { Text } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { ReactNativeJoystick } from "@korsolutions/react-native-joystick";
import { Link } from 'expo-router';
import { styles } from '../styles';

export default function Page() {
    return (
      <GestureHandlerRootView style={styles.container}>
        <Text style={styles.title}>Manual drive</Text>
        <Link href="/">Back</Link>
        <ReactNativeJoystick color="#06b6d4" radius={75} onMove={onJoystickMove} onStop={onJoystickStop }/>
        <StatusBar style="auto" />
      </GestureHandlerRootView>
    );
  }

function onJoystickMove(data) {
  console.log('Joystick move');
  console.log(data);
}

function onJoystickStop() {
  console.log('Joystick stop');
}
