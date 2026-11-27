@echo off
rem Write the art in art_src back into assets/ (PNG), rebuild @2x, verify round-trip.
setlocal
cd /d "%~dp0..\.."
echo === 1/3 export art_src -> assets (PNG) ===
python tools\aseprite_export.py --apply
if errorlevel 1 goto fail
echo === 2/3 rebuild @2x from 1x ===
python tools\fix_sprite_frames.py --apply
if errorlevel 1 goto fail
echo === 3/3 spec padding + person-scale audit ===
python tools\sync_spec_padding.py
python tools\audit_person_scale.py
echo.
echo Done. Now rebuild the game: cli build -p .
pause
exit /b 0
:fail
echo FAILED - nothing else was run.
pause
exit /b 1
