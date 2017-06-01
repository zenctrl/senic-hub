import React from 'react';
import {
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { Button } from 'react-native-elements';
import Screen from './Screen'
import { API_URL } from '../Config';

export default class SetupCompletion extends Screen {
  constructor(props) {
    super(props)

    this.setTitle("Completion")
  }

  render() {
    return (
      <View style={styles.container}>
        <View>
          <Text style={styles.title}>You're all set</Text>
          <Text style={styles.title}>Your smart home is now ready to use</Text>
        </View>

        <View>
          <Button color={'#000'} backgroundColor={'#fff'} title="Watch tutorial" />
        </View>

        <View>
          <Button
            buttonStyle={styles.button}
            onPress={() => this.pushScreen('app.nuimoComponents')}
            title="Done" />
        </View>
      </View>
    );
  }

  didAppear() {
    fetch(API_URL + '/-/setup/config', {method: 'POST'})
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
