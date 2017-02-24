import React, { Component } from 'react'
import { Link } from 'react-router';

class SetupWelcome extends Component {
  render() {
    return (
      <div>
        <p>Welcome to Nuimo Hub. Press "continue" to continue :)</p>
        <Link to="setup/wifi">Continue</Link>
      </div>
    );
  }
}

export default SetupWelcome
