import { StatusBar } from 'expo-status-bar';
import { Text, View, FlatList } from 'react-native';
import { Link } from 'expo-router';
import { styles } from '../styles';

const MENU_ITEMS = [
  { id: 'manual_drive', label: 'Manual drive' },
  { id: 'behavior_path', label: 'Drive path'},
  { id: 'distance_plotter', label: 'Distance plotter'},
  { id: 'behavior_simple_avoiding' , label: 'Simple Wall Avoiding Behavior'},
  { id: 'power_off', label: 'Power off'},
];

function Item({item}) {
  return (
  <View style={styles.item}>
    <Link href={item.id}>{item.label}</Link>
  </View>
  );
}

export default function App() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Robot control</Text>
      <FlatList
        data={MENU_ITEMS}
        renderItem={({ item }) => <Item item={item}/>}
        keyExtractor={item => item.id}
      />
      <StatusBar style="auto" />
    </View>
  );
}
