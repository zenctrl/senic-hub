package com.senichubsetup;

import com.facebook.react.ReactPackage;
import com.oblador.vectoricons.VectorIconsPackage;
import com.pusherman.networkinfo.RNNetworkInfoPackage;
import com.reactnativenavigation.NavigationApplication;
import com.polidea.reactnativeble.BlePackage;

import java.util.Arrays;
import java.util.List;

public class MainApplication extends NavigationApplication {
    @Override
    public boolean isDebug() {
        return BuildConfig.DEBUG;
    }

    protected List<ReactPackage> getPackages() {
        return Arrays.<ReactPackage>asList(
            new BlePackage(),
            new RNNetworkInfoPackage(),
            new VectorIconsPackage()
        );
    }

    @Override
    public List<ReactPackage> createAdditionalReactPackages() {
        return getPackages();
    }
}
