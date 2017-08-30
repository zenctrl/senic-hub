import React from 'react';
import { SectionList, View, ListView, FlatList, StyleSheet, Text, Button } from 'react-native';
import { List, ListItem } from 'react-native-elements';
import BaseScreen from './BaseScreen'
import Settings from '../lib/Settings'

import Swipeout from 'react-native-swipeout';



const styles = StyleSheet.create({
  baseText: {
    fontFamily: 'Cochin',
  },
  titleText: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  container: {
    flexDirection: 'row',
    height: 30,
    alignSelf: 'flex-end',
  },
  btn: {
    fontSize: 20,
    fontWeight: 'bold',
    alignSelf: 'flex-end',
  }
});

export default class NuimosMenuScreen extends BaseScreen {
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
        onPress: () => this.pushScreen('setupNuimoScreen')
      },
      {
        title: 'Settings',
        id: 'reset',
        onPress: () => this.pushScreen('settingsScreen'),
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
      })
      .catch((error) => console.error(error))
  }

  render() {
    return (
        <FlatList
          data={this.state.nuimos}
          renderItem={({item}) => this.renderComponentList(item.mac_address.replace(/:/g, '-'), item)}
          keyExtractor={(nuimos) => nuimos.mac_address}
        >
        </FlatList>
    );
  }

  renderComponentList(nuimoId, item) {
    return (
      <View>
        <Text style={styles.titleText}> {item.name} </Text>
        <View style={styles.container}>
          <Text style={styles.btn} onPress={() => { this.deleteNuimo(nuimoId)}}> - </Text>
        </View>
        <List>
        <FlatList
          data={item.components}
          renderItem={({item}) => this.renderComponentListRow(nuimoId, item)}
          keyExtractor={(components) => components.id}
        />
        <ListItem
          title="Add an app"
          onPress={() => {
            this.pushScreen('addComponentScreen', { nuimoId: nuimoId})
          }} />
        </List>
        <View
          style={{
            borderBottomColor: 'black',
            borderBottomWidth: 1,
          }}
        />
      </View>
    );
  }

  renderComponentListRow(nuimoId, item) {
    let swipeBtns = [{
       text: 'Delete',
       backgroundColor: 'red',
       underlayColor: 'rgba(0, 0, 0, 0.6)',
       onPress: () => {
         alert(
           'Delete Component',
           'Are you sure?',
           [
             {text: 'Cancel', style: 'cancel'},
             {text: 'Delete', onPress: this.deleteComponent(nuimoId, item.id)},
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
            this.pushScreen('deviceSelectionScreen', {nuimoId: nuimoId, component: item})
          }} />
      </Swipeout>
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
    url = Settings.HUB_API_URL + 'nuimos/' + itemId
    return fetch(url, params)
      .then(response => {
        if (!response.ok) {
          throw new Error('Deleting component failed with status: ' + response.status)
        } else {
          this.didAppear()
        }
      })
  }

  deleteComponent(nuimoId, itemId){
    component = {}
    let body = JSON.stringify(component)
    let params = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    }
    url = Settings.HUB_API_URL + 'nuimos/' + nuimoId + '/components/' + itemId
    return fetch(url, params)
      .then(response => {
        if (!response.ok) {
          throw new Error('Deleting component failed with status: ' + response.status)
        } else {
          this.didAppear()
        }
      })
  }

}
