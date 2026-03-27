# Terraforge Labs — Plain Language Overview

## In one sentence
This project helps geologists turn raw field files into easy-to-read maps, model outputs, and draft reports.

## What happens step by step
1. A field team uploads instrument files (for example XRF chemistry, resistivity, magnetics, and GPS logs).
2. The backend parses those files into a consistent format.
3. The geodata service creates gridded outputs (mean, variance, uncertainty bands).
4. A simple deposit-model step produces 3D/model artifacts.
5. A JORC-style draft report is generated with an explicit AI-assistance disclaimer.
6. A mobile app shell provides screens for field data capture, map viewing, classification, and report workflow.

## Why this matters
- Reduces manual data wrangling.
- Gives small teams a repeatable workflow.
- Keeps the stack offline-first and low-cost for early deployments.
