import React from 'react';
import {
  ActivityIndicator,
  Button,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import Screen from './Screen.js';
import Settings from '../Settings'

export default class BootScreen extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      hubUnreachable: false,
    }
  }

  didAppear() {
    this.pingHub()
  }

  pingHub() {
    Settings.getHubApiUrl()
      .then(hubApiUrl => {
        if (hubApiUrl) {
          console.log('Stored Hub API URL:', hubApiUrl)

          fetch(hubApiUrl)
            .then(response => {
              Settings.HUB_API_URL = hubApiUrl  // TODO is there a better way?
              console.log('Host', Settings.HUB_API_URL, 'reachable...')

              if (!response.ok) {
                throw new Error('App info request led to unexpected response code')
              }
              return response.json()
            })
            .then(appInfo => {
              console.log('Hub onboarded:', appInfo.onboarded)
              if (appInfo.onboarded) {
                this.resetTo('app.nuimoComponents')
              }
              else {
                // We restart onboarding with Nuimo discovery if hub is reachable but not full onboarded
                this.resetTo('setup.nuimo')
              }
            })
            .catch(error => {
              console.warn('Failed requesting app info:', error)
              this.setState({hubUnreachable: true})
            })
        }
        else {
          this.resetTo('setup.welcome')
        }
      })
      .catch(error => {
        console.warn(error)

        this.resetTo('setup.welcome')
      })
  }

  render() {
    return (
      <View style={styles.container}>
        {this._renderContent()}
      </View>
    );
  }

  _renderContent() {
    if (this.state.hubUnreachable) {
      this.setTitle('Oh, noes')

      return (
        <View>
          <View>
            <Text>
              We couldn't reach your Senic hub. Make sure it's connected to power and within reach of your Wi-Fi network.
            </Text>
            <Text>
              In case the onboarding process fails, please try powering on/off the device. If that doesn't help, then perform the factory reset of the device.
            </Text>
          </View>
          <View>
            <Button title={"Try again to connect to the hub"} onPress={() => this.setState({hubUnreachable: false})} />
            <Button title={"Restart onboarding"} onPress={() => this.resetTo('setup.welcome')} />
          </View>
        </View>
      )
    }
    else {
      this.setTitle('Connecting to the hub...')

      return (
        <ActivityIndicator size={"large"} />
      )
    }
  }
}

const styles = StyleSheet.create({
 container: {
    flex: 1,
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: 10,
  },
});
