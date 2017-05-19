import { AppRegistry } from 'react-native';
import { StackNavigator } from 'react-navigation';

import SetupWelcome from './components/SetupWelcome';
import SetupNuimo from './components/SetupNuimo';
import SetupDevices from './components/SetupDevices';
import SetupCompletion from './components/SetupCompletion';
import NuimoComponents from './components/NuimoComponents'
import DeviceSelection from './components/DeviceSelection'
import AddComponent from './components/AddComponent'
import SelectComponentDevices from './components/SelectComponentDevices'

const SenicHubSetup = StackNavigator({
    Welcome: { screen: SetupWelcome },
    Nuimo: { screen: SetupNuimo },
    Devices: { screen: SetupDevices },
    Completion: { screen: SetupCompletion },
    NuimoComponents: { screen: NuimoComponents },
    DeviceSelection: { screen: DeviceSelection },
    AddComponent: { screen: AddComponent },
    SelectComponentDevices: { screen: SelectComponentDevices },
});

AppRegistry.registerComponent('SenicHubSetup', () => SenicHubSetup);
