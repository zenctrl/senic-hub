import React, { Component } from 'react';
import {
    Button,
    StyleSheet,
    Text,
    View,
    TextInput,
} from 'react-native';

import HubOnboarding, { WifiConnectionState } from '../HubOnboarding'
import Screen from './Screen';
import Settings from '../Settings'


export default class SetupWifiPassword extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      password: '',
    }

    this.setTitle('Wi-Fi Password')
  }

  onSubmit() {
    let password = this.state.password

    HubOnboarding.hubDevice.onConnectionStateChanged((connectionState, currentSsid) => {
      console.log("ssid:", currentSsid, "state:", connectionState)

      if (connectionState === WifiConnectionState.CONNECTION_STATE_DISCONNECTED) {
        alert('Wrong password! Try again please...')
      }
      else if (connectionState === WifiConnectionState.CONNECTION_STATE_CONNECTED) {
        Settings.setHubApiUrl(HubOnboarding.hubDevice.dnsName)
          .then(() => this.pushScreen('setup.nuimo'))
      }
    })
    HubOnboarding.hubDevice.sendPassword(password)
  }

  render() {
    return (
      <View style={styles.container}>
        <View>
          <Text style={styles.title}>
            Password for WiFi network {HubOnboarding.hubDevice.lastSsidSent}:
          </Text>
        </View>

        <TextInput
          style={{height: 40, borderColor: 'gray', borderWidth: 1}}
          onChangeText={(password) => this.setState({password})}
          value={this.state.password}
          placeholder="Password"
          secureTextEntry={true}
        />

        <Button
          onPress={() => { this.onSubmit() }}
          title="Submit"
          accessibilityLabel="Submit Password"
        />
      </View>
    );
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
})
