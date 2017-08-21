import React from 'react';
import {
  ActivityIndicator,
  Button,
  StyleSheet,
  Text,
  View,
  Platform,
} from 'react-native';
import HubOnboarding from '../HubOnboarding'
import Screen from './Screen.js';
import Settings from '../Settings'

export default class BootScreen extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      hubUnreachable: false,
      didAppearLaunched: false,
    }

    this.updateTitle()
  }

  didAppear() {
    this.state.didAppearLaunched = true
    // When this screen is entered we either (re-)start onboarding a Hub or we
    // have just successfully provisioned the Hub with Wi-Fi. In both cases we
    // need to disconnect from the Hub if it we previously connected to it via
    // Bluetooth. In the case of (re-)starting onboarding we need to disconnect
    // as otherwise the Hub wouldn't be discovered via the Bluetooth discovery
    // that we are running. In case of successfully provisioning the Hub with
    // Wi-Fi via Bluetooth we now need to disconnect the Bluetooth connection
    // to the Hub as otherwise Nuimo controllers cannot be discovered and
    // connected.
    if (HubOnboarding.hubDevice) {
      HubOnboarding.hubDevice.disconnect()
        .catch(error => this.resetTo('setup.bluetoothConnectionFailure'))
    }
    this.detectHubReachabilityAndResetToNextScreenOnSuccess()
  }

  detectHubReachabilityAndResetToNextScreenOnSuccess() {
    this.setState({ hubUnreachable: false })

    Promise.resolve()
      .then(() => {
        return Settings.getHubApiUrl()
          .catch(() => {
            // No Hub API Url stored -> Start Hub onboarding
            this.resetTo('setup.welcome')
            throw new Error('No Hub API Url stored') // Cancel outer promise chain
          })
      })
      .then(hubApiUrl => {
        console.log('Trying to fetch Hub info at', hubApiUrl)
        // TODO: Try to fetch Hub Info a couple of times as user might have just restarted
        //       the Hub thus it takes a while to boot and start the web server
        return Promise
          .race([
            this.fetchHubInfoAndResetToNextScreenOnSuccess(hubApiUrl),
            new Promise((resolve, reject) => setTimeout(reject, 3000, 'Fetching Hub info timed out')),
          ])
          .catch((error) => {
            console.log('Hub unreachable because:', error)
            this.setState({ hubUnreachable: true })
            throw new Error('Could not reach Hub') // Cancel outer promise chain
          })
      })
      .catch(() => null /* Already handled by inner promise chains */)
  }

  fetchHubInfoAndResetToNextScreenOnSuccess(hubApiUrl) {
    return fetch(hubApiUrl)
      .then(response => {
        console.log('Host', hubApiUrl, 'reachable...')

        Settings.HUB_API_URL = hubApiUrl

        if (!response.ok) {
          throw new Error('App info request led to unexpected response code')
        }
        return response.json()
      })
      .then(hubInfo => {
        console.log('Hub onboarded:', hubInfo.onboarded)
        if (hubInfo.onboarded) {
          this.fetchNuimoId()
            .then(nuimoId => {
              this.resetTo('app.nuimosMenu', { nuimoId: nuimoId })
            })
            .catch(() => {
              // This case should not happen, because the Hub already said it's onboarded
              this.resetTo('setup.nuimo')
            })
        }
        else {
          // We restart onboarding with Nuimo discovery if hub is reachable but not fully onboarded
          this.resetTo('setup.nuimo')
        }
      })
  }

  fetchNuimoId() {
    return fetch(Settings.HUB_API_URL + 'nuimos')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Request failed: ' + JSON.stringify(response))
        }
        return response.json()
      })
      .then((response) => {
        if (response.nuimos.length > 0) {
          return response.nuimos[0]
        }
        else {
          throw new Error("No Nuimo found")
        }
      })
  }

  render() {
    return (
      <View style={styles.container}>
        {
          this.state.hubUnreachable
            ? this.renderHubUnreachableView()
            : <ActivityIndicator size={"large"} />
        }
      </View>
    )
  }

  renderHubUnreachableView() {
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
          <Button
            title="Try again to connect to the Hub"
            onPress={() => this.detectHubReachabilityAndResetToNextScreenOnSuccess()}
          />
          <Button
            title="Restart Hub Setup"
            onPress={() => this.restartOnboarding()} />
        </View>
      </View>
    )
  }

  componentDidUpdate() {
    this.updateTitle()
  }

  updateTitle() {
    this.setTitle(this.state.hubUnreachable
      ? "Oh, noes"
      : "Connecting to the Hub...")
      setTimeout(
      () => { if (Platform.OS === 'android' && !this.state.didAppearLaunched){this.didAppear() }},
      500);
  }

  restartOnboarding() {
    Settings.resetHubApiUrl()
      .then(() => this.resetTo('setup.welcome'))
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
