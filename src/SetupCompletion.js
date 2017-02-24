import React, { Component } from 'react'
import { Link } from 'react-router'

import './SetupCompletion.css'

class SetupCompletion extends Component {
  render() {
    return (
      <div className="SetupCompletion">
        <p>That was easy, he?</p>
        <Link to="setup/tutorial">Continue</Link>
      </div>
    );
  }
}

export default SetupCompletion
