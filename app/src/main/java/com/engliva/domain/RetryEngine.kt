package com.engliva.domain
class RetryEngine(private val maximumAttempts: Int = 3) { fun canRetry(attempts: Int, enabled: Boolean) = enabled && attempts < maximumAttempts }
