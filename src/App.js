import React, { Component } from 'react'
import { Router, Route, Link, IndexRoute, hashHistory, browserHistory } from 'react-router'
import './App.css'
import WifiPassword from './WifiPassword'
import WifiSelection from './WifiSelection'

class App extends Component {
  render() {
    return (
      <div className="App">
        <Router history={hashHistory}>
	        <Route path='/setup/wifi-selection' component={WifiSelection} />
	        <Route path='/setup/wifi-selection/:ssid' component={WifiPassword} />
	      </Router>
      </div>
    );
  }
}

export default App;
