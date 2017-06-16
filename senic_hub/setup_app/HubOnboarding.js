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
  DNS_NAME: 'FBE51526-B3E6-4F68-B6DA-410C0BBA1A78',
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
    console.log("Hub: instance created for " + device.id + " - " + device.name)
    this.device = device
    this.connectionState = WifiConnectionState.CONNECTION_STATE_UNKNOWN
    this.currentSsid = ''
    this.dnsName = ''
    this.version = ''
    this.lastSsidSent = ''
    this.lastPasswordSent = ''
    this.networksChangedCallback = () => {}
    this.connectionStateChangedCallback = () => {}
    // TODO add a way to unsubscribe from notifications
    this.availableNetworksSubscription = null
    this.connectionStateSubscription = null
  }

  connect() {
    console.log("Hub: connecting")
    return this.device
      .connect()
      .then(device => {
        console.log("Hub: discovering services and characteristics")
        return device.discoverAllServicesAndCharacteristics()
      })
      .then(device => {
        console.log("Hub: setting up notifications")
        return this._setupNotifications()
      })
      .then(() => {
        console.log("Hub: connected")
        this._retrieveInitialValues()
      })
      .catch(error => {
        console.log("Hub: error while trying to connect: " + error.message)
        if (retry) {
          console.log("Hub: trying again to connect")
          return this.connect(retry=false)
        }
      })
  }

  disconnect() {
    console.log("Hub: disconnecting")
    this.device.cancelConnection().then((device) => {
      console.log("Hub: disconnected successful")
    })
  }

  /** callback(availableNetworks: String) */
  onNetworksChanged(callback) {
    this.networksChangedCallback = callback
  }

  /** callback(connectionState: Integer, currentSsid: String) */
  onConnectionStateChanged(callback) {
    this.connectionStateChangedCallback = callback
  }

  sendSsid(ssid) {
    console.log("Hubs: sending SSID: " + ssid)
    return this.device
      .writeCharacteristicWithResponseForService(
        OnboardingUuids.SERVICE,
        OnboardingUuids.SSID,
        base64.encode(ssid))
      .then(() => {
        this.lastSsidSent = ssid
      })
  }

  sendPassword(password) {
    console.log("Hub: sending password: " + password)
    return this.device
      .writeCharacteristicWithResponseForService(
        OnboardingUuids.SERVICE,
        OnboardingUuids.CREDENTIALS,
        base64.encode(password))
      .then(() => {
        this.lastPasswordSent = password
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
    console.log("Hub: retrieving initial values")
    this.device.readCharacteristicForService(OnboardingUuids.SERVICE, OnboardingUuids.CONNECTION_STATE)
      .then((characteristic) => { this._updateConnectionState(null, characteristic) })
      .catch(error => console.log("Hub: read connection state error: " + error.message))
    this.device.readCharacteristicForService(OnboardingUuids.SERVICE, OnboardingUuids.DNS_NAME)
      .then((characteristic) => { this._updateDnsName(null, characteristic) })
      .catch(error => console.log("Hub: read dns name error: " + error.message))
    this.device.readCharacteristicForService(OnboardingUuids.SERVICE, OnboardingUuids.VERSION)
      .then((characteristic) => { this._updateVersion(null, characteristic) })
      .catch(error => console.log("Hub: read version error: " + error.message))
  }

  _updateAvailableNetworks(error, characteristic) {
    if (error) {
      console.log("Hub: error from networks chrc: " + error.message)
      return
    }
    let ssid = base64.decode(characteristic.value)

    this.networksChangedCallback(ssid)
  }

  _updateConnectionState(error, characteristic) {
    if (error) {
      console.log("Hub: error from connection state chrc: " + error.message)
      return
    }
    if (characteristic.value.length < 4) {
      console.log("Hub: received empty connection state.")
      return;
    }
    let rawState = base64.decode(characteristic.value)
    this.connectionState = rawState.charCodeAt(0)
    if (this.connectionState > 1 && rawState.length > 1) {
      this.currentSsid = rawState.slice(1)
      console.log("Hub: received connection state: " + this.getConnectionStateString() + " to " + this.currentSsid)
    }
    else {
      this.currentSsid = ''
      console.log("Hub: received connection state: " + this.getConnectionStateString())
    }

    this.connectionStateChangedCallback(this.connectionState, this.currentSsid)
  }

  _updateDnsName(error, characteristic) {
    if (error) {
      console.log("Hub: error from DNS name chrc: " + error.message)
      return
    }
    this.dnsName = base64.decode(characteristic.value)
  }

  _updateVersion(error, characteristic) {
    if (error) {
      console.log("Hub: error from version chrc: " + error.message)
      return
    }
    this.version = base64.decode(characteristic.value)
  }

}
