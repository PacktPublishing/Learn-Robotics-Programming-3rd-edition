import { StatusBar } from 'expo-status-bar';
import { useState } from 'react';
import { View , Text, Button } from 'react-native';
import { Link } from 'expo-router';
import { styles } from '../styles';
import { connect } from '../lib/connection'
import { StyleSheet } from 'react-native';


export const gridStyles = StyleSheet.create({
    grid: {
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
    },
    gridRow: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    gridCell: {
        width: 32,
        height: 32,
    }
});

function SensorGrid({grid}) {
    const gridRows = grid.map((row, i) => (
        <View key={i} style={gridStyles.gridRow}>
            {row.map((value, j) => (
                <View key={j} style={[{backgroundColor: `rgb(${value}, ${value}, ${value})`}, gridStyles.gridCell]}></View>
            ))}
        </View>
    ));
    return (
        <View style={gridStyles.grid}>
            {gridRows}
        </View>
    )
}

mqttClient = connect({
    onConnectionMade: (client) => {
        client.subscribe("sensors/distance_mm");
    }
});

export default function Page() {
    const [grid, setGrid] = useState(new Array(8).fill(new Array(8).fill(0)));
    const onMessageArrived = (message) => {
        try {
            if (message.destinationName === "sensors/distance_mm") {
                const data = JSON.parse(message.payloadString);
                const mapped_data = data.map(
                    (row) => row.map((value) => 255 - Math.min(Math.floor(value * 0.7), 255))
                );
                console.log(mapped_data);
                setGrid(
                    mapped_data
                )
            }
        } catch (e) {
            console.log(e.stack);
        }
    };
    mqttClient.onMessageArrived = onMessageArrived;

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Distance Sensor</Text>
            <Link href="/">Back</Link>
            <Button title="Start" onPress={() => mqttClient.publish("sensors/distance/control/start_ranging", "{}")} />
            <Button title="Stop" onPress={() => mqttClient.publish("sensors/distance/control/stop_ranging", "{}")} />
            <SensorGrid grid={grid}/>
            <StatusBar style="auto" />
        </View>
    );
}
