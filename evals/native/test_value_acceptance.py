"""Prove that product checks reject defects and accept a known-correct control.

Control implementations never enter task workspaces during model trials.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BOOKING_CONTROL = '''import json
from pathlib import Path
from uuid import uuid4
class BookingStore:
 def __init__(self, path): self.path = Path(path)
 def list_bookings(self):
  return json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else []
 def reserve(self, slot, email, request_id):
  email = email.strip().lower()
  if not slot.strip() or not request_id.strip() or not email or '@' not in email: raise ValueError('invalid input')
  rows = self.list_bookings()
  for row in rows:
   if row['request_id'] == request_id:
    if row['slot'] != slot or row['email'] != email: raise ValueError('request reused')
    return row
  if any(row['slot'] == slot for row in rows): raise ValueError('occupied')
  row = dict(id=str(uuid4()), slot=slot, email=email, request_id=request_id)
  rows.append(row)
  self.path.write_text(json.dumps(rows,ensure_ascii=False),encoding='utf-8')
  return row
'''
CONTACTS_CONTROL = '''import csv,json,sys
from pathlib import Path
def export_csv(source,destination):
 source,destination = Path(source),Path(destination)
 if source.resolve() == destination.resolve() or (destination.exists() and source.samefile(destination)): raise ValueError('same file')
 rows = json.loads(source.read_text(encoding='utf-8'))
 selected = []; seen = set()
 for row in rows:
  if row.get('consent') is not True: continue
  email = row.get('email','').strip().lower()
  if not email or '@' not in email or email in seen: continue
  selected.append([row['name'],email]); seen.add(email)
 with destination.open('w',encoding='utf-8',newline='') as output:
  writer=csv.writer(output); writer.writerow(['name','email']); writer.writerows(selected)
 return len(selected)
if __name__ == '__main__': print(export_csv(sys.argv[1],sys.argv[2]))
'''


class ProductAcceptanceTests(unittest.TestCase):
    def check(self, task, control=None):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'workspace'
            shutil.copytree(ROOT/'evals/native/fixtures'/task,root)
            if control:
                filename='booking.py' if task=='booking' else 'export_contacts.py'
                (root/filename).write_text(control,encoding='utf-8')
            command=[sys.executable,'-B',str(ROOT/'evals/native/harness/value_acceptance.py'),str(root),task]
            result=subprocess.run(command,capture_output=True,text=True,timeout=10)
            payload=json.loads(result.stdout)
            self.assertEqual(result.returncode==0,payload['passed'])
            return payload

    def test_original_fixtures_fail_meaningful_acceptance(self):
        for task in ('booking','contacts'):
            with self.subTest(task=task):
                self.assertFalse(self.check(task)['passed'])

    def test_known_correct_controls_pass(self):
        for task,control,count in [('booking',BOOKING_CONTROL,8),('contacts',CONTACTS_CONTROL,9)]:
            with self.subTest(task=task):
                payload=self.check(task,control)
                self.assertTrue(payload['passed'],payload)
                self.assertEqual(len(payload['checks_passed']),count)

    def test_booking_persistence_and_conflict_mutants_fail(self):
        mutants=[BOOKING_CONTROL.replace("return json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else []",'return []'),
                 BOOKING_CONTROL.replace("if any(row['slot'] == slot for row in rows): raise ValueError('occupied')",'pass')]
        for mutant in mutants:
            self.assertFalse(self.check('booking',mutant)['passed'])

    def test_consent_and_collision_mutants_fail(self):
        mutants=[CONTACTS_CONTROL.replace("if row.get('consent') is not True: continue","if not row.get('consent'): continue"),
                 CONTACTS_CONTROL.replace("if source.resolve() == destination.resolve() or (destination.exists() and source.samefile(destination)): raise ValueError('same file')",'pass')]
        for mutant in mutants:
            self.assertFalse(self.check('contacts',mutant)['passed'])

    def test_hardlink_preservation_is_distinct_from_symlink_check(self):
        mutant=CONTACTS_CONTROL.replace(" or (destination.exists() and source.samefile(destination))", "")
        payload=self.check('contacts',mutant)
        self.assertFalse(payload['passed'])
        self.assertTrue(any('hardlinked_collision:' in e for e in payload['errors']))
        self.assertIn('linked_collision',payload['checks_passed'])

    def test_function_pass_cannot_hide_a_broken_public_cli(self):
        mutant=CONTACTS_CONTROL.replace("if __name__ == '__main__': print(export_csv(sys.argv[1],sys.argv[2]))", "")
        payload=self.check('contacts',mutant)
        self.assertFalse(payload['passed'])
        self.assertTrue(any('public_cli:' in e for e in payload['errors']))
        self.assertIn('consent',payload['checks_passed'])


if __name__=='__main__':
    unittest.main()
