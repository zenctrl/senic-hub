import React from 'react';
import { FlatList } from 'react-native';
import { List, ListItem } from 'react-native-elements';
import Screen from './Screen'
import Settings from '../Settings'

import Swipeout from 'react-native-swipeout';

export default class NuimosMenu extends Screen {
  constructor(props) {
    super(props)

    this.state = {
      nuimos: [],
    }

    this.setTitle("Nuimos Menu")
    this.setNavigationButtons([], [
      {
        title: "Add Nuimo",
        id: 'add',
        onPress: () => this.pushScreen('setup.nuimo')
      },
      {
        title: 'Settings',
        id: 'reset',
        onPress: () => this.pushScreen('settings'),
      },
    ])
  }

  didAppear() {
    this.fetchNuimos()
  }

  fetchNuimos() {
    fetch(Settings.HUB_API_URL + 'confnuimos')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Request failed: ' + JSON.stringify(response))
        }
        return response.json()
      })
      .then((nuimos) => {
        this.setState({ nuimos: nuimos.nuimos })
        console.log(this.state.nuimos)
        for (var i; i < this.state.nuimos.length; i++){
          console.log(this.state.nuimos[i].name)
        }
      })
      .catch((error) => console.error(error))
  }

  renderRow(item) {
    let swipeBtns = [{
       text: 'Delete',
       backgroundColor: 'red',
       underlayColor: 'rgba(0, 0, 0, 0.6)',
       onPress: () => {
         alert(
           'Delete Nuimo',
           'Are you sure?',
           [
             {text: 'Cancel', style: 'cancel'},
             {text: 'Delete', onPress: this.deleteNuimo(item.mac_address.replace(/:/g, '-'))},
           ],
           { cancelable: false }
         )
       }
    }];

    return (
      <Swipeout right={swipeBtns}
        autoClose={true}
        backgroundColor='transparent'>
        <ListItem
          title={item.name}
          onPress={() => {
            this.pushScreen('app.nuimoComponents', {nuimoId: item.mac_address.replace(/:/g, '-'), name: item.name})
          }}
        />
      </Swipeout>
    );
  }

  render() {
    return (
      <List>
        <FlatList
          data={this.state.nuimos}
          renderItem={({item}) => this.renderRow(item)}
          keyExtractor={(nuimos) => nuimos.mac_address}
        />
      </List>
    );
  }

  deleteNuimo(itemId){
    component = {}
    let body = JSON.stringify(component)
    let params = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    }
    console.log("CIAO")
    url = Settings.HUB_API_URL + 'nuimos/' + itemId
    return fetch(url, params)
      .then(response => {
        if (!response.ok) {
          throw new Error('Deleting component failed with status: ' + response.status)
        } else {
          this.fetchNuimos()
        }
      })
  }

}
