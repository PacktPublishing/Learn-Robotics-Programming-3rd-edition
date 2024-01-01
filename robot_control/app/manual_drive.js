import Paho from "paho-mqtt";
import { StatusBar } from 'expo-status-bar';
import { Text } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { KorolJoystick } from "korol-joystick";
import { Link } from 'expo-router';
import { styles } from '../styles';

export default function Page() {
    return (
      <GestureHandlerRootView style={styles.container}>
        <Text style={styles.title}>Manual drive</Text>
        <Link href="/">Back</Link>
        <KorolJoystick color="#06b6d4" radius={75} onMove={onJoystickMove} onStop={onJoystickStop }/>
        <StatusBar style="auto" />
      </GestureHandlerRootView>
    );
  }

const env = {
  PI_HOSTNAME: "learnrob3.local",
  MQTT_USERNAME: "robot",
  MQTT_PASSWORD: "robot",
};

const mqttClient = new Paho.Client(
  env.PI_HOSTNAME,
  9001,
  "robot_control"
);

mqttClient.onConnectionLost = (err) => {
  console.log("Connected to MQTT broker lost");
  console.log(err);
};

console.log("Attempting to connect to " + env.PI_HOSTNAME);
mqttClient.connect({
  userName: env.MQTT_USERNAME,
  password: env.MQTT_PASSWORD,
  onSuccess: () => {
    console.log("Connected");
  },
  onFailure: (err) => {
    console.log('Connection failed');
    console.log(err)
  },
});

function onJoystickMove(data) {
  let speed = Math.sin(data.angle.radian) * Math.min(1, data.force);
  let curve = Math.cos(data.angle.radian) * Math.min(1, data.force);
  console.log("speed: "+speed+"\t curve: "+curve);
  mqttClient.publish("motors/left", JSON.stringify(speed + curve));
  mqttClient.publish("motors/right", JSON.stringify(speed - curve));
}

function onJoystickStop() {
  console.log('Joystick stop');
  mqttClient.publish("motors/stop", "{}");
}
