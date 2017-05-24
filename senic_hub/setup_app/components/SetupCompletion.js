import React, { Component } from 'react';
import {
  AppRegistry,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Button } from 'react-native-elements';

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
          <Button color={'#000'} backgroundColor={'#fff'} title="Watch tutorial" />
        </View>

        <View>
          <Button buttonStyle={styles.button} onPress={() => navigate('NuimoComponents')} title="Done" />
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
    padding: 10,
  },
  title: {
    fontSize: 18,
    textAlign: 'center',
    margin: 10,
  },
  button: {
    backgroundColor: '#397af8',
  }
});

AppRegistry.registerComponent('SetupCompletion', () => SetupCompletion);
