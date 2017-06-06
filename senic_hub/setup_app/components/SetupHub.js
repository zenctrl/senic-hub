import React from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  View,
  Platform,
} from 'react-native';

import { BleManager } from 'react-native-ble-plx';
import { List, ListItem } from 'react-native-elements'

import HubOnboarding from '../HubOnboarding'
import Screen from './Screen'


export default class SetupHub extends Screen {
  constructor(props) {
    super(props)

    this.manager = new BleManager()

    this.state = {
      hubs: [],
    }

    this.setTitle("Hub")
  }

  willAppear() {
    if (Platform.OS === 'ios') {
      this.manager.onStateChange((state) => {
        if (state === 'PoweredOn') this.startScanning()
      })
    } else {
      this.startScanning()
    }
  }

  willDisappear() {
    this.manager.stopDeviceScan()
  }

  startScanning() {
    this.manager.startDeviceScan(null, null, (error, device) => {
      if (error) {
        alert("An error occurred while scanning: " + JSON.stringify(error))
        console.error("An error occurred while scanning:", error)
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
    console.log('device', device)
    this.manager.stopDeviceScan()
    
    HubOnboarding.hubDevice = new HubOnboarding(device)

    this.pushScreen('setup.wifi')
  }

  render() {
    return (
      <View style={styles.container}>
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

        <ActivityIndicator animating={this.state.hubs.length === 0} />
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
