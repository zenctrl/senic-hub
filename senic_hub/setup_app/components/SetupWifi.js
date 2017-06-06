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


export default class SetupWifi extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      networks: [],
      currentSsid: null,
    }

    this.setTitle('Wi-Fi')

    this.setNavigationButtons([], [{
      title: 'Skip',
      id: 'skip',
      disabled: true,
    }])
  }

  didAppear() {
    HubOnboarding.hubDevice.connect()

    HubOnboarding.hubDevice.onNetworksChanged((networks) => {
      console.log(networks)
      this.setState({networks: networks})
    })

    HubOnboarding.hubDevice.onConnectionStateChanged((connectionState, currentSsid) => {
      console.log("ssid:", currentSsid, "state:", connectionState)

      if (connectionState === WifiConnectionState.CONNECTION_STATE_CONNECTED) {
        this.setState({currentSsid: currentSsid})

        // TODO check if it's possible to just update disabled state
        this.setNavigationButtons([], [{
          title: 'Skip',
          id: 'skip',
          disabled: false,
          onPress: () => this.pushScreen('setup.nuimo')
        }])
      }
    })
  }

  willDisappear() {
    // TODO unsubscribe from ssid notifications
  }

  onNetworkSelected(ssid) {
    console.log("Network selected: " + ssid)
    HubOnboarding.hubDevice.sendSsid(ssid)
    this.pushScreen('setup.wifiPassword')
  }

  render() {
    return (
      <View style={styles.container}>
        <View>
          <Text style={styles.title}>
            Select your Wifi network
          </Text>
          <List>
            <FlatList
              data={this.state.networks}
              renderItem={({item}) => (
                <ListItem title={item} onPress={() => this.onNetworkSelected(item)} leftIcon={this.state.currentSsid == item ? {name: 'done'} : {}} />
              )}
              keyExtractor={(item) => item}
            />
          </List>
        </View>
      
        <ActivityIndicator animating={this.state.networks.length === 0} />

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
