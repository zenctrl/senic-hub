import React, { Component } from 'react'
import { Link } from 'react-router';
import './SetupWelcome.css'

class SetupWelcome extends Component {
  render() {
    return (
      <div className="SetupWelcome">
        <p>Welcome to Nuimo Hub. Press "continue" to continue :)</p>
        <Link to="setup/wifi">Continue</Link>
      </div>
    );
  }
}

export default SetupWelcome
