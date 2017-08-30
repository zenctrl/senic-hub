import React from 'react';
import {
    ActivityIndicator,
    Keyboard,
    StyleSheet,
    Text,
    TextInput,
    View,
} from 'react-native';
import { Button } from 'react-native-elements'

import HubOnboarding from '../../lib/HubOnboarding'
import BluetoothRequiringScreen from './BluetoothRequiringScreen';
import Settings from '../../lib/Settings'


export default class SetupWifiPasswordScreen extends BluetoothRequiringScreen {
  constructor(props) {
    super(props)

    this.state = {
      password: '',
      isJoining: false,
      isJoined: false,
      didJoinFail: false,
    }

    this.setTitle("Wi-Fi Password")
  }

  didAppear() {
    super.didAppear()
  }

  willDisappear() {
    super.willDisappear()
  }

  render() {
    return (
      <View style={styles.container}>
        <View>
          <Text style={styles.title}>
            Password for WiFi network {this.props.ssid}:
          </Text>
        </View>

        { this.renderPasswordInput() }
        { this.renderConnectionState() }

        <Button
          onPress={() => this.continue()}
          buttonStyle={styles.button}
          title="Continue"
          disabled={!this.state.isJoined}
        />
      </View>
    );
  }

  renderPasswordInput() {
    if (this.state.isJoining || this.state.isJoined) {
      return
    }

    return (
      <TextInput
        style={{height: 40, borderColor: 'gray', borderWidth: 1}}
        onChangeText={(password) => this.setState({password})}
        value={this.state.password}
        placeholder="Password"
        returnKeyType='send'
        secureTextEntry={true}
        onSubmitEditing={() => this.joinWifi()}
       />
    )
  }

  renderConnectionState() {
    //TODO: Include name of Wi-Fi network in rendered labels
    if (this.state.isJoining) {
      return (
        <View>
          <Text>The Hub is trying to connect to the Wi-Fi network...</Text>
          <ActivityIndicator size={"large"} />
        </View>
      )
    }
    else if (this.state.isJoined) {
      return (
        <Text>Successfully connected to the Wi-Fi network</Text>
      )
    }
    else if (this.state.didJoinFail) {
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

    console.log('Sending Wi-Fi password ' + this.state.password)
    this.setState({
      isJoining: true,
      isJoined: false,
      didJoinFail: false,
    })

    HubOnboarding.hubDevice
      .joinWifi(this.props.ssid, this.state.password)
      .then((apiUrl) => Settings.setHubApiUrl(apiUrl))
      .then(() => {
        this.setState({
          isJoining: false,
          isJoined: true,
        })
      })
      .catch((error) => {
        this.setState({
          isJoining: false,
          didJoinFail: true,
        })
        //TODO: Handle all different errors, such as Bluetooth connection lost
        console.log(error)
      })
  }

  continue() {
    // Now that we know the Hub's API URL we can go back to the boot screen and check
    // if we can reach Hub via its HTTP API. If that's the case then we will
    // automatically continue with the onboarding of Nuimo if the Hub isn't yet
    // fully onboarded.
    this.resetTo('bootScreen')
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
