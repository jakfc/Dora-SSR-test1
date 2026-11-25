import os
import wave
import numpy as np
from scipy import signal

SR = 44100
AUDIO_DIR = r"C:\Users\jakfc\AppData\Roaming\IppClub\DoraSSR\test\assets\audio"
BGM_DIR = os.path.join(AUDIO_DIR, "bgm")
SFX_DIR = os.path.join(AUDIO_DIR, "sfx")
os.makedirs(BGM_DIR, exist_ok=True)
os.makedirs(SFX_DIR, exist_ok=True)

def save_wav(path, audio, sr=SR):
    """Normalize safely without clipping and write 16-bit PCM WAV."""
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / max(peak, 1e-6) * 0.88
    pcm = np.clip(audio * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        n_ch = 2 if pcm.ndim == 2 else 1
        wf.setnchannels(n_ch)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    print(f"Saved {os.path.relpath(path, AUDIO_DIR)} ({len(audio)/sr:.2f}s)")

def env_ad(n, attack_s, decay_s, sr=SR):
    a = min(n, max(1, int(attack_s * sr)))
    env = np.zeros(n)
    env[:a] = np.linspace(0.0, 1.0, a)
    rem = n - a
    if rem > 0:
        t = np.linspace(0.0, rem / sr, rem)
        env[a:] = np.exp(-t / max(decay_s, 1e-4))
    return env

def karplus_strong(freq, duration_s, brightness=0.5, damping=0.996, sr=SR):
    """Physical modeling plucked Chinese string (guzheng/pipa)."""
    n = int(duration_s * sr)
    delay = max(2, int(round(sr / freq)))
    rng = np.random.default_rng(int(freq * 100))
    buf = rng.uniform(-1.0, 1.0, delay)
    # Warm initial pluck filter
    b, a = signal.butter(1, min(0.95, max(0.05, brightness)), btype="low")
    buf = signal.lfilter(b, a, buf)
    out = np.zeros(n)
    idx = 0
    prev = 0.0
    for i in range(n):
        val = buf[idx]
        out[i] = val
        next_val = damping * 0.5 * (val + prev)
        prev = val
        buf[idx] = next_val
        idx = (idx + 1) % delay
    # Short fade-out at end
    fade = min(n, int(0.03 * sr))
    out[-fade:] *= np.linspace(1.0, 0.0, fade)
    return out

def war_drum(base_freq=78.0, duration_s=0.65, punch=1.0, sr=SR):
    """Ming dynasty ox-hide war drum (pitch-drop membrane + body resonance)."""
    n = int(duration_s * sr)
    t = np.linspace(0, duration_s, n)
    freq_env = base_freq * (1.0 + 1.8 * punch * np.exp(-t / 0.025))
    phase = 2 * np.pi * np.cumsum(freq_env) / sr
    body = np.sin(phase) * env_ad(n, 0.004, 0.22)
    sub = np.sin(2 * np.pi * (base_freq * 0.65) * t) * env_ad(n, 0.006, 0.30) * 0.5
    rng = np.random.default_rng(42)
    slap = rng.normal(0, 1, n) * env_ad(n, 0.001, 0.025)
    b, a = signal.butter(2, 1200 / (sr / 2), btype="low")
    slap = signal.lfilter(b, a, slap) * 0.45
    return body + sub + slap

def chime_bell(freq, duration_s=1.2, sr=SR):
    """Ancient bronze chime / qing bell."""
    n = int(duration_s * sr)
    t = np.linspace(0, duration_s, n)
    s = (
        np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.45)
        + 0.45 * np.sin(2 * np.pi * (freq * 2.0) * t) * np.exp(-t / 0.28)
        + 0.22 * np.sin(2 * np.pi * (freq * 2.756) * t) * np.exp(-t / 0.16)
    )
    s *= np.minimum(1.0, t / 0.004)
    return s

def make_stereo(mono, width=0.15):
    """Create subtle stereo ambience from mono signal."""
    delay = int(0.012 * SR)
    right = np.roll(mono, delay) * (1.0 - width * 0.2)
    return np.column_stack([mono, right])

# -------------------------------------------------------------
# 1. BGM Tracks (Seamless Pentatonic Ming Coastal Scores)
# -------------------------------------------------------------
def generate_bgm():
    # D minor / D pentatonic: D4=293.66, F4=349.23, G4=392.00, A4=440.00, C5=523.25, D5=587.33
    # D major pentatonic: D4=293.66, E4=329.63, F#4=369.99, A4=440.00, B4=493.88, D5=587.33
    bpm_title = 72
    beat_t = 60.0 / bpm_title
    # 16 beats = ~13.33s seamless loop
    total_s = 16 * beat_t
    n_tot = int(total_s * SR)

    # BGM 1: bgm_title.wav (Solemn D-minor pentatonic guzheng + deep war drum + ocean breeze)
    rng = np.random.default_rng(1558)
    title_mix = np.zeros(n_tot)
    # Subtle ocean wind drone
    noise = rng.normal(0, 1, n_tot)
    b, a = signal.butter(2, [180 / (SR / 2), 620 / (SR / 2)], btype="band")
    wind = signal.lfilter(b, a, noise) * (0.08 + 0.04 * np.sin(2 * np.pi * np.linspace(0, 2, n_tot)))
    title_mix += wind

    melody_title = [
        (0, 293.66, 2.2), (2, 440.00, 1.8), (3.5, 392.00, 1.5), (4, 349.23, 2.5),
        (6, 293.66, 2.0), (8, 587.33, 2.2), (10, 523.25, 1.6), (11, 440.00, 2.0),
        (12, 392.00, 1.8), (14, 349.23, 1.5), (15, 293.66, 1.8)
    ]
    for beat_idx, freq, dur in melody_title:
        pos = int(beat_idx * beat_t * SR)
        plucked = karplus_strong(freq, dur, brightness=0.35, damping=0.997) * 0.55
        end = min(n_tot, pos + len(plucked))
        title_mix[pos:end] += plucked[:end - pos]
    for beat_idx in [0, 4, 8, 12]:
        pos = int(beat_idx * beat_t * SR)
        dr = war_drum(68.0, 0.85, punch=0.7) * 0.65
        end = min(n_tot, pos + len(dr))
        title_mix[pos:end] += dr[:end - pos]
    save_wav(os.path.join(BGM_DIR, "bgm_title.wav"), make_stereo(title_mix, 0.25))

    # BGM 2: bgm_day.wav (Warm, steady daytime village & fortress building, D major pentatonic)
    bpm_day = 96
    bt_d = 60.0 / bpm_day
    n_day = int(16 * bt_d * SR)
    day_mix = np.zeros(n_day)
    day_notes = [
        (0, 293.66), (1, 329.63), (2, 369.99), (3, 440.00),
        (4, 587.33), (5, 493.88), (6, 440.00), (7, 369.99),
        (8, 329.63), (9, 369.99), (10, 440.00), (11, 493.88),
        (12, 440.00), (13, 369.99), (14, 329.63), (15, 293.66),
    ]
    for b_idx, freq in day_notes:
        pos = int(b_idx * bt_d * SR)
        pl = karplus_strong(freq, 1.1, brightness=0.52, damping=0.995) * 0.5
        end = min(n_day, pos + len(pl))
        day_mix[pos:end] += pl[:end - pos]
        # Bass drone on downbeats
        if b_idx % 4 == 0:
            bs = karplus_strong(freq * 0.5, 2.0, brightness=0.25, damping=0.996) * 0.35
            e2 = min(n_day, pos + len(bs))
            day_mix[pos:e2] += bs[:e2 - pos]
        # Light wooden clapper (muyu)
        if b_idx % 2 == 0:
            cl = chime_bell(880.0 if b_idx % 4 == 0 else 660.0, 0.09) * 0.14
            e3 = min(n_day, pos + len(cl))
            day_mix[pos:e3] += cl[:e3 - pos]
    save_wav(os.path.join(BGM_DIR, "bgm_day.wav"), make_stereo(day_mix, 0.2))

    # BGM 3: bgm_night.wav (Urgent anti-wokou night battle: fast war drums + sharp D-minor ostinato)
    bpm_night = 132
    bt_n = 60.0 / bpm_night
    n_night = int(32 * bt_n * SR)
    night_mix = np.zeros(n_night)
    ostinato = [293.66, 293.66, 349.23, 440.00, 392.00, 349.23, 329.63, 293.66]
    for i in range(32):
        pos = int(i * bt_n * SR)
        freq = ostinato[i % len(ostinato)]
        pl = karplus_strong(freq, 0.55, brightness=0.68, damping=0.993) * 0.45
        end = min(n_night, pos + len(pl))
        night_mix[pos:end] += pl[:end - pos]
        if i % 2 == 0:
            dr = war_drum(74.0 if i % 4 == 0 else 92.0, 0.45, punch=1.2) * (0.85 if i % 4 == 0 else 0.55)
            ed = min(n_night, pos + len(dr))
            night_mix[pos:ed] += dr[:ed - pos]
    save_wav(os.path.join(BGM_DIR, "bgm_night.wav"), make_stereo(night_mix, 0.18))

    # BGM 4: bgm_victory.wav (Triumphant ascending fanfare + drums, ~6s)
    n_vic = int(6.0 * SR)
    vic_mix = np.zeros(n_vic)
    fanfare = [(0.0, 293.66, 1.5), (0.35, 369.99, 1.5), (0.7, 440.00, 1.8), (1.1, 587.33, 3.5), (2.2, 493.88, 1.2), (2.6, 587.33, 3.2)]
    for t0, f, dur in fanfare:
        pos = int(t0 * SR)
        ch = chime_bell(f, dur) * 0.5 + karplus_strong(f, dur, 0.6) * 0.4
        end = min(n_vic, pos + len(ch))
        vic_mix[pos:end] += ch[:end - pos]
    for t0 in [0.0, 0.7, 1.1, 2.6]:
        pos = int(t0 * SR)
        dr = war_drum(76.0, 0.8, punch=1.1) * 0.7
        end = min(n_vic, pos + len(dr))
        vic_mix[pos:end] += dr[:end - pos]
    save_wav(os.path.join(BGM_DIR, "bgm_victory.wav"), make_stereo(vic_mix, 0.25))

    # BGM 5: bgm_defeat.wav (Somber slow bell & descending lament, ~6s)
    n_def = int(6.0 * SR)
    def_mix = np.zeros(n_def)
    lament = [(0.0, 440.00, 2.5), (1.3, 392.00, 2.5), (2.6, 349.23, 2.5), (3.8, 293.66, 2.2)]
    for t0, f, dur in lament:
        pos = int(t0 * SR)
        pl = karplus_strong(f * 0.5, dur, 0.22, 0.997) * 0.6 + chime_bell(f, dur) * 0.25
        end = min(n_def, pos + len(pl))
        def_mix[pos:end] += pl[:end - pos]
    save_wav(os.path.join(BGM_DIR, "bgm_defeat.wav"), make_stereo(def_mix, 0.3))

# -------------------------------------------------------------
# 2. SFX Library (Combat, Skills, Construction, UI)
# -------------------------------------------------------------
def generate_sfx():
    rng = np.random.default_rng(1558)

    # 1. sfx_sword_slash.wav (Crisp metallic whoosh + steel ring)
    dur = 0.28
    n = int(dur * SR)
    t = np.linspace(0, dur, n)
    noise = rng.normal(0, 1, n)
    # Bandpass sweep
    b, a = signal.butter(2, [900 / (SR / 2), 4500 / (SR / 2)], btype="band")
    whoosh = signal.lfilter(b, a, noise) * env_ad(n, 0.015, 0.08)
    steel = (np.sin(2 * np.pi * 2400 * t) + 0.5 * np.sin(2 * np.pi * 3850 * t)) * env_ad(n, 0.002, 0.06) * 0.25
    save_wav(os.path.join(SFX_DIR, "sfx_sword_slash.wav"), whoosh + steel)

    # 2. sfx_qilin_punch.wav (Heavy qi punch impact + wind rush)
    dur = 0.42
    n = int(dur * SR)
    t = np.linspace(0, dur, n)
    impact = war_drum(88.0, dur, punch=1.5) * 0.85
    b, a = signal.butter(2, [400 / (SR / 2), 2600 / (SR / 2)], btype="band")
    wind = signal.lfilter(b, a, rng.normal(0, 1, n)) * env_ad(n, 0.02, 0.14) * 0.7
    save_wav(os.path.join(SFX_DIR, "sfx_qilin_punch.wav"), impact + wind)

    # 3. sfx_drum_rally.wav (Three rapid Ming war drum strikes)
    n_tot = int(1.1 * SR)
    rally = np.zeros(n_tot)
    for t0, amp in [(0.0, 0.9), (0.22, 0.75), (0.44, 1.0)]:
        pos = int(t0 * SR)
        dr = war_drum(76.0, 0.62, punch=1.2) * amp
        end = min(n_tot, pos + len(dr))
        rally[pos:end] += dr[:end - pos]
    save_wav(os.path.join(SFX_DIR, "sfx_drum_rally.wav"), rally)

    # 4. sfx_shockwave.wav (Ground seismic burst)
    dur = 0.55
    n = int(dur * SR)
    t = np.linspace(0, dur, n)
    sub = np.sin(2 * np.pi * (55 * np.exp(-t * 2.5) + 32) * t) * env_ad(n, 0.005, 0.25)
    b, a = signal.butter(2, 900 / (SR / 2), btype="low")
    rumble = signal.lfilter(b, a, rng.normal(0, 1, n)) * env_ad(n, 0.01, 0.22) * 0.7
    save_wav(os.path.join(SFX_DIR, "sfx_shockwave.wav"), sub + rumble)

    # 5. sfx_arrow_shoot.wav (Bowstring twang + arrow whistle)
    dur = 0.24
    n = int(dur * SR)
    t = np.linspace(0, dur, n)
    twang = np.sin(2 * np.pi * 220 * t) * env_ad(n, 0.002, 0.06) * 0.6
    b, a = signal.butter(2, [1800 / (SR / 2), 5200 / (SR / 2)], btype="band")
    air = signal.lfilter(b, a, rng.normal(0, 1, n)) * env_ad(n, 0.005, 0.07) * 0.7
    save_wav(os.path.join(SFX_DIR, "sfx_arrow_shoot.wav"), twang + air)

    # 6. sfx_arrow_hit.wav (Crisp thud impact)
    dur = 0.16
    n = int(dur * SR)
    thud = war_drum(160.0, dur, punch=0.8) * 0.8
    save_wav(os.path.join(SFX_DIR, "sfx_arrow_hit.wav"), thud)

    # 7. sfx_cannon_fire.wav (Deep Folangji cannon boom)
    dur = 0.95
    n = int(dur * SR)
    boom = war_drum(52.0, dur, punch=2.0)
    b, a = signal.butter(2, 1600 / (SR / 2), btype="low")
    blast = signal.lfilter(b, a, rng.normal(0, 1, n)) * env_ad(n, 0.002, 0.28) * 1.1
    save_wav(os.path.join(SFX_DIR, "sfx_cannon_fire.wav"), boom + blast)

    # 8. sfx_cannon_hit.wav (Explosion + debris crackle)
    dur = 0.85
    n = int(dur * SR)
    b, a = signal.butter(2, 1100 / (SR / 2), btype="low")
    exp_n = signal.lfilter(b, a, rng.normal(0, 1, n)) * env_ad(n, 0.004, 0.26)
    sub = war_drum(48.0, dur, punch=1.6)
    save_wav(os.path.join(SFX_DIR, "sfx_cannon_hit.wav"), exp_n + sub)

    # 9. sfx_hurt.wav (Short muffled armor hit)
    dur = 0.20
    n = int(dur * SR)
    hit = war_drum(130.0, dur, punch=1.1) * 0.7 + chime_bell(1400.0, dur) * 0.2
    save_wav(os.path.join(SFX_DIR, "sfx_hurt.wav"), hit)

    # 10. sfx_enemy_die.wav (Body fall thump + katana clatter)
    dur = 0.45
    n = int(dur * SR)
    fall = war_drum(85.0, dur, punch=0.6) * 0.7
    clatter = np.zeros(n)
    p = int(0.14 * SR)
    cl = chime_bell(2800.0, 0.22) * 0.25
    clatter[p:min(n, p + len(cl))] = cl[:min(n - p, len(cl))]
    save_wav(os.path.join(SFX_DIR, "sfx_enemy_die.wav"), fall + clatter)

    # 11. sfx_build_hammer.wav (Wooden mallet striking stone/timber)
    dur = 0.22
    n = int(dur * SR)
    t = np.linspace(0, dur, n)
    knock = (np.sin(2 * np.pi * 340 * t) + 0.5 * np.sin(2 * np.pi * 780 * t)) * env_ad(n, 0.002, 0.045)
    save_wav(os.path.join(SFX_DIR, "sfx_build_hammer.wav"), knock)

    # 12. sfx_farm_hoe.wav (Crisp soil/salt rake)
    dur = 0.24
    n = int(dur * SR)
    b, a = signal.butter(2, [700 / (SR / 2), 3200 / (SR / 2)], btype="band")
    rustle = signal.lfilter(b, a, rng.normal(0, 1, n)) * env_ad(n, 0.01, 0.07)
    save_wav(os.path.join(SFX_DIR, "sfx_farm_hoe.wav"), rustle)

    # 13. sfx_gate_open.wav (Heavy iron sluice/portcullis rumble)
    dur = 0.90
    n = int(dur * SR)
    b, a = signal.butter(2, [120 / (SR / 2), 550 / (SR / 2)], btype="band")
    grind = signal.lfilter(b, a, rng.normal(0, 1, n)) * env_ad(n, 0.08, 0.45)
    clunk = war_drum(95.0, 0.3, punch=0.7) * 0.5
    grind[:len(clunk)] += clunk
    save_wav(os.path.join(SFX_DIR, "sfx_gate_open.wav"), grind)

    # 14. sfx_recruit.wav (Warm two-tone bronze chime)
    n = int(0.9 * SR)
    rec = np.zeros(n)
    c1 = chime_bell(587.33, 0.65)
    c2 = chime_bell(880.00, 0.70)
    rec[:len(c1)] += c1 * 0.7
    p = int(0.14 * SR)
    rec[p:min(n, p + len(c2))] += c2[:min(n - p, len(c2))] * 0.8
    save_wav(os.path.join(SFX_DIR, "sfx_recruit.wav"), rec)

    # 15. sfx_upgrade.wav (Ascending 3-note pentatonic chime)
    n = int(1.2 * SR)
    upg = np.zeros(n)
    for idx, f in enumerate([440.00, 587.33, 880.00]):
        pos = int(idx * 0.12 * SR)
        c = chime_bell(f, 0.85) * 0.7
        upg[pos:min(n, pos + len(c))] += c[:min(n - pos, len(c))]
    save_wav(os.path.join(SFX_DIR, "sfx_upgrade.wav"), upg)

    # 16. sfx_coin_silver.wav (Silver sycee clink)
    n_coin = int(0.45 * SR)
    coin = np.zeros(n_coin)
    c1 = chime_bell(2637.0, 0.35) * 0.6
    coin[:len(c1)] += c1
    p = int(0.08 * SR)
    c2 = chime_bell(3520.0, 0.32) * 0.55
    end_c = min(n_coin, p + len(c2))
    coin[p:end_c] += c2[:end_c - p]
    save_wav(os.path.join(SFX_DIR, "sfx_coin_silver.wav"), coin)

    # 17. sfx_wave_horn.wav (Low Ming coastal warning horn + drum)
    dur = 1.4
    n = int(dur * SR)
    t = np.linspace(0, dur, n)
    # Sawtooth-like brassy horn filtered low
    horn_freq = 146.83 * (1.0 - 0.04 * np.exp(-t / 0.15))
    horn = (
        np.sin(2 * np.pi * horn_freq * t)
        + 0.55 * np.sin(2 * np.pi * horn_freq * 2 * t)
        + 0.30 * np.sin(2 * np.pi * horn_freq * 3 * t)
    ) * np.minimum(1.0, t / 0.12) * np.exp(-np.maximum(0, t - 0.7) / 0.35)
    dr = war_drum(72.0, 0.8, punch=1.0) * 0.7
    horn[:len(dr)] += dr
    save_wav(os.path.join(SFX_DIR, "sfx_wave_horn.wav"), horn)

    # 18. sfx_ui_click.wav & sfx_ui_hover.wav
    n_c = int(0.08 * SR)
    tc = np.linspace(0, 0.08, n_c)
    click = np.sin(2 * np.pi * 680 * tc) * env_ad(n_c, 0.001, 0.018)
    save_wav(os.path.join(SFX_DIR, "sfx_ui_click.wav"), click)

    n_h = int(0.05 * SR)
    th = np.linspace(0, 0.05, n_h)
    hover = np.sin(2 * np.pi * 960 * th) * env_ad(n_h, 0.002, 0.012) * 0.5
    save_wav(os.path.join(SFX_DIR, "sfx_ui_hover.wav"), hover)

if __name__ == "__main__":
    print("Generating Ming coastal game audio suite...")
    generate_bgm()
    generate_sfx()
    print("ALL AUDIO ASSETS GENERATED!")
