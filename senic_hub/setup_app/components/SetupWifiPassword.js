import React, { Component } from 'react';
import {
    ActivityIndicator,
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
      isSendingPassword: false,
      didSendPassword: false,
      connectionState: WifiConnectionState.CONNECTION_STATE_DISCONNECTED,
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

        { this.renderConnectionState() }

        <Button
          onPress={() => this.continue()}
          buttonStyle={styles.button}
          title="Continue"
          disabled={this.state.connectionState != WifiConnectionState.CONNECTION_STATE_CONNECTED}
        />
      </View>
    );
  }

  renderConnectionState() {
    //TODO: Include name of Wi-Fi network in rendered labels
    if (this.state.isSendingPassword || this.state.connectionState == WifiConnectionState.CONNECTION_STATE_CONNECTING) {
      return (
        <View>
          <Text>The Hub is trying to connect to the Wi-Fi network...</Text>
          <ActivityIndicator size={"large"} />
        </View>
      )
    }
    else if (this.state.connectionState == WifiConnectionState.CONNECTION_STATE_CONNECTED) {
      return (
        <Text>Successfully connected to the Wi-Fi network</Text>
      )
    }
    else if (this.state.didSendPassword) {
      return (
        <Text>Failed connecting the Hub to the Wi-Fi network. Please check the password.</Text>
      )
    }
    else {
      return (
        <Text>Please enter the password for the Wi-Fi network</Text>
      )
    }
  }

  joinWifi() {
    Keyboard.dismiss()
    //TODO: Unsubscribe from state changes when screen disappears
    HubOnboarding.hubDevice.onConnectionStateChanged((connectionState, currentSsid) => {
      console.log("ssid:", currentSsid, "state:", connectionState)
      this.setState({connectionState: connectionState})
    })
    console.log('Sending Wi-Fi password')
    this.setState({
      isSendingPassword: true,
      didSendPassword: true,
    })
    //TODO: Make `sendPassword` should become a Promise that succeeds when the wifi could be connected
    //      This said, this component shouldn't observe wifi connection state changes
    HubOnboarding.hubDevice
      .sendPassword(this.state.password)
      .then(() => {
        this.setState({isSendingPassword: false})
      })
      .catch((error) => {
        this.setState({isSendingPassword: false})
        console.error(error)
      })
  }

  continue() {
    // TODO: We have to read hub's host name from the hub only after it connected
    //       to wi-fi network, because the hostname depends on which IP address it got
    Settings
      .setHubApiUrl(HubOnboarding.hubDevice.dnsName)
      .then(() => this.pushScreen('setup.nuimo'))
    HubOnboarding.hubDevice.disconnect()
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
