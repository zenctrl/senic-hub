import React, { Component } from 'react';
import {
  AppRegistry,
  FlatList,
} from 'react-native';

import { List, ListItem } from 'react-native-elements';


export default class DeviceSelection extends Component {
  static navigationOptions = ({ navigation }) => ({
    title: `${navigation.state.params.type}`,
  });

  constructor(props) {
    super(props)

    this.state = {
      component: props.navigation.state.params,
    }
  }

  render() {
    return (
      <List>
        <FlatList
          data={this.state.component.selected_devices}
          renderItem={({item}) => <ListItem title={item} hideChevron={true} />}
          keyExtractor={(device) => device}
        />
      </List>
    );
  }
}

AppRegistry.registerComponent('DeviceSelection', () => DeviceSelection);
