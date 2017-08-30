import React, { Component } from 'react';

export default class BaseScreen extends Component {
  constructor(props) {
    super(props)
    this.props.navigator.setOnNavigatorEvent(this.onNavigatorEvent.bind(this))
  }

  setTitle(title) {
    this.props.navigator.setTitle({
      title: title
    })
  }

  setNavigationButtons(left, right, animated = false) {
    function makeButtons(buttons) {
      return buttons.map(button => ({
        id: button.id,
        title: button.title,
        disabled: button.disabled || false,
      }))
    }

    this.props.navigator.setButtons({
      leftButtons: makeButtons(left),
      rightButtons: makeButtons(right),
      animated: animated
    })

    this.navigationButtonPressCallbacks = {}

    left.concat(right).forEach(button => this.navigationButtonPressCallbacks[button.id] = button.onPress)
  }

  pushScreen(screen, props) {
    this.props.navigator.push({screen: screen, passProps: props})
  }

  popScreen() {
    this.props.navigator.pop()
  }

  showModal(screen, props) {
    this.props.navigator.showModal({screen: screen, passProps: props})
  }

  dismissModal() {
    this.props.navigator.dismissModal()
  }

  dismissAllModals() {
    this.props.navigator.dismissAllModals()
  }

  onNavigatorEvent(event) {
    switch (event.type) {
      case 'ScreenChangedEvent':
        switch (event.id) {
          case 'willAppear':
            this.willAppear()
            break
          case 'didAppear':
            this.didAppear()
            break
          case 'willDisappear':
            this.willDisappear()
            break
          case 'didDisappear':
            this.didDisappear()
            break
        }
        break
      case 'NavBarButtonPress':
        callback = this.navigationButtonPressCallbacks[event.id]
        if (callback === undefined) {
          console.error("No touch callback for navigation button '" + event.id + "' registered")
          break
        }
        callback()
        break
    }
  }

  resetTo(screen, props) {
    this.props.navigator.resetTo({screen: screen, passProps: props})
  }

  willAppear() {}
  didAppear() {}
  willDisappear() {}
  didDisappear() {}
}
