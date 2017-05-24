import React, { Component } from 'react'
import {
  AppRegistry,
  FlatList,
} from 'react-native'

import { List, ListItem } from 'react-native-elements'


export default class AddComponent extends Component {
  static navigationOptions = {
    title: 'Select Component Type',
  }

  constructor() {
    super()

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
  }

  render() {
    return (
      <List>
        <FlatList
          data={this.state.componentTypes}
          renderItem={({item}) => <ListItem title={item.name} onPress={() => this.onComponentTypeSelected(item.type)} />}
          keyExtractor={(component) => component.type}
        />
      </List>
    )
  }

  onComponentTypeSelected(type) {
    const { navigate } = this.props.navigation
    navigate('SelectComponentDevices', {type: type})
  }
}

AppRegistry.registerComponent('AddComponent', () => AddComponent)
