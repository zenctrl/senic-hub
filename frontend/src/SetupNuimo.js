import React, { Component } from 'react';
import { Link } from 'react-router';

import './SetupNuimo.css'

class SetupNuimo extends Component {
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
    this.bootstrapNuimos()
  }

  bootstrapNuimos() {
    //TODO: Promise chain doesn't get cancelled when component unmounts
    //TODO: Write tests for all possible API call responses, server not available, etc.
    fetch('/-/setup/nuimo/bootstrap', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({})
    })
      .then((response) => response.json())
      .then((response) => {
        let controllers = response.connectedControllers
        if (controllers.length > 0) {
          this.setState({ nuimos: controllers[0] })
        }
        else {
          // Try again to bootstrap
          this.bootstrapNuimos()
        }
      })
      .catch((error) => {
        console.error(error)
        // Try again to bootstrap
        //TODO: Only retry after a few seconds after an error occurred. Cancel timer if component unmounted.
        this.bootstrapNuimos()
      })
  }
}

export default SetupNuimo
