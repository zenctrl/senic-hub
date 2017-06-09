import React from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { List, ListItem } from 'react-native-elements'

import HubOnboarding, { WifiConnectionState } from '../HubOnboarding'
import Screen from './Screen';
import Settings from '../Settings'


export default class SetupWifi extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      ssids: [],
      currentSsid: null,
    }

    this.setTitle('Wi-Fi')
  }

  didAppear() {
    HubOnboarding.hubDevice.connect()

    HubOnboarding.hubDevice.onNetworksChanged((ssid) => {
      console.log('Discovered new network:', ssid)

      if (!this.state.ssids.find(s => s === ssid)) {
        this.setState({ssids: this.state.ssids.concat([ssid])})
      }
    })

    HubOnboarding.hubDevice.onConnectionStateChanged((connectionState, currentSsid) => {
      console.log("ssid:", currentSsid, "state:", connectionState)

      if (connectionState === WifiConnectionState.CONNECTION_STATE_CONNECTED) {
        this.setState({currentSsid: currentSsid})
      }
    })
  }

  willDisappear() {
    // TODO unsubscribe from ssid notifications
  }

  onNetworkSelected(ssid) {
    console.log("Network selected: " + ssid)

    if (ssid == this.state.currentSsid) {
      Settings.setHubApiUrl(HubOnboarding.hubDevice.dnsName)
        .then(() => this.pushScreen('setup.nuimo'))
    }
    else {
      HubOnboarding.hubDevice.sendSsid(ssid)
      this.pushScreen('setup.wifiPassword') // TODO make it a modal
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
    if (this.state.ssids.length > 0) {
      return (
        <View>
          <Text style={styles.title}>
            Select your Wi-Fi network
          </Text>
          <List>
            <FlatList
              data={this.state.ssids}
              renderItem={({item}) => (
                <ListItem title={item}
                  onPress={() => this.onNetworkSelected(item)}
                  leftIcon={this.state.currentSsid == item ? {name: 'done'} : {name: 'wifi'}}
                />
              )}
              keyExtractor={(item) => item}
            />
          </List>
        </View>
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
