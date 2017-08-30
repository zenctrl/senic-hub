import React from 'react';
import {
    ActivityIndicator,
    Keyboard,
    StyleSheet,
    Text,
    TextInput,
    View,
} from 'react-native';
import { Button } from 'react-native-elements'

import BaseScreen from '../BaseScreen';
import Settings from '../../lib/Settings'


export default class SetupHubApiUrlScreen extends BaseScreen {
  constructor(props) {
    super(props)

    this.state = {
      ip: '',
    }

    this.setTitle("Enter Hub's IP")
  }

  render() {
    return (
      <View style={styles.container}>
        <View>
          <Text style={styles.title}>
            Enter IP address for your Hub:
          </Text>
        </View>

        <TextInput
          style={{height: 40, borderColor: 'gray', borderWidth: 1}}
          onChangeText={(ip) => this.setState({ip})}
          value={this.state.ip}
          placeholder="IP address"
          returnKeyType='send'
          onSubmitEditing={() => this.continue()}
         />

        <Button
          onPress={() => this.continue()}
          buttonStyle={styles.button}
          title="Continue"
        />
      </View>
    );
  }

  continue() {
    Keyboard.dismiss()

    Settings.setHubApiUrl('http://' + this.state.ip + ':6543/-/')
      .then(() => this.resetTo('bootScreen'))
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
  },
})
