import React, { Component } from 'react';
import {
  AppRegistry,
  Button,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { API_URL } from '../Config';

export default class SetupCompletion extends Component {
  static navigationOptions = {
    title: 'Setup complete',
  };

  render() {
    const { navigate } = this.props.navigation;
    return (
      <View style={styles.container}>
        <View>
          <Text style={styles.title}>You're all set</Text>
          <Text style={styles.title}>Your smart home is now ready to use</Text>
        </View>

        <View>
          <Button onPress={() => navigate('Tutorial')} title="Watch tutorial" />
        </View>
      </View>
    );
  }

  componentDidMount() {
    fetch(API_URL + '/-/setup/config', {method: 'POST'})
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'column',
    justifyContent: 'space-between',
  },
  title: {
    fontSize: 18,
    textAlign: 'center',
    margin: 10,
  },
});

AppRegistry.registerComponent('SetupCompletion', () => SetupCompletion);
