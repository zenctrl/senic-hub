import React, { Component } from 'react';

class WifiPassword extends Component {
  render() {
    return (
      <div>
        <div>Please enter your Wi-Fi password</div>
        <div>Wi-Fi network: { this.props.params.ssid }</div>
        <input type="password" />
      </div>
    )
  }
}

export default WifiPassword
