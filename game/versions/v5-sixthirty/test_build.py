import contextlib
import copy
import io
import unittest

import build
import story


class ReadingBudgetTests(unittest.TestCase):
    def setUp(self):
        self.cards = copy.deepcopy(story.CARDS)
        self.meta = dict(cards=story.META, endings=story.ENDINGS)

    def validate(self):
        with contextlib.redirect_stdout(io.StringIO()):
            build.validate(self.cards, self.meta)

    def test_current_deck_fits(self):
        self.validate()

    def test_each_visible_field_rejects_overlong_copy(self):
        for field, limit in build.COPY_LIMITS.items():
            with self.subTest(field=field):
                self.cards = copy.deepcopy(story.CARDS)
                self.cards[0][field] = '字' * (limit + 1)
                with self.assertRaisesRegex(SystemExit, '超出阅读预算'):
                    self.validate()

    def test_paragraphs_and_rendered_names_count(self):
        self.cards[0]['question'] = '先读背景。\n然后再选。'
        with self.assertRaisesRegex(SystemExit, '不分段讲故事'):
            self.validate()
        self.cards = copy.deepcopy(story.CARDS)
        self.cards[0]['answer_no'] = '{maker}' * 6
        with self.assertRaisesRegex(SystemExit, '超出阅读预算'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
