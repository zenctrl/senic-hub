import React, { Component } from 'react'
import { Router, Route, hashHistory, browserHistory } from 'react-router'
import './App.css'
import Onboarding from './Onboarding'
import WifiPassword from './WifiPassword'
import WifiSelection from './WifiSelection'

class App extends Component {
  render() {
    return (
      <div className="App">
        <Router history={hashHistory}>
          <Route path='setup' component={Onboarding}>
            <Route path='wifi-selection' component={WifiSelection} />
            <Route path='wifi-selection/:ssid' component={WifiPassword} />
          </Route>
        </Router>
      </div>
    );
  }
}

export default App;
