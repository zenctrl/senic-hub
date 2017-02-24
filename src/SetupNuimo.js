import React, { Component } from 'react';
import { Link } from 'react-router';

import './SetupNuimo.css'

class SetupNuimo extends Component {
  nuimoPollInterval = 1000
  nuimoPollTimer = 0

  constructor() {
    super()
    this.state = {
      nuimos: []
    }
  }

  render() {
    return (
      <div className="SetupNuimo">
        <p>Were now looking for your Nuimo</p>
        <p>Number of Nuimos found: { this.state.nuimos.length }</p>
      </div>
    )
  }

  componentDidMount() {
    this.pollNuimos()
  }

  componentWillUnmount() {
    clearTimeout(this.nuimoPollTimer)
  }

  pollNuimos() {
    fetch('/-/setup/nuimo')
      //TODO: Write tests for all possible API call responses, server not available, etc.
      .then((response) => response.json())
      .then((nuimos) => {
        console.log(nuimos)
        this.setState({ nuimos: nuimos })
        this.nuimoPollTimer = setTimeout(this.pollNuimos.bind(this), this.nuimoPollInterval)
      })
  }
}

export default SetupNuimo
