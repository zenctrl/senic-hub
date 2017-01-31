import React, { Component } from 'react'
import './App.css'
import WifiPassword from './WifiPassword'
import WifiSelection from './WifiSelection'

class App extends Component {
  render() {
    return (
      <div className="App">
        <WifiSelection />
        <WifiPassword ssid="WIFI-1" />
      </div>
    );
  }
}

export default App;
