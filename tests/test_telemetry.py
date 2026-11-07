import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('telemetry', Path(__file__).parents[1]/'scripts/update_analytics.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 7, 12, tzinfo=timezone.utc)
        self.days = [{'date': (self.now.date()-timedelta(days=364-i)).isoformat(), 'count': 0, 'level': 0} for i in range(365)]
        self.user = {'login':'AshuNewatia','public_repos':3,'followers':3}
        self.repos = [{'fork':False,'language':'C++','stargazers_count':2}, {'fork':True,'language':'Python','stargazers_count':100}, {'fork':False,'language':None,'stargazers_count':1}]

    def test_today_can_be_unfinished_and_fork_stars_are_excluded(self):
        for d in self.days[-3:-1]: d.update(count=2, level=1)
        data=m.summarize(self.user,self.repos,self.days,self.now,'API')
        self.assertEqual(data['metrics']['contributions'],4)
        self.assertEqual(data['metrics']['current_streak_days'],2)
        self.assertEqual(data['metrics']['best_streak_days'],2)
        self.assertEqual(data['metrics']['stars_on_original_repositories'],3)
        self.assertEqual(data['languages_by_primary_repository_count'],{'C++':1})
        ET.fromstring(m.calendar_svg(data))
        self.assertNotIn('<text',m.calendar_svg(data))

    def test_missing_day_fails_instead_of_inventing_zero(self):
        with self.assertRaisesRegex(RuntimeError,'Incomplete'):
            m.summarize(self.user,self.repos,self.days[1:],self.now,'API')

    def test_empty_languages_and_old_best_streak(self):
        for d in self.days[10:15]: d.update(count=1,level=1)
        data=m.summarize(self.user,[],self.days,self.now,'API')
        self.assertEqual(data['metrics']['best_streak_days'],5)
        self.assertEqual(data['metrics']['current_streak_days'],0)
        self.assertIn('No detected languages',m.markdown(data))

if __name__=='__main__':unittest.main()
