import {
  AsyncStorage,
} from 'react-native';

export default class Settings {
  static SETTINGS_STORE_NAME = '@SettingsStore'

  // API URL including the trailing slash
  static HUB_API_URL = null

  static async getHubApiUrl() {
    return await AsyncStorage.getItem(this.SETTINGS_STORE_NAME + ':hubApiUrl')
  }

  static async setHubApiUrl(value) {
    return await AsyncStorage.setItem(this.SETTINGS_STORE_NAME + ':hubApiUrl', value)
      .then(() => this.HUB_API_URL = value)
  }

  static async resetHubApiUrl() {
    return await AsyncStorage.removeItem(this.SETTINGS_STORE_NAME + ':hubApiUrl')
      .then(() => this.HUB_API_URL = null)
  }
}
