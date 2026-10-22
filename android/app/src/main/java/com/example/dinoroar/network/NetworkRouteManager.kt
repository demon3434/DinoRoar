package com.example.dinoroar.network

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.util.Log
import com.example.dinoroar.data.local.SecurePrefs
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/**
 * DinoRoar 客户端网络自适应路由中枢：
 * 1. 深度监听 ConnectivityManager 硬件接口与网络能力跳变
 * 2. 引入 300ms 智能协程防抖，等待 WiFi DHCP 租约与局域网路由就绪，根除误判离线
 * 3. 蜂窝网络 0ms 拓扑快轨 (Cellular Fast-Path)：移动网络下秒切外网
 * 4. 独立 1.2s 超轻量探针 Client + 双轨并发竞速选线 (Racing Probe) 局域网极速优先
 * 5. 全状态流维护与响应式 UI 绑定 (isProbing / probeMessage)
 */
@Singleton
class NetworkRouteManager @Inject constructor(
    @ApplicationContext private val context: Context,
    private val securePrefs: SecurePrefs
) {
    private val TAG = "NetworkRouteManager"
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val switchMutex = Mutex()
    private var debounceJob: Job? = null
    private var networkCallback: ConnectivityManager.NetworkCallback? = null

    private val _isProbing = MutableStateFlow(false)
    val isProbing: StateFlow<Boolean> = _isProbing.asStateFlow()

    private val _probeMessage = MutableStateFlow<String?>(null)
    val probeMessage: StateFlow<String?> = _probeMessage.asStateFlow()

    // 独立轻量探针 Client，严控超时为 1.2s，与业务长连接/文件上传彻底隔离
    private val probeClient = OkHttpClient.Builder()
        .connectTimeout(1200, TimeUnit.MILLISECONDS)
        .readTimeout(1200, TimeUnit.MILLISECONDS)
        .writeTimeout(1200, TimeUnit.MILLISECONDS)
        .build()

    /**
     * 启动网络状态深度监听
     */
    fun startMonitoring() {
        if (networkCallback != null) return
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager ?: return
        val request = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .build()

        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                Log.d(TAG, "NetworkCallback: onAvailable ($network)")
                handleNetworkChange(cm)
            }

            override fun onCapabilitiesChanged(network: Network, networkCapabilities: NetworkCapabilities) {
                Log.d(TAG, "NetworkCallback: onCapabilitiesChanged ($network)")
                handleNetworkChange(cm, networkCapabilities)
            }

            override fun onLost(network: Network) {
                Log.d(TAG, "NetworkCallback: onLost ($network)")
                handleNetworkChange(cm)
            }
        }

        networkCallback = callback
        try {
            cm.registerNetworkCallback(request, callback)
            Log.i(TAG, "NetworkCallback registered successfully.")
            handleNetworkChange(cm)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to register NetworkCallback: ${e.message}")
        }
    }

    /**
     * 注销网络监听
     */
    fun stopMonitoring() {
        val callback = networkCallback ?: return
        networkCallback = null
        debounceJob?.cancel()
        try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            cm?.unregisterNetworkCallback(callback)
            Log.i(TAG, "NetworkCallback unregistered.")
        } catch (e: Exception) {
            Log.w(TAG, "Unregister callback error: ${e.message}")
        }
    }

    /**
     * 处理网络硬件或能力跳变
     */
    private fun handleNetworkChange(cm: ConnectivityManager, specificCaps: NetworkCapabilities? = null) {
        val activeNetwork = cm.activeNetwork
        if (activeNetwork == null) {
            _probeMessage.value = "物理网络已断开"
            Log.w(TAG, "物理网络已断开，转入离线状态")
            return
        }

        val caps = specificCaps ?: cm.getNetworkCapabilities(activeNetwork)
        if (caps == null || !caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)) {
            _probeMessage.value = "无可用互联网连接"
            return
        }

        val isVpn = caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN)
        val isCellular = caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)

        val intranetUrl = securePrefs.intranetUrl?.trim()?.removeSuffix("/") ?: ""
        val extranetUrl = securePrefs.extranetUrl?.trim()?.removeSuffix("/") ?: ""

        // 1. 蜂窝网络 0ms 拓扑快轨 (CELLULAR 且无 VPN)
        if (isCellular && !isVpn && isPrivateNetwork(intranetUrl)) {
            Log.i(TAG, "🚀 检测到蜂窝移动网络，启用 0ms 拓扑快轨 (直跳外网)")
            debounceJob?.cancel()
            if (extranetUrl.isNotBlank()) {
                applyRoute(extranetUrl, "云端外网 (蜂窝快轨)")
            }
            return
        }

        // 2. WiFi / 以太网 / VPN: 智能防抖 300ms 等待 DHCP 租约和路由表就绪
        debounceJob?.cancel()
        debounceJob = scope.launch {
            Log.d(TAG, "⏳ 接入网络接口，执行 300ms 防抖等待系统 DHCP/路由就绪...")
            delay(300)
            raceAndSwitchRoutes(intranetUrl, extranetUrl, isManualTrigger = false)
        }
    }

    /**
     * 双轨并发竞速选线 (局域网极速优先)
     */
    suspend fun raceAndSwitchRoutes(
        intranetUrl: String = securePrefs.intranetUrl?.trim()?.removeSuffix("/") ?: "",
        extranetUrl: String = securePrefs.extranetUrl?.trim()?.removeSuffix("/") ?: "",
        isManualTrigger: Boolean = false
    ): String? = withContext(Dispatchers.IO) {
        switchMutex.withLock {
            _isProbing.value = true
            _probeMessage.value = "正在探测最佳线路..."
            Log.i(TAG, "⚡ 发起线路并发竞速选线 (手动=$isManualTrigger, 内网=$intranetUrl, 外网=$extranetUrl)")

            try {
                if (intranetUrl.isBlank() && extranetUrl.isBlank()) {
                    _probeMessage.value = "未配置服务器地址"
                    return@withContext null
                }

                // 仅配置了单通道
                if (intranetUrl.isNotBlank() && extranetUrl.isBlank()) {
                    val ok = checkHealth(intranetUrl, 1200L)
                    if (ok) {
                        applyRoute(intranetUrl, "家庭局域网")
                        return@withContext intranetUrl
                    }
                    _probeMessage.value = "家庭局域网不可达"
                    return@withContext null
                }

                if (intranetUrl.isBlank() && extranetUrl.isNotBlank()) {
                    val ok = checkHealth(extranetUrl, 1500L)
                    if (ok) {
                        applyRoute(extranetUrl, "云端外网")
                        return@withContext extranetUrl
                    }
                    _probeMessage.value = "云端外网不可达"
                    return@withContext null
                }

                // 双轨并行竞速：内网 1.2s 优先，外网 1.5s 兜底
                val bestUrl = coroutineScope {
                    val intraDeferred = async { checkHealth(intranetUrl, 1200L) }
                    val extraDeferred = async { checkHealth(extranetUrl, 1500L) }

                    // 等待局域网探针 (家庭 WiFi 环境下通常 20~50ms 极速返回)
                    val intraOk = intraDeferred.await()
                    if (intraOk) {
                        extraDeferred.cancel()
                        Log.i(TAG, "🏁 内网探针极速胜出，已取消外网探测")
                        intranetUrl
                    } else {
                        val extraOk = extraDeferred.await()
                        if (extraOk) {
                            Log.i(TAG, "🏁 内网不可达，外网探针胜出")
                            extranetUrl
                        } else {
                            null
                        }
                    }
                }

                if (bestUrl != null) {
                    val isIntra = (bestUrl == intranetUrl)
                    applyRoute(bestUrl, if (isIntra) "家庭局域网 (极速)" else "云端外网")
                    bestUrl
                } else {
                    _probeMessage.value = "内外网线路均不可达"
                    Log.w(TAG, "内外网线路探测均失败，维持原有设置")
                    null
                }
            } finally {
                _isProbing.value = false
            }
        }
    }

    /**
     * 超轻量级探针检测
     */
    suspend fun checkHealth(url: String, timeoutMs: Long = 1200L): Boolean = withContext(Dispatchers.IO) {
        if (url.isBlank()) return@withContext false
        val clean = url.trim().removeSuffix("/")
        try {
            val req = Request.Builder().url("$clean/api/health").get().build()
            val client = probeClient.newBuilder()
                .connectTimeout(timeoutMs, TimeUnit.MILLISECONDS)
                .readTimeout(timeoutMs, TimeUnit.MILLISECONDS)
                .build()
            client.newCall(req).execute().use { response ->
                response.isSuccessful
            }
        } catch (e: Exception) {
            Log.d(TAG, "Probe failed for $clean: ${e.message}")
            false
        }
    }

    /**
     * 应用选线结果并原子持久化
     */
    private fun applyRoute(cleanUrl: String, channelDesc: String) {
        val current = securePrefs.serverUrl?.trim()?.removeSuffix("/") ?: ""
        val target = cleanUrl.trim().removeSuffix("/")

        _probeMessage.value = "已连接: $channelDesc"
        if (current == target) {
            Log.d(TAG, "当前已处于目标通道，保持状态: $target ($channelDesc)")
            return
        }

        securePrefs.serverUrl = target
        Log.i(TAG, "🎯 成功切换通信基地址 -> $channelDesc: $target")
    }

    /**
     * 判断是否为 RFC 1918 私有局域网网段
     */
    fun isPrivateNetwork(url: String): Boolean {
        if (url.isBlank()) return false
        val host = url.trim()
            .removePrefix("http://")
            .removePrefix("https://")
            .substringBefore("/")
            .substringBefore(":")
            .lowercase()

        if (host == "localhost" || host == "127.0.0.1") return true
        if (host.startsWith("192.168.") || host.startsWith("10.")) return true
        if (host.startsWith("172.")) {
            val parts = host.split(".")
            if (parts.size >= 2) {
                val second = parts[1].toIntOrNull() ?: 0
                if (second in 16..31) return true
            }
        }
        return false
    }

    /**
     * 判断当前 BaseUrl 是否为家庭局域网
     */
    fun isCurrentIntranet(): Boolean {
        val current = securePrefs.serverUrl?.trim()?.removeSuffix("/") ?: ""
        val intra = securePrefs.intranetUrl?.trim()?.removeSuffix("/") ?: ""
        if (intra.isNotBlank() && current.startsWith(intra)) return true
        val extra = securePrefs.extranetUrl?.trim()?.removeSuffix("/") ?: ""
        if (extra.isNotBlank() && current.startsWith(extra)) return false
        return isPrivateNetwork(current)
    }
}
