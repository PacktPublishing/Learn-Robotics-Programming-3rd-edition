import { StatusBar } from 'expo-status-bar';
import { Text, View, FlatList } from 'react-native';
import { styles } from '../styles';

const MENU_ITEMS = [
  { id: 'manual_drive', label: 'Manual drive' },
  { id: 'behavior_path', label: 'Drive path'}
];

function Item({label}) {
  return (
  <View style={styles.item}>
    <Text>{label}</Text>
  </View>
  );
}

export default function App() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Robot control</Text>
      <FlatList 
        data={MENU_ITEMS}
        renderItem={({ item }) => <Item label={item.label}/>}
        keyExtractor={item => item.id}
      />
      <StatusBar style="auto" />
    </View>
  );
}
