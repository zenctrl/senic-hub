import React, { Component } from 'react';
import './SetupWifiPassword.css'

class SetupWifiPassword extends Component {
  constructor(props) {
    super(props);
    this.state = { password: '' };
  }

  render() {
    return (
      <div className='SetupWifiPassword'>
        <div>Please enter the password for { this.props.params.ssid }</div>
        <input type="password" value={this.state.password} onChange={this.onPasswordChange.bind(this)} />
        <a href="#" onClick={this.submitPassword.bind(this)}>Continue</a>
      </div>
    )
  }

  onPasswordChange(event) {
    this.setState({password: event.target.value})
  }

  submitPassword(event) {
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

export default SetupWifiPassword
