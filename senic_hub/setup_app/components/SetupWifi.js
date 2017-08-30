import React from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { List, ListItem } from 'react-native-elements'
import { NetworkInfo } from 'react-native-network-info';

import HubOnboarding, { WifiConnectionState } from '../HubOnboarding'
import BluetoothRequiringScreen from './BluetoothRequiringScreen';
import Settings from '../Settings'

export default class SetupWifi extends BluetoothRequiringScreen {
  constructor(props) {
    super(props)

    this.state = {
      ssids: [],
      currentHubSsid: null,
      currentPhoneSsid: null,
      scanningSpinnerVisible: true,
    }

    NetworkInfo.getSSID(ssid => {
      this.setState({
        currentPhoneSsid: ssid,
      })
    });

    this.scanTimeoutId = null

    this.setTitle('Wi-Fi')
  }

  subscribeToWifiEvents() {
    HubOnboarding.hubDevice.onNetworksChanged((ssid) => {
      if (!this.state.ssids.find(s => s === ssid)) {
        this.setState({ssids: this.state.ssids
          .concat([ssid])
          .sort(function (a, b) {
            return a.toLowerCase().localeCompare(b.toLowerCase());
          })
        })
      }

      if (this.state.scanningSpinnerVisible && this.state.currentPhoneSsid === ssid) {
        if (this.scanTimeoutId) {
          clearTimeout(this.scanTimeoutId)
        }
        this.onNetworkSelected(this.state.currentPhoneSsid)
      }
    })

    HubOnboarding.hubDevice.onConnectionStateChanged = (connectionState, currentHubSsid) => {
      if (connectionState === WifiConnectionState.CONNECTION_STATE_CONNECTED) {
        this.setState({currentHubSsid: currentHubSsid})
      }
    }
  }

  didAppear() {
    super.didAppear()

    HubOnboarding.hubDevice.disconnect()
    HubOnboarding.hubDevice
      .connect()
      .then(() => {
        this.subscribeToWifiEvents()
        this.scanTimeoutId = setTimeout(() => {
          this.setState({scanningSpinnerVisible: false})
          this.setTitle('Select your Wi-Fi')
        }, 30000)
      })
      .catch((error) => {
        console.warn(error)
        this.resetTo('setup.bluetoothConnectionFailure')
      })
  }

  willDisappear() {
    //TODO: Setting an empty callback isn't clean – use proper approach.
    HubOnboarding.hubDevice.onNetworksChanged(() => {})
    HubOnboarding.hubDevice.onConnectionStateChanged = null
    super.willDisappear()
  }

  onNetworkSelected(ssid) {
    if (this.state.currentHubSsid === ssid) {
      // The Hub is already connected to the network the user just selected
      // In the case we can directly jump to the boot screen where we try
      // to locate the Hub at its API URL.
      HubOnboarding.hubDevice.readApiUrl()
        .then(apiUrl => Settings.setHubApiUrl(apiUrl))
        .then(() => this.pushScreen('setup.boot'))
    }
    else {
      this.pushScreen('setup.wifiPassword', {ssid: ssid})
    }
  }

  render() {
    return (
      <View style={styles.container}>
        {this._renderContent()}
      </View>
    );
  }

  _renderContent() {
    if (!this.state.scanningSpinnerVisible && this.state.ssids.length > 0) {
      return (
        <List>
          <FlatList
            data={this.state.ssids}
            renderItem={({item}) => (
              <ListItem
                title={item}
                onPress={() => this.onNetworkSelected(item)}
                leftIcon={this.state.currentHubSsid == item ? {name: 'done'} : {name: 'wifi'}}
              />
            )}
            keyExtractor={(item) => item}
          />
        </List>
      )
    }
    else {
      return (
        <View>
          <Text style={styles.title}>Searching for Wi-Fi networks...</Text>
          <ActivityIndicator size={"large"} />
        </View>
      )
    }
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  title: {
    fontSize: 18,
    textAlign: 'center',
    margin: 10,
  },
})
