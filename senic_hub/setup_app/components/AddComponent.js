import React from 'react'
import { FlatList } from 'react-native'
import { List, ListItem } from 'react-native-elements'
import Screen from './Screen'
import Settings from '../Settings'

export default class AddComponent extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      // TODO get this from the API
      discovered_devices: []
    }

    this.setTitle("Select a Device Type")
  }

  render() {
    return (
      <List>
        <FlatList
          data={this.state.discovered_devices}
          renderItem={({item}) => <ListItem
            title={item.name}
            onPress={() => this.saveComponent([item.id])} />}
          keyExtractor={(component) => component.type}
        />
      </List>
    )
  }

  didAppear() {
    let that = this;
    //TODO: Promise usage can be probably simplified
    (new Promise((res, rej) => res()))
      .then(() => that.fetchDevices())
      .catch((error) => console.log('error:', error))
  }


  fetchDevices() {
    let that = this
    return fetch(Settings.HUB_API_URL + 'discovered')
      .then(response => {
        if (!response.ok) throw new Error('Request failed: ' + response)
        return response.json()
      })
      .then(response => {
        console.log(response.devices)
        devices = response.devices
        that.setState({discovered_devices: devices})
        console.log(this.state.discovered_devices)
      })
  }


  saveComponent(deviceId) {
    let body = JSON.stringify({device_ids: deviceId})
    let params = {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    }
    fetch(Settings.HUB_API_URL + 'nuimos/' + this.props.nuimoId + '/components', params)
      .then(() => this.dismissAllModals())
      .then(() => this.popScreen())
      .catch((error) => console.error(error))
  }
}
