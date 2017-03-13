import React, { Component } from 'react'
import { Link } from 'react-router'

import './SetupCompletion.css'

class SetupCompletion extends Component {
  render() {
    return (
      <div className="SetupCompletion">
        <p>You're all set</p>
        <p>Your smart home is now ready to use</p>
        <Link to="setup/tutorial">Watch tutorial</Link>
      </div>
    );
  }

  componentDidMount() {
    fetch('/-/setup/config', {method: 'POST'})
  }
}

export default SetupCompletion
