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
      discoveredDevices: []
    }

    this.setTitle("Select a Device Type")
  }

  render() {
    return (
      <List>
        <FlatList
          data={this.state.discoveredDevices}
          renderItem={({item}) => <ListItem
            title={item.name}
            onPress={() => this.saveComponent(item.id)} />}
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
    return fetch(Settings.HUB_API_URL + 'devices')
      .then(response => {
        if (!response.ok) throw new Error('Request failed: ' + response)
        return response.json()
      })
      .then(response => {
        devices = response.devices

        var devIds = []
        var bridgeIndex = null
        //TODO: to be tested with multiple HUE BRIDGES
        //can be probably simplified
        for (var i = devices.length-1; i >= 0; i--){
          if (devices[i].type == 'philips_hue'){
            if (!devices[i].id.includes('-light-')){
              bridgeIndex = i
            }else{
              devIds.push(devices[i].id)
              devices.splice(i, 1)
            }
          }else{
            devices[i].id = [devices[i].id]
          }
        }
        if (devices[bridgeIndex].type == 'philips_hue'){
          devices[bridgeIndex].id = devIds
        }

        that.setState({discoveredDevices: devices})
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
