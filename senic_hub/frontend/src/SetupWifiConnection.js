import React, { Component } from 'react';
import './SetupWifiConnection.css'

let Activity = {
  ENTER_WIFI_PASSWORD: 'ENTER_WIFI_PASSWORD',
  HUB_IS_JOINING_HOME_WIFI: 'HUB_IS_JOINING_HOME_WIFI'
}

class SetupWifiConnection extends Component {
  constructor(props) {
    super(props);
    this.state = {
      activity: Activity.ENTER_WIFI_PASSWORD,
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
              <input type="password" value={this.state.password} onChange={this.onPasswordChange.bind(this)} />
              <a href="#" onClick={this.joinHomeWifi.bind(this)}>Continue</a>
            </div>
          )
        case Activity.HUB_IS_JOINING_HOME_WIFI:
          return (
            <div className='SetupWifiConnection'>
              <div>Senic Hub is now joining your WiFi network </div>
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

  onPasswordChange(event) {
    this.setState({password: event.target.value})
  }

  joinHomeWifi(event) {
    let postBody = {
      'ssid':     this.props.params.ssid,
      'password': this.state.password,
      //TODO: Remove following line as soon as it isn't required any longer
      'device':   'wlan0'
    }
    //TODO: Handle all error cases
    fetch('/-/setup/wifi', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(postBody)
    })
      .then((response) => response.json())
      .then((json) => this.props.router.push('/setup/nuimo'))
      .catch((error) => console.error(error))
    event.preventDefault()
  }
}

export default SetupWifiConnection
