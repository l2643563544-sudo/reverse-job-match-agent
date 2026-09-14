@echo off
cd /d "%~dp0"
if exist "vendor\boss-zhipin-scraper\.git" (
  echo Upstream collector already exists.
  exit /b 0
)
git clone --depth 1 --branch master https://github.com/eatmoreduck/boss-zhipin-scraper.git vendor/boss-zhipin-scraper
python -m pip install -r vendor\boss-zhipin-scraper\requirements.txt
