import React, { Component } from 'react';
import {
  ActivityIndicator,
  AppRegistry,
  FlatList,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Button, List, ListItem } from 'react-native-elements'

import { API_URL } from '../Config';

export default class SetupDevices extends Component {
  static navigationOptions = {
    title: 'Device Discovery',
  };

  devicesPollInterval = 5000  // 5 seconds
  devicesPollTimer = null
  dataSource = null

  constructor() {
    super()

    this.state = {
      devices: [],
    }
  }

  render() {
    const { navigate } = this.props.navigation;
    return (
      <View style={styles.container}>
        <View>
          <Text style={styles.title}>
            We're now looking for your smart devices
          </Text>
        </View>

        <List>
          <FlatList
            data={this.state.devices}
            renderItem={({item}) => (
              <ListItem
                title={item.name}
                hideChevron={true}
                subtitle={item.authenticated ? 'Authenticated' : 'Not Authenticated'} />
            )}
            keyExtractor={(item) => item.id}
           />
        </List>

        <ActivityIndicator animating={this.state.devices.length === 0} />

        <View>
          <Button buttonStyle={styles.button} disabled={this.state.devices.length === 0} onPress={() => navigate('Completion')} title="Continue" />
        </View>
      </View>
    );
  }

  componentDidMount() {
    this.pollDevices()
  }

  componentWillUnmount() {
    console.log('will clear timer', this.devicesPollTimer)

    if (this.devicesPollTimer) {
      clearTimeout(this.devicesPollTimer)
    }
  }

  pollDevices() {
    //TODO: Promise chain doesn't get cancelled when component unmounts
    //TODO: Figure out why {cache: "no-cache"} doesn't work
    fetch(API_URL + '/-/setup/devices?cache-bust=' + Date.now())
      .then((response) => {
        if (response.ok) {
          return response.json()
        }
        throw new Error('Request failed: ' + JSON.stringify(response))
      })
      .then((devices) => {
        console.log(devices)
        this.setState({ devices: devices })
        devices
          .filter((device) => device.authenticationRequired && !device.authenticated)
          .forEach((device) => this.authenticateDevice(device))

          this.devicesPollTimer = setTimeout(this.pollDevices.bind(this), this.devicesPollInterval)
      })
      .catch((error) => alert(error))
  }

  authenticateDevice(device) {
    console.log('authenticating', device)
    fetch(API_URL + '/-/setup/devices/' + device.id + '/authenticate', {method: 'POST'})
      .then((response) => response.json())
      .then((response) => {
        device.authenticated = response.authenticated
        this.forceUpdate()
      })
      .catch((error) => alert(error))
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
  }
});

AppRegistry.registerComponent('SetupDevices', () => SetupDevices);
