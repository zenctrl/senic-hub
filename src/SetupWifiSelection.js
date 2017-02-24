import React, { Component } from 'react';
import { Link } from 'react-router';

import './SetupWifiSelection.css'

import nav from './nav-dots-1.png';

class SetupWifiSelection extends Component {
  ssidPollInterval = 1000
  ssidPollTimer = null

  constructor() {
    super()
    this.state = {
      ssids: []
    }
  }

  render() {
    return (
      <div className="SetupWifiSelection">
        <p>Please select your Wi-Fi network:</p>
        <table>
          <tbody>
          {
            this.state.ssids.map((name) => <tr key={name}><td><Link to={'/setup/wifi/' + name}>{name}</Link></td></tr>)
          }
          </tbody>
        </table>
        <img src={nav} role="presentation" />
      </div>
    )
  }

  componentDidMount() {
    this.pollSsids()
  }

  componentWillUnmount() {
    clearTimeout(this.ssidPollTimer)
  }

  pollSsids() {
    fetch('/-/setup/wifi')
      //TODO: Write tests for all possible API call responses, server not available, etc.
      .then((response) => response.json())
      .then((ssids) => {
        //TODO: Remove random SSID filtering
        ssids = ssids.filter(() => Math.random() > 0.2)
        this.setState({ssids: ssids})
        this.ssidPollTimer = setTimeout(this.pollSsids.bind(this), this.ssidPollInterval)
      })
  }
}

export default SetupWifiSelection
