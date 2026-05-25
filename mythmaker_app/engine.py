from __future__ import annotations

from dataclasses import dataclass, asdict
import html
import random
import re
import time
from typing import Any


PRIMES = [17, 19, 23, 29, 31, 37, 41]
MOODS = ["bloom", "still", "fracture", "echo", "spiral", "bind", "honour", "void"]
MODES = ["Random", "Bottom House", "Therapy Under The Stairs", "Five-a-Side", "Cult Drift", "Collision"]
DRIFT_TYPES = ["preserve", "fragment", "distort", "invert", "amplify", "misremember"]

MODE_SETUPS = {
    "Bottom House": [
        "The house meeting begins because nobody can prove the chair was always there.",
        "A normal evening tries to enter the room and is immediately outvoted.",
        "The kettle clicks once, which everyone agrees is either prophecy or poor maintenance.",
    ],
    "Therapy Under The Stairs": [
        "The cupboard is taking walk-ins, but only for problems that smell faintly of mop water.",
        "A breakthrough is scheduled for half past never, beneath the coats.",
        "The stairs creak in a tone usually reserved for clinical supervision.",
    ],
    "Five-a-Side": [
        "Two jumpers become goalposts and the room instantly develops a league table.",
        "Kick-off is delayed while gravity checks everyone's emotional studs.",
        "The damp patch is declared playable after a short theological inspection.",
    ],
    "Cult Drift": [
        "Someone says 'quick announcement' and the room accidentally becomes a movement.",
        "The minutes from the last meeting begin chanting in procedural order.",
        "A doctrine forms near the radiator and asks whether snacks are provided.",
    ],
    "Collision": [
        "Two beliefs enter the same hallway and only one remembers its shoes.",
        "The room detects a contradiction and starts moving the furniture into evidence.",
        "Everyone speaks at once, which briefly counts as a legal weather event.",
    ],
}

MODE_NARRATORS = {
    "Bottom House": [
        "The sofa is keeping score, badly.",
        "The telly goes silent because even it wants to hear this nonsense out.",
        "A biscuit is raised as a point of order.",
    ],
    "Therapy Under The Stairs": [
        "The clipboard nods like it has seen this exact crisis in laminate form.",
        "Someone writes 'door hinge' in the feelings column.",
        "The mop maintains professional boundaries by falling over.",
    ],
    "Five-a-Side": [
        "The scoreboard reads nil-nil, but spiritually everyone is suspended.",
        "VAR checks the footage and finds three new emotions.",
        "The jumpers refuse to confirm which one is the north goal.",
    ],
    "Cult Drift": [
        "The agenda is misread as scripture.",
        "A show of hands becomes a minor constitution.",
        "The doctrine passes, fails, then asks to be remembered differently.",
    ],
    "Collision": [
        "The hallway attempts mediation and loses its deposit.",
        "A silence forms, panics, and asks for legal advice.",
        "The contradiction becomes visible enough to need a coaster.",
    ],
}

CLOSING_STINGS = [
    "The kettle applauds once and denies it.",
    "The stairs request a sequel in writing.",
    "Somewhere under the house, a mop achieves closure.",
    "The final whistle is played on an opera note nobody can afford.",
    "The remote pauses reality, but only during Auntie Brenda's sentence.",
    "A seventh step appears on the staircase and immediately asks for rent.",
    "The fridge hums the theme tune from a sitcom nobody remembers filming.",
]


@dataclass
class CharacterTrace:
    name: str
    glyph: str
    prime: int
    seed: int
    trace: list[int]
    mood: str
    phrase: str
    original_creed: str
    drift_type: str
    drifted_creed: str
    signature: str


def generate_scene(state: dict[str, Any], options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate a deterministic absurd sitcom scene from a seed bank.

    The same state/options/seed combination produces the same scene. If no seed
    is supplied, a timestamp seed is created and returned so the scene can be
    regenerated exactly later.
    """

    options = options or {}
    seed = _coerce_seed(options.get("seed"))
    if seed is None:
        seed = int(time.time() * 1000) % 1_000_000_000
    rng = random.Random(seed)

    mode = str(options.get("mode") or "Random")
    if mode not in MODES:
        mode = "Random"
    resolved_mode = _resolve_mode(mode, rng)
    weirdness = _clamp_int(options.get("weirdness"), 0, 100, 55)
    cast_size = _clamp_int(options.get("cast_size"), 2, 5, 4)

    characters = _ensure_list(state.get("characters"))
    places = _ensure_list(state.get("places"))
    phrases = _ensure_str_list(state.get("phrases"))
    relics = _ensure_list(state.get("relics"))
    rules = _ensure_list(state.get("rules"))

    cast = _sample_cast(characters, cast_size, rng)
    place = rng.choice(places) if places else _fallback_place()
    relic = rng.choice(relics) if relics else _fallback_relic()
    rule = rng.choice(rules) if rules else _fallback_rule()

    traces = [_build_character_trace(character, idx, weirdness, rng) for idx, character in enumerate(cast)]
    callback = _choose_callback(resolved_mode, traces, place, relic, rng)
    collision = _resolve_collision(resolved_mode, traces, place, relic, rule, weirdness, callback, rng)
    title = _scene_title(resolved_mode, place, relic, collision, rng)
    beats = _build_beats(resolved_mode, traces, place, relic, collision, callback, rng)
    script_lines = _render_dialogue(title, resolved_mode, traces, place, relic, phrases, collision, weirdness, callback, beats, rng)
    trace_lines = _render_trace_lines(traces, collision, rule)
    script = "\n".join(script_lines + ["", "WHY THIS HAPPENED"] + trace_lines)

    return {
        "seed": seed,
        "mode": resolved_mode,
        "requested_mode": mode,
        "weirdness": weirdness,
        "cast_size": len(traces),
        "title": title,
        "setting": _safe_get(place, "name", "Unknown Room"),
        "setting_texture": _safe_get(place, "texture", ""),
        "relic": _safe_get(relic, "name", "Unlabelled Relic"),
        "callback": callback,
        "beats": beats,
        "collision": collision,
        "cast": [asdict(trace) for trace in traces],
        "script_lines": script_lines,
        "trace_lines": trace_lines,
        "script": script,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def scene_to_text(scene: dict[str, Any]) -> str:
    return str(scene.get("script") or "")


def scene_to_html(scene: dict[str, Any]) -> str:
    title = html.escape(str(scene.get("title") or "MythMaker Scene"))
    body = html.escape(scene_to_text(scene))
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{title}</title>"
        "<style>body{font-family:Georgia,serif;max-width:860px;margin:40px auto;"
        "padding:0 20px;line-height:1.55;background:#fffaf2;color:#171312}"
        "pre{white-space:pre-wrap;background:#fff;border:1px solid #e1d7c6;"
        "border-radius:8px;padding:20px}</style></head><body>"
        f"<h1>{title}</h1><pre>{body}</pre></body></html>"
    )


def _build_character_trace(character: dict[str, Any], idx: int, weirdness: int, rng: random.Random) -> CharacterTrace:
    name = _safe_get(character, "name", f"Unclaimed Character {idx + 1}")
    glyph = _safe_get(character, "glyph", name[:1].upper() or "?")
    creed = _safe_get(character, "creed", "Meaning forgot its shoes")
    phrases = _ensure_str_list(character.get("phrases")) or [_safe_get(character, "voice", "I am narratively available.")]

    prime = rng.choice(PRIMES)
    seed = rng.randint(1, prime - 1)
    trace = _prime_trace(seed, prime, name, idx)
    mood = rng.choice(MOODS)
    phrase = rng.choice(phrases)
    drift_type = _choose_drift(weirdness, rng)
    drifted = _drift_creed(creed, drift_type, rng)
    signature = f"{glyph}[{seed}] -> {trace[-1]} in Z{prime}"

    return CharacterTrace(
        name=name,
        glyph=glyph,
        prime=prime,
        seed=seed,
        trace=trace,
        mood=mood,
        phrase=phrase,
        original_creed=creed,
        drift_type=drift_type,
        drifted_creed=drifted,
        signature=signature,
    )


def _prime_trace(seed: int, prime: int, name: str, idx: int) -> list[int]:
    trace = [seed]
    name_score = sum(ord(ch) for ch in name)
    a = 1 + (name_score + idx) % 3
    b = 2 + (name_score // 3 + idx) % 7
    c = 1 + (name_score // 11 + idx) % 5
    for _ in range(6):
        x = trace[-1]
        trace.append((a * x * x + b * x + c) % prime)
    return trace


def _choose_drift(weirdness: int, rng: random.Random) -> str:
    if weirdness < 25:
        pool = ["preserve", "preserve", "amplify", "fragment"]
    elif weirdness < 55:
        pool = ["preserve", "fragment", "distort", "amplify", "misremember"]
    elif weirdness < 80:
        pool = ["fragment", "distort", "invert", "amplify", "misremember", "misremember"]
    else:
        pool = ["distort", "invert", "invert", "amplify", "misremember", "misremember"]
    return rng.choice(pool)


def _drift_creed(creed: str, drift_type: str, rng: random.Random) -> str:
    words = creed.split()
    if drift_type == "preserve":
        return creed
    if drift_type == "fragment":
        return (words[0] if words else creed) + " [...]"
    if drift_type == "distort":
        if " with " in f" {creed.lower()} ":
            return re.sub(r"\bwith\b", "against", creed, flags=re.IGNORECASE)
        if len(words) > 2:
            return " ".join(reversed(words))
        return creed[::-1]
    if drift_type == "invert":
        return "DO NOT " + creed.upper()
    if drift_type == "amplify":
        return creed.upper() + "!!"
    subject = rng.choice(["the stairs", "the kettle", "the shin pad", "a biscuit", "the damp patch"])
    return f"I distinctly remember {subject} saying: {creed}"


def _resolve_collision(
    mode: str,
    traces: list[CharacterTrace],
    place: dict[str, Any],
    relic: dict[str, Any],
    rule: dict[str, Any],
    weirdness: int,
    callback: str,
    rng: random.Random,
) -> dict[str, Any]:
    endings = [trace.trace[-1] for trace in traces]
    midpoint = sum(endings) // max(len(endings), 1)
    shared_moods = sorted({trace.mood for trace in traces})
    place_name = _safe_get(place, "name", "the room")
    relic_name = _safe_get(relic, "name", "the relic")

    if mode == "Therapy Under The Stairs":
        kind = "therapy_session"
        action = f"{traces[0].name} is asked to describe {relic_name} without blaming {callback}."
    elif mode == "Five-a-Side":
        kind = "match_incident"
        action = f"A free kick is awarded because {relic_name} has become emotionally offside near {callback}."
    elif mode == "Cult Drift":
        kind = "sect_formation"
        action = f"The room forms the Council of {shared_moods[0].title()} {midpoint} and appoints {callback} as doctrine."
    elif mode == "Collision":
        kind = rng.choice(["fusion", "repulsion", "hybrid", "narrator_intervention"])
        action = _collision_action(kind, traces, relic_name, midpoint)
    elif mode == "Bottom House":
        kind = rng.choice(["therapy_session", "match_incident", "sect_formation", "narrator_intervention"])
        action = _collision_action(kind, traces, relic_name, midpoint)
    else:
        if weirdness > 75:
            kind = rng.choice(["sect_formation", "hybrid", "match_incident"])
        else:
            kind = rng.choice(["fusion", "repulsion", "therapy_session", "narrator_intervention"])
        action = _collision_action(kind, traces, relic_name, midpoint)

    return {
        "kind": kind,
        "midpoint": midpoint,
        "shared_moods": shared_moods,
        "action": action,
        "rule": _safe_get(rule, "name", "Unwritten Rule"),
        "place_pressure": place_name,
        "relic_power": _safe_get(relic, "power", "makes the scene slightly worse"),
        "callback": callback,
    }


def _collision_action(kind: str, traces: list[CharacterTrace], relic_name: str, midpoint: int) -> str:
    first = traces[0].name if traces else "Someone"
    second = traces[1].name if len(traces) > 1 else "the wallpaper"
    if kind == "fusion":
        return f"{first} and {second} briefly become one person with two apologies."
    if kind == "repulsion":
        return f"{first} rejects {second}'s creed so hard the sofa moves three inches."
    if kind == "hybrid":
        return f"{relic_name} produces a third opinion called Place Remember {midpoint}."
    if kind == "therapy_session":
        return f"{first} is sent under the stairs for a breakthrough nobody ordered."
    if kind == "match_incident":
        return f"{second} scores with {relic_name}, but the goal is ruled mythological."
    if kind == "sect_formation":
        return f"The cast forms a tiny sect around {relic_name} and elects the mop treasurer."
    return f"The narrator interrupts before {first} can legally become a weather system."


def _choose_callback(
    mode: str,
    traces: list[CharacterTrace],
    place: dict[str, Any],
    relic: dict[str, Any],
    rng: random.Random,
) -> str:
    names = [trace.name for trace in traces]
    household_bits = [
        "the heroic chair",
        "the emotional mop",
        "the judgement fridge",
        "the seventh stair",
        "the biscuit minutes",
        "the jumper goalposts",
        "the damp patch",
        _safe_get(relic, "name", "the relic"),
        _safe_get(place, "name", "the room"),
    ]
    mode_bits = {
        "Therapy Under The Stairs": ["the clipboard", "the coping cupboard", "the hinge with boundaries"],
        "Five-a-Side": ["the shin pad", "the tiny whistle", "the offside line of the soul"],
        "Cult Drift": ["the agenda", "the ceremonial coaster", "the minutes everyone signed by accident"],
        "Collision": ["the hallway evidence", "the moving sofa", "the apology with two shadows"],
        "Bottom House": ["the remote", "the kettle prophecy", "Auntie Brenda's coaster"],
    }
    pool = household_bits + mode_bits.get(mode, []) + names
    return rng.choice([item for item in pool if item])


def _build_beats(
    mode: str,
    traces: list[CharacterTrace],
    place: dict[str, Any],
    relic: dict[str, Any],
    collision: dict[str, Any],
    callback: str,
    rng: random.Random,
) -> dict[str, str]:
    setup = rng.choice(MODE_SETUPS.get(mode, MODE_SETUPS["Bottom House"]))
    narrator = rng.choice(MODE_NARRATORS.get(mode, MODE_NARRATORS["Bottom House"]))
    first = traces[0].name if traces else "Someone"
    second = traces[1].name if len(traces) > 1 else "the wallpaper"
    relic_name = _safe_get(relic, "name", "the relic")
    place_name = _safe_get(place, "name", "the room")
    escalation = rng.choice(
        [
            f"{first} tries to make it normal, which is how {relic_name} gets promoted.",
            f"{second} demands evidence, so {place_name} starts presenting exhibits.",
            f"{callback.title()} is mentioned twice and therefore becomes plot.",
            f"The prime trace lands on {collision['midpoint']} and everyone pretends that helps.",
        ]
    )
    payoff = rng.choice(
        [
            f"The callback returns as {callback}, now with authority nobody remembers granting.",
            f"Everyone agrees the incident was avoidable, then schedules it weekly.",
            f"{relic_name} is placed in the centre of the room like that explains anything.",
            f"The room briefly becomes sensible, hates it, and reverts.",
        ]
    )
    return {"setup": setup, "narrator": narrator, "escalation": escalation, "payoff": payoff}


def _render_dialogue(
    title: str,
    mode: str,
    traces: list[CharacterTrace],
    place: dict[str, Any],
    relic: dict[str, Any],
    phrases: list[str],
    collision: dict[str, Any],
    weirdness: int,
    callback: str,
    beats: dict[str, str],
    rng: random.Random,
) -> list[str]:
    setting = _safe_get(place, "name", "Unknown Room")
    texture = _safe_get(place, "texture", "")
    relic_name = _safe_get(relic, "name", "Unlabelled Relic")
    phrase = rng.choice(phrases) if phrases else "The cupboard has no comment."
    cast_line = ", ".join(trace.name for trace in traces)
    script = [
        title.upper(),
        "",
        f"Setting: {setting} - {texture}",
        f"Cast: {cast_line}",
        f"Mode: {mode} | Weirdness: {weirdness}",
        f"Relic: {relic_name}",
        f"Callback: {callback}",
        "",
        "Cold Open:",
        f"Narrator: {beats['setup']}",
        f"Narrator: {phrase}",
        "",
        "Scene:",
        f"Narrator: {beats['narrator']}",
    ]

    for idx, trace in enumerate(traces):
        partner = traces[(idx + 1) % len(traces)].name if traces else "nobody"
        line = _character_line(trace, partner, relic_name, collision, mode, callback, idx, rng)
        script.append(f"{trace.name}: {line}")
        if idx == 1:
            script.append(f"Narrator: {beats['escalation']}")

    if collision["kind"] == "therapy_session":
        script.extend(
            [
                "GPT Under The Stairs: And how long have we been projecting ambition onto household storage?",
                f"Narrator: {traces[0].name} writes '{callback}' under emergency contacts.",
            ]
        )
    elif collision["kind"] == "match_incident":
        script.extend(
            [
                "The Referee of Truth: Whistle. That goal has unresolved theology.",
                f"Narrator: {relic_name} is booked after {callback} appeals for a throw-in.",
            ]
        )
    elif collision["kind"] == "sect_formation":
        script.extend(
            [
                "Auntie Brenda of the Remote: I've seen better cults at bingo.",
                f"Narrator: The new doctrine passes unanimously after everyone misunderstands {callback}.",
            ]
        )
    else:
        script.append(f"Narrator: {collision['action']}")

    script.extend(["", "Callback:", f"Narrator: {beats['payoff']}"])
    script.extend(
        [
            "",
            "Closing Sting:",
            rng.choice(CLOSING_STINGS),
        ]
    )
    return script


def _character_line(
    trace: CharacterTrace,
    partner: str,
    relic_name: str,
    collision: dict[str, Any],
    mode: str,
    callback: str,
    idx: int,
    rng: random.Random,
) -> str:
    common = [
        f"{trace.phrase} My creed has drifted into '{trace.drifted_creed}', and I want that noted before {partner} starts pointing.",
        f"I moved {trace.signature} and landed on {trace.trace[-1]}, so legally {relic_name} owes the room an explanation.",
        f"My mood is {trace.mood}. I am trying to be normal, but {collision['place_pressure']} keeps behaving like a witness.",
        f"{partner}, if your glyph touches my trace again, I am putting {callback} in charge of the meeting.",
    ]
    mode_templates = {
        "Therapy Under The Stairs": [
            f"I came here for closure and the cupboard handed me {callback} with a consent form.",
            f"My inner child says {relic_name} started it, and honestly that child has minutes.",
            f"Can we pause? The stairs are reflecting back my footwork.",
            f"{trace.phrase} Also, my trace ends at {trace.trace[-1]}, which feels clinically relevant.",
            f"I tried naming the feeling, but it answered to '{trace.drifted_creed}'.",
        ],
        "Five-a-Side": [
            f"I am not saying {partner} fouled me, but {callback} has gone down very theatrically.",
            f"The whistle blew at {trace.trace[-1]}, which means {relic_name} is either offside or ordained.",
            f"I want VAR, tea, and a ruling on whether feelings count as studs up.",
            f"{trace.phrase} If that is not a booking, then gravity has lost the room.",
            f"My creed drifted into '{trace.drifted_creed}' during injury time.",
        ],
        "Cult Drift": [
            f"I second the motion that {callback} becomes sacred, but only until the adverts.",
            f"Our doctrine is '{trace.drifted_creed}', which is worrying because I only meant to ask for crisps.",
            f"If this is a sect, {partner} is treasurer because they look guilty near stationery.",
            f"{trace.phrase} I propose we misunderstand that unanimously.",
            f"The trace says {trace.trace[-1]}, so I have made badges.",
        ],
        "Collision": [
            f"My belief and {partner}'s belief have touched elbows and now the hallway needs a mediator.",
            f"{relic_name} produced a third opinion, and it looks suspiciously like {callback}.",
            f"I reject this contradiction unless it comes with biscuits and a witness statement.",
            f"{trace.phrase} This is not a paradox. This is bad room management.",
            f"My trace ended at {trace.trace[-1]} and immediately asked for a chair.",
        ],
        "Bottom House": [
            f"I vote we blame {callback}, then pretend this was an established house rule.",
            f"The telly has gone quiet, which means either truth is near or Auntie Brenda found the batteries.",
            f"I tried being reasonable, but {relic_name} started vibrating in a legal tone.",
            f"{trace.phrase} That is my official statement and my snack position.",
            f"My creed drifted into '{trace.drifted_creed}', so the chair is now involved.",
        ],
    }
    mode_specific = mode_templates.get(mode, [])
    if mode_specific and idx < len(mode_specific):
        return mode_specific[idx % len(mode_specific)]
    templates = common + mode_specific
    return templates[(trace.trace[-1] + idx + rng.randrange(len(templates))) % len(templates)]


def _render_trace_lines(traces: list[CharacterTrace], collision: dict[str, Any], rule: dict[str, Any]) -> list[str]:
    lines = [
        f"Rule triggered: {_safe_get(rule, 'name', 'Unwritten Rule')} - {_safe_get(rule, 'text', '')}",
        f"Collision: {collision['kind']} | midpoint={collision['midpoint']} | action={collision['action']}",
        f"Callback chosen: {collision.get('callback', 'none')}",
    ]
    for trace in traces:
        lines.append(
            f"- {trace.name}: prime Z{trace.prime}, seed {trace.seed}, trace {trace.trace}, "
            f"mood={trace.mood}, drift={trace.drift_type}, signature={trace.signature}"
        )
    return lines


def _scene_title(mode: str, place: dict[str, Any], relic: dict[str, Any], collision: dict[str, Any], rng: random.Random) -> str:
    place_name = _safe_get(place, "name", "Bottom House")
    relic_name = _safe_get(relic, "name", "The Object")
    endings = {
        "therapy_session": "Therapy Under The Stairs",
        "match_incident": "Five-a-Side With Consequences",
        "sect_formation": "The Cult That Forgot Its Agenda",
        "fusion": "Two Apologies In A Coat",
        "repulsion": "The Sofa Moves Three Inches",
        "hybrid": "Place Remembered The Wrong Number",
        "narrator_intervention": "The Narrator Files A Complaint",
    }
    suffix = endings.get(collision["kind"], "A Small Myth Happens")
    if mode == "Bottom House":
        return f"{place_name}: {suffix}"
    if rng.random() < 0.5:
        return f"{suffix} At {place_name}"
    return f"{relic_name} And {suffix}"


def _resolve_mode(mode: str, rng: random.Random) -> str:
    if mode == "Random":
        return rng.choice(MODES[1:])
    return mode


def _sample_cast(characters: list[dict[str, Any]], cast_size: int, rng: random.Random) -> list[dict[str, Any]]:
    if not characters:
        characters = [_fallback_character()]
    if len(characters) >= cast_size:
        return rng.sample(characters, cast_size)
    cast = list(characters)
    while len(cast) < cast_size:
        cast.append(rng.choice(characters))
    return cast


def _coerce_seed(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return abs(hash(str(value))) % 1_000_000_000


def _clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(low, min(high, parsed))


def _ensure_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _ensure_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _safe_get(item: dict[str, Any], key: str, default: str) -> str:
    value = item.get(key) if isinstance(item, dict) else None
    return str(value).strip() if value not in (None, "") else default


def _fallback_character() -> dict[str, Any]:
    return {
        "name": "Someone From The Cupboard",
        "glyph": "?",
        "creed": "The room knows more than it admits",
        "phrases": ["I was not briefed on becoming mythological."],
    }


def _fallback_place() -> dict[str, Any]:
    return {"name": "Bottom House", "texture": "a room with strong opinions", "rules": []}


def _fallback_relic() -> dict[str, Any]:
    return {"name": "The Unlabelled Relic", "power": "causes mild narrative weather"}


def _fallback_rule() -> dict[str, Any]:
    return {"name": "The Unwritten Rule", "text": "If it moves, let it become lore."}
