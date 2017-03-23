import React, { Component } from 'react';
import './SetupWifiConnection.css'

let log = console.log
console.log = (...args) => log(...[new Date().toLocaleTimeString(), ...args])

let Activity = {
  ENTER_WIFI_PASSWORD:               'ENTER_WIFI_PASSWORD',
  SUBMIT_WIFI_CREDENTIALS:           'SUBMIT_WIFI_CREDENTIALS',
  SUBMIT_WIFI_CREDENTIALS_FAILED:    'SUBMIT_WIFI_CREDENTIALS_FAILED',
  WAITING_FOR_HUB_TO_JOIN_HOME_WIFI: 'WAITING_FOR_HUB_TO_JOIN_HOME_WIFI',
  LOOKING_FOR_HUB_IN_HOME_WIFI:      'LOOKING_FOR_HUB_IN_HOME_WIFI',
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
      password: '',
      waitingForHubToJoinStartDate: null
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
              <a onClick={(event) => this.setActivity(Activity.SUBMIT_WIFI_CREDENTIALS) }>Continue</a>
            </div>
          )
        case Activity.SUBMIT_WIFI_CREDENTIALS:
          return (
            <div className='SetupWifiConnection'>
              <div>Sending your WiFi credentials to Senic Hub</div>
            </div>
          )
        case Activity.SUBMIT_WIFI_CREDENTIALS_FAILED:
          return (
            <div className='SetupWifiConnection'>
              <div>Senic Hub could not connect to your home WiFi: { this.state.error }</div>
            </div>
          )
        case Activity.WAITING_FOR_HUB_TO_JOIN_HOME_WIFI:
          return (
            <div className='SetupWifiConnection'>
              <div>Please wait while Senic hub tries to connect to your home Wi-Fi</div>
            </div>
          )
        case Activity.LOOKING_FOR_HUB_IN_HOME_WIFI:
          return (
            <div className='SetupWifiConnection'>
              <div>Please connect your computer back to your home Wi-Fi</div>
            </div>
          )
        case Activity.HUB_FAILED_TO_JOIN_HOME_WIFI:
          return (
            <div className='SetupWifiConnection'>
              <div>Your Senic Hub failed to connect to your home Wi-Fi: { this.state.error }</div>
            </div>
          )
        case Activity.HUB_IS_CONNECTED_TO_HOME_WIFI:
          return (
            <div className='SetupWifiConnection'>
              <div>Your Senic Hub is now connected to your home Wi-Fi</div>
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
      case Activity.SUBMIT_WIFI_CREDENTIALS:
        postWifiCredentials(this.state.ssid, this.state.password)
          .then(() => this.setActivity(Activity.WAITING_FOR_HUB_TO_JOIN_HOME_WIFI))
          .catch((error) => this.setActivity(Activity.SUBMIT_WIFI_CREDENTIALS_FAILED, error))
        break
      case Activity.SUBMIT_WIFI_CREDENTIALS_FAILED:
        break
      case Activity.WAITING_FOR_HUB_TO_JOIN_HOME_WIFI:
        // This is when we expect the user to be still connected to the adhoc
        if (this.state.activity != Activity.WAITING_FOR_HUB_TO_JOIN_HOME_WIFI) {
          this.state.waitingForHubToJoinStartDate = new Date()
        }
        else if ((new Date()).getTime() - this.state.waitingForHubToJoinStartDate.getTime() > 10000) {
          this.setActivity(Activity.LOOKING_FOR_HUB_IN_HOME_WIFI)
          break
        }
        // intentionally fall-through to next case
      case Activity.LOOKING_FOR_HUB_IN_HOME_WIFI:
        // This is when we want the user to connect her machine back to the home wifi
        getWifiConnection(1000)
          .then((connection) => {
            console.log('HUB CONNECTION: ' + JSON.stringify(connection))
            if (connection.ssid === this.state.ssid) {
              console.log('SSID OK, status=' + connection.status)
              switch (connection.status) {
                case 'connected':  this.setActivity(Activity.HUB_IS_CONNECTED_TO_HOME_WIFI); break
                case 'connecting': this.setActivity(activity); break
                default:           this.setActivity(Activity.HUB_FAILED_TO_JOIN_HOME_WIFI, 'unknown reason'); break
              }
            }
            else {
              this.setActivity(Activity.HUB_FAILED_TO_JOIN_HOME_WIFI, 'unknown reason')
            }
          })
          .catch((error) => this.setActivity(activity) /* try again */)
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
    - resolves if request times out after some seconds
      expected behavior if hub joins another network and therefor needs to shutdown adhoc network
    - resolves if response code is 200 (if hub can both open adhoc and join another network)
    - otherwise rejects if response code != 200
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
  let requestTimeout = new Promise((resolve, reject) => setTimeout(resolve, 15000))
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
