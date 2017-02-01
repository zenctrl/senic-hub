import React, { Component } from 'react'
import { Router, Route, hashHistory } from 'react-router'
import './App.css'
import Onboarding from './Onboarding'
import OnboardingWelcome from './OnboardingWelcome'
import WifiPassword from './WifiPassword'
import WifiSelection from './WifiSelection'

class App extends Component {
  render() {
    //TODO: Use `browserHistory` instead of `hashHistory`, see also https://github.com/ReactTraining/react-router/blob/master/docs/guides/Histories.md#browserhistory
    return (
      <div className="App">
        <Router history={hashHistory}>
          <Route path='setup' component={Onboarding}>
            <Route path='welcome' component={OnboardingWelcome} />
            <Route path='wifi' component={WifiSelection} />
            <Route path='wifi/:ssid' component={WifiPassword} />
          </Route>
        </Router>
      </div>
    );
  }
}

export default App;
