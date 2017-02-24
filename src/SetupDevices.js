import React, { Component } from 'react';
import { Link } from 'react-router';

import './SetupDevices.css'

class SetupDevices extends Component {
  devicesPollInterval = 1000
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
          <tbody>
          {
            this.state.devices.map((device, index) => <tr key={index}><td>{ device.label }</td></tr>)
          }
          </tbody>
        </table>
        <Link to="setup/completed">Continue</Link>
      </div>
    )
  }

  componentDidMount() {
    this.pollDevices()
  }

  componentWillUnmount() {
    clearTimeout(this.devicesPollTimer)
  }

  pollDevices() {
    //TODO: Promise chain doesn't get cancelled when component unmounts
    fetch('/-/setup/devices')
      //TODO: Write tests for all possible API call responses, server not available, etc.
      .then((response) => response.json())
      .then((devices) => {
        this.setState({ devices: devices })
        this.devicesPollTimer = setTimeout(this.pollDevices.bind(this), this.devicesPollInterval)
      })
  }
}

export default SetupDevices
