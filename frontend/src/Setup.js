import React, { Component } from 'react'
import './Setup.css'

class Setup extends Component {
  render() {
    return (
      <div className='Setup'>
        <span />
        <h1>SETUP</h1>
        {this.props.children}
      </div>
    );
  }
}

export default Setup
