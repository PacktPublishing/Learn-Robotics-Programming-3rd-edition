import { StatusBar } from 'expo-status-bar';
import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'stretch',
    justifyContent: 'flex-start',
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
