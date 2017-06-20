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
    let subscribeForWifiEvents = () => {
      HubOnboarding.hubDevice.onNetworksChanged((ssid) => {
        if (!this.state.ssids.find(s => s === ssid)) {
          this.setState({ssids: this.state.ssids
            .concat([ssid])
            .sort(function (a, b) {
              return a.toLowerCase().localeCompare(b.toLowerCase());
            })
          })
        }
      })

      HubOnboarding.hubDevice.onConnectionStateChanged((connectionState, currentSsid) => {
        if (connectionState === WifiConnectionState.CONNECTION_STATE_CONNECTED) {
          this.setState({currentSsid: currentSsid})
        }
      })
    }

    HubOnboarding.hubDevice
      .connect()
      .then(() => {
        subscribeForWifiEvents()
      })
      .catch((error) => {
        alert("Could not connect to the Hub. Please try again.")
        //TODO: Present error message on screen with a "retry" button that connects again
      })
  }

  willDisappear() {
    //TODO: Setting an empty callback isn't clean – use proper approach.
    HubOnboarding.hubDevice.onNetworksChanged(() => {})
    HubOnboarding.hubDevice.onConnectionStateChanged(() => {})
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
