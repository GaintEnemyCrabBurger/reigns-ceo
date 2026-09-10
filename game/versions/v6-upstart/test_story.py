"""Focused acceptance checks for the independent deck."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build  # noqa: E402
import story  # noqa: E402
import simulate  # noqa: E402


class StoryContractTests(unittest.TestCase):
    def test_deck_shape_and_build_contract(self):
        cards = story.CARDS
        self.assertGreaterEqual(len(cards), 80)
        self.assertEqual(sum(card["thematic"] == "open" for card in cards), 42)
        self.assertEqual(sum(card["thematic"] == "endings" for card in cards), 16)
        self.assertEqual(build.validate(cards), [])
        build.assert_source_fresh(build.load_cards())
        build.assert_artifacts_consistent(cards)

    def test_opening_and_promotion_pacing(self):
        cards = {card["card"]: card for card in story.CARDS}
        self.assertEqual(cards["intern_open"]["conditions"], "turn=1")
        self.assertIn(">_intern_audit", cards["intern_open"]["no_custom"])
        self.assertIn(">_intern_fix", cards["intern_open"]["yes_custom"])
        self.assertIn("manager_role", cards["intern_promotion"]["no_custom"])
        self.assertIn("manager_role", cards["intern_promotion"]["yes_custom"])
        self.assertIn("ceo_run", cards["ceo_crowning"]["no_custom"])
        self.assertIn("ceo_open=0", cards["ceo_first_reckoning"]["conditions"])

    def test_risky_choices_leave_route_trace(self):
        risky = []
        for card in story.CARDS:
            for side in ("no", "yes"):
                flags = card[f"{side}_custom"].split(" and ")
                if "risk+" in flags or "credit_hog" in flags:
                    risky.append((card["card"], side, "dirty_route" in flags))
        self.assertTrue(risky)
        self.assertTrue(all(has_trace for _, _, has_trace in risky))

    def test_all_story_endings_have_a_trigger(self):
        cards = story.CARDS
        names = {card["card"] for card in cards}
        explicit_targets = set()
        for card in cards:
            for side in ("no", "yes"):
                for token in card[f"{side}_custom"].split(" and "):
                    if token.startswith(">_"):
                        explicit_targets.add(token[2:])
        implicit = {
            "ending_cash_zero", "ending_cash_max", "ending_team_zero", "ending_team_max",
            "ending_market_zero", "ending_market_max", "ending_capital_zero", "ending_capital_max",
        }
        for card in cards:
            if card["thematic"] == "endings":
                self.assertIn(card["card"], explicit_targets | implicit)
                self.assertTrue(card["card"].startswith("ending_"))
                self.assertTrue(story.META[card["card"]].get("trigger"))
                self.assertEqual(card["conditions"], "")

    def test_ending_metadata_matches_explicit_entries(self):
        cards = story.CARDS
        expected = {
            card["card"]: []
            for card in cards
            if card["thematic"] == "endings"
        }
        for card in cards:
            if card["thematic"] == "endings":
                continue
            for side in ("no", "yes"):
                for raw_token in card[f"{side}_custom"].split(" and "):
                    token = raw_token.strip()
                    if token.startswith(">_ending_"):
                        ending_name = f"ending_{token[len('>_ending_'):]}"
                    elif token.startswith("end_"):
                        ending_name = f"ending_{token[len('end_'):]}"
                    else:
                        continue
                    if ending_name not in expected:
                        continue
                    expected[ending_name].append({
                        "card": card["card"],
                        "side": side,
                        "choice": card[f"override_{side}"],
                        "condition": card["conditions"],
                    })

        for ending_name, entries in expected.items():
            metadata = story.META[ending_name]
            self.assertEqual(metadata.get("entries", []), entries)
            if entries:
                self.assertEqual(metadata["trigger_type"], "explicit_choice")
                self.assertEqual(metadata["trigger"], "显式选择")
            else:
                self.assertEqual(metadata["trigger_type"], "resource_edge")
                self.assertTrue(metadata.get("trigger"))

    def test_card_copy_is_quick_to_read(self):
        for card in story.CARDS:
            self.assertLessEqual(len(card["question"]), 24, card["card"])
            self.assertLessEqual(len(card["override_no"]), 8, card["card"])
            self.assertLessEqual(len(card["override_yes"]), 8, card["card"])
            self.assertLessEqual(len(card["answer_no"]), 24, card["card"])
            self.assertLessEqual(len(card["answer_yes"]), 24, card["card"])
            for field in ("question", "answer_no", "answer_yes"):
                self.assertNotIn("\n", card[field], f"{card['card']}.{field}")
            if card["thematic"] == "endings":
                self.assertEqual(card["override_no"], "结束本局")
                self.assertEqual(card["override_yes"], "结束本局")

    def test_explicit_ending_actions_are_not_ambiguous(self):
        cards = {card["card"]: card for card in story.CARDS}
        self.assertIn(">_ending_sold", cards["exit_offer"]["no_custom"])
        self.assertIn(">_ending_sold", cards["board_budget"]["no_custom"])
        for name in ("exit_offer", "handover", "board_budget", "final_investigation", "scapegoat_offer", "final_clean", "final_black"):
            self.assertIn("ceo_open>=7", cards[name]["conditions"])
        for name in ("callback_team_credit", "callback_credit_hog", "callback_shared_secret"):
            self.assertEqual(cards[name]["lockturn"], "del")
        self.assertEqual(cards["market_fake"]["lockturn"], "8")

    def test_browser_ending_parser_only_accepts_explicit_tokens(self):
        engine = (HERE / "engine.js").read_text(encoding="utf-8")
        html = (HERE / "玩.html").read_text(encoding="utf-8")
        for artifact in (engine, html):
            self.assertIn("token.match(/^>_ending_", artifact)
            self.assertIn("token.match(/^end_", artifact)
            self.assertNotIn("str.indexOf(k)", artifact)
            self.assertIn("resourceEnding() || explicitEnding", artifact)

        self.assertIsNone(simulate.explicit_ending("scapegoat_ready and clean_ceo and company_sold"))
        self.assertEqual(simulate.explicit_ending(">_ending_sold"), "sold")
        self.assertEqual(simulate.explicit_ending("end_arrest"), "arrest")
        self.assertIsNone(simulate.explicit_ending(">_ending_not_registered"))

        for name in ("acting_crisis", "ceo_crowning"):
            card = next(card for card in story.CARDS if card["card"] == name)
            for side in ("no", "yes"):
                self.assertIsNone(simulate.explicit_ending(card[f"{side}_custom"]))

    def test_resource_edges_precede_plot_endings(self):
        edge_game = simulate.Game(17)
        edge_game.flags.update(ceo_run=1, ceo_open=7)
        edge_game.values["cash"] = 99
        edge_game.forced = simulate.BY_NAME["exit_offer"]
        self.assertEqual(edge_game.play(lambda *_: "no", max_turns=1), "cash_max")

        plot_game = simulate.Game(18)
        plot_game.flags.update(ceo_run=1, ceo_open=7)
        plot_game.forced = simulate.BY_NAME["exit_offer"]
        self.assertEqual(plot_game.play(lambda *_: "no", max_turns=1), "sold")

    def test_random_runs_reach_ceo(self):
        reached = 0
        for seed in range(100):
            game = simulate.Game(seed)
            game.play(simulate.policy_for("random"), max_turns=80)
            if any(flags.get("ceo_run") for *_, flags in game.history):
                reached += 1
        self.assertGreaterEqual(reached, 95)


if __name__ == "__main__":
    unittest.main()
