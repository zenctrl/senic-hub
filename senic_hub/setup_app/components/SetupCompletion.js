import React from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Button } from 'react-native-elements';
import Screen from './Screen'
import Settings from '../Settings'

export default class SetupCompletion extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      configured: false,
    }

    this.setTitle("Completion")
  }

  render() {
    return (
      <View style={styles.container}>
        {this._renderContent()}

        <View>
          <Button
            disabled={!this.state.configured}
            buttonStyle={styles.button}
            onPress={() => this.resetTo('app.nuimoComponents', {nuimoId: this.props.nuimoId})}
            title="Done" />
        </View>
      </View>
    );
  }

  _renderContent() {
    if (this.state.configured) {
      return (
        <View>
          <Text style={styles.title}>You're all set</Text>
          <Text style={styles.title}>Your smart home is now ready to use</Text>
        </View>
      )
    }
    else {
      return (
        <ActivityIndicator />
      )
    }
  }

  didAppear() {
    fetch(Settings.HUB_API_URL + 'config', {method: 'POST'})
      .then(response => {
        if (!response.ok) {
          throw new Error('Request failed: ' + JSON.stringify(response))
        }
        this.setState({configured: true})
      })
      .catch(error => alert(error))
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
