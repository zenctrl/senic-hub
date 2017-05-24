import React, { Component } from 'react'
import {
  AppRegistry,
  Text,
} from 'react-native'

import { Button } from 'react-native-elements'

import { API_URL } from '../Config';


export default class AddComponent extends Component {
  //TODO: Replace the dummy deviceId value
  static navigationOptions = ({navigation}) => ({
    title: 'Select devices',
    headerRight: <Button title={'Save'} backgroundColor={'transparent'} color={'#397af8'}
                    onPress={() => navigation.state.params.saveComponent('001788176885', navigation)} />,
  })

  constructor(props) {
    super(props)
  }

  saveComponent(deviceId, navigation) {
    let body = JSON.stringify({device_id: deviceId})
    let params = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    }
    fetch(API_URL + '/-/nuimos/0/components', params)
      .then(() => navigation.navigate('NuimoComponents'))
      .catch((error) => console.error(error))
  }

  componentDidMount() {
    this.props.navigation.setParams({saveComponent: this.saveComponent})
  }

  render() {
    return (
      <Text>TODO</Text>
    )
  }
}

AppRegistry.registerComponent('SelectComponentDevices', () => SelectComponentDevices)
