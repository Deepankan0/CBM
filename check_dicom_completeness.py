#!/usr/bin/env python3
"""
check_dicom_completeness.py

This script parses DICOM data stored in a nested folder structure and verifies
whether all required sequences are present and complete based on expected file counts.
It also checks for the presence of associated behavioral data (VFT, TRENDS) and exam cards.

Outputs:
- modified_test.csv: Metadata and sequence completeness info.
- missing_test.csv: Per-subject missing sequences and behavioral data availability.

Author: Deepankan
Last Updated: 2025-08-04
"""

import os
import pandas as pd
from collections import defaultdict
from pydicom import dcmread as dr

# ----------------------------- Configuration -------------------------------- #

# Root path containing subject folders
ROOT_PATH = '/mnt/f/Deepankan/XNAT/Subject_data/adbs-20250729_135320'

# Output files
MODIFIED_CSV = '/mnt/f/Deepankan/XNAT/output/modified_test.csv'
MISSING_CSV = '/mnt/f/Deepankan/XNAT/output/missing_test.csv'

# Expected number of DICOM files per cleaned sequence name
EXPECTED_FILES = {
    'dki': 4480,
    'ref_rest_ap': 88,
    'ref_dwi_pa': 112,
    'ref_dwi_ap': 112,
    'ref_rest_pa': 88,
    'ref_trends_pa': 84,
    'ref_trends_ap': 84,
    't2w': 136,
    'flair': 150,
    'dti_6dir': 448,
    'b0_prescan': 0,
    'survey': 9,
    'fieldmap': 176,
    'task-rest_bold': 12100,
    'task-trends_bold': 6720,
    't1w': 192,
    't1w_psir': 576,
    'ref_vft_ap': 88,
    'ref_vft_pa': 88,
    'task-vft_bold': 4752
}

# ---------------------------- Data Extraction ------------------------------- #

final_info = []
behavioral_status = {}

for subj in os.listdir(ROOT_PATH):
    subj_path = os.path.join(ROOT_PATH, subj)
    if not os.path.isdir(subj_path):
        continue

    behavioral_status[subj] = {"VFT": 0, "TRENDS": 0, "EXAMCARD": 0}

    for seq in os.listdir(subj_path):
        seq_path = os.path.join(subj_path, seq)
        if not os.path.isdir(seq_path):
            continue

        # --- Numeric folders (DICOM) ---
        if seq.isnumeric():
            dicom_dir = os.path.join(seq_path, "DICOM")
            if os.path.isdir(dicom_dir):
                dcm_files = [f for f in os.listdir(dicom_dir) if f.endswith('.dcm')]
                if dcm_files:
                    dcm_path = os.path.join(dicom_dir, dcm_files[0])
                    print(f"Reading: {dcm_path}")
                    try:
                        dcm_data = dr(dcm_path, force=True)
                        final_info.append([
                            subj,
                            getattr(dcm_data, 'AccessionNumber', None),
                            getattr(dcm_data, 'PatientName', None),
                            getattr(dcm_data, 'StudyDescription', None),
                            getattr(dcm_data, 'StudyComments', None),
                            seq,
                            getattr(dcm_data, 'ProtocolName', None),
                            len(os.listdir(dicom_dir)),
                            getattr(dcm_data, 'PerformedProcedureStepStartDate', None)
                        ])
                    except Exception as e:
                        print(f"Error reading {dcm_path}: {e}")

        # --- Behavioral/Examcard folders ---
        elif seq[0].isalpha():
            resources_dir = os.path.join(seq_path, "resources")
            if not os.path.isdir(resources_dir):
                continue

            vft_path = os.path.join(resources_dir, "Behavioral%20data-VFT", "VFT")
            if os.path.isdir(vft_path):
                vft_files = os.listdir(vft_path)
                if any(f.lower().endswith(".wav") for f in vft_files) and any("export.txt" in f.lower() for f in vft_files):
                    behavioral_status[subj]["VFT"] = 1

            trends_path = os.path.join(resources_dir, "Behavioral%20data-TRENDS", "TRENDS")
            if os.path.isdir(trends_path):
                if any("export.txt" in f.lower() for f in os.listdir(trends_path)):
                    behavioral_status[subj]["TRENDS"] = 1

            examcard_path = os.path.join(resources_dir, "Examcards")
            if os.path.isdir(examcard_path):
                behavioral_status[subj]["EXAMCARD"] = 1

# -------------------------- Data Cleaning & Check --------------------------- #

# Create DataFrame
data = pd.DataFrame(final_info, columns=[
    'SUBJ', 'ANCID', 'Name', 'ADBS_ID', 'Assesment_ID',
    'Seq', 'Sequence_name', 'N_files', 'DATE'
])

# Remove secondary sequences
data = data[data['Seq'].str.lower() != 'secondary'].reset_index(drop=True)

# Clean sequence names
data['Sequence_name_clean'] = data['Sequence_name'].str.replace(r'^WIP\s+', '', regex=True).str.lower()

# Check completeness
def is_complete(row):
    seq = row['Sequence_name_clean']
    if seq in EXPECTED_FILES:
        return int(row['N_files'] >= EXPECTED_FILES[seq])
    return -1  # Unknown sequence

data['N_files_Complete'] = data.apply(is_complete, axis=1)

# Save modified metadata
data.drop(columns=['Sequence_name_clean']).to_csv(MODIFIED_CSV, index=False)
print(f"[✓] Modified metadata saved: {MODIFIED_CSV}")

# ---------------------- Identify Missing Sequences -------------------------- #

missing_sequences = defaultdict(list)
for subject, group in data.groupby('SUBJ'):
    group = group.set_index('Sequence_name_clean')
    for expected_seq, expected_count in EXPECTED_FILES.items():
        if expected_seq not in group.index:
            missing_sequences[subject].append(expected_seq)
        elif group.loc[expected_seq, 'N_files'].max() < expected_count:
            missing_sequences[subject].append(expected_seq)
    if subject not in missing_sequences:
        missing_sequences[subject].append('NIL')

# Create summary DataFrame
missing_data = []
for subj, missing in missing_sequences.items():
    subj_data = data[data['SUBJ'] == subj]
    row = [
        subj,
        subj_data['ANCID'].iloc[0] if not subj_data.empty else None,
        subj_data['Name'].iloc[0] if not subj_data.empty else None,
        subj_data['ADBS_ID'].iloc[0] if not subj_data.empty else None,
        subj_data['Assesment_ID'].iloc[0] if not subj_data.empty else None,
        subj_data['DATE'].iloc[0] if not subj_data.empty else None,
        ','.join(sorted(set(missing)))
    ]
    bstatus = behavioral_status.get(subj, {"VFT": 0, "TRENDS": 0, "EXAMCARD": 0})
    row.extend([bstatus["VFT"], bstatus["TRENDS"], bstatus["EXAMCARD"]])
    missing_data.append(row)

missing_df = pd.DataFrame(missing_data, columns=[
    'SUBJ', 'ANCID', 'Name', 'ADBS_ID', 'Assesment_ID', 'Date',
    'Missing Sequences', 'VFT', 'TRENDS', 'EXAMCARD'
])

missing_df.to_csv(MISSING_CSV, index=False)
print(f"[✓] Missing sequences saved: {MISSING_CSV}")
