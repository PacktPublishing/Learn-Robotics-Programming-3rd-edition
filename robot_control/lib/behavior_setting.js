import { useState } from 'react';
import { View , Text } from 'react-native';
import Slider from '@react-native-community/slider';

import { publish_json } from './connection';

// npx expo install @react-native-community/slider

export function BehaviorSetting({title, name, minimum, maximum, step, start_value}) {
    const [value, setValue] = useState(start_value);
    const change_value = (value) => {
        settings = {}
        settings[name] = value;
        setValue(value);
        publish_json("behavior/settings", settings);
    }
    return (
        <View>
            <Text>{title}</Text>
            <Text style={{textAlign: "center"}}>{value}</Text>
            <Slider
                style={{width: "80%", marginLeft: "10%"}}
                minimumValue={minimum}
                maximumValue={maximum}
                value = {value}
                step={step}
                onValueChange={change_value}
            />
        </View>
    );
}
