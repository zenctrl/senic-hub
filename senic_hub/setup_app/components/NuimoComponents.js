import React from 'react';
import { FlatList } from 'react-native';
import { Button, List, ListItem } from 'react-native-elements';
import Screen from './Screen'
import { API_URL } from '../Config';

export default class NuimoComponents extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      components: [],
    }

    this.setTitle("My Nuimo")
    this.setNavigationButtons([], [
      {
        title: "Add",
        id: 'add',
        onPress: () => this.showModal('app.addComponent')
      }
    ])
  }

  willAppear() {
    this.fetchComponents()
  }

  fetchComponents() {
    fetch(API_URL + '/-/nuimos/0/components')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Request failed: ' + JSON.stringify(response))
        }
        return response.json()
      })
      .then((components) => {
        this.setState({ components: components.components })
      })
      .catch((error) => console.error(error))
  }

  render() {
    return (
      <List>
        <FlatList
          data={this.state.components}
          renderItem={({item}) =>
            <ListItem
              title={item.type}
              onPress={() => {
                this.pushScreen('app.deviceSelection', {component: item})
              }} />
          }
          keyExtractor={(component) => component.id}
        />
      </List>
    );
  }
}
