import { StatusBar } from 'expo-status-bar';
import { StyleSheet } from 'react-native';
import { Link } from 'expo-router';

export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'stretch',
    justifyContent: 'flex-start',
    marginTop: StatusBar.currentHeight || 60,
  },
  titleBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  backlink: {
    marginLeft: 10,
  },
  title: {
    alignSelf: 'center',
  },
  item: {
    backgroundColor: '#cdcdcd',
    alignItems: 'center',
    padding: 20,
    borderTopWidth: 4,
    borderBottomWidth: 4,
    borderColor: '#000',
  },
  back: {
    margin: 8,
    padding: 8,
    fontSize: 20,
    borderColor: '#000',
    borderWidth: 1,
    backgroundColor: 'lightgray',
  }
});

export function BackButton() {
  return (
    <Link style={styles.back} href="/">&lt; Back</Link>
  );
}