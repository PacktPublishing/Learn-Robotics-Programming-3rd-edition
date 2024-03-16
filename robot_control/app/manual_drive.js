import { StatusBar } from 'expo-status-bar';
import { Text } from 'react-native';
import { Link } from 'expo-router';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { ReactNativeJoystick } from "@korsolutions/react-native-joystick";
import { styles, BackButton } from '../lib/styles';


export default function Page() {
  return (
    <GestureHandlerRootView style={styles.container}>
      <Text style={styles.title}>Manual drive</Text>
      <BackButton/>
      <ReactNativeJoystick color="#06b6d4" radius={75} onMove={onJoystickMove} onStop={onJoystickStop }/>
      <ReactNativeJoystick color="#06b6d4" radius={75} onMove={onServoJoystickMove} onStop={onServoJoystickStop }/>
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

function onServoJoystickMove(data) {
  let pan = Math.cos(data.angle.radian) * Math.min(1, data.force) * 70;
  let tilt = -Math.sin(data.angle.radian) * Math.min(1, data.force) * 70;
  // console.log("angle: "+angle+"\t force: "+force);
  global.mqttClient.publish(
    "motors/servos", 
    JSON.stringify({pan: pan, tilt: tilt})
  );
}

function onServoJoystickStop() {
  console.log('Servo joystick stop');
  global.mqttClient.publish(
    "motors/servos", 
    JSON.stringify({ pan: 0, tilt: 0 })
  );
  setTimeout(() => {
    global.mqttClient.publish(
      "motors/servos", 
      JSON.stringify({ pan: "disable", tilt: "disable" })
    );
  }, 1500);
}
