import enum
import time


class CooldownError(Exception):
    """Raised when packets are sent whilst a cooldown is active"""
    pass


class BucketType(enum.Enum):
    Default = 1
    Penguin = 1
    Server = 2


class _Cooldown:

    __slots__ = ['rate', 'per', 'bucket_type', 'last',
                 '_window', '_tokens']

    def __init__(self, per, rate, bucket_type):
        self.per = float(per)
        self.rate = int(rate)
        self.bucket_type = bucket_type
        self.last = 0.0

        self._window = 0.0
        self._tokens = self.rate

    @property
    def is_cooling(self):
        current = time.time()
        self.last = current

        if self._tokens == self.rate:
            self._window = current

        if current > self._window + self.per:
            self._tokens = self.rate
            self._window = current

        if self._tokens == 0:
            return self.per - (current - self._window)

        self._tokens -= 1
        if self._tokens == 0:
            self._window = current

    def reset(self):
        self._tokens = self.rate
        self.last = 0.0

    def copy(self):
        return _Cooldown(self.per, self.rate, self.bucket_type)


class _CooldownMapping:

    __slots__ = ['_cooldown', '_cache', 'callback']

    def __init__(self, callback, cooldown_object):
        self._cooldown = cooldown_object

        self.callback = callback

        self._cache = {}

    def _get_bucket_key(self, p):
        if self._cooldown.bucket_type == BucketType.Default:
            return p.id
        return p.server

    def _verify_cache_integrity(self):
        current = time.time()
        self._cache = {cache_key: bucket for cache_key, bucket in
                       self._cache.items() if current < bucket.last + bucket.per}

    def get_bucket(self, p):
        self._verify_cache_integrity()
        cache_key = self._get_bucket_key(p)
        if cache_key not in self._cache:
            bucket = self._cooldown.copy()
            self._cache[cache_key] = bucket
        else:
            bucket = self._cache[cache_key]
        return bucket

