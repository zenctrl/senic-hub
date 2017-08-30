import React from 'react'
import { FlatList } from 'react-native'
import { List, ListItem } from 'react-native-elements'
import BaseScreen from './BaseScreen'
import Settings from '../lib/Settings'

export default class AddComponentScreen extends BaseScreen {
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
          keyExtractor={(component) => component.id}
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

        var deviceIds = []
        var userIndex = null
        //can be probably simplified
        for (var i = devices.length-1; i >= 0; i--){
          if (devices[i].type == 'philips_hue'){
            if (!devices[i].id.includes('-light-') && devices[i].id == userIndex){
              devices[i].id = deviceIds
              deviceIds = []
              userIndex = null
            }else{
              userIndex = devices[i].id.split("-")[0]
              deviceIds.push(devices[i].id)
              devices.splice(i, 1)
            }
          }else{
            devices[i].id = [devices[i].id]
          }
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
