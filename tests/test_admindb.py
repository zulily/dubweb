#!/usr/bin/env python
"""
   Tests for admindb.py
   Called via nosetests tests/test_admindb.py
"""

# Global imports
import datetime
import calendar
import json
import unittest

# Local imports
from app import admindb

class TestDubwebDB(unittest.TestCase):

    def test_get_budget_items(self):
        """ Test the API used for admindb budget admin, 
            returning the default (all budget entries) dataset. """
        all_providers_projects_teams = admindb.AdmIDs(
                                         prv_id=None, team_id=None,
                                         project_id=None,
                                         budget_id=None)
        all_budgets = admindb.get_budget_items(
                                         all_providers_projects_teams,
                                         m_filter=None, bgt_filter=None)
        for series in all_budgets:
            self.assertEqual(len(series), 6)

    def test_edit_budget_items(self):
        """ Test the API used for admindb budget admin edit.
            Edit teamid, check it, then return to original.
            Assert: at least one budget in budget table. """
        test_teamid = 3
        budget_id_one = admindb.AdmIDs( prv_id=None, team_id=None,
                                        project_id=None, budget_id=1)
        budget_list = admindb.get_budget_items(
                                         budget_id_one,
                                         m_filter=None, bgt_filter=None)
        first_budget = budget_list[0]
        self.assertEqual(len(first_budget), 6)
        orig_comment = first_budget['Comment']
        orig_month = first_budget['Month']
        orig_budget = first_budget['Budget']
        orig_teamid = first_budget['TeamID']
        test_budget_id = admindb.AdmIDs(prv_id=first_budget['ProviderID'],
                              team_id=test_teamid,
                              project_id=None,
                              budget_id=first_budget['ID'])
        item = admindb.edit_budget_item(test_budget_id,
                                           orig_month, orig_budget,
                                           orig_comment)
        self.assertEqual(len(item), 6)
        test_budgets = admindb.get_budget_items(
                                 test_budget_id,
                                 m_filter=None, bgt_filter=None)
        test_budget = test_budgets[0]
        self.assertEqual(test_budget['TeamID'], test_teamid)
        orig_budget_id = admindb.AdmIDs(prv_id=first_budget['ProviderID'],
                              team_id=first_budget['TeamID'],
                              project_id=None,
                              budget_id=first_budget['ID'])
        orig_item = admindb.edit_budget_item(orig_budget_id,
                                           orig_month, orig_budget,
                                           orig_comment)
        self.assertEqual(len(orig_item), 6)
     
    def test_insert_delete_budget_items(self):
        """ Test the APIs used for admindb insert/delete budget.
            insert budget, check it, delete it, check it. 
            Requires at least one provider, and team.""" 
        prvid_test = 1
        teamid_test = 1
        budget_test = 2
        month_test = '2015-01'
        comment_test = 'please delete me.'
        new_budget_id = admindb.AdmIDs( prvid_test, teamid_test,
                                        project_id=None, budget_id=None)
        new_item = admindb.insert_budget_item(
                                         new_budget_id,
                                         my_month=month_test,
                                         my_budget=budget_test,
                                         my_comment=comment_test)
        
        self.assertEqual(new_item['ProviderID'], prvid_test)
        self.assertEqual(new_item['TeamID'], teamid_test)
        self.assertEqual(new_item['Budget'], budget_test)
        self.assertEqual(new_item['Month'], month_test)
        self.assertEqual(new_item['Comment'], comment_test)
        delete_budget_id = admindb.AdmIDs(prvid_test, teamid_test,
                              project_id=None,
                              budget_id=new_item['ID'])
        item = admindb.delete_budget_item(delete_budget_id,
                                           month_test, budget_test,
                                           comment_test)
        self.assertEqual(len(item), 6)
        test_budget = admindb.get_budget_items(
                                 delete_budget_id,
                                 m_filter=None, bgt_filter=None)
        null_list = []
        self.assertEqual(test_budget, null_list)
     
  

if __name__ == "__main__":
    unittest.main()
