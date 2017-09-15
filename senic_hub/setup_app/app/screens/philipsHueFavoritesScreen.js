import React from 'react';
import {
  FlatList,
  Switch,
  Text,
  View,
  StyleSheet
} from 'react-native';
import { List, ListItem } from 'react-native-elements';
import BaseScreen from './BaseScreen'
import Settings from '../lib/Settings'


const styles = StyleSheet.create({
  titleText: {
    fontSize: 20,
    fontWeight: 'bold',
  }
});

export default class philipsHueFavoritesScreen extends BaseScreen {
  constructor(props) {
    super(props)

    //TODO: Only pass component's ID and fetch the component to get latest state

    this.state = {
      favorites: [],
    }

    this.setTitle("Favorites")
  }

  render() {
    return (
      <View>
      <Text style={styles.titleText}> Available Favorites </Text>
      <List>
        <FlatList
          data={this.state.favorites}
          renderItem={({item}) =>
              <ListItem
                title={item.name}
                onPress={() => {
                this.save(item).then(() => this.resetTo('nuimosMenuScreen'))
              }} />
          }
          keyExtractor={(favorite) => favorite.id}
        />
      </List>
      </View>
    );
  }

  didAppear() {
    let that = this;
    //TODO: Promise usage can be probably simplified
    (new Promise((res, rej) => res()))
      .then(() => that.fetchFavorites())
      .catch((error) => console.log('error:', error))
  }

  fetchFavorites() {
    let that = this
      return fetch(Settings.HUB_API_URL + 'nuimos/' + this.props.nuimoId + '/components/' + this.props.component.id + '/phuefavs')
        .then(response => {
          if (!response.ok) throw new Error('Request failed: ' + response)
          return response.json()
        })
        .then(response => {
          favorites = response.favorites
          that.setState({favorites: favorites})
        })
  }

  save(item) {
    favorite = {}
    favorite.number = this.props.favoriteNumber
    favorite.item = {'id' : item.id, 'name' : item.name}
    let body = JSON.stringify(favorite)
    console.log(body)
    let params = {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    }
    url = Settings.HUB_API_URL + 'nuimos/' + this.props.nuimoId + '/components/' + this.props.component.id + '/nuimophuefavs'
    return fetch(url, params)
      .then(response => {
        if (!response.ok) {
          throw new Error('Saving component failed with status: ' + response.status)
        }
      })
  }

}
