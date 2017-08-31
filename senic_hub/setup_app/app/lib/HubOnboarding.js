import base64 from 'base-64'
import { Device as BleDevice } from 'react-native-ble-plx';


export const WifiConnectionState = {
  CONNECTION_STATE_UNKNOWN: -1,
  CONNECTION_STATE_DOWN: 0,
  CONNECTION_STATE_DISCONNECTED: 1,
  CONNECTION_STATE_CONNECTING: 2,
  CONNECTION_STATE_CONNECTED: 3,
}

const OnboardingUuids = {
  SERVICE: 'FBE51523-B3E6-4F68-B6DA-410C0BBA1A78',

  AVAILABLE_NETWORKS: 'FBE51524-B3E6-4F68-B6DA-410C0BBA1A78',
  CONNECTION_STATE: 'FBE51525-B3E6-4F68-B6DA-410C0BBA1A78',
  API_URL: 'FBE51526-B3E6-4F68-B6DA-410C0BBA1A78',
  VERSION: 'FBE51527-B3E6-4F68-B6DA-410C0BBA1A78',

  SSID: 'FBE51528-B3E6-4F68-B6DA-410C0BBA1A78',
  CREDENTIALS: 'FBE51529-B3E6-4F68-B6DA-410C0BBA1A78'
};

export default class HubOnboarding {

  // holds reference to the Hub device object that is currently being onboarded
  static hubDevice = null

  static isHub(device) {
    if (!(device instanceof BleDevice)) return false
    if (!device.serviceUUIDs) return false
    // check if hub service is in advertised services of this device:
    console.log('advertised services', device.serviceUUIDs)
    return device.serviceUUIDs.findIndex(uuid => OnboardingUuids.SERVICE.toLowerCase() === uuid.toLowerCase()) !== -1
  }

  constructor(device) {
    console.log("Hub Bluetooth: instance created for " + device.id + " - " + device.name)
    this.device = device
    this.connectionState = WifiConnectionState.CONNECTION_STATE_UNKNOWN
    this.currentSsid = ''
    this.version = ''
    this.networksChangedCallback = () => {}
    this.onConnectionStateChanged = null
    this.onDisconnected = null  // callback in the form of 'function(error)'
    // TODO add a way to unsubscribe from notifications
    this.availableNetworksSubscription = null
    this.connectionStateSubscription = null

    this.onDisconnectedSubscription = this.device.onDisconnected((error, device) => {
        if (error) {
          console.log("Hub Bluetooth: disconnected: " + error.message)
        }
        if (this.onDisconnected) {
          this.onDisconnected(error)
        }
      }
    )
  }

  connect(retry = true) {
    console.log("Hub Bluetooth: connecting...")
    return this.device
      .connect()
      .then(device => {
        console.log("Hub Bluetooth: discovering services and characteristics")
        return device.discoverAllServicesAndCharacteristics()
      })
      .then(device => {
        console.log("Hub Bluetooth: setting up notifications")
        return this._setupNotifications()
      })
      .then(() => {
        console.log("Hub Bluetooth: connected")
        this._retrieveInitialValues()
      })
      .catch(error => {
        console.log("Hub Bluetooth: error while trying to connect: " + error.message)
        if (retry) {
          console.log("Hub Bluetooth: trying again to connect")
          return this.connect(retry=false)
        }
      })
  }

  disconnect() {
    return this.device.isConnected()
      .then(connected => {
        if (!connected) {
          return Promise.resolve()
        }
        console.log("Hub Bluetooth: disconnecting...")
        if (this.availableNetworksSubscription) {
          this.availableNetworksSubscription.remove()
          this.availableNetworksSubscription = null
        }
        if (this.connectionStateSubscription) {
          this.connectionStateSubscription.remove()
          this.connectionStateSubscription = null
        }
        return this.device.cancelConnection()
          .then(device => {
            console.log("Hub Bluetooth: disconnected")
          })
          .catch(error => {
            console.log("Hub Bluetooth: disconnect failed with error: " + error)
            throw error
          })
      })
  }

  /** callback(availableNetworks: String) */
  onNetworksChanged(callback) {
    this.networksChangedCallback = callback
  }

  joinWifi(ssid, password) {
    return this.device
      .writeCharacteristicWithResponseForService(OnboardingUuids.SERVICE, OnboardingUuids.SSID, base64.encode(ssid))
      .then(() => this.device.writeCharacteristicWithResponseForService(OnboardingUuids.SERVICE, OnboardingUuids.CREDENTIALS, base64.encode(password)))
      .then(() => {
        let that = this
        return new Promise(function(resolve, reject) {
          that.onConnectionStateChanged = (connectionState, currentSsid) => {
            console.log("ssid:", currentSsid, "state:", connectionState)
            if (connectionState == WifiConnectionState.CONNECTION_STATE_CONNECTED) {
              that.onConnectionStateChanged = null
              resolve()
            }
            else if (connectionState == WifiConnectionState.CONNECTION_STATE_DISCONNECTED) {
              that.onConnectionStateChanged = null
              reject(new Error("Failed to connect to wifi network"))
            }
          }
        })
      })
      .then(() => this.readApiUrl())
  }

  readApiUrl() {
    return this.device.readCharacteristicForService(OnboardingUuids.SERVICE, OnboardingUuids.API_URL)
      .then((characteristic) => {
        let apiUrl = base64.decode(characteristic.value)
        if (!apiUrl) {
          throw new Error("Failed to retrieve hub's API URL")
        }
        return apiUrl
      })
  }

  getConnectionStateString() {
    if (this.connectionState === WifiConnectionState.CONNECTION_STATE_DOWN) {
      return "down"
    } else if (this.connectionState === WifiConnectionState.CONNECTION_STATE_DISCONNECTED) {
      return "disconnected"
    } else if (this.connectionState === WifiConnectionState.CONNECTION_STATE_CONNECTING) {
      return "connecting"
    } else if (this.connectionState === WifiConnectionState.CONNECTION_STATE_CONNECTED) {
      return "connected"
    } else {
      return "unknown"
    }
  }

  async _setupNotifications() {
    this.availableNetworksSubscription = this.device.monitorCharacteristicForService(
      OnboardingUuids.SERVICE, OnboardingUuids.AVAILABLE_NETWORKS,
      (error, characteristic) => { this._updateAvailableNetworks(error, characteristic) })

    this.connectionStateSubscription = this.device.monitorCharacteristicForService(
      OnboardingUuids.SERVICE, OnboardingUuids.CONNECTION_STATE,
      (error, characteristic) => { this._updateConnectionState(error, characteristic) })
  }

  _retrieveInitialValues() {
    console.log("Hub Bluetooth: retrieving initial values")
    return this.device
      .readCharacteristicForService(OnboardingUuids.SERVICE, OnboardingUuids.CONNECTION_STATE)
      .then((characteristic) => this._updateConnectionState(null, characteristic))
      .then(() => this.device.readCharacteristicForService(OnboardingUuids.SERVICE, OnboardingUuids.VERSION))
      .then((characteristic) => this._updateVersion(null, characteristic))
      .catch(error => console.log("Hub: reading initial values failed: " + error.message))
  }

  _updateAvailableNetworks(error, characteristic) {
    if (error) {
      console.log("Hub Bluetooth: error from wifi networks chrc: " + error.message)
      return
    }
    let ssid = base64.decode(characteristic.value)

    this.networksChangedCallback(ssid)
  }

  _updateConnectionState(error, characteristic) {
    if (error) {
      console.log("Hub Bluetooth: error from wifi connection state chrc: " + error.message)
      return
    }
    if (characteristic.value.length < 4) {
      console.log("Hub Bluetooth: received empty wifi connection state.")
      return;
    }
    let rawState = base64.decode(characteristic.value)
    this.connectionState = rawState.charCodeAt(0)
    if (this.connectionState > 1 && rawState.length > 1) {
      this.currentSsid = rawState.slice(1)
      console.log("Hub Bluetooth: received wifi connection state: " + this.getConnectionStateString() + " to " + this.currentSsid)
    }
    else {
      this.currentSsid = ''
      console.log("Hub Bluetooth: received wifi connection state: " + this.getConnectionStateString())
    }

    if (this.onConnectionStateChanged) {
      this.onConnectionStateChanged(this.connectionState, this.currentSsid)
    }
  }

  _updateVersion(error, characteristic) {
    if (error) {
      console.log("Hub: error from version chrc: " + error.message)
      return
    }
    this.version = base64.decode(characteristic.value)
  }

}
