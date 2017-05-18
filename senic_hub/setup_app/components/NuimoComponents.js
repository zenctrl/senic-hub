import React, { Component } from 'react';
import {
  AppRegistry,
  FlatList,
  StyleSheet,
  View,
} from 'react-native';

import { Button, List, ListItem } from 'react-native-elements';

import { API_URL } from '../Config';


class AddComponent extends Component {
  render() {
    return (
      <Button title={"Add"} onPress={() => alert('TODO')} />
    )
  }
}

export default class NuimoComponents extends Component {
  static navigationOptions = {
    headerLeft: null,
    headerRight: <AddComponent />,
  }

  constructor() {
    super()

    this.state = {
      components: [],
    }
  }

  componentDidMount() {
    this.fetchComponents()
  }

  fetchComponents() {
    fetch(API_URL + '/-/nuimos/0/components')
      .then((response) => response.json())
      .then((components) => {
        console.log(components)
        this.setState({ components: components.components })
      })
      .catch((error) => console.error(error))
  }

  render() {
    return (
      <View style={styles.container}>
        <List>
          <FlatList
            data={this.state.components}
            renderItem={({item}) => <ListItem title={item.type} onPress={() => this.onComponentSelected(item)} />}
            keyExtractor={(component) => component.id}
           />
        </List>
      </View>
    );
  }

  onComponentSelected(component) {
    console.log('component', component)
    const { navigate } = this.props.navigation
    navigate('DeviceSelection', component)
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: 10,
  },
  title: {
    fontSize: 18,
    textAlign: 'center',
    margin: 10,
  },
  button: {
    backgroundColor: '#397af8',
  }
});

AppRegistry.registerComponent('NuimoComponents', () => NuimoComponents);
