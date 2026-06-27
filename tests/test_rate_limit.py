from vk_checker.rate_limit import AsyncRateLimiter, LimitConfig, SyncRateLimiter


def test_limit_config_guards_zero_rpm():
    sync = SyncRateLimiter(LimitConfig(rpm=0, jitter_ms=0))
    async_limiter = AsyncRateLimiter(LimitConfig(rpm=0, jitter_ms=0))
    assert sync.delay == 60
    assert async_limiter.delay == 60
