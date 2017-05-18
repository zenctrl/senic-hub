import React, { Component } from 'react';
import {
  AppRegistry,
  FlatList,
  StyleSheet,
  View,
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
      <View style={styles.container}>
        <List>
          <FlatList
            data={this.state.component.selected_devices}
            renderItem={({item}) => <ListItem title={item} hideChevron={true} />}
            keyExtractor={(device) => device}
           />
        </List>
      </View>
    );
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: 10,
  },
});

AppRegistry.registerComponent('DeviceSelection', () => DeviceSelection);
