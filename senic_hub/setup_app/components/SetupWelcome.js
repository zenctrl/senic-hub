import React, { Component } from 'react';
import { NetworkInfo } from 'react-native-network-info';
import {
  AppRegistry,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Button } from 'react-native-elements';


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
            Welcome to Senic Hub
          </Text>
        </View>

        <View>
          <Button buttonStyle={styles.button} onPress={() => navigate('Nuimo')} title="Continue" />
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

AppRegistry.registerComponent('SetupWelcome', () => SetupWelcome);
