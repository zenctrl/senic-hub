import React, { Component } from 'react'

class Setup extends Component {
  render() {
    return (
      <div>
        <h1>Setup</h1>
        {this.props.children}
      </div>
    );
  }
}

export default Setup
