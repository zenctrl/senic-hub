import React, { Component } from 'react'
import ReactCSSTransitionGroup from 'react-addons-css-transition-group'
import { Link } from 'react-router'

import './SetupDevices.css'

class SetupDevices extends Component {
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
            this.state.devices.map((device, index) =>
              <tr key={device.id}>
                <td>
                  { device.type.replace('_', ' ') }
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
    this.discoverDevices()
  }

  discoverDevices() {
    //TODO: Promise chain doesn't get cancelled when component unmounts
    fetch('/-/setup/devices/discover', {method: 'POST'})
      //TODO: Write tests for all possible API call responses, server not available, etc.
      .then((response) => response.json())
      .then((devices) => {
        this.setState({ devices: devices })
        //TODO: Run device discovery again as long as component is mounted
      })
  }
}

export default SetupDevices
