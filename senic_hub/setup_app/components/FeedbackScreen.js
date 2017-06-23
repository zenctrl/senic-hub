import React from 'react';
import {
    StyleSheet,
    View,
    WebView,
} from 'react-native';

import Screen from './Screen';


export default class FeedbackScreen extends Screen {
  constructor(props) {
    super(props)

    this.setTitle("Send Feedback")
  }

  render() {
    //TODO: Add app's version to `app` query parameter
    return (
      <View style={styles.container}>
        <WebView source={{uri: 'https://www.senic.com/nuimo-app-feedback?app=Senic%20Hub%20App'}} />
      </View>
    );
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: 10,
  },
})
