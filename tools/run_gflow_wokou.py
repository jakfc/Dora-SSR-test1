import subprocess
import os

OUT_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\raw_assets\gflow_sheets"
os.makedirs(OUT_DIR, exist_ok=True)

JOBS = [
    (
        "enemy_samurai_walk.png",
        "A clean horizontal 4-frame 2D game sprite sheet of a 16th-century wokou elite samurai raider (topknot hair with headband, fierce iron demon menpo mask, crimson-red #C53030 laced lamellar armor, dark trousers, straw sandals, holding a long curved odachi katana), marching walk cycle facing LEFT. 4 evenly spaced side-profile walking poses in one horizontal row, consistent head height and foot baseline. Flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), NO grid lines, NO boxes, NO text, NO drop shadow, isolated on a pure solid white background."
    ),
    (
        "enemy_samurai_slash_fall.png",
        "A clean horizontal 3-frame 2D game sprite sheet of a 16th-century wokou elite samurai raider (topknot hair with headband, fierce iron demon menpo mask, crimson-red #C53030 laced lamellar armor, straw sandals, long curved odachi katana), facing LEFT: frames 1-2 show a heavy two-handed overhead katana slash attack, frame 3 shows him defeated and collapsed flat on the ground. 3 evenly spaced side-profile figures in one horizontal row, flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), NO grid lines, NO boxes, NO text, NO drop shadow, isolated on a pure solid white background."
    ),
    (
        "enemy_boss_walk.png",
        "A clean horizontal 4-frame 2D game sprite sheet of a towering 16th-century wokou warlord boss (horned kabuto helmet with fierce demon mask, ornate dark blood-red #742A2A samurai armor, tattered dark jinbaori surcoat, wielding dual katanas), heavy intimidating march cycle facing LEFT. 4 evenly spaced side-profile walking poses in one horizontal row, consistent head height and foot baseline. Flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), NO grid lines, NO boxes, NO text, NO drop shadow, isolated on a pure solid white background."
    ),
    (
        "enemy_boss_slash_fall.png",
        "A clean horizontal 3-frame 2D game sprite sheet of a towering 16th-century wokou warlord boss (horned kabuto helmet with fierce demon mask, ornate dark blood-red #742A2A samurai armor, tattered dark jinbaori surcoat, dual katanas), facing LEFT: frames 1-2 show a fierce dual-katana cross slash attack, frame 3 shows him defeated and collapsed flat on the ground. 3 evenly spaced side-profile figures in one horizontal row, flat semi-shaded Chinese guofeng 2D game art style, clean 1.5px dark outline (#1A202C), NO grid lines, NO boxes, NO text, NO drop shadow, isolated on a pure solid white background."
    ),
]

for fname, prompt in JOBS:
    out_file = os.path.join(OUT_DIR, fname)
    print(f"Generating {fname}...", flush=True)
    cmd = [
        "gflow", "image", "t2i", prompt,
        "--model", "nano2.1",
        "--aspect", "16:9",
        "--out-file", out_file
    ]
    res = subprocess.run(cmd, capture_output=False)
    print(f"Finished {fname} with exit code {res.returncode}", flush=True)
