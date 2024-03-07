import { StatusBar } from 'expo-status-bar';
import { Text } from 'react-native';
import { Link } from 'expo-router';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { ReactNativeJoystick } from "@korsolutions/react-native-joystick";
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
  let speed = Math.sin(data.angle.radian) * Math.min(1, data.force);
  let curve = Math.cos(data.angle.radian) * Math.min(1, data.force);
  // console.log("speed: "+speed+"\t curve: "+curve);
  global.mqttClient.publish(
    "motors/wheels", 
    JSON.stringify([speed + curve, speed - curve])
  );
}

function onJoystickStop() {
  console.log('Joystick stop');
  global.mqttClient.publish("motors/stop", "{}");
}
