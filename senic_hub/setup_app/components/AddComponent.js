import React from 'react'
import { FlatList } from 'react-native'
import { List, ListItem } from 'react-native-elements'
import Screen from './Screen'

export default class AddComponent extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      // TODO get this from the API
      componentTypes: [{
        name: 'Sonos',
        type: 'sonos',
      }, {
        name: 'Philips Hue',
        type: 'philips_hue',
      }]
    }

    this.setTitle("Select a Device Type")
  }

  render() {
    return (
      <List>
        <FlatList
          data={this.state.componentTypes}
          renderItem={({item}) => <ListItem
            title={item.name}
            onPress={() => this.showModal('app.selectComponentDevices', { type: item.type })} />}
          keyExtractor={(component) => component.type}
        />
      </List>
    )
  }
}
