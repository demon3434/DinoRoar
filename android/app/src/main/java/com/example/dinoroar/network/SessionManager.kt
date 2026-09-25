package com.example.dinoroar.network

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import java.util.concurrent.atomic.AtomicBoolean
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SessionManager @Inject constructor() {
    private val _sessionExpiredEvent = MutableSharedFlow<Unit>(extraBufferCapacity = 1)
    val sessionExpiredEvent: SharedFlow<Unit> = _sessionExpiredEvent.asSharedFlow()

    private val isHandlingExpired = AtomicBoolean(false)

    /**
     * 触发服务端 401 令牌过期事件（带原子防抖保护）
     */
    fun notifySessionExpired() {
        if (isHandlingExpired.compareAndSet(false, true)) {
            _sessionExpiredEvent.tryEmit(Unit)
        }
    }

    /**
     * 用户重新验证登录成功后复位防抖标记
     */
    fun resetExpiredFlag() {
        isHandlingExpired.set(false)
    }
}
