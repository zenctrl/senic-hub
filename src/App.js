import React, { Component } from 'react'
import { Router, Route, hashHistory } from 'react-router'
import './App.css'
import Setup              from './Setup'
import SetupWelcome       from './SetupWelcome'
import SetupWifiPassword  from './SetupWifiPassword'
import SetupWifiSelection from './SetupWifiSelection'
import SetupNuimo         from './SetupNuimo'
import SetupDevices       from './SetupDevices'
import SetupCompletion    from './SetupCompletion'
import SetupTutorialVideo from './SetupTutorialVideo'

class App extends Component {
  render() {
    //TODO: Use `browserHistory` instead of `hashHistory`, see also https://github.com/ReactTraining/react-router/blob/master/docs/guides/Histories.md#browserhistory
    return (
      <div className="App">
        <Router history={hashHistory}>
          <Route path='setup' component={Setup}>
            <Route path='welcome' component={SetupWelcome} />
            <Route path='wifi' component={SetupWifiSelection} />
            <Route path='wifi/:ssid' component={SetupWifiPassword} />
            <Route path='nuimo' component={SetupNuimo} />
            <Route path='devices' component={SetupDevices} />
            <Route path='completed' component={SetupCompletion} />
            <Route path='tutorial' component={SetupTutorialVideo} />
          </Route>
        </Router>
      </div>
    );
  }
}

export default App
