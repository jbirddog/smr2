# -*- coding: utf-8 -*-

import unittest
import random

from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from tests.SpiffWorkflow.camunda.BaseTestCase import BaseTestCase

__author__ = 'matth'

debug = True

class MultiInstanceParallelArrayTest(BaseTestCase):
    """The example bpmn diagram tests both a set cardinality from user input
    as well as looping over an existing array."""

    def setUp(self):
        spec, subprocesses = self.load_workflow_spec('multi_instance_array_parallel.bpmn', 'MultiInstanceArray')
        self.workflow = BpmnWorkflow(spec, subprocesses)

    def testRunThroughHappy(self):
        self.actual_test(False)

    def testRunThroughSaveRestore(self):
        self.actual_test(True)

    def actual_test(self, save_restore=False):

        first_task = self.workflow.task_tree

        # A previous task (in this case the root task) will set the data
        # so it must be found later.
        first_task.update_data({"FamilySize": 3})
        self.workflow.do_engine_steps()
        if save_restore: self.reload_save_restore()
        # Set initial array size to 3 in the first user form.
        task = self.workflow.get_ready_user_tasks()[0]
        self.assertEqual("Activity_FamSize", task.task_spec.name)
        task.update_data({"FamilySize": 3})
        self.workflow.complete_task_from_id(task.id)
        if save_restore: self.reload_save_restore()
        self.workflow.do_engine_steps()

        # Set the names of the 3 family members.
        for i in range(3):

            tasks = self.workflow.get_ready_user_tasks()
            self.assertEqual(len(tasks),1) # still with sequential MI
            task = tasks[0]
            if i > 0:
                self.assertEqual("FamilyMemberTask"+"_%d"%(i-1), task.task_spec.name)
            else:
                self.assertEqual("FamilyMemberTask", task.task_spec.name)
            task.update_data({"FamilyMember": {"FirstName": "The Funk #%i" % i}})
            self.workflow.complete_task_from_id(task.id)
            self.workflow.do_engine_steps()
            if save_restore:
                self.reload_save_restore()
        tasks = self.workflow.get_ready_user_tasks()

        self.assertEqual(3,len(tasks))
        # Set the birthdays of the 3 family members.
        for i in range(3): # emulate random Access
            task = random.choice(tasks)
            x = task.internal_data['runtimes'] -1
            self.assertEqual("FamilyMemberBday", task.task_spec.name[:16])
            self.assertEqual({"FirstName": "The Funk #%i" % x},
                              task.data["CurrentFamilyMember"])
            task.update_data(
                {"CurrentFamilyMember": {"Birthdate": "10/05/1985" + str(x)}})
            self.workflow.do_engine_steps()
            self.workflow.complete_task_from_id(task.id)
            # The data should still be available on the current task.
            self.assertEqual({'FirstName': "The Funk #%i" % x,
                               'Birthdate': '10/05/1985' + str(x)},
                              self.workflow.get_task(task.id)
                              .data['CurrentFamilyMember'])
            self.workflow.do_engine_steps()
            if save_restore:
                self.reload_save_restore()
            self.workflow.do_engine_steps()

            tasks = self.workflow.get_ready_user_tasks()

        self.workflow.do_engine_steps()
        if save_restore:
            self.reload_save_restore()

        names = task.data['FamilyMembers']
        bdays = task.data['FamilyMemberBirthday']
        for x in list(names.keys()):
            self.assertEqual(str(names[x]['FirstName'][-1]),str(bdays[x]['Birthdate'][-1]))
        self.assertTrue(self.workflow.is_completed())


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(MultiInstanceParallelArrayTest)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
