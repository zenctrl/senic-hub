import AddComponent from './components/AddComponent'
import BootScreen from './components/BootScreen'
import DeviceSelection from './components/DeviceSelection'
import FeedbackScreen from './components/FeedbackScreen'
import NuimoComponents from './components/NuimoComponents'
import SelectComponentDevices from './components/SelectComponentDevices'
import SettingsScreen from './components/Settings'
import SetupCompletion from './components/SetupCompletion'
import SetupDevices from './components/SetupDevices'
import SetupHub from './components/SetupHub'
import SetupHubApiUrl from './components/SetupHubApiUrl'
import SetupNuimo from './components/SetupNuimo'
import SetupWelcome from './components/SetupWelcome'
import SetupWifi from './components/SetupWifi'
import SetupWifiPassword from './components/SetupWifiPassword'

import { Navigation } from 'react-native-navigation'

Navigation.registerComponent('app.addComponent', () => AddComponent)
Navigation.registerComponent('app.deviceSelection', () => DeviceSelection)
Navigation.registerComponent('app.nuimoComponents', () => NuimoComponents)
Navigation.registerComponent('app.selectComponentDevices', () => SelectComponentDevices)
Navigation.registerComponent('feedback', () => FeedbackScreen)
Navigation.registerComponent('settings', () => SettingsScreen)
Navigation.registerComponent('setup.boot', () => BootScreen)
Navigation.registerComponent('setup.completion', () => SetupCompletion)
Navigation.registerComponent('setup.devices', () => SetupDevices)
Navigation.registerComponent('setup.hub', () => SetupHub)
Navigation.registerComponent('setup.hubApiUrl', () => SetupHubApiUrl)
Navigation.registerComponent('setup.nuimo', () => SetupNuimo)
Navigation.registerComponent('setup.welcome', () => SetupWelcome)
Navigation.registerComponent('setup.wifi', () => SetupWifi)
Navigation.registerComponent('setup.wifiPassword', () => SetupWifiPassword)

// For more info on wix/react-native-navigation, check out: https://github.com/wix/react-native-navigation/issues/657

Navigation.startSingleScreenApp({
  screen: {
    screen: 'setup.boot',
  }
})
