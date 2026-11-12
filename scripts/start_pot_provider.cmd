@echo off
echo Starting bgutil PO Token Provider on port 4416...
node "%~dp0..\..\bgutil-ytdlp-pot-provider\server\build\main.js" -p 4416 -H 127.0.0.1
pause
