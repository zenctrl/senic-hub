import React, { Component } from 'react';
import {
  AppRegistry,
  FlatList,
} from 'react-native';

import { Button, List, ListItem } from 'react-native-elements';

import { API_URL } from '../Config';


export default class NuimoComponents extends Component {
  static navigationOptions = ({ navigation }) => ({
    title: 'Components',
    headerLeft: null,
    headerRight: <Button
                    backgroundColor={'transparent'}
                    icon={{name: 'add', color: '#397af8'}}
                    onPress={() => navigation.navigate('AddComponent')} />,
  });

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
      .then((response) => {
        if (response.ok) {
          return response.json()
        }
        throw new Error('Request failed: ' + JSON.stringify(response))
      })
      .then((components) => {
        this.setState({ components: components.components })
      })
      .catch((error) => alert(error))
  }

  render() {
    return (
      <List>
        <FlatList
          data={this.state.components}
          renderItem={({item}) => <ListItem title={item.type} onPress={() => this.onComponentSelected(item)} />}
          keyExtractor={(component) => component.id}
        />
      </List>
    );
  }

  onComponentSelected(component) {
    const { navigate } = this.props.navigation
    navigate('DeviceSelection', component)
  }
}

AppRegistry.registerComponent('NuimoComponents', () => NuimoComponents);
