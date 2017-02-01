import React, { Component } from 'react';

class WifiPassword extends Component {
  render() {
    return (
      <div>
        <div>Please enter the password for { this.props.params.ssid }</div>
        <input type="password" />
      </div>
    )
  }
}

export default WifiPassword
