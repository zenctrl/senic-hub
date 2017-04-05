import React, { Component } from 'react'
import { Link } from 'react-router'
import './SetupWifiConnection.css'

let log = console.log
console.log = (...args) => log(...[new Date().toLocaleTimeString(), ...args])

let Activity = {
  ENTER_WIFI_PASSWORD:               'ENTER_WIFI_PASSWORD',
  WAITING_FOR_HUB_TO_JOIN_HOME_WIFI: 'WAITING_FOR_HUB_TO_JOIN_HOME_WIFI',
  HUB_IS_CONNECTED_TO_HOME_WIFI:     'HUB_IS_CONNECTED_TO_HOME_WIFI',
  HUB_FAILED_TO_JOIN_HOME_WIFI:      'HUB_FAILED_TO_JOIN_HOME_WIFI'
}

class SetupWifiConnection extends Component {
  constructor(props) {
    super(props);
    this.state = {
      activity: Activity.ENTER_WIFI_PASSWORD,
      error: null,
      ssid: props.params.ssid,
      password: ''
    };
  }

  render() {
    return (() => {
      switch (this.state.activity) {
        case Activity.ENTER_WIFI_PASSWORD:
          return (
            <div className='SetupWifiConnection'>
              <div>Please enter the password for { this.state.ssid }</div>
              <input type="password" value={this.state.password} onChange={(event) => this.setState({password: event.target.value})} />
              <a onClick={(event) => this.setActivity(Activity.WAITING_FOR_HUB_TO_JOIN_HOME_WIFI) }>Continue</a>
            </div>
          )
        case Activity.WAITING_FOR_HUB_TO_JOIN_HOME_WIFI:
          return (
            <div className='SetupWifiConnection'>
              <div>Please wait while Senic hub tries to connect to your home Wi-Fi</div>
            </div>
          )
        case Activity.HUB_FAILED_TO_JOIN_HOME_WIFI:
          //TODO: Provide retry button that asks again for wifi password
          return (
            <div className='SetupWifiConnection'>
              <div>Your Senic Hub failed to connect to your home Wi-Fi: { this.state.error }</div>
            </div>
          )
        case Activity.HUB_IS_CONNECTED_TO_HOME_WIFI:
          return (
            <div className='SetupWifiConnection'>
              <div>Your Senic Hub is now connected to your home Wi-Fi</div>
              <Link to="setup/nuimo">Continue</Link>
            </div>
          )
        default:
          return (
            <div className='SetupWifiConnection'>
              <div>TODO: Provide support to user for this unexpected state!</div>
            </div>
          )
        }
      })()
  }

  setActivity(activity, error=null) {
    //TODO: Stop state machine if component isn't mounted any longer? I.e. early exit.
    console.log('SET ACTIVITY:', activity, 'ERROR:', error)
    switch (activity) {
      case Activity.ENTER_WIFI_PASSWORD:
        break
      case Activity.WAITING_FOR_HUB_TO_JOIN_HOME_WIFI:
        postWifiCredentials(this.state.ssid, this.state.password)
          .then(() => this.setActivity(Activity.HUB_IS_CONNECTED_TO_HOME_WIFI))
          .catch((error) => this.setActivity(Activity.HUB_FAILED_TO_JOIN_HOME_WIFI, error))
        break
      case Activity.HUB_FAILED_TO_JOIN_HOME_WIFI:
        break
      case Activity.HUB_IS_CONNECTED_TO_HOME_WIFI:
        break
      default:
        console.error('Unexpected activity requested: ' + activity)
        break
    }
    this.setState({ activity: activity, error: String(error) })
  }
}

function postWifiCredentials(ssid, password) {
  /*
    Returns a promise that
    - resolves if response code is 200
    - otherwise rejects if response code != 200
    - rejects if request isn't responded within time limit
  */
  let request = fetch('/-/setup/wifi/connection', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 'ssid': ssid, 'password': password })
    })
    .then((response) => { if (!response.ok) throw new Error('not-ok') })
  let requestTimeout = new Promise((resolve, reject) => setTimeout(resolve, 60000))
  return Promise.race([request, requestTimeout])
}

function getWifiConnection(timeout) {
  let request = fetch('/-/setup/wifi/connection')
    .then((response) => { if (response.ok) { return response } else { throw new Error('not-ok') }})
    .then((response) => response.json())
    .then((response) => ({ ssid: response.ssid, status: response.status }))
  let requestTimeout = new Promise((resolve, reject) => setTimeout(() => reject(new Error('timeout')), timeout))
  return Promise.race([request, requestTimeout])
}

export default SetupWifiConnection
