@echo off
cd /d "%~dp0"
set COLLECTOR_CDP_PORT=9223
python vendor\boss-zhipin-scraper\scripts\boss_cdp_raw.py --setup-chrome --cdp-port 9223
pause
