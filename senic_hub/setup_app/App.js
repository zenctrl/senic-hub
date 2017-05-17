import { AppRegistry } from 'react-native';
import { StackNavigator } from 'react-navigation';

import SetupWelcome from './components/SetupWelcome';
import SetupNuimo from './components/SetupNuimo';
import SetupDevices from './components/SetupDevices';
import SetupCompletion from './components/SetupCompletion';

const SenicHubSetup = StackNavigator({
    Welcome: { screen: SetupWelcome },
    Nuimo: { screen: SetupNuimo },
    Devices: { screen: SetupDevices },
    Completion: { screen: SetupCompletion },
});

AppRegistry.registerComponent('SenicHubSetup', () => SenicHubSetup);
