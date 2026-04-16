package com.quicksail.sailor.api

import com.quicksail.sailor.BuildConfig
import java.io.IOException
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NetworkOfflineBehaviorTest {

    @Test
    fun offlineQueueFeatureFlagIsEnabledForCurrentBuild() {
        assertTrue(BuildConfig.FEATURE_OFFLINE_QUEUE)
    }

    @Test
    fun transientNetworkErrorsAreRecognized() {
        assertTrue(Network.isTransientNetworkError(SocketTimeoutException("timeout")))
        assertTrue(Network.isTransientNetworkError(UnknownHostException("host unreachable")))
        assertTrue(Network.isTransientNetworkError(ConnectException("failed to connect")))
        assertTrue(Network.isTransientNetworkError(IOException("network down")))
        assertTrue(Network.isTransientNetworkError(RuntimeException("Connection reset by peer")))
    }

    @Test
    fun nonNetworkErrorsAreNotTreatedAsOfflineFailures() {
        assertFalse(Network.isTransientNetworkError(IllegalArgumentException("bad request")))
        assertFalse(Network.isTransientNetworkError(RuntimeException("validation failed")))
    }

    @Test
    fun timeoutErrorsAreClassifiedSeparately() {
        assertTrue(Network.isTimeoutError(SocketTimeoutException("request timeout")))
        assertTrue(Network.isTimeoutError(IOException("timeout while reading")))
        assertFalse(Network.isTimeoutError(IOException("connection reset")))
    }
}
