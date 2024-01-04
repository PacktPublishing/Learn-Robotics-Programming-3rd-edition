import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { ReactNativeJoystick } from "@korsolutions/react-native-joystick";
import { connect } from '../lib/connection'
import { styles } from '../styles';
import { TitleBar } from '../components/title_bar';


export default function Page() {
  mqttClient = connect({});

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

    return (
      <GestureHandlerRootView style={styles.container}>
        <TitleBar title="Manual drive" />
        <ReactNativeJoystick color="#06b6d4" radius={75} onMove={onJoystickMove} onStop={onJoystickStop }/>
        <StatusBar style="auto" />
      </GestureHandlerRootView>
    );
  }
