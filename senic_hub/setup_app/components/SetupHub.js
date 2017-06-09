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

import HubOnboarding from '../HubOnboarding'
import Screen from './Screen'


export default class SetupHub extends Screen {
  constructor(props) {
    super(props)

    this.manager = new BleManager()
    this.stateChangeListener = null

    this.state = {
      hubs: [],
      bluetoothState: null,
    }

    this.setTitle("Hub")
  }

  willAppear() {
    this.stateChangeListener = this.manager.onStateChange((state) => {
      console.log('BleManager.state:', state)

      this.updateBluetoothState(state)
    }, true)
  }

  updateBluetoothState(state) {
    this.setState({bluetoothState: state})

    if (state === 'PoweredOn') {
      this.startScanning()
    } else {
      this.manager.stopDeviceScan()
    }
  }

  willDisappear() {
    if (this.stateChangeListener) {
      this.stateChangeListener.remove()
      this.stateChangeListener = null
    }
    this.manager.stopDeviceScan()
  }

  startScanning() {
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

    this.pushScreen('setup.wifi')
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
                    title={item.name}
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
