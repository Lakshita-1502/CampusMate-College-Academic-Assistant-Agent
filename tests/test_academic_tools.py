"""Unit tests for deterministic academic tools."""
import unittest

from agent.parsing import attendance_counts, study_inputs
from agent.router import normalize_query
from tools.attendance import calculate_attendance
from tools.deadlines import get_assignment_deadline
from tools.study_planner import generate_study_plan


class AcademicToolTests(unittest.TestCase):
    def test_attendance_36_of_50(self):
        result = calculate_attendance(36, 50, 75)
        self.assertEqual(result["percentage"], 72)
        self.assertEqual(result["classes_needed"], 6)

    def test_study_plan_shape(self):
        plan = generate_study_plan(["NLP", "Compiler"], 3, 2)
        self.assertEqual(len(plan), 3)
        self.assertEqual(len(plan[0]["sessions"]), 4)

    def test_deadline_lookup(self):
        result = get_assignment_deadline("NLP")
        self.assertTrue(result["found"])
        self.assertEqual(result["deadlines"][0]["due_date"], "2026-10-05")

    def test_acceptance_study_query_preserves_all_inputs(self):
        query = normalize_query("I have 5 subjects, 20 days remaining and I can study for 3 hours per day")
        inputs = study_inputs(query)
        self.assertEqual(len(inputs["subjects"]), 5)
        self.assertEqual(inputs["days"], 20)
        self.assertEqual(inputs["hours_per_day"], 3)
        self.assertEqual(inputs["days"] * inputs["hours_per_day"], 60)
        plan = generate_study_plan(inputs["subjects"], inputs["days"], inputs["hours_per_day"])
        self.assertEqual(len(plan), 20)
        self.assertEqual(sum(len(day["sessions"]) for day in plan), 120)

    def test_informal_planner_abbreviations_and_week_conversion(self):
        query = normalize_query("I have 5 subj, 2 weeks left and can study 4 hrs daily")
        inputs = study_inputs(query)
        self.assertEqual(len(inputs["subjects"]), 5)
        self.assertEqual(inputs["days"], 14)
        self.assertEqual(inputs["hours_per_day"], 4)

    def test_named_subjects_and_month_horizon(self):
        query = normalize_query("Create a 1-month plan for NLP and Compiler, 2 hours per day")
        inputs = study_inputs(query)
        self.assertEqual(inputs["subjects"], ["nlp", "compiler"])
        self.assertEqual(inputs["days"], 30)
        self.assertEqual(inputs["hours_per_day"], 2)

    def test_attendance_count_phrasings(self):
        cases = (
            ("i attended 36/50 what is my attendance", (36, 50)),
            ("i went to 36 classes out of 50", (36, 50)),
            ("missed 8 classes out of 40, calculate attendance", (32, 40)),
            ("i attended 36 classes and missed 14", (36, 50)),
        )
        for query, expected in cases:
            with self.subTest(query=query):
                self.assertEqual(attendance_counts(normalize_query(query)), expected)


if __name__ == "__main__":
    unittest.main()
