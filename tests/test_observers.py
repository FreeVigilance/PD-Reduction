import unittest
from free_vigilance_reduction.reporting.observers import ConsoleObserver
from free_vigilance_reduction.entity_recognition.entity import Entity
from free_vigilance_reduction.reporting.reduction_report import ReductionReport


class TestConsoleObserver(unittest.TestCase):
    def setUp(self):
        self.observer = ConsoleObserver()
        self.sample_text = "Иван Иванович работает в Газпроме."
        self.entities = [
            Entity("Иван Иванович", "PER", 0, 13),
            Entity("Газпроме", "ORG", 25, 33)
        ]
        self.report = ReductionReport(
            original_text=self.sample_text,
            reduced_text="[PERSON] работает в [ORG].",
            entities=self.entities,
            replacements={"PER": ["Иван Иванович"], "ORG": ["Газпроме"]}
        )

    def test_on_process_start_with_text(self):
        try:
            self.observer.on_process_start(text=self.sample_text)
        except Exception as e:
            self.fail(f"on_process_start raised an exception: {e}")

    def test_on_entities_detected(self):
        try:
            self.observer.on_entities_detected(self.entities)
        except Exception as e:
            self.fail(f"on_entities_detected raised an exception: {e}")

    def test_on_text_reduced(self):
        try:
            self.observer.on_text_reduced(self.report.reduced_text)
        except Exception as e:
            self.fail(f"on_text_reduced raised an exception: {e}")

    def test_on_process_complete(self):
        try:
            self.observer.on_process_complete(self.report)
        except Exception as e:
            self.fail(f"on_process_complete raised an exception: {e}")

    def test_on_error(self):
        try:
            self.observer.on_error(ValueError("Тестовая ошибка"))
        except Exception as e:
            self.fail(f"on_error raised an exception: {e}")


if __name__ == '__main__':
    unittest.main()
