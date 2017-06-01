import React from 'react';
import {
  FlatList,
} from 'react-native';

import { List, ListItem } from 'react-native-elements';

import Screen from './Screen'


export default class DeviceSelection extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      component: props.component,
    }

    this.setTitle(props.component.type)
  }

  render() {
    return (
      <List>
        <FlatList
          data={this.state.component.device_ids}
          renderItem={({item}) => <ListItem title={item} hideChevron={true} />}
          keyExtractor={(device) => device}
        />
      </List>
    );
  }
}
