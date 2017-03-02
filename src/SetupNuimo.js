import React, { Component } from 'react';
import { Link } from 'react-router';

import './SetupNuimo.css'

class SetupNuimo extends Component {
  nuimoPollInterval = 1000
  nuimoPollTimer = null

  constructor() {
    super()
    this.state = {
      nuimos: []
    }
  }

  render() {
    return (
      <div className="SetupNuimo">
        <p>We're now looking for your Nuimo</p>
        {
          this.state.nuimos.length === 0
            ? <div className="SetupNuimo_Progress" />
            : [
                <svg key="1" className="SetupNuimo_Success" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                  <circle cx="26" cy="26" r="25" fill="none"/>
                  <path fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>,
                <Link key="2" to="setup/devices">Continue</Link>
              ]
        }
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
    //TODO: Promise chain doesn't get cancelled when component unmounts
    fetch('/-/setup/nuimo')
      //TODO: Write tests for all possible API call responses, server not available, etc.
      .then((response) => response.json())
      .then((nuimos) => {
        this.setState({ nuimos: nuimos })
        this.nuimoPollTimer = setTimeout(this.pollNuimos.bind(this), this.nuimoPollInterval)
      })
  }
}

export default SetupNuimo
