import BootScreen              from './screens/BootScreen'
import AddComponentScreen      from './screens/AddComponentScreen'
import DeviceSelectionScreen   from './screens/DeviceSelectionScreen'
import sonosFavoritesScreen    from './screens/sonosFavoritesScreen'
import FeedbackScreen          from './screens/FeedbackScreen'
import SettingsScreen          from './screens/SettingsScreen'
import SetupCompletionScreen   from './screens/setup/CompletionScreen'
import SetupDevicesScreen      from './screens/setup/DevicesScreen'
import SetupHubScreen          from './screens/setup/HubScreen'
import SetupHubApiUrlScreen    from './screens/setup/HubApiUrlScreen'
import SetupNuimoScreen        from './screens/setup/NuimoScreen'
import SetupWelcomeScreen      from './screens/setup/WelcomeScreen'
import SetupWifiScreen         from './screens/setup/WifiScreen'
import SetupWifiPasswordScreen from './screens/setup/WifiPasswordScreen'
import NuimosMenuScreen        from './screens/NuimosMenuScreen'
import BluetoothConnectionFailureScreen from './screens/BluetoothConnectionFailureScreen'

import { Navigation } from 'react-native-navigation'

Navigation.registerComponent('bootScreen',               () => BootScreen)
Navigation.registerComponent('addComponentScreen',       () => AddComponentScreen)
Navigation.registerComponent('deviceSelectionScreen',    () => DeviceSelectionScreen)
Navigation.registerComponent('sonosFavoritesScreen',     () => sonosFavoritesScreen)
Navigation.registerComponent('nuimosMenuScreen',         () => NuimosMenuScreen)
Navigation.registerComponent('feedbackScreen',           () => FeedbackScreen)
Navigation.registerComponent('settingsScreen',           () => SettingsScreen)
Navigation.registerComponent('setupCompletionScreen',    () => SetupCompletionScreen)
Navigation.registerComponent('setupDevicesScreen',       () => SetupDevicesScreen)
Navigation.registerComponent('setupHubScreen',           () => SetupHubScreen)
Navigation.registerComponent('setupHubApiUrlScreen',     () => SetupHubApiUrlScreen)
Navigation.registerComponent('setupNuimoScreen',         () => SetupNuimoScreen)
Navigation.registerComponent('setupWelcomeScreen',       () => SetupWelcomeScreen)
Navigation.registerComponent('setupWifiScreen',          () => SetupWifiScreen)
Navigation.registerComponent('setupWifiPasswordScreen',  () => SetupWifiPasswordScreen)
Navigation.registerComponent('bluetoothConnectionFailureScreen', () => BluetoothConnectionFailureScreen)

// For more info on wix/react-native-navigation, check out: https://github.com/wix/react-native-navigation/issues/657

Navigation.startSingleScreenApp({
  screen: {
    screen: 'bootScreen',
  }
})
