@echo off
rem Open one art family (or a whole folder) in Aseprite.
rem Usage: double-click  -> opens player/player_walk.aseprite
rem        drag a file/folder from art_src onto this bat -> opens that
setlocal
set "AS=C:\Users\jakfc\AppData\Local\Programs\Aseprite\aseprite.exe"
set "ROOT=%~dp0..\..\"
set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=art_src\player\player_walk.aseprite"
start "" "%AS%" "%ROOT%%TARGET%"
