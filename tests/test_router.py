"""Regression tests for intent routing, especially attendance policy vs math."""
import unittest

from agent.router import classify


class IntentRoutingTests(unittest.TestCase):
    def test_requested_routes(self):
        cases = {
            "What is the minimum attendance requirement?": "rag",
            "I attended 36 out of 50 classes. Calculate my attendance.": "attendance",
            "What is the attendance policy?": "rag",
            "How many classes do I need to attend to reach 75%?": "attendance",
            "What percentage attendance is required?": "rag",
            "I attended 40 out of 50 classes. What is my attendance percentage?": "attendance",
            "I have exams in 10 days and 4 subjects. Create a study plan.": "study_plan",
            "When is the NLP assignment due?": "deadline",
            "Explain what NLP is.": "general",
            "What is the weather today?": "unsupported",
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(classify(query), expected)

    def test_policy_language_never_selects_calculator_by_itself(self):
        queries = (
            "What is the college attendance policy?",
            "What happens if my attendance is below 75%?",
            "What are the attendance rules?",
            "How much attendance do I need to maintain?",
            "Is 75% attendance compulsory?",
            "Are there any rules for low attendance?",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertEqual(classify(query), "rag")

    def test_calculation_language_selects_calculator(self):
        queries = (
            "I attended 40 classes out of 50. What is my percentage?",
            "My attendance is 72%. How many classes do I need to attend to reach 75%?",
            "How many classes can I miss and still maintain 75%?",
            "I have attended 36 classes and missed 14. Calculate my attendance.",
            "I went to 36 classes out of 50.",
            "I missed 8 classes out of 40, calculate my attendance.",
            "i attended 36/50 what is my attendance",
            "need 75% how many more classes",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertEqual(classify(query), "attendance")

    def test_informal_study_planning_variations(self):
        queries = (
            "I have 5 subjects, 20 days remaining and I can study for 3 hours per day",
            "I have 5 subjects and only 20 days left. I study 3 hrs daily.",
            "5 subjects, 20 days, 3 hours a day. Make a plan.",
            "I've got 20 days for 5 subjects and can study 3 hours every day.",
            "My exams are in 20 days and I have 5 subjects. I can give 3 hours daily.",
            "Can you make me a timetable? I have 20 days and 5 subjects.",
            "How should I divide my 3 hours between my 5 subjects?",
            "Help me plan my preparation for the next 20 days.",
            "can u make a timetable i got 5 subj n 20 days",
            "I have 2 weeks left and don't know how to divide my study time",
            "I can study 4 hrs every day. How should I prepare?",
            "My exams are next month. How should I prepare?",
            "Create a 7-day revision plan.",
        )
        for query in queries:
            with self.subTest(query=query):
                self.assertEqual(classify(query), "study_plan")

    def test_informal_deadline_and_document_questions(self):
        deadline_queries = (
            "When is my DBMS assignment due?",
            "What's the last date for DBMS?",
            "When do I have to submit DBMS?",
            "When is the DBMS submission?",
            "I need to submit DBMS soon. When is it due?",
            "Tell me the deadline for DBMS.",
        )
        rag_queries = (
            "what's the min attendance",
            "What is the required attendance percentage?",
            "Tell me about the attendance rules",
            "What are the rules for internal assessment?",
            "What is mentioned in the academic guidelines?",
            "What documents do I need?",
        )
        for query in deadline_queries:
            with self.subTest(query=query):
                self.assertEqual(classify(query), "deadline")
        for query in rag_queries:
            with self.subTest(query=query):
                self.assertEqual(classify(query), "rag")

    def test_general_academic_and_unsupported_external_queries(self):
        general = (
            "What is NLP?",
            "Explain machine learning",
            "What is TCP?",
            "How does a compiler work?",
            "Explain inheritance in Java",
            "What is quantum entanglement?",
        )
        unsupported = (
            "What's the weather today?",
            "Who won today's match?",
            "What is today's stock price?",
            "What is the current Bitcoin price?",
        )
        for query in general:
            with self.subTest(query=query):
                self.assertEqual(classify(query), "general")
        for query in unsupported:
            with self.subTest(query=query):
                self.assertEqual(classify(query), "unsupported")

    def test_ambiguous_personal_attendance_asks_for_clarification(self):
        self.assertEqual(classify("My attendance is low."), "clarify")


if __name__ == "__main__":
    unittest.main()
