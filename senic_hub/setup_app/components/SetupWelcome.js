import React from 'react';
import { RNNetworkInfo } from 'react-native-network-info';
import {
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Button } from 'react-native-elements';
import Screen from './Screen.js';

export default class SetupWelcome extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      networkSSID: null,
    }

    this.setTitle("Welcome")
  }

  componentDidMount() {
    if (RNNetworkInfo === undefined) {
      this.setState({
        networkSSID: 'emulator',
      })
      return
    }
    RNNetworkInfo.getSSID(ssid => {
      this.setState({
        networkSSID: ssid,
      })
    });
  }

  render() {
    return (
      <View style={styles.container}>

        <View>
          <Text style={styles.title}>
            Welcome to Senic Hub
          </Text>
        </View>

        <Text>
          Phone's WiFi SSID: {this.state.networkSSID}
        </Text>

        <View>
          <Button
            buttonStyle={styles.button}
            onPress={ () => this.pushScreen('setup.nuimo') }
            title="Continue" />
        </View>
      </View>
    );
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
