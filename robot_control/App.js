import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, FlatList } from 'react-native';

const MENU_ITEMS = [
  { id: 'manual_drive', label: 'Manual drive' },
  { id: 'behavior_path', label: 'Drive path'}
];

function Item({item}) {
  return (
  <View style={styles.item}>
    <Text>{item.label}</Text>
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

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'stretch',
    justifyContent: 'center',
    marginTop: StatusBar.currentHeight || 60,
  },
  title: {
    alignSelf: 'center',
    marginBottom: 20,
  },
  item: {
    backgroundColor: '#cdcdcd',
    alignItems: 'center',
    padding: 20,
    borderTopWidth: 4,
    borderBottomWidth: 4,
    borderColor: '#000',
  },
});
