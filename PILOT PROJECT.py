#Import Libraries
import pandas as pd
import numpy as np
from pathlib import Path

#Setting folders and file names
DATA_DIR = Path(r"C:\R\ADaM\excel_output")
OUTPUT_DIR = Path(r"C:\R\ADaM\excel_output\outputs")

# Reading the ADAM datasets in the form excel and checking the loading status
ADSL_FILE = DATA_DIR / "adsl.xlsx"
ADAE_FILE = DATA_DIR / "adae.xlsx"
ADLBHY_FILE = DATA_DIR / "adlbhy.xlsx"

print("ADSL exists:", ADSL_FILE.exists())

adsl = pd.read_excel(ADSL_FILE, sheet_name="ADSL")
adae = pd.read_excel(ADAE_FILE, sheet_name="ADAE")
adlb = pd.read_excel(ADLBHY_FILE, sheet_name="ADLBHY")

# cleaning the chartacter columns
def clean_char_cols(df):
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": np.nan, "None": np.nan})
    return df

adsl = clean_char_cols(adsl)
adae = clean_char_cols(adae)
adlb = clean_char_cols(adlb)

#Selecting the required variables
required_cols = {
    "ADSL": ["USUBJID", "TRT01A", "SAFFL", "SEX", "RACE", "AGE"],
    "ADAE": ["USUBJID", "TRTA", "AESOC", "AEDECOD", "AESER", "AESEV", "TRTEMFL"],
    "ADLB": ["USUBJID", "TRTA", "PARAM", "PARAMCD", "AVAL", "BASE", "AVISIT"]
}

#CHecking the required columns
for ds_name, df in [("ADSL", adsl), ("ADAE", adae), ("ADLB", adlb)]:
    missing = [c for c in required_cols[ds_name] if c not in df.columns]
    print(f"{ds_name} missing columns: {missing if missing else 'None'}")

# Import Libraries
import pandas as pd
import numpy as np
from pathlib import Path
# Setting folders and file names
DATA_DIR = Path(r"C:\R\ADaM\excel_output")
OUTPUT_DIR = Path(r"C:\R\ADaM\excel_output\outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
# Reading the ADaM dataset in Excel format
ADSL_FILE = DATA_DIR / "adsl.xlsx"
# Load ADSL
adsl = pd.read_excel(ADSL_FILE, sheet_name="ADSL")

# Deriving the safety population
adsl_saf = adsl[adsl["SAFFL"] == "Y"].copy()
trt_counts = (
    adsl_saf.groupby("TRT01A")["USUBJID"]
    .nunique()
    .reset_index(name="N")
)
print("Treatment Counts:")
print(trt_counts)

#Deriving the safety Population
adsl_saf = adsl[adsl["SAFFL"] == "Y"].copy()

trt_counts = (
    adsl_saf.groupby("TRT01A")["USUBJID"]
    .nunique()
    .reset_index(name="N")
)
trt_counts


def pct(n, d):
    return round((n / d) * 100, 1) if d and d != 0 else np.nan

#Creating Demongraphic QC table
def create_demog_tfl(adsl_df):
    df = adsl_df[adsl_df["SAFFL"] == "Y"].copy()
    denom = df.groupby("TRT01A")["USUBJID"].nunique().to_dict()

    rows = []

    # AGE statistics
    age_stats = df.groupby("TRT01A")["AGE"].agg(["count", "mean", "std", "median", "min", "max"]).reset_index()

    for _, r in age_stats.iterrows():
        rows.append(["AGE", "n", r["TRT01A"], f"{int(r['count'])}"])
        rows.append(["AGE", "Mean (SD)", r["TRT01A"], f"{r['mean']:.1f} ({r['std']:.2f})" if pd.notna(r["std"]) else f"{r['mean']:.1f}"])
        rows.append(["AGE", "Median", r["TRT01A"], f"{r['median']:.1f}"])
        rows.append(["AGE", "Min, Max", r["TRT01A"], f"{r['min']:.1f}, {r['max']:.1f}"])

    # SEX
    sex_counts = df.groupby(["TRT01A", "SEX"])["USUBJID"].nunique().reset_index(name="n")
    for _, r in sex_counts.iterrows():
        d = denom.get(r["TRT01A"], 0)
        rows.append(["SEX", r["SEX"], r["TRT01A"], f"{r['n']} ({pct(r['n'], d):.1f}%)"])

    # RACE
    race_counts = df.groupby(["TRT01A", "RACE"])["USUBJID"].nunique().reset_index(name="n")
    for _, r in race_counts.iterrows():
        d = denom.get(r["TRT01A"], 0)
        rows.append(["RACE", r["RACE"], r["TRT01A"], f"{r['n']} ({pct(r['n'], d):.1f}%)"])

    # ETHNIC if present
    if "ETHNIC" in df.columns:
        eth_counts = df.groupby(["TRT01A", "ETHNIC"])["USUBJID"].nunique().reset_index(name="n")
        for _, r in eth_counts.iterrows():
            d = denom.get(r["TRT01A"], 0)
            rows.append(["ETHNIC", r["ETHNIC"], r["TRT01A"], f"{r['n']} ({pct(r['n'], d):.1f}%)"])

    out = pd.DataFrame(rows, columns=["SECTION", "CATEGORY", "TRT01A", "VALUE"])
    return out

demog_tfl = create_demog_tfl(adsl)
demog_tfl.head(20)

demog_tfl.to_excel(OUTPUT_DIR / "tfl_demographics.xlsx", index=False)
demog_tfl.to_csv(OUTPUT_DIR / "tfl_demographics.csv", index=False)

#Creating AE Summary QC Table
def create_ae_summary_tfl(adae_df, adsl_df):
    saf = adsl_df[adsl_df["SAFFL"] == "Y"][["USUBJID", "TRT01A"]].drop_duplicates()
    denom = saf.groupby("TRT01A")["USUBJID"].nunique().to_dict()

    ae = adae_df[adae_df["TRTEMFL"] == "Y"].copy()
    ae = ae.merge(saf, on="USUBJID", how="inner", suffixes=("", "_ADSL"))
    ae["TRTGRP"] = ae["TRTA"].fillna(ae["TRT01A"])

    rows = []
    # Any TEAE
    teae = ae.groupby("TRTGRP")["USUBJID"].nunique().reset_index(name="n")
    for _, r in teae.iterrows():
        d = denom.get(r["TRTGRP"], 0)
        rows.append(["Subjects with at least one TEAE", r["TRTGRP"], f"{r['n']} ({pct(r['n'], d):.1f}%)"])

    # Serious TEAE
    ser = ae[ae["AESER"] == "Y"].groupby("TRTGRP")["USUBJID"].nunique().reset_index(name="n")
    for _, r in ser.iterrows():
        d = denom.get(r["TRTGRP"], 0)
        rows.append(["Subjects with at least one Serious TEAE", r["TRTGRP"], f"{r['n']} ({pct(r['n'], d):.1f}%)"])

    # Severe TEAE
    sev = ae[ae["AESEV"].str.upper() == "SEVERE"].groupby("TRTGRP")["USUBJID"].nunique().reset_index(name="n")
    for _, r in sev.iterrows():
        d = denom.get(r["TRTGRP"], 0)
        rows.append(["Subjects with at least one Severe TEAE", r["TRTGRP"], f"{r['n']} ({pct(r['n'], d):.1f}%)"])

    out = pd.DataFrame(rows, columns=["METRIC", "TRT", "VALUE"])
    return out

ae_summary_tfl = create_ae_summary_tfl(adae, adsl)
ae_summary_tfl

ae_summary_tfl.to_excel(OUTPUT_DIR / "tfl_ae_summary.xlsx", index=False)
ae_summary_tfl.to_csv(OUTPUT_DIR / "tfl_ae_summary.csv", index=False)

#Creating AE SOC/PT QC Table
def create_ae_soc_pt_tfl(adae_df, adsl_df):
    saf = adsl_df[adsl_df["SAFFL"] == "Y"][["USUBJID", "TRT01A"]].drop_duplicates()
    denom = saf.groupby("TRT01A")["USUBJID"].nunique().to_dict()

    ae = adae_df[adae_df["TRTEMFL"] == "Y"].copy()
    ae = ae.merge(saf, on="USUBJID", how="inner", suffixes=("", "_ADSL"))
    ae["TRTGRP"] = ae["TRTA"].fillna(ae["TRT01A"])

    soc = ae.groupby(["TRTGRP", "AESOC"])["USUBJID"].nunique().reset_index(name="n")
    soc["pct"] = soc.apply(lambda x: pct(x["n"], denom.get(x["TRTGRP"], 0)), axis=1)
    soc["LEVEL"] = "SOC"
    soc["TERM"] = soc["AESOC"]

    pt = ae.groupby(["TRTGRP", "AESOC", "AEDECOD"])["USUBJID"].nunique().reset_index(name="n")
    pt["pct"] = pt.apply(lambda x: pct(x["n"], denom.get(x["TRTGRP"], 0)), axis=1)
    pt["LEVEL"] = "PT"
    pt["TERM"] = pt["AEDECOD"]

    soc_out = soc[["TRTGRP", "AESOC", "LEVEL", "TERM", "n", "pct"]]
    pt_out = pt[["TRTGRP", "AESOC", "LEVEL", "TERM", "n", "pct"]]

    out = pd.concat([soc_out, pt_out], ignore_index=True)
    out["N_PCT"] = out.apply(lambda x: f"{x['n']} ({x['pct']:.1f}%)" if pd.notna(x["pct"]) else f"{x['n']}", axis=1)

    return out.sort_values(["TRTGRP", "AESOC", "LEVEL", "TERM"])

ae_soc_pt_tfl = create_ae_soc_pt_tfl(adae, adsl)
ae_soc_pt_tfl.head(25)

ae_soc_pt_tfl.to_excel(OUTPUT_DIR / "tfl_ae_soc_pt.xlsx", index=False)
ae_soc_pt_tfl.to_csv(OUTPUT_DIR / "tfl_ae_soc_pt.csv", index=False)

#Creating a lab table

#Derive CHG based on AVAL and BASE

if "CHG" not in adlb.columns:
    adlb["CHG"] = np.where(
        adlb["AVAL"].notna() & adlb["BASE"].notna(),
        adlb["AVAL"] - adlb["BASE"],
        np.nan
    )

def create_lab_tfl(adlb_df, adsl_df):
    saf = adsl_df[adsl_df["SAFFL"] == "Y"][["USUBJID", "TRT01A"]].drop_duplicates()

    lb = adlb_df.merge(saf, on="USUBJID", how="inner", suffixes=("", "_ADSL"))
    lb["TRTGRP"] = lb["TRTA"].fillna(lb["TRT01A"])

    # Optional: use only analysis records if available
    if "ANL01FL" in lb.columns:
        lb = lb[(lb["ANL01FL"] == "Y") | (lb["ANL01FL"].isna())]

    # Post-baseline only if needed
    lb_post = lb[lb["AVISIT"].notna()].copy()

    out = (
        lb_post.groupby(["TRTGRP", "PARAM", "AVISIT"])
        .agg(
            N=("AVAL", lambda x: x.notna().sum()),
            MEAN_AVAL=("AVAL", "mean"),
            SD_AVAL=("AVAL", "std"),
            MIN_AVAL=("AVAL", "min"),
            MAX_AVAL=("AVAL", "max"),
            MEAN_CHG=("CHG", "mean"),
            SD_CHG=("CHG", "std")
        )
        .reset_index()
    )

    return out

lab_tfl = create_lab_tfl(adlb, adsl)
lab_tfl.head(20)

lab_tfl.to_excel(OUTPUT_DIR / "tfl_lab_summary.xlsx", index=False)
lab_tfl.to_csv(OUTPUT_DIR / "tfl_lab_summary.csv", index=False)

#Patient Profile

def create_subject_profile(adsl_df, adae_df, adlb_df):
    profile = adsl_df.copy()

    # AE counts
    ae = adae_df[adae_df["TRTEMFL"] == "Y"].copy()
    ae_count = ae.groupby("USUBJID").size().reset_index(name="AE_COUNT")
    serious_ae = ae[ae["AESER"] == "Y"].groupby("USUBJID").size().reset_index(name="SERIOUS_AE_COUNT")

    profile = profile.merge(ae_count, on="USUBJID", how="left")
    profile = profile.merge(serious_ae, on="USUBJID", how="left")

    profile["AE_COUNT"] = profile["AE_COUNT"].fillna(0).astype(int)
    profile["SERIOUS_AE_COUNT"] = profile["SERIOUS_AE_COUNT"].fillna(0).astype(int)

    return profile

subject_profile = create_subject_profile(adsl, adae, adlb)
subject_profile.head()

subject_profile.to_excel(OUTPUT_DIR / "subject_profile.xlsx", index=False)
subject_profile.to_csv(OUTPUT_DIR / "subject_profile.csv", index=False)

#Basic QC Checks
validation_results = []

def add_result(dataset, check, status, details):
    validation_results.append({
        "DATASET": dataset,
        "CHECK": check,
        "STATUS": status,
        "DETAILS": details
    })

# ADSL subject uniqueness
dup_subj = adsl["USUBJID"].duplicated().sum()
add_result("ADSL", "Unique USUBJID", "PASS" if dup_subj == 0 else "FAIL", f"Duplicate count = {dup_subj}")

# Safety population
saf_n = adsl.loc[adsl["SAFFL"] == "Y", "USUBJID"].nunique()
add_result("ADSL", "Safety population", "PASS", f"N = {saf_n}")

# ADAE subjects in ADSL
adae_not_in_adsl = set(adae["USUBJID"].dropna()) - set(adsl["USUBJID"].dropna())
add_result("ADAE", "Subjects exist in ADSL", "PASS" if len(adae_not_in_adsl) == 0 else "FAIL",
           f"Unmatched subjects = {len(adae_not_in_adsl)}")

# ADLB subjects in ADSL
adlb_not_in_adsl = set(adlb["USUBJID"].dropna()) - set(adsl["USUBJID"].dropna())
add_result("ADLB", "Subjects exist in ADSL", "PASS" if len(adlb_not_in_adsl) == 0 else "FAIL",
           f"Unmatched subjects = {len(adlb_not_in_adsl)}")

# CHG validation
if "CHG" in adlb.columns:
    calc_chg = np.where(adlb["AVAL"].notna() & adlb["BASE"].notna(), adlb["AVAL"] - adlb["BASE"], np.nan)
    mismatch = ((pd.Series(calc_chg).round(8) != adlb["CHG"].round(8)) &
                pd.Series(calc_chg).notna() &
                adlb["CHG"].notna()).sum()
    add_result("ADLB", "CHG = AVAL - BASE", "PASS" if mismatch == 0 else "FAIL", f"Mismatched rows = {mismatch}")

validation_df = pd.DataFrame(validation_results)
validation_df

# Export Validation Report

with pd.ExcelWriter(OUTPUT_DIR / "validation_report.xlsx", engine="openpyxl") as writer:
    validation_df.to_excel(writer, sheet_name="Validation", index=False)
    demog_tfl.to_excel(writer, sheet_name="Demographics", index=False)
    ae_summary_tfl.to_excel(writer, sheet_name="AE_Summary", index=False)
    ae_soc_pt_tfl.to_excel(writer, sheet_name="AE_SOC_PT", index=False)
    lab_tfl.to_excel(writer, sheet_name="Lab_Summary", index=False)
    subject_profile.to_excel(writer, sheet_name="Subject_Profile", index=False)

print("All TFLs and validation outputs created successfully.")

# Example: read ADAE
adae = pd.read_excel("adae.xlsx", sheet_name="ADAE")

# Convert to datetime
date_cols = ["AESTDT", "TRTSDT", "TRTEDT"]
for col in date_cols:
    if col in adae.columns:
        adae[col] = pd.to_datetime(adae[col], errors="coerce")

# reatment-emergent window: 0 days after last dose
window_days = 0

adae["TRTEMFL"] = np.where(
    adae["AESTDT"].notna() &
    adae["TRTSDT"].notna() &
    (adae["AESTDT"] >= adae["TRTSDT"]) &
    (
        adae["TRTEDT"].isna() |
        (adae["AESTDT"] <= adae["TRTEDT"] + pd.Timedelta(days=window_days))
    ),
    "Y",
    ""
)

print(adae[["USUBJID", "AESTDT", "TRTSDT", "TRTEDT", "TRTEMFL"]].head())

import pandas as pd
import numpy as np

def derive_trtemfl(df, aestdt="AESTDT", trtsdt="TRTSDT", trtedt="TRTEDT", window_days=30):
    out = df.copy()

    for col in [aestdt, trtsdt, trtedt]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")

    out["TRTEMFL"] = np.where(
        out[aestdt].notna() &
        out[trtsdt].notna() &
        (out[aestdt] >= out[trtsdt]) &
        (
            out[trtedt].isna() |
            (out[aestdt] <= out[trtedt] + pd.Timedelta(days=window_days))
        ),
        "Y",
        ""
    )
    return out

adae = derive_trtemfl(adae, aestdt="AESTDT", trtsdt="TRTSDT", trtedt="TRTEDT", window_days=0)

print(adae["TRTEMFL"].value_counts(dropna=False))

qc = adae.loc[:, ["USUBJID", "AETERM", "AESTDT", "TRTSDT", "TRTEDT", "TRTEMFL"]]
print(qc.head(20))


