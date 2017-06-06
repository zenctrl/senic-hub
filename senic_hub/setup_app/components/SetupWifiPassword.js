import React, { Component } from 'react';
import {
    Button,
    StyleSheet,
    Text,
    View,
    TextInput,
} from 'react-native';

import HubOnboarding, { WifiConnectionState } from '../HubOnboarding'


export default class SetupWifiPassword extends Component {
  constructor(props) {
    super(props)

    this.state = {
      password: '',
    }
  }

  onSubmit() {
    let password = this.state.password

    HubOnboarding.hubDevice.onConnectionStateChanged((connectionState, currentSsid) => {
      console.log("ssid:", currentSsid, "state:", connectionState)

      if (connectionState === WifiConnectionState.CONNECTION_STATE_DISCONNECTED) {
        alert('Wrong password! Try again please...')
      }
      else if (connectionState === WifiConnectionState.CONNECTION_STATE_CONNECTED) {
        this.props.navigator.push({screen: 'setup.nuimo', title: 'Nuimo'})
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
