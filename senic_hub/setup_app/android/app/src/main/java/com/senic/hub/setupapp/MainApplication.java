package com.senic.hub.setupapp;

import com.facebook.react.ReactPackage;
import com.learnium.RNDeviceInfo.RNDeviceInfo;
import com.oblador.vectoricons.VectorIconsPackage;
import com.pusherman.networkinfo.RNNetworkInfoPackage;
import com.reactnativenavigation.NavigationApplication;
import com.polidea.reactnativeble.BlePackage;
import com.senic.hub.setupapp.BuildConfig;
import com.smixx.fabric.FabricPackage;
import com.crashlytics.android.Crashlytics;
import io.fabric.sdk.android.Fabric;

import java.util.Arrays;
import java.util.List;

public class MainApplication extends NavigationApplication {
   @Override
   public void onCreate() {
       super.onCreate();
       Fabric.with(this, new Crashlytics());
   }

    @Override
    public boolean isDebug() {
        return BuildConfig.DEBUG;
    }

    protected List<ReactPackage> getPackages() {
        return Arrays.<ReactPackage>asList(
            new BlePackage(),
            new FabricPackage(),
            new RNDeviceInfo(),
            new RNNetworkInfoPackage(),
            new VectorIconsPackage()
        );
    }

    @Override
    public List<ReactPackage> createAdditionalReactPackages() {
        return getPackages();
    }
}
