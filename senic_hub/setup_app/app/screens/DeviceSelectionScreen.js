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

export default class DeviceSelectionScreen extends BaseScreen {
  constructor(props) {
    super(props)

    //TODO: Only pass component's ID and fetch the component to get latest state

    this.state = {
      component: props.component,
      devices: [],
      station1: {},
      station2: {},
      station3: {},
    }

    this.setTitle(props.component.type)
    this.setNavigationButtons([], [
      {
        title: "Save",
        id: 'save',
        onPress: () => {
          this.save()
            .then(() => this.popScreen())
            .catch(e => console.warn(e))
        }
      }
    ])
  }

  render() {
    const type = this.state.component.type
    if (type == 'sonos') {
      return (
        <View>
        <List>
          <FlatList
            data={this.state.devices}
            renderItem={({item}) =>
              <View>
                <Switch
                  value={item.selected}
                  onValueChange={(value) => this.onDeviceSelectionChanged(item, value)}
                  />
                <Text>{item.name}</Text>
              </View>
            }
            keyExtractor={(device) => device.id}
          />
        </List>
        <View
          style={{
            borderBottomColor: 'black',
            borderBottomWidth: 1,
          }}
        />
        <Text style={styles.titleText}> STATIONS </Text>
        <List>
        <ListItem
          //roundAvatar
          avatar={{uri:'http://www.drodd.com/images15/1-7.jpg'}}
          title={this.state.station1.title}
          onPress={() => {
            this.pushScreen('sonosFavoritesScreen', {nuimoId: this.props.nuimoId, component: this.state.component, favoriteNumber: 1})
          }}
        />
        <ListItem
          //roundAvatar
          avatar={{uri:'http://www.drodd.com/images15/2-23.jpg'}}
          title={this.state.station2.title}
          onPress={() => {
            this.pushScreen('sonosFavoritesScreen', {nuimoId: this.props.nuimoId, component: this.state.component, favoriteNumber: 2})
          }}
        />
        <ListItem
          //roundAvatar
          avatar={{uri:'http://www.drodd.com/images15/3-12.jpg'}}
          title={this.state.station3.title}
          onPress={() => {
            this.pushScreen('sonosFavoritesScreen', {nuimoId: this.props.nuimoId, component: this.state.component, favoriteNumber: 3})
          }}
        />
        </List>
        </View>
      );
    } else {
      return (
        <View>
        <List>
          <FlatList
            data={this.state.devices}
            renderItem={({item}) =>
              <View>
                <Switch
                  value={item.selected}
                  onValueChange={(value) => this.onDeviceSelectionChanged(item, value)}
                  />
                <Text>{item.name}</Text>
              </View>
            }
            keyExtractor={(device) => device.id}
          />
        </List>
        </View>
      );
    }
  }

  didAppear() {
    let that = this;
    //TODO: Promise usage can be probably simplified
    (new Promise((res, rej) => res()))
      .then(() => that.fetchComponent())
      .then(() => that.fetchDevices())
      .then(() => that.fetchStations())
      .catch((error) => console.log('error:', error))
  }

  fetchComponent() {
    let that = this
    return fetch(Settings.HUB_API_URL + 'nuimos/' + this.props.nuimoId + '/components/' + that.state.component.id)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed fetching component with status: ' + response.status)
        }
        return response.json()
      })
      .then(component => {
        that.setState({component: component})
      })
  }

  fetchDevices() {
    let that = this
    return fetch(Settings.HUB_API_URL + 'devices')
      .then(response => {
        if (!response.ok) throw new Error('Request failed: ' + response)
        return response.json()
      })
      .then(response => {
        devices = response.devices
          .filter(device => device.type == that.state.component.type)
          .filter(device => !(device.virtual || false))
          .filter(device => device.id.includes(that.state.component.device_ids[0].split('-')[0]))
        devices.forEach(device =>
          device.selected = that.state.component.device_ids.indexOf(device.id) > -1
        )
        that.setState({devices: devices})
      })
  }

  fetchStations() {
    let that = this
    if (that.state.component.type == 'sonos'){
      return fetch(Settings.HUB_API_URL + 'nuimos/' + this.props.nuimoId + '/components/' + that.state.component.id + '/nuimosonosfavs')
        .then(response => {
          if (!response.ok) throw new Error('Request failed: ' + response)
          return response.json()
        })
        .then(response => {
          that.setState({station1: response.station1})
          that.setState({station2: response.station2})
          that.setState({station3: response.station3})
        })
    }
  }

  onDeviceSelectionChanged(device, selected) {
    devices = this.state.devices.map((d) => {
      if (d.id == device.id) {
        d.selected = selected
      }
      return d
    })
    this.setState({devices: devices})
  }

  save() {
    component = {}
    component.device_ids = this.state.devices
      .filter(device => device.selected)
      .map(device => device.id)
    let body = JSON.stringify(component)
    let params = {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    }
    url = Settings.HUB_API_URL + 'nuimos/' + this.props.nuimoId + '/components/' + this.state.component.id
    console.log(url)
    return fetch(url, params)
      .then(response => {
        if (!response.ok) {
          throw new Error('Saving component failed with status: ' + response.status)
        }
      })
  }

}
