import random


def roll_dice(sides=6, count=1):
    """Roll dice and return results."""
    sides = max(2, min(sides, 100))
    count = max(1, min(count, 20))
    results = [random.randint(1, sides) for _ in range(count)]
    return {
        "rolls": results,
        "total": sum(results),
        "sides": sides,
        "count": count
    }


TOOL_DEFINITION = {
    "name": "roll_dice",
    "description": "Wuerfelt mit einem oder mehreren Wuerfeln. Gibt die Einzelergebnisse und die Summe zurueck.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sides": {
                "type": "integer",
                "description": "Anzahl Seiten pro Wuerfel (Standard: 6)",
                "default": 6
            },
            "count": {
                "type": "integer",
                "description": "Anzahl der Wuerfel (Standard: 1)",
                "default": 1
            }
        },
        "required": []
    }
}
