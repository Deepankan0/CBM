# Author: Deepankan
# date: 26th May 2025
# Purpose: Extract and validate metadata from DICOM files for each subject and sequence. this is the updated version to handle seq names with unknown prefix

# Import necessary libraries for DICOM reading, OS operations, data handling, and grouping
from pydicom import dcmread as dr  # Alias dcmread to dr for brevity
import os
import pandas as pd
from collections import defaultdict

# Define the path to the directory containing the DICOM subject folders
path = 'path_to_your_raw_data'

# Initialize a list that will hold all extracted metadata rows
final_info = []

# Iterate over each subject folder in the main path
for subj in os.listdir(path):
    subj_path = os.path.join(path, subj)
    if not os.path.isdir(subj_path):
        # Skip non-directory entries
        continue

    # Iterate over each sequence folder within the subject directory
    for seq in os.listdir(subj_path):
        seq_path = os.path.join(subj_path, seq)
        # Skip unwanted folders: must be a dir, exclude calibration (S0) and DIRFILE
        if not os.path.isdir(seq_path) or 'S0' in seq or seq == 'DIRFILE':
            continue

        # Remove 'WIP ' prefix from sequence name if present
        clean_seq = seq[4:] if seq.startswith('WIP ') else seq

        # Identify DICOM files by looking for filenames starting with 'I'
        i_files = [f for f in os.listdir(seq_path) if f.startswith('I')]
        if not i_files:
            print(f'No I file found in {seq_path}. Skipping...')
            continue

        # Use the first identified DICOM file for metadata extraction
        i_file_path = os.path.join(seq_path, i_files[0])
        print('Trying to read DICOM file:', i_file_path)
        try:
            # Read the DICOM file, forcing read even if headers are noncompliant
            data = dr(i_file_path, force=True)
        except IOError:
            print('Failed to read DICOM file:', i_file_path)
            continue

        # Extract relevant metadata attributes, using None if missing
        data_info = [
            subj,  # Subject identifier (folder name)
            getattr(data, 'AccessionNumber', None),            # ADBS accession number
            getattr(data, 'PatientName', None),                # Patient name
            getattr(data, 'StudyDescription', None),           # Study description
            getattr(data, 'StudyComments', None),              # Study comments
            clean_seq,                                          # Cleaned sequence name
            getattr(data, 'ProtocolName', None),               # Scanner protocol name
            len(os.listdir(seq_path)),                         # Number of files in this sequence folder
            getattr(data, 'PerformedProcedureStepStartDate', None)  # Scan date
        ]
        final_info.append(data_info)

# Convert the collected metadata into a pandas DataFrame
data = pd.DataFrame(
    final_info,
    columns=[
        'SUBJ',           # Subject identifier
        'ANCID',          # Accession number
        'Name',           # Patient name
        'ADBS_ID',        # Study description (misnamed in original?)
        'Assesment_ID',   # Study comments (misnamed)
        'Seq',            # Cleaned sequence name
        'Sequence_name',  # Protocol name (column header mismatch? adjust as needed)
        'N_files',        # Count of files in sequence folder
        'DATE'            # Performed procedure start date
    ]
)

# Define expected file counts for each sequence type
expected_files = {
    'DKI': 4480,
    'Ref_rest_AP': 88,
    'Ref_DWI_PA': 112,
    'Ref_DWI_AP': 112,
    'Ref_rest_PA': 88,
    'Ref_TRENDS_PA': 84,
    'Ref_TRENDS_AP': 84,
    'T2w': 136,
    'FLAIR': 150,
    'DTI_6dir': 448,
    'B0_PreScan': 0,
    'Survey': 9,
    'fieldmap': 176,
    'task-rest_bold': 12100,
    'task-trends_bold': 6720,
    'T1w': 192,
    'T1w_PSIR': 576,
    'Ref_vft_AP': 88,
    'Ref_vft_PA': 88,
    'task-vft_bold': 4752
}

# Helper function: returns 1 if sequence is complete, 0 if incomplete, -1 if unknown
def is_complete(row):
    seq_name = row['Sequence_name']
    if seq_name in expected_files:
        return 1 if row['N_files'] >= expected_files[seq_name] else 0
    return -1

# Apply completeness check across all rows
data['N_files_Complete'] = data.apply(is_complete, axis=1)

# Save the annotated metadata to CSV
modified_data_file = 'DICOM_information/modified/_____.csv'
data.to_csv(modified_data_file, index=False)
print('Modified data saved to', modified_data_file)

# Identify missing or incomplete sequences per subject
missing_sequences = defaultdict(list)
for subject, group in data.groupby('SUBJ'):
    for seq_name, expected_count in expected_files.items():
        subset = group[group['Sequence_name'] == seq_name]
        # Sequence missing or has fewer files than expected
        if subset.empty or subset['N_files'].iloc[0] < expected_count:
            missing_sequences[subject].append(seq_name)
    if not missing_sequences[subject]:
        missing_sequences[subject].append('NIL')

# Build DataFrame summarizing missing sequences
missing_data = []
for subj, seqs in missing_sequences.items():
    row = data[data['SUBJ'] == subj].iloc[0]
    missing_data.append([
        subj,
        row['ANCID'],
        row['Name'],
        row['ADBS_ID'],
        row['Assesment_ID'],
        row['DATE'],
        ','.join(seqs)
    ])

missing_df = pd.DataFrame(
    missing_data,
    columns=['SUBJ', 'ANCID', 'Name', 'ADBS_ID', 'Assesment_ID', 'Date', 'Missing Sequences']
)

# Save the missing-sequence report to CSV
missing_sequences_file = '/DICOM_information/missing/_____.csv'
missing_df.to_csv(missing_sequences_file, index=False)
print('Missing sequences saved to', missing_sequences_file)
