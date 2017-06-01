import React from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Button } from 'react-native-elements';
import Screen from './Screen'
import { API_URL } from '../Config';

export default class SetupNuimo extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      nuimos: [],
    }

    this.setTitle("Nuimo")
  }

  render() {
    return (
      <View style={styles.container}>
        <View>
          <Text style={styles.title}>
            We're now looking for your Nuimo
          </Text>
        </View>

        <View style={this.state.nuimos.length > 0 ? '' : styles.hidden}>
          <Text style={styles.title}>
            Found your Nuimo {this.state.nuimos[0]}
          </Text>
        </View>

        <ActivityIndicator animating={this.state.nuimos.length === 0} />

        <View>
          <Button
            buttonStyle={styles.button}
            disabled={this.state.nuimos.length === 0}
            onPress={() => this.pushScreen('setup.devices')}
            title="Continue" />
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
      .then((response) => {
        if (response.ok) {
          return response.json()
        }
        throw new Error('Request failed: ' + JSON.stringify(response))
      })
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
        alert(error)
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
  button: {
    backgroundColor: '#397af8',
  }
});
