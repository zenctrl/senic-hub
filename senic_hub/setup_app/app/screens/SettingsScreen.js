import React from 'react';
import {
  FlatList,
  StyleSheet,
  View,
} from 'react-native';

import { List, ListItem } from 'react-native-elements'

import BaseScreen from './BaseScreen';
import Settings from '../lib/Settings'

export default class SettingsScreen extends BaseScreen {
  constructor(props) {
    super(props)

    this.items = [
      { title: 'Feedback', onPress: () => this.pushScreen('feedbackScreen') },
      { title: 'Restart Setup', onPress: () => Settings.resetHubApiUrl().then(() => this.resetTo('setupWelcomeScreen')) },
    ]

    this.setTitle('Settings')
    this.setNavigationButtons([], [
      {
        title: "Close",
        id: 'close',
        onPress: () => this.popScreen()
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
