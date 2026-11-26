@echo off
echo Starting CivicPulse AI Unified Application...
start "CivicPulse Backend" cmd /k "%~dp0start_backend.bat"
start "CivicPulse Frontend" cmd /k "%~dp0start_frontend.bat"
echo Applications launched!
echo Website: http://localhost:5173
echo API Docs: http://localhost:8000/docs
