import React, { Component } from 'react'

import './SetupTutorialVideo.css'

import video from './SetupTutorialVideo.mp4';

class SetupTutorialVideo extends Component {
  render() {
    return (
      <div className="SetupTutorialVideo">
        <video autoPlay="true" loop="true">
          <source type="video/mp4" src={video} />
        </video>
      </div>
    );
  }
}

export default SetupTutorialVideo
