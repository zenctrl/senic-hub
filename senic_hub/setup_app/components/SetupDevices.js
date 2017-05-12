import React, { Component } from 'react';
import {
  ActivityIndicator,
  AppRegistry,
  Button,
  ListView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

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

    dataSource = new ListView.DataSource({rowHasChanged: (r1, r2) => r1 !== r2})

    this.state = {
      devices: [],
      dataSource: dataSource.cloneWithRows([]),
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

        <View style={this.state.devices.length > 0 ? styles.hidden : ''}>
          <ActivityIndicator size={96} />
        </View>

        <View style={this.state.devices.length > 0 ? '' : styles.hidden}>
          <ListView
            dataSource={this.state.dataSource}
            renderRow={(rowData) => <Text style={styles.device}>{rowData}</Text>}
          />
        </View>

        <View>
          <Button disabled={this.state.devices.length === 0} onPress={() => navigate('Completion')} title="Continue" />
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
        deviceNames = devices.map((d) => d.authenticationRequired && (d.authenticated ? d.name + ' - Authenticated' : d.name + ' - Not authenticated') || d.name)
        this.setState({ devices: devices, dataSource: dataSource.cloneWithRows(deviceNames) })
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
  }
});

AppRegistry.registerComponent('SetupDevices', () => SetupDevices);
