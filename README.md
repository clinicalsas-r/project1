# Optimizing Clinical TFL Review with Python and Power BI: A Reproducible Workflow to Reduce QC Time and Improve Traceability 
This project demonstrates a hybrid QC workflow integrating:

- SAS (Production TFLs)
- Python (QC validation)
- Power BI (Visualization)

## Workflow

1. SAS generates ADaM datasets and TFL outputs
2. Python scripts perform independent QC checks
3. Power BI visualizes discrepancies

## How to Run

```bash
pip install -r requirements.txt
python python/demog_qc.py
