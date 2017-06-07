import BootScreen from './components/BootScreen';
import SetupWelcome from './components/SetupWelcome';
import SetupNuimo from './components/SetupNuimo';
import SetupDevices from './components/SetupDevices';
import SetupCompletion from './components/SetupCompletion';
import NuimoComponents from './components/NuimoComponents'
import DeviceSelection from './components/DeviceSelection'
import AddComponent from './components/AddComponent'
import SelectComponentDevices from './components/SelectComponentDevices'
import SetupHub from './components/SetupHub'
import SetupWifi from './components/SetupWifi'
import SetupWifiPassword from './components/SetupWifiPassword'

import { Navigation } from 'react-native-navigation';

Navigation.registerComponent('app.addComponent', () => AddComponent);
Navigation.registerComponent('app.deviceSelection', () => DeviceSelection);
Navigation.registerComponent('app.nuimoComponents', () => NuimoComponents);
Navigation.registerComponent('app.selectComponentDevices', () => SelectComponentDevices);
Navigation.registerComponent('setup.boot', () => BootScreen);
Navigation.registerComponent('setup.completion', () => SetupCompletion);
Navigation.registerComponent('setup.devices', () => SetupDevices);
Navigation.registerComponent('setup.nuimo', () => SetupNuimo);
Navigation.registerComponent('setup.welcome', () => SetupWelcome);
Navigation.registerComponent('setup.hub', () => SetupHub)
Navigation.registerComponent('setup.wifi', () => SetupWifi)
Navigation.registerComponent('setup.wifiPassword', () => SetupWifiPassword)

// For more info on wix/react-native-navigation, check out: https://github.com/wix/react-native-navigation/issues/657

Navigation.startSingleScreenApp({
  screen: {
    screen: 'setup.boot',
  }
})
