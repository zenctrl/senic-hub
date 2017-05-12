import React, { Component } from 'react';
import { NetworkInfo } from 'react-native-network-info';
import {
  AppRegistry,
  StyleSheet,
  Text,
  View,
  Button
} from 'react-native';


export default class SetupWelcome extends Component {
  static navigationOptions = {
    title: 'Welcome',
  };

  constructor() {
    super()

    this.state = {
      currentSSID: '',
    }
  }

  componentDidMount() {
    NetworkInfo.getSSID(ssid => {
      console.log(ssid);

      this.setState({
        currentSSID: ssid,
      })
    });
  }

  render() {
    const { navigate } = this.props.navigation;
    return (
      <View style={styles.container}>

        <View>
          <Text style={styles.title}>
            Welcome to Senic Hub. Press "continue" to continue :)
          </Text>
        </View>

        <View>
          <Text>
            You're connected to {this.state.currentSSID} wifi network!
          </Text>
        </View>

        <View>
          <Button onPress={() => navigate('Nuimo')} title="Continue" />
        </View>

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
});

AppRegistry.registerComponent('SetupWelcome', () => SetupWelcome);
