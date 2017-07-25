============
Installation
============

1. ``brew install carthage`` (Necessary for managing iOS dependencies)
2. ``brew install watchman`` (Necessary for react packager to watch for file changes)
3. ``npm install -g react-native-cli``
4. ``npm install``
5. ``react-native run-ios`` or ``react-native run-android``. Append `--device` to run on a connected phone/tablet.

For more details refer to the React Native `getting started guide <https://facebook.github.io/react-native/docs/getting-started.html#getting-started>`_.

==================================
Publish new release using Fastlane
==================================

One time setup
==============

* Install Fabric macOS app from the `Fabric website <https://get.fabric.io/>`_
* Install Fastlane from Fabric macOS app

Android
=======

One time setup
--------------

* Save ``setupapp-release-key.keystore`` file from 1Password entry ``Software/Senic Hub Android release key`` to ``senic_hub/setup_app/android/app/`` directory
* Create a new entry in ``login`` keychain of ``application password`` kind called ``android_keystore``. Password can be copied from 1Password entry ``Software/Senic Hub Android release key``

Publish new beta app
--------------------

* Increase version code and version name in ``senic_hub/setup_app/android/app/build.gradle``
* Run ``CRASHLYTICS_BUILD_SECRET=secret_goes_here fastlane beta`` from ``senic_hub/setup_app/android`` directory. ``CRASHLYTICS_BUILD_SECRET`` is available in 1Password entry ``Software/Crashlytics Android Secret build key``

iOS
===

One time setup
--------------

* From the ``senic_hub/setup_app/ios`` directory run ``fastlane match`` to download signing certificates & profiles. You will be asked for encryption passphrase which you can find in 1Password entry ``Software/fastlane-match Git repository encryption passphrase``. You might be asked a password for Apple ID ``developers@senic.com``, it can be found in the 1Password entry ``Shared/Apple ID for developers@senic.com``.

Adding new iOS devices as beta testers
--------------------------------------

* Invite iOS user to beta test
* User needs open the beta invitation on their iOS and accept the invite
* Gather the user's iOS UDID with the `Beta section of fabric.com <https://fabric.io/senic/ios/apps/com.senic.hub.setupapp/beta/releases/latest>`_
* Add the UDID at https://developer.apple.com/account/ios/device/create
* Run ``fastlane match`` to download the latest signing and provisioning certificates
* Publish a new beta app. Make sure to increase at least build number, otherwise the user doesn't seem to get a new email invite for the new release.
* Let user install latest release from within the "Beta" app that is downloaded on their phone by following the instructions in their beta test invitation mail.

Publish new beta app
--------------------

* Increase version numbers in ``senic_hub/setup_app/ios/SenicHubSetup/Info.plist`` file
* Run ``CRASHLYTICS_BUILD_SECRET=secret_goes_here fastlane beta`` from ``senic_hub/setup_app/ios`` directory. The value for ``CRASHLYTICS_BUILD_SECRET`` is available in 1Password entry ``Software/Crashlytics iOS Secret build key``.
* The new build will have no testers assigned. `Assign testers to new beta build <https://fabric.io/senic/ios/apps/com.senic.hub.setupapp/beta/releases/latest>`_.
