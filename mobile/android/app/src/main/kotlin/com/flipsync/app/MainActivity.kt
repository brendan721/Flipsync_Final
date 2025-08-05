package com.flipsync.app

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import android.content.Context
import android.content.Intent
import android.os.Bundle

class MainActivity: FlutterActivity() {
    private val CHANNEL = "com.flipsync.app/native"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "getDeviceInfo" -> {
                    val deviceInfo = getDeviceInfo()
                    result.success(deviceInfo)
                }
                "openAppSettings" -> {
                    openAppSettings()
                    result.success(true)
                }
                "shareContent" -> {
                    val content = call.argument<String>("content")
                    shareContent(content ?: "")
                    result.success(true)
                }
                "handleOAuthCallback" -> {
                    val code = call.argument<String>("code")
                    val state = call.argument<String>("state")
                    handleOAuthCallback(code, state)
                    result.success(true)
                }
                else -> {
                    result.notImplemented()
                }
            }
        }
    }

    private fun getDeviceInfo(): Map<String, String> {
        return mapOf(
            "model" to android.os.Build.MODEL,
            "manufacturer" to android.os.Build.MANUFACTURER,
            "version" to android.os.Build.VERSION.RELEASE,
            "sdk" to android.os.Build.VERSION.SDK_INT.toString()
        )
    }

    private fun openAppSettings() {
        val intent = Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
        intent.data = android.net.Uri.parse("package:$packageName")
        startActivity(intent)
    }

    private fun shareContent(content: String) {
        val shareIntent = Intent().apply {
            action = Intent.ACTION_SEND
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, content)
        }
        startActivity(Intent.createChooser(shareIntent, "Share via"))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Handle deep links
        handleDeepLink(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleDeepLink(intent)
    }

    private fun handleDeepLink(intent: Intent?) {
        intent?.data?.let { uri ->
            when {
                // Handle FlipSync deep links
                uri.scheme == "flipsync" -> {
                    val path = uri.path
                    val params = uri.queryParameterNames.associateWith { uri.getQueryParameter(it) }

                    // Send deep link data to Flutter
                    flutterEngine?.dartExecutor?.binaryMessenger?.let { messenger ->
                        MethodChannel(messenger, CHANNEL).invokeMethod("handleDeepLink", mapOf(
                            "path" to path,
                            "params" to params
                        ))
                    }
                }
                // Handle eBay OAuth redirects (Custom URL scheme: flipsync://oauth/ebay)
                uri.scheme == "flipsync" && uri.host == "oauth" && uri.path == "/ebay" -> {
                    handleEbayOAuthRedirect(uri)
                }
                // Handle other OAuth redirects
                uri.queryParameterNames.contains("code") && uri.queryParameterNames.contains("state") -> {
                    handleGenericOAuthRedirect(uri)
                }
            }
        }
    }

    private fun handleEbayOAuthRedirect(uri: android.net.Uri) {
        val code = uri.getQueryParameter("code")
        val state = uri.getQueryParameter("state")
        val error = uri.getQueryParameter("error")

        flutterEngine?.dartExecutor?.binaryMessenger?.let { messenger ->
            if (error != null) {
                // Handle OAuth error
                MethodChannel(messenger, CHANNEL).invokeMethod("handleOAuthError", mapOf(
                    "marketplace" to "ebay",
                    "error" to error,
                    "error_description" to uri.getQueryParameter("error_description")
                ))
            } else if (code != null) {
                // Handle successful OAuth callback
                MethodChannel(messenger, CHANNEL).invokeMethod("handleOAuthSuccess", mapOf(
                    "marketplace" to "ebay",
                    "code" to code,
                    "state" to state
                ))
            }
        }
    }

    private fun handleGenericOAuthRedirect(uri: android.net.Uri) {
        val code = uri.getQueryParameter("code")
        val state = uri.getQueryParameter("state")
        val error = uri.getQueryParameter("error")

        flutterEngine?.dartExecutor?.binaryMessenger?.let { messenger ->
            if (error != null) {
                MethodChannel(messenger, CHANNEL).invokeMethod("handleOAuthError", mapOf(
                    "marketplace" to "unknown",
                    "error" to error,
                    "error_description" to uri.getQueryParameter("error_description")
                ))
            } else if (code != null) {
                MethodChannel(messenger, CHANNEL).invokeMethod("handleOAuthSuccess", mapOf(
                    "marketplace" to "unknown",
                    "code" to code,
                    "state" to state
                ))
            }
        }
    }

    private fun handleOAuthCallback(code: String?, state: String?) {
        // This method can be called directly from Flutter if needed
        flutterEngine?.dartExecutor?.binaryMessenger?.let { messenger ->
            MethodChannel(messenger, CHANNEL).invokeMethod("handleOAuthSuccess", mapOf(
                "marketplace" to "manual",
                "code" to code,
                "state" to state
            ))
        }
    }
}
