import { Text, View } from 'react-native';
import { Link } from 'expo-router';
import { styles } from '../styles';

export function TitleBar({title}) {
    return (
        <View style={styles.titleBar}>
            <Link style={styles.backlink} href="/">Back</Link>
            <Text style={styles.title}>{title}</Text>
        </View>
    );
}
