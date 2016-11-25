#!/usr/bin/env python
"""
   Tests for admindb.py
   Called via nosetests tests/test_admindb.py
   Assumes test.sql has been used to create test database,
   and settings file .admin_settings points at that database.
"""

# Global imports
import unittest

# Local imports
from app import admindb

class TestDubwebDB(unittest.TestCase):
    """
    Standard test class, for all admindb functions
    """

    def test_get_budget_items(self):
        """
        Test the API used for admindb budget admin,
        returning the default (all budget entries) dataset.
        """
        all_providers_projects_teams = admindb.AdmIDs(prv_id=None,
                                                      team_id=None,
                                                      project_id=None,
                                                      budget_id=None,
                                                      div_id=None)
        all_budgets = admindb.get_budget_items(all_providers_projects_teams,
                                               m_filter=None, bgt_filter=None)
        for series in all_budgets:
            self.assertEqual(len(series), 7)

    def test_edit_budget_items(self):
        """
        Test the API used for admindb budget admin edit.
        Edit teamid, check it, then return to original.
        Assert: at least one budget in budget table.
        """
        test_teamid = 3
        budget_id_one = admindb.AdmIDs(prv_id=None, team_id=None,
                                       project_id=None, budget_id=1,
                                       div_id=None)
        budget_list = admindb.get_budget_items(budget_id_one,
                                               m_filter=None, bgt_filter=None)
        first_budget = budget_list[0]
        self.assertEqual(len(first_budget), 7)
        orig_comment = first_budget['Comment']
        orig_response = first_budget['Response']
        orig_month = first_budget['Month']
        orig_budget = first_budget['Budget']
        orig_teamid = first_budget['TeamID']
        test_budget_id = admindb.AdmIDs(prv_id=first_budget['ProviderID'],
                                        team_id=test_teamid,
                                        project_id=None,
                                        budget_id=first_budget['ID'],
                                        div_id=None)
        item = admindb.edit_budget_item(test_budget_id, orig_month,
                                        orig_budget, orig_comment,
                                        orig_response)
        self.assertEqual(len(item), 7)
        test_budgets = admindb.get_budget_items(test_budget_id,
                                                m_filter=None, bgt_filter=None)
        test_budget = test_budgets[0]
        self.assertEqual(test_budget['TeamID'], test_teamid)
        orig_budget_id = admindb.AdmIDs(prv_id=first_budget['ProviderID'],
                                        team_id=orig_teamid,
                                        project_id=None,
                                        budget_id=first_budget['ID'],
                                        div_id=None)
        orig_item = admindb.edit_budget_item(orig_budget_id,
                                             orig_month, orig_budget,
                                             orig_comment, orig_response)
        self.assertEqual(len(orig_item), 7)

    def test_insert_delete_budget_items(self):
        """
        Test the APIs used for admindb insert/delete budget.
        Insert budget, check it, delete it, check it.
        Requires at least one provider, and team.
        """
        prvid_test = 1
        teamid_test = 1
        budget_test = 2
        month_test = '2015-01'
        comment_test = 'please delete me.'
        response_test = 'Yes, please delete me.'
        new_budget_id = admindb.AdmIDs(prvid_test, teamid_test,
                                       project_id=None, budget_id=None,
                                       div_id=None)
        new_item = admindb.insert_budget_item(new_budget_id,
                                              my_month=month_test,
                                              my_budget=budget_test,
                                              my_comment=comment_test,
                                              my_response=response_test)

        self.assertEqual(new_item['ProviderID'], prvid_test)
        self.assertEqual(new_item['TeamID'], teamid_test)
        self.assertEqual(new_item['Budget'], budget_test)
        self.assertEqual(new_item['Month'], month_test)
        self.assertEqual(new_item['Comment'], comment_test)
        self.assertEqual(new_item['Response'], response_test)
        delete_budget_id = admindb.AdmIDs(prvid_test, teamid_test,
                                          project_id=None,
                                          budget_id=new_item['ID'],
                                          div_id=None)
        item = admindb.delete_budget_item(delete_budget_id,
                                          month_test, budget_test,
                                          comment_test)
        self.assertEqual(len(item), 7)
        test_budget = admindb.get_budget_items(delete_budget_id,
                                               m_filter=None, bgt_filter=None)
        null_list = []
        self.assertEqual(test_budget, null_list)

    def test_clone_delete_budget_items(self):
        """
        Test the APIs used for admindb cloning budget.
        Insert budget, clone budget, check it, delete all budgets from
        cloned month.
        """
        prvid_one = 1
        teamid_one = 3
        prvid_two = 2
        teamid_two = 1
        old_month_test = '2014-01'
        clone_month_test = '2014-02'
        budget_test = 2
        comment_test = 'please delete me.'
        response_test = 'Yes, please delete me.'
        clone_comment = 'Cloned from ' + old_month_test
        new_budget_one = admindb.AdmIDs(prvid_one, teamid_one,
                                        project_id=None, budget_id=None,
                                        div_id=None)
        new_item_one = admindb.insert_budget_item(new_budget_one,
                                                  my_month=old_month_test,
                                                  my_budget=budget_test,
                                                  my_comment=comment_test,
                                                  my_response=response_test)

        self.assertEqual(new_item_one['Month'], old_month_test)
        new_budget_two = admindb.AdmIDs(prvid_two, teamid_two,
                                        project_id=None, budget_id=None,
                                        div_id=None)
        new_item_two = admindb.insert_budget_item(new_budget_two,
                                                  my_month=old_month_test,
                                                  my_budget=budget_test,
                                                  my_comment=comment_test,
                                                  my_response=response_test)

        no_filter = admindb.AdmIDs(prv_id=None, team_id=None,
                                   project_id=None, budget_id=None,
                                   div_id=None)
        test_item2 = admindb.clone_budget_month(no_filter, old_month_test,
                                                clone_month_test)
        test_item2 = admindb.get_budget_items(ids=new_budget_two,
                                              m_filter=clone_month_test,
                                              bgt_filter=None)
        self.assertEqual(len(test_item2), 1)
        self.assertEqual(test_item2[0]['Budget'], budget_test)
        self.assertEqual(test_item2[0]['TeamID'], teamid_two)
        self.assertEqual(test_item2[0]['Month'], clone_month_test)
        self.assertEqual(test_item2[0]['Comment'], clone_comment)
        self.assertEqual(test_item2[0]['Response'], None)

        delete_items = admindb.get_budget_items(ids=no_filter,
                                                m_filter=clone_month_test,
                                                bgt_filter=None)

        for del_item in delete_items:
            delete_id = admindb.AdmIDs(prv_id=None, team_id=None,
                                       project_id=None,
                                       budget_id=del_item['ID'],
                                       div_id=None)
            item = admindb.delete_budget_item(delete_id,
                                              my_month=clone_month_test,
                                              my_budget=None,
                                              my_comment=None)
            self.assertEqual(len(item), 7)
        delete_budget_id = admindb.AdmIDs(prv_id=None, team_id=None,
                                          project_id=None,
                                          budget_id=new_item_two['ID'],
                                          div_id=None)
        item = admindb.delete_budget_item(delete_budget_id,
                                          my_month=old_month_test,
                                          my_budget=budget_test,
                                          my_comment=comment_test)
        self.assertEqual(len(item), 7)
        delete_budget_id = admindb.AdmIDs(prv_id=None, team_id=None,
                                          project_id=None,
                                          budget_id=new_item_one['ID'],
                                          div_id=None)
        item = admindb.delete_budget_item(delete_budget_id,
                                          my_month=old_month_test,
                                          my_budget=budget_test,
                                          my_comment=comment_test)
        self.assertEqual(len(item), 7)

    def test_all_get_provider_admin(self):
        """
        Test that all providers in MySQL have 4 fields
        """
        all_providers = admindb.AdmIDs(prv_id=None, team_id=None,
                                       project_id=None, budget_id=None,
                                       div_id=None)
        providers = admindb.get_providers_admin(ids=all_providers)
        for pkey in providers:
            self.assertEquals(len(pkey), 4)


    def test_get_team_items(self):
        """
        Test the API used for admindb team admin,
        returning the default (all team entries) dataset.
        """
        all_providers_projects_teams = admindb.AdmIDs(prv_id=None,
                                                      team_id=None,
                                                      project_id=None,
                                                      budget_id=None,
                                                      div_id=None)

        all_teams = admindb.get_team_items(all_providers_projects_teams,
                                           name_filter=None)
        for series in all_teams:
            self.assertEqual(len(series), 3)

    def test_edit_team_items(self):
        """
        Test the API used for admindb team admin edit.
        Edit teamname/DivID, check it, then return to original.
        Assert: at least one team in team table.
        """
        test_teamname = "__testing_please_ignore"
        test_divid = 1
        team_id_one = admindb.AdmIDs(prv_id=None, budget_id=None,
                                     project_id=None, team_id=1,
                                     div_id=None)
        team_list = admindb.get_team_items(team_id_one, name_filter=None)
        first_team = team_list[0]
        self.assertEqual(len(first_team), 3)
        orig_teamname = first_team['Name']
        orig_divid = first_team['DivisionID']
        team_id_test = admindb.AdmIDs(prv_id=None, budget_id=None,
                                      project_id=None, team_id=1,
                                      div_id=test_divid)
        item = admindb.edit_team_item(team_id_test, test_teamname)
        self.assertEqual(len(item), 3)
        test_teams = admindb.get_team_items(team_id_one, name_filter=None)
        test_team = test_teams[0]
        self.assertEqual(test_team['Name'], test_teamname)
        self.assertEqual(test_team['DivisionID'], test_divid)
        team_id_one.div = orig_divid
        orig_item = admindb.edit_team_item(team_id_one, orig_teamname)
        self.assertEqual(len(orig_item), 3)

    def test_insert_delete_team_items(self):
        """
        Test the APIs used for admindb insert/delete team.
        Insert team, check it, delete it, check it.
        Requires at least one provider, team, and division.
        """
        teamname_test = 'please delete my teamname'
        divid_test = 1
        new_team_id = admindb.AdmIDs(prv_id=None, budget_id=None,
                                     project_id=None, team_id=None,
                                     div_id=divid_test)
        new_item = admindb.insert_team_item(new_team_id,
                                            my_teamname=teamname_test)

        self.assertEqual(new_item['Name'], teamname_test)
        delete_team_id = admindb.AdmIDs(prv_id=None, budget_id=None,
                                        project_id=None, team_id=new_item['ID'],
                                        div_id=divid_test)
        item = admindb.delete_team_item(delete_team_id, teamname_test)
        self.assertEqual(len(item), 3)
        test_team = admindb.get_team_items(delete_team_id,
                                           name_filter=teamname_test)
        null_list = []
        self.assertEqual(test_team, null_list)

    def test_get_division_items(self):
        """
        Test the API used for admindb division admin,
        returning the default (all division entries) dataset.
        """
        all_providers_projects_teams = admindb.AdmIDs(prv_id=None,
                                                      team_id=None,
                                                      project_id=None,
                                                      budget_id=None,
                                                      div_id=None)

        all_divs = admindb.get_division_items(all_providers_projects_teams,
                                              name_filter=None)
        for series in all_divs:
            self.assertEqual(len(series), 2)

    def test_edit_division_items(self):
        """
        Test the API used for admindb division admin edit.
        Edit Divisionname, check it, then return to original.
        Assert: at least one division in table.
        """
        test_divname = "__testing_please_ignore"
        test_divid = 1
        div_id_one = admindb.AdmIDs(prv_id=None, budget_id=None,
                                    project_id=None, team_id=None,
                                    div_id=test_divid)
        div_list = admindb.get_division_items(div_id_one, name_filter=None)
        first_div = div_list[0]
        self.assertEqual(len(first_div), 2)
        orig_divname = first_div['Name']
        item = admindb.edit_division_item(div_id_one, test_divname)
        self.assertEqual(len(item), 2)
        test_divs = admindb.get_division_items(div_id_one, name_filter=None)
        test_div = test_divs[0]
        self.assertEqual(test_div['Name'], test_divname)
        self.assertEqual(test_div['ID'], test_divid)
        orig_item = admindb.edit_division_item(div_id_one, orig_divname)
        self.assertEqual(len(orig_item), 2)

    def test_insert_delete_div_items(self):
        """
        Test the APIs used for admindb insert/delete division.
        Insert division, delete it, check it.
        """
        divname_test = 'please delete my division'
        all_ids = admindb.AdmIDs(prv_id=None,
                                 team_id=None,
                                 project_id=None,
                                 budget_id=None,
                                 div_id=None)

        new_item = admindb.insert_division_item(ids=all_ids,
                                                my_divname=divname_test)

        self.assertEqual(new_item['Name'], divname_test)
        delete_div_id = admindb.AdmIDs(prv_id=None, budget_id=None,
                                       project_id=None, team_id=None,
                                       div_id=new_item['ID'])
        item = admindb.delete_division_item(delete_div_id, divname_test)
        self.assertEqual(len(item), 2)
        test_division = admindb.get_division_items(delete_div_id,
                                                   name_filter=divname_test)
        null_list = []
        self.assertEqual(test_division, null_list)

    def test_get_project_items(self):
        """
        Test the API used for admindb project admin,
        returning the default (all project entries) dataset.
        """
        all_providers_projects_teams = admindb.AdmIDs(prv_id=None, team_id=None,
                                                      project_id=None,
                                                      budget_id=None,
                                                      div_id=None)
        all_projects = admindb.get_project_items(all_providers_projects_teams,
                                                 name_filter=None,
                                                 extid_filter=None)
        for series in all_projects:
            self.assertEqual(len(series), 5)

    def test_edit_project_items(self):
        """
        Test the API used for admindb project admin edit.
        Edit ExtName, check it, then return to original.
        Assert: at least one project in projects table.
        """
        test_extname = "temporary name only"
        project_id_one = admindb.AdmIDs(prv_id=None, team_id=None,
                                        budget_id=None, project_id=1,
                                        div_id=None)
        project_list = admindb.get_project_items(project_id_one,
                                                 name_filter=None,
                                                 extid_filter=None)
        first_project = project_list[0]
        self.assertEqual(len(first_project), 5)
        orig_extname = first_project['ExtName']
        orig_extid = first_project['ExtID']
        test_project_id = admindb.AdmIDs(prv_id=first_project['ProviderID'],
                                         team_id=first_project['TeamID'],
                                         budget_id=None,
                                         project_id=first_project['ID'],
                                         div_id=None)
        item = admindb.edit_project_item(test_project_id,
                                         my_extname=test_extname,
                                         my_extid=orig_extid)
        self.assertEqual(len(item), 5)
        test_projects = admindb.get_project_items(test_project_id,
                                                  name_filter=None,
                                                  extid_filter=None)
        test_project = test_projects[0]
        self.assertEqual(test_project['ExtName'], test_extname)
        orig_item = admindb.edit_project_item(test_project_id,
                                              my_extname=orig_extname,
                                              my_extid=orig_extid)
        self.assertEqual(len(orig_item), 5)

    def test_ins_del_project_items(self):
        """
        Test the APIs used for admindb insert/delete project.
        Insert project, check it, delete it, check it.
        Requires at least one provider, and team.
        """
        prvid_test = 1
        teamid_test = 1
        extname_test = 'My external test name'
        extid_test = 'My test id is external'
        new_project_id = admindb.AdmIDs(prvid_test, teamid_test,
                                        project_id=None, budget_id=None,
                                        div_id=None)
        new_item = admindb.insert_project_item(new_project_id,
                                               my_extname=extname_test,
                                               my_extid=extid_test)

        self.assertEqual(new_item['ProviderID'], prvid_test)
        self.assertEqual(new_item['TeamID'], teamid_test)
        self.assertEqual(new_item['ExtName'], extname_test)
        self.assertEqual(new_item['ExtID'], extid_test)
        self.assertGreater(new_item['ID'], 0)
        delete_project_id = admindb.AdmIDs(prvid_test, teamid_test,
                                           project_id=new_item['ID'],
                                           budget_id=None,
                                           div_id=None)
        item = admindb.delete_project_item(delete_project_id,
                                           my_extname=extname_test,
                                           my_extid=extid_test)
        self.assertEqual(len(item), 5)
        test_project = admindb.get_project_items(delete_project_id,
                                                 name_filter=None,
                                                 extid_filter=None)
        null_list = []
        self.assertEqual(test_project, null_list)

if __name__ == "__main__":
    unittest.main()
