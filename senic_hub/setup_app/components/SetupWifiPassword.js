import React, { Component } from 'react';
import {
    Keyboard,
    StyleSheet,
    Text,
    TextInput,
    View,
} from 'react-native';
import { Button } from 'react-native-elements'

import HubOnboarding, { WifiConnectionState } from '../HubOnboarding'
import Screen from './Screen';
import Settings from '../Settings'


export default class SetupWifiPassword extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      password: '',
      joined: false,
    }

    this.setTitle('Wi-Fi Password')
    this.setNavigationButtons([], [
      {
        title: "Join",
        id: 'join',
        onPress: () => this.joinWifi()
      },
    ])
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
          returnKeyType='send'
          secureTextEntry={true}
          onSubmitEditing={() => this.joinWifi()}
        />

        <Button
          onPress={() => this.pushScreen('setup.nuimo')}
          buttonStyle={styles.button}
          title="Continue"
          disabled={!this.state.joined}
        />
      </View>
    );
  }

  joinWifi() {
    Keyboard.dismiss()
    //TODO: Unsubscribe from state changes when screen disappears
    HubOnboarding.hubDevice.onConnectionStateChanged((connectionState, currentSsid) => {
      console.log("ssid:", currentSsid, "state:", connectionState)

      if (connectionState === WifiConnectionState.CONNECTION_STATE_DISCONNECTED) {
        alert('Wrong password! Try again please...')
      }
      else if (connectionState === WifiConnectionState.CONNECTION_STATE_CONNECTED) {
        Settings.setHubApiUrl(HubOnboarding.hubDevice.dnsName)
          .then(() => this.setState({joined: true}))
      }
    })
    //TODO: Make `sendPassword` become a `Promise`
    console.log('Sending Wi-Fi password')
    HubOnboarding.hubDevice.sendPassword(this.state.password)
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
  },
})
