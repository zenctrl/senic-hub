import React from 'react';
import {
  FlatList,
  StyleSheet,
  View,
} from 'react-native';

import { List, ListItem } from 'react-native-elements'

import Screen from './Screen';
import Settings from '../Settings'

export default class SettingsScreen extends Screen {
  constructor(props) {
    super(props)

    this.items = [
      { title: 'Feedback', onPress: () => this.pushScreen('feedback') },
      { title: 'Restart Setup', onPress: () => Settings.resetHubApiUrl().then(() => this.resetTo('setup.welcome')) },
    ]

    this.setTitle('Settings')
    this.setNavigationButtons([], [
      {
        title: "Close",
        id: 'close',
        onPress: () => this.dismissModal()
      }
    ])
  }

  render() {
    return (
      <View style={styles.container}>
        <List>
          <FlatList
            data={this.items}
            renderItem={({item}) => (
              <ListItem
                title={item.title}
                onPress={item.onPress}
              />
            )}
            keyExtractor={(item) => item.title}
          />
        </List>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  title: {
    fontSize: 18,
    textAlign: 'center',
    margin: 10,
  },
})
