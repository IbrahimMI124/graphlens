"""Pure paired-outcome tests; no graph/model backend or experimental execution."""
import unittest
from kgc.research.structure_report import frozen_family_gap


def outcomes(values,certified=True):
    if len(values)!=6:raise ValueError("This fixture has three triples and both directions")
    return [{"query_id":f"test:{i//2}:{direction}","triple_id":f"test:{i//2}",
             "head":f"h{i//2}","relation":"r","tail":f"t{i//2}","direction":direction,
             "hits1":value,"hits_certified":certified}
            for i,(direction,value) in enumerate(zip(("head","tail")*3,values))]


class FrozenFamilyGapTests(unittest.TestCase):
    def test_known_difference_in_differences_and_unique_sample_size(self):
        result=frozen_family_gap(
            general_t=outcomes([1]*6),general_c=outcomes([0]*6),
            constants_t=outcomes([0]*6),constants_c=outcomes([1]*6),
            repetitions=50)
        # Treatment family gap is +1, control family gap is -1.
        self.assertEqual(result["difference"],2)
        self.assertEqual((result["ci_low"],result["ci_high"]),(2,2))
        self.assertEqual(result["n_unique_queries"],6)
        self.assertEqual(result["n_triples"],3)
        self.assertEqual(result["n_fixed_family_subsets"],2)
        self.assertEqual(result["n_treatment_models"],1)
        self.assertEqual(result["n_control_models"],1)
        self.assertTrue(result["all_rankings_certified"])

    def test_shared_triple_bootstrap_keeps_directions_and_families_paired(self):
        args={"general_t":outcomes([1,1,1,1,0,0]),"general_c":outcomes([0]*6),
              "constants_t":outcomes([0,0,0,0,1,1]),"constants_c":outcomes([0]*6),
              "repetitions":2000,"seed":2026}
        first=frozen_family_gap(**args);second=frozen_family_gap(**args)
        self.assertEqual(first,second)
        self.assertAlmostEqual(first["difference"],1/3)
        # Three cluster contrasts are +1,+1,-1, each containing both directions.
        # Their bootstrap lower 2.5% quantile is -1 (not a six-independent-query CI).
        self.assertEqual((first["ci_low"],first["ci_high"]),(-1,1))
        self.assertEqual(first["n_unique_queries"],6)
        self.assertEqual(first["n_triples"],3)

    def test_rejects_a_different_fact_in_any_of_the_four_sequences(self):
        for changed in range(4):
            with self.subTest(changed=changed):
                sequences=[outcomes([0]*6) for _ in range(4)]
                sequences[changed][2]["tail"]="another_entity"
                with self.assertRaisesRegex(ValueError,"identities"):
                    frozen_family_gap(*sequences,repetitions=5)

    def test_rejects_censored_or_missing_certification(self):
        sequences=[outcomes([0]*6) for _ in range(4)]
        sequences[2][0]["hits_certified"]=False
        with self.assertRaisesRegex(ValueError,"certified"):
            frozen_family_gap(*sequences,repetitions=5)
        for rows in sequences:
            for row in rows:row["hits_certified"]=False
        with self.assertRaisesRegex(ValueError,"certified"):
            frozen_family_gap(*sequences,repetitions=5)


if __name__=="__main__":unittest.main()
