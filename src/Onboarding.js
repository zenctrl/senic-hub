import React, { Component } from 'react'

class Onboarding extends Component {
  render() {
    return (
      <div>
        <h1>Onboarding</h1>
        {this.props.children}
      </div>
    );
  }
}

export default Onboarding
