import math
import random


class Dist:
    @property
    def mean(self) -> float:
        raise NotImplemented

    @property
    def uncertain(self) -> bool:
        raise NotImplemented

    def generate(self) -> float:
        raise NotImplemented


class Constant(Dist):
    def __init__(self, value):
        self._value = value

    @property
    def mean(self) -> float:
        return self._value

    @property
    def uncertain(self) -> bool:
        return False

    def generate(self) -> float:
        return self._value


ERFINV_95 = 1.1630871536766738
ERFINV_90 = 0.9061938024368232
ERFINV_50 = 0


class LogNormal(Dist):
    def __init__(self, p50: float, p95: float):
        self._mu = math.log(p50)

        mu = self._mu
        sqr = (math.log(p95) - mu) / ERFINV_95
        sigma2 = sqr * sqr / 2
        sigma = math.sqrt(sigma2)

        self._sigma = sigma

        self._mean = math.exp(self._mu + self._sigma * self._sigma / 2)

    @property
    def mean(self) -> float:
        return self._mean

    @property
    def uncertain(self) -> bool:
        return True

    def generate(self) -> float:
        return math.exp(random.gauss(self._mu, self._sigma))


def test_lognormal():
    dist = LogNormal(p50=100, p95=150)
    results = []
    for i in range(10000):
        results.append(dist.generate())
    results.sort()
    actual_p50 = results[int(len(results) * 0.5)]
    actual_p95 = results[int(len(results) * 0.95)]
    actual_p99 = results[int(len(results) * 0.99)]
    actual_p05 = results[int(len(results) * 0.05)]
    print(actual_p05, actual_p50, actual_p95, actual_p99, max(results))
    assert abs(actual_p50 - 100) < 2
    assert abs(actual_p95 - 150) < 2
