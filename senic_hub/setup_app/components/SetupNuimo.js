import React, { Component } from 'react';
import {
  ActivityIndicator,
  AppRegistry,
  Button,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { API_URL } from '../Config';

export default class SetupNuimo extends Component {
  static navigationOptions = {
    title: 'Nuimo',
  };

  constructor() {
    super()

    console.log(API_URL)

    this.state = {
      nuimos: [],
    }
  }

  render() {
    const { navigate } = this.props.navigation;
    return (
      <View style={styles.container}>
        <View>
          <Text style={styles.title}>
            We're now looking for your Nuimo
          </Text>
        </View>

        <View style={this.state.nuimos.length > 0 ? styles.hidden : ''}>
          <ActivityIndicator size={96} />
        </View>

        <View style={this.state.nuimos.length > 0 ? '' : styles.hidden}>
          <Text style={styles.title}>
            Found your Nuimo {this.state.nuimos[0]}
          </Text>
        </View>

        <View>
          <Button disabled={this.state.nuimos.length === 0} onPress={() => navigate('Devices')} title="Continue" />
        </View>
      </View>
    );
  }

  componentDidMount() {
    this.bootstrapNuimos()
  }

  bootstrapNuimos() {
    //TODO: Promise chain doesn't get cancelled when component unmounts
    //TODO: Write tests for all possible API call responses, server not available, etc.
    fetch(API_URL + '/-/setup/nuimo/bootstrap', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({})
    })
      .then((response) => response.json())
      .then((response) => {
        let controllers = response.connectedControllers
        if (controllers.length > 0) {
          this.setState({ nuimos: controllers })
        }
        else {
          // Try again to bootstrap
          this.bootstrapNuimos()
        }
      })
      .catch((error) => {
        console.error(error)
        // Try again to bootstrap
        //TODO: Only retry after a few seconds after an error occurred. Cancel timer if component unmounted.
        this.bootstrapNuimos()
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
  }
});

AppRegistry.registerComponent('SetupNuimo', () => SetupNuimo);
