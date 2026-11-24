import unittest
from kgc.research.structure_cases import comparison_categories


class CaseCategoryTests(unittest.TestCase):
    def test_success_and_relative_winner_change_are_separate(self):
        yes={"hits1":1};no={"hits1":0,"covered":True,"true_returned":True}
        labels=comparison_categories(yes,no,yes,yes,yes)
        self.assertIn("relative_winner_changed",labels)
        self.assertIn("neural_success_lost",labels)
        self.assertIn("general_rule_success_embedding_miss",labels)
        self.assertNotIn("rule_success_lost",labels)
        labels=comparison_categories(no,yes,no,no,no)
        self.assertIn("embedding_success_all_rules_miss",labels)
        self.assertIn("embedding_success_general_rules_miss",labels)

    def test_coverage_and_truth_generation_do_not_define_correctness(self):
        no={"hits1":0,"covered":True,"true_returned":True}
        self.assertEqual(comparison_categories(no,no,no,no,no),[])
