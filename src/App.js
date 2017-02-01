import React, { Component } from 'react'
import { Router, Route, hashHistory } from 'react-router'
import './App.css'
import Onboarding from './Onboarding'
import WifiPassword from './WifiPassword'
import WifiSelection from './WifiSelection'

class App extends Component {
  render() {
    //TODO: Use `browserHistory` instead of `hashHistory`, see also https://github.com/ReactTraining/react-router/blob/master/docs/guides/Histories.md#browserhistory
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
