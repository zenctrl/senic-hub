import React from 'react';

import HubOnboarding from '../HubOnboarding'
import Screen from './Screen';


export default class BluetoothRequiringScreen extends Screen {

  didAppear() {
    HubOnboarding.hubDevice.onDisconnected = (error) => {
      if (error) {
        this.resetTo('setup.bluetoothConnectionFailure')
      }
    }
  }

  willDisappear() {
    HubOnboarding.hubDevice.onDisconnected = null
  }
}
