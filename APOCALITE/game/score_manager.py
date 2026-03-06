import json
import os

SCORE_FILE = "scores.json"

class ScoreManager:
    @staticmethod
    def load_scores():
        if not os.path.exists(SCORE_FILE):
            return []
        try:
            with open(SCORE_FILE, "r", encoding="utf-8") as f:
                scores = json.load(f)
                return sorted(scores, key=lambda x: x.get("score", 0), reverse=True)
        except Exception as e:
            print(f"Error loading scores: {e}")
            return []

    @staticmethod
    def save_score(name, score, character, time_survived, level, kills):
        scores = ScoreManager.load_scores()
        
        new_entry = {
            "name": name if name else "UNKNOWN",
            "score": int(score),
            "character": character,
            "time_survived": time_survived,
            "level": int(level),
            "kills": int(kills)
        }
        
        scores.append(new_entry)
        # Sort and keep top 10
        scores = sorted(scores, key=lambda x: x.get("score", 0), reverse=True)[:10]
        
        try:
            with open(SCORE_FILE, "w", encoding="utf-8") as f:
                json.dump(scores, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving score: {e}")
