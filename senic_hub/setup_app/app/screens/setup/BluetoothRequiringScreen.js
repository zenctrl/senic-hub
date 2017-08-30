import React from 'react';

import HubOnboarding from '../../lib/HubOnboarding'
import BaseScreen from '../BaseScreen';


export default class BluetoothRequiringScreen extends BaseScreen {

  didAppear() {
    HubOnboarding.hubDevice.onDisconnected = (error) => {
      if (error) {
        this.resetTo('bluetoothConnectionFailureScreen')
      }
    }
  }

  willDisappear() {
    HubOnboarding.hubDevice.onDisconnected = null
  }
}
