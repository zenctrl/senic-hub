import React from 'react';
import {
  ActivityIndicator,
  Button,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { BleManager } from 'react-native-ble-plx';

import HubOnboarding from '../HubOnboarding'
import Screen from './Screen.js';
import Settings from '../Settings'

export default class BluetoothConnectionFailureScreen extends Screen {

    // When this screen is entered the bluetooth connection to the hub was lost
    // while provisioning the hub and before the Wifi connection was established.
    // The user should be able to choose between trying again to connect to the hub
    // or restarting the onboarding process.

  constructor(props) {
    super(props)

    this.manager = new BleManager()
    this.bluetoothStateChangeListener = null

    this.state = {
      bluetoothReenabled: false,
    }

    this.setTitle("Oh, noes")
  }

  render() {
    return (
      <View style={styles.container}>
        <View>
          <Text>
            We lost the Bluetooth connection to your Senic Hub.{"\n"}
            {"\n"}
            Please help us connecting to
            it again by disabling Bluetooth on this phone and then enabling it again. Please
            also make sure that your Senic Hub is not too far away from this phone.{"\n"}
            {"\n"}
            Please tap "Continue" after you have first disabled and then enabled Bluetooth
            again on this phone.
          </Text>
        </View>
        <View>
          <Button
            title="Continue"
            disabled={!this.state.bluetoothReenabled}
            onPress={() => this.resetTo('setup.hub')} />
        </View>
      </View>
    );
  }

  didAppear() {
    this.bluetoothStateChangeListener = this.manager.onStateChange(state => {
      console.log('Bluetooth state changed to: ' + state)
      if (state === 'PoweredOn') {
        this.setState({ bluetoothReenabled: true })
      }
    }, false /* Only receive _changed_ Bluetooth connection state, not the current */)
  }

  willDisappear() {
    this.bluetoothStateChangeListener.remove()
  }
}

const styles = StyleSheet.create({
 container: {
    flex: 1,
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: 10,
  },
});
