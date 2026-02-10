import unittest

from msft_realtime_analyzer import RealtimeAnalyzer


class TestRealtimeAnalyzer(unittest.TestCase):
    def test_sma(self):
        analyzer = RealtimeAnalyzer(window=30)
        for p in [1, 2, 3, 4, 5]:
            analyzer.update(float(p))
        self.assertAlmostEqual(analyzer.sma(5), 3.0)

    def test_ema(self):
        analyzer = RealtimeAnalyzer(window=30)
        for p in [10, 11, 12, 13, 14, 15]:
            analyzer.update(float(p))
        value = analyzer.ema(5)
        self.assertIsNotNone(value)
        self.assertGreater(value, 12.0)

    def test_rsi_all_gain(self):
        analyzer = RealtimeAnalyzer(window=30)
        for p in range(1, 20):
            analyzer.update(float(p))
        self.assertEqual(analyzer.rsi(14), 100.0)


if __name__ == "__main__":
    unittest.main()
