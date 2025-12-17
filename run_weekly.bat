@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0backend

echo ===================================================
echo 🚀 STEP 1: SCRAPING NEW DATA (Week 15+)
echo ===================================================
python -m etl.run_etl

echo.
echo ===================================================
echo 📊 STEP 2: UPDATING LEADERBOARDS (Season Stats)
echo ===================================================
python -m etl.aggregate

echo.
echo ===================================================
echo 🔍 STEP 3: VALIDATING DATA QUALITY
echo ===================================================
python -m etl.validate

echo.
echo ✅ PIPELINE COMPLETE!
pause