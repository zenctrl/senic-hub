import React from 'react'
import { Text } from 'react-native'
import { Button } from 'react-native-elements'
import Screen from './Screen'
import Settings from '../Settings'

export default class AddComponent extends Screen {
  constructor(props) {
    super(props)

    this.setNavigationButtons([], [{
      'title': "Save",
      'id': 'save',
      //TODO: Replace the dummy deviceId value
      'onPress': () => this.saveComponent('001788176885')
    }])
  }

  saveComponent(deviceId) {
    let body = JSON.stringify({device_id: deviceId})
    let params = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    }
    fetch(Settings.HUB_API_URL + 'nuimos/0/components', params)
      .then(() => this.dismissAllModals())
      .catch((error) => console.error(error))
  }

  render() {
    return (
      <Text>TODO</Text>
    )
  }
}
