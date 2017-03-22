import React, { Component } from 'react'
import ReactCSSTransitionGroup from 'react-addons-css-transition-group'
import { Link } from 'react-router'

import './SetupDevices.css'

class SetupDevices extends Component {
  devicesPollInterval = 5000  // 5 seconds
  devicesPollTimer = null

  constructor() {
    super()
    this.state = {
      devices: []
    }
  }

  render() {
    return (
      <div className="SetupDevices">
        <p>We're now looking for your smart devices</p>
        <table>
          <ReactCSSTransitionGroup component="tbody" transitionName="SetupDevices_Transition" transitionEnterTimeout={500}>
          {
            this.state.devices.map((device) =>
              <tr key={device.id}>
                <td>
                  { device.name }
                  { device.authenticationRequired && (device.authenticated ? ' - Authenticated' : ' - Not Authenticated') }
                </td>
              </tr>
            )
          }
          </ReactCSSTransitionGroup>
        </table>
        <Link to="setup/completed">Continue</Link>
      </div>
    )
  }

  componentDidMount() {
    this.pollDevices()
  }

  componentWillUnmount() {
    if (this.devicesPollTimer) {
      clearTimeout(this.devicesPollTimer)
    }
  }

  pollDevices() {
    //TODO: Promise chain doesn't get cancelled when component unmounts
    fetch('/-/setup/devices')
      //TODO: Write tests for all possible API call responses, server not available, etc.
      .then((response) => response.json())
      .then((devices) => {
        this.setState({ devices: devices })
        devices
          .filter((device) => device.authenticationRequired && !device.authenticated)
          .forEach((device) => this.authenticateDevice(device))

          this.devicesPollTimer = setTimeout(this.pollDevices.bind(this), this.devicesPollInterval)
      })
      .catch((error) => console.error(error))
  }

  authenticateDevice(device) {
    fetch('/-/setup/devices/' + device.id + '/authenticate', {method: 'POST'})
      .then((response) => response.json())
      .then((response) => {
        let i = this.state.devices.findIndex((d) => d.id == device.id)
        this.state.devices[i].authenticated = response.authenticated
        this.setState({ devices: this.state.devices })
      })
  }
}

export default SetupDevices
