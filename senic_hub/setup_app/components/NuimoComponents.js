import React from 'react';
import { FlatList } from 'react-native';
import { List, ListItem } from 'react-native-elements';
import Screen from './Screen'
import Settings from '../Settings'

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
        onPress: () => this.showModal('app.addComponent', { nuimoId: this.props.nuimoId })
      },
      {
        title: 'Settings',
        id: 'reset',
        onPress: () => this.showModal('settings'),
      },
    ])
  }

  didAppear() {
    this.fetchComponents()
  }

  fetchComponents() {
    fetch(Settings.HUB_API_URL + 'nuimos/' + this.props.nuimoId + '/components')
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
                this.pushScreen('app.deviceSelection', {nuimoId: this.props.nuimoId, component: item})
              }} />
          }
          keyExtractor={(component) => component.id}
        />
      </List>
    );
  }
}
