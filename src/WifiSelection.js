import React, { Component } from 'react';

class WifiSelection extends Component {
  ssidPollInterval = 1000
  ssidPollTimer = 0

  constructor() {
    super()
    this.state = {
      ssids: []
    }
  }

  render() {
    return (
      <div>
        Please select your Wi-Fi network:
        <table>
        {
          this.state.ssids.map((name) => <tr key={name}>{name}</tr>)
        }
        </table>
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
    console.log('poll')
    let ssids = ['WIFI-1', 'WIFI-2', 'WIFI-3', 'WIFI-4', 'WIFI-5'].filter(() => Math.random() > 0.2)
    this.setState({ssids: ssids})
    this.ssidPollTimer = setTimeout(this.pollSsids.bind(this), this.ssidPollInterval)
  }
}

export default WifiSelection
