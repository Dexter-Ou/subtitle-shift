import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from subtitle_shift import shift

SAMPLE = '1\n00:00:01,000 --> 00:00:02,500\nHello\nworld\n'


class TimingTests(unittest.TestCase):
    def test_exact_shift_and_text(self):
        output, warnings = shift(SAMPLE, 1250)
        self.assertEqual(output, '1\n00:00:02,250 --> 00:00:03,750\nHello\nworld\n')
        self.assertEqual(warnings, [])

    def test_negative_valid(self):
        self.assertIn('00:00:00,000 --> 00:00:01,500', shift(SAMPLE, -1000)[0])

    def test_negative_rejected(self):
        with self.assertRaisesRegex(ValueError, 'negative'):
            shift(SAMPLE, -1001)

    def test_malformed(self):
        for text in ['', SAMPLE.replace('01,000', '61,000'), SAMPLE.replace('02,500', '00,500'), SAMPLE.replace(' --> ', ' -> '), SAMPLE.replace('02,500', '02,500 align:start')]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                shift(text, 0)

    def test_overlap_and_boundary(self):
        tail = '2\n00:00:02,000 --> 00:00:03,000\nTwo\n'
        self.assertEqual(len(shift(SAMPLE + '\n' + tail, 0)[1]), 1)
        self.assertEqual(shift(SAMPLE + '\n' + tail.replace('02,000', '02,500'), 0)[1], [])

    def test_bom_crlf_and_hour_carry(self):
        self.assertEqual(shift('\ufeff' + SAMPLE.replace('\n', '\r\n'), 0)[0], SAMPLE)
        self.assertIn('01:00:00,000', shift(SAMPLE, 3599000)[0])

    def test_unordered(self):
        with self.assertRaisesRegex(ValueError, 'ordered'):
            shift(SAMPLE + '\n' + SAMPLE.replace('01,000', '00,500'), 0)

    def test_cli_safety_and_fresh_start(self):
        script = str(Path(__file__).with_name('subtitle_shift.py').resolve())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root/'source.srt', root/'shifted.srt'
            source.write_text(SAMPLE)
            def run(output, offset):
                return subprocess.run([sys.executable, script, str(source), str(output), '--offset-ms', str(offset)], capture_output=True, text=True, cwd=root)
            self.assertEqual(run(target, -1001).returncode, 2)
            self.assertFalse(target.exists())
            self.assertEqual(run(target, 500).returncode, 0)
            self.assertIn('00:00:01,500', target.read_text())
            original = target.read_bytes()
            self.assertEqual(run(target, 0).returncode, 2)
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(run(source, 0).returncode, 2)
            self.assertEqual(source.read_text(), SAMPLE)
            source.write_bytes(b'\xff')
            self.assertEqual(run(root/'invalid.srt', 0).returncode, 2)
            self.assertFalse((root/'invalid.srt').exists())
            source.write_bytes(b'x' * (8*1024*1024+1))
            self.assertEqual(run(root/'large.srt', 0).returncode, 2)
            self.assertFalse((root/'large.srt').exists())


if __name__ == '__main__':
    unittest.main()
