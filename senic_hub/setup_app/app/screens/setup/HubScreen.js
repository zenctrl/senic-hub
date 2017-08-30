import React from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { BleManager } from 'react-native-ble-plx';
import { List, ListItem } from 'react-native-elements'

import HubOnboarding from '../../lib/HubOnboarding'
import BaseScreen from '../BaseScreen'

export default class SetupHubScreen extends BaseScreen {
  constructor(props) {
    super(props)

    this.manager = new BleManager()
    this.bluetoothStateChangeListener = null

    this.state = {
      hubs: [],
      bluetoothState: null,
    }

    this.setTitle("Hub")
  }

  didAppear() {
    this.bluetoothStateChangeListener = this.manager.onStateChange((state) => {
      console.log('BleManager.state:', state)
      this.setState({ bluetoothState: state })
      if (state === 'PoweredOn') {
        this.startScanning()
      } else {
        this.manager.stopDeviceScan()
      }
    }, true)

    // Disconnect hub if it was connected in the meanwhile (i.e. by a following onboarding step),
    // otherwise it wouldn't be discovered in connected state
    if (HubOnboarding.hubDevice) {
      HubOnboarding.hubDevice.disconnect()
        .catch(error => this.resetTo('bluetoothConnectionFailureScreen'))
    }
  }

  willDisappear() {
    this.bluetoothStateChangeListener.remove()
    this.manager.stopDeviceScan()
  }

  startScanning() {
    //TODO: We need to retrieve all already via BLE connected hubs to the phone
    //      We might be in a state where a hub is still connected to us, it will
    //      thus not be discovered.

    this.manager.startDeviceScan(null, null, (error, device) => {
      if (error) {
        alert("An error occurred while scanning: " + JSON.stringify(error))
        return
      }

      if (HubOnboarding.isHub(device)) {
        console.log("Found hub:", device)

        if (!this.state.hubs.find(hub => hub.id === device.id)) {
          this.setState({hubs: this.state.hubs.concat([device])});
        }
      }
    });
  }

  onHubSelected(device) {
    this.manager.stopDeviceScan()

    HubOnboarding.hubDevice = new HubOnboarding(device)

    this.pushScreen('setupWifiScreen')
  }

  render() {
    return (
      <View style={styles.container}>
        {this._renderContent()}
      </View>
    )
  }

  _renderContent() {
    if (this.state.bluetoothState === 'PoweredOn') {
      if (this.state.hubs.length > 0) {
        return (
          <View>
            <Text style={styles.title}>
              Select your hub
            </Text>
            <List>
              <FlatList
                data={this.state.hubs}
                renderItem={({item}) => (
                  <ListItem
                    title={item.name || "Senic Hub"}
                    subtitle={item.id}
                    onPress={() => this.onHubSelected(item)}
                  />
                )}
                keyExtractor={(item) => item.id}
              />
            </List>
          </View>
        )
      }
      else {
        return (
          <View>
            <Text style={styles.title}>Searching for Senic Hub...</Text>
            <ActivityIndicator size={"large"} />
          </View>
        )
      }
    }
    else if (this.state.bluetoothState == 'PoweredOff') {
      return (
        <Text style={styles.title}>Looks like Bluetooth is turned off on your device. Senic Hub needs Bluetooth enabled to proceed with the Senic Hub onboarding...</Text>
      )
    }
    else {
      // HACK for Android: screen is not activated & willAppear doesn't get called if render() doesn't return any content "right away". Here we return an empty Text component to trigger the screen activation...
      return (
        <Text></Text>
      )
    }
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
