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

        <ActivityIndicator animating={this.state.devices.length === 0} />

        <List style={this.state.devices.length > 0 ? '' : styles.hidden}>
          <FlatList
            data={this.state.devices}
            renderItem={({item}) => <ListItem title={item.name} hideChevron={true} />}
            keyExtractor={(item) => item.id}
           />
        </List>

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
    if (this.devicesPollTimer) {
      clearTimeout(this.devicesPollTimer)
    }
  }

  pollDevices() {
    //TODO: Promise chain doesn't get cancelled when component unmounts
    fetch(API_URL + '/-/setup/devices')
      //TODO: Write tests for all possible API call responses, server not available, etc.
      .then((response) => response.json())
      .then((devices) => {
        this.setState({ devices: devices })
        devices
          .filter((device) => device.authenticationRequired && !device.authenticated)
          .forEach((device) => this.authenticateDevice(device))

          this.devicesPollTimer = setTimeout(this.pollDevices.bind(this), this.devicesPollInterval)
      })
      .catch((error) => console.error(error))
  }

  authenticateDevice(device) {
    fetch(API_URL + '/-/setup/devices/' + device.id + '/authenticate', {method: 'POST'})
      .then((response) => response.json())
      .then((response) => {
        device.authenticated = response.authenticated
        this.forceUpdate()
      })
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
  hidden: {
    display: 'none',
  },
  device: {
    fontSize: 18,
  },
  button: {
    backgroundColor: '#397af8',
  }
});

AppRegistry.registerComponent('SetupDevices', () => SetupDevices);
