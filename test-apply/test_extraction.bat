@echo off
echo ========================================
echo Testing UNIVERSAL EXTRACTOR
echo ========================================
echo.

python -m apply https://recruiting.ultipro.com/HOM1007HSUC/JobBoard/04366c17-7ee4-499a-a9e9-38ae46d03ef6/OpportunityDetail?opportunityId=ee7df30c-30b9-4d95-9244-b3a0c9411fd7

echo.
echo ========================================
echo ANALYZING RESULTS...
echo ========================================
echo.

python analyze_universal_extraction.py

pause
