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
        <div className="SetupWifiSelection_Ssids">
        {
          this.state.ssids.map((name) =>
            <Link key={name} to={'/setup/wifi/' + name}>
              { name }
            </Link>
          )
        }
        </div>
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
    //TODO: Promise chain doesn't get cancelled when component unmounts
    fetch('/-/setup/wifi')
      //TODO: Write tests for all possible API call responses, server not available, etc.
      .then((response) => response.json())
      .then((ssids) => {
        //TODO: Remove random SSID filtering
        ssids = ssids
          .filter(() => Math.random() > 0.05)
          .sort((lhs, rhs) => lhs.toLowerCase().localeCompare(rhs.toLowerCase()))
        this.setState({ssids: ssids})
        this.ssidPollTimer = setTimeout(this.pollSsids.bind(this), this.ssidPollInterval)
      })
  }
}

export default SetupWifiSelection
