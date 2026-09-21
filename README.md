# CargoBici Schedule Planner

A small logistics planning tool built in Python to turn route and worker data into practical daily schedules and Excel summaries.

The application was created around a real operational workflow: route data and weekly worker availability are pasted into a simple Streamlit interface, configurable planning rules are applied, and the result can be reviewed in the browser and exported to Excel.

> **Portfolio context:** this is a personal implementation from 2024. It was built as a focused operational tool rather than as a generic scheduling platform.

## What it does

CargoBici has two main workflows.

### Route and shift planning

The schedule generator processes route and worker data and assigns work while taking operational constraints into account, including:

- planned route start and end times;
- worker availability and maximum working hours;
- route priority and configurable early/late departure margins;
- maximum waiting time between routes;
- hub continuity;
- vehicle type requirements (`TRIKE` or `4W`);
- configurable preparation, finishing and between-route times;
- route duration based on travel time and number of deliveries.

The generated plan includes the effective route times, assigned workers, working hours and route timelines. The result can then be exported as an `.xlsx` file.

### Weekly schedule summary

A second workflow converts route-level planning data into a weekly worker schedule. It calculates each worker's first entry and final exit time for the day, derives worked hours, optionally compares the result with a previous schedule, and exports the summary to Excel.

## Why I built it

The aim was to reduce the amount of repetitive manual work involved in turning operational route information into usable worker schedules.

The interesting part of the project is not the interface itself, but translating real planning rules into code: parsing irregular tabular input, handling time calculations, respecting several scheduling constraints at once, and producing an output that could be used directly in the existing Excel-based workflow.

## Technology

| Area | Technology |
| --- | --- |
| Language | Python |
| Interface | Streamlit |
| Data processing | pandas |
| Excel generation | openpyxl |
| Configuration | JSON |

The application is intentionally lightweight: it does not require a database or backend service.

## How it works

```text
Route data + worker availability
            |
            v
      Parse and normalize
            |
            v
 Apply configurable planning rules
            |
            v
Assign routes / calculate shifts
            |
       +----+----+
       |         |
       v         v
 Streamlit     Excel
  review       export
```

Planning parameters are kept in `variables.json`, so values such as route margins, maximum waiting time, maximum working hours, delivery time and vehicle-weight thresholds can be adjusted without changing the scheduling logic.

## Project structure

```text
manager.py           Streamlit entry point and workflow selector
generadorHoraris.py  Route processing and schedule generation
horariSumary.py      Weekly worker-schedule summary and Excel export
variables.json       Configurable scheduling parameters
variablesSumary.json Parameters used by the weekly-summary workflow
requirements.txt     Python dependencies
```

## Run locally

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install the dependencies

```bash
pip install streamlit pandas openpyxl
```

### 3. Start the application

```bash
streamlit run manager.py
```

The **Horari Sumary** workflow uses the `es_ES.UTF-8` locale when parsing weekday/date information, so that locale must be available on the operating system.

## Input and output

The tool was designed around tabular operational data copied from the original planning workflow. The Streamlit interface provides text areas for pasting that data directly.

Depending on the selected mode, the application produces:

- a detailed route assignment and worker timeline;
- calculated shift start/end times and total hours;
- an Excel route-planning file (`output.xlsx`);
- an Excel weekly schedule summary (`ResumHorari.xlsx`).

## Scope

This project solves a specific scheduling workflow and therefore makes assumptions about the structure of its input tables and the meaning of the operational fields. It is not intended to be a general-purpose workforce-optimization engine.

For portfolio purposes, it demonstrates a practical end-to-end Python workflow: parsing real-world input, encoding business constraints, processing tabular data, building a lightweight UI and generating usable Excel output.
