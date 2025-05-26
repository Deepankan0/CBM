# Author: Deepankan
# date: 26th May 2025
# Purpose: Extract and validate metadata from DICOM files for each subject and sequence. this is the updated version to handle seq names with unknown prefix

from pydicom import dcmread as dr
import os
import pandas as pd
from collections import defaultdict

# Define the path to the directory containing the DICOM files
path = '/path_to_your_dicom_files'

# Initialize a list to store final information
final_info = []

# Loop through each subject
for subj in os.listdir(path):
    subj_path = os.path.join(path, subj)
    if os.path.isdir(subj_path):
        for seq in os.listdir(subj_path):
            seq_path = os.path.join(subj_path, seq)
            if os.path.isdir(seq_path) and 'S0' not in seq and seq != 'DIRFILE':
                i_files = [file for file in os.listdir(seq_path) if file.startswith('I')]
                if i_files:
                    i_file_path = os.path.join(seq_path, i_files[0])
                    print('Trying to read DICOM file:', i_file_path)
                    try:
                        data = dr(i_file_path, force=True)
                        data_info = [
                            subj,
                            getattr(data, 'AccessionNumber', None),
                            getattr(data, 'PatientName', None),
                            getattr(data, 'StudyDescription', None),
                            getattr(data, 'StudyComments', None),
                            seq,
                            getattr(data, 'ProtocolName', None),
                            len(os.listdir(seq_path)),
                            getattr(data, 'PerformedProcedureStepStartDate', None)
                        ]
                        final_info.append(data_info)
                    except IOError:
                        print('Failed to read DICOM file:', i_file_path)
                else:
                    print('No I file found in {}. Skipping...'.format(seq_path))

# Convert to DataFrame
data = pd.DataFrame(final_info, columns=[
    'SUBJ', 'ANCID', 'Name', 'ADBS_ID', 'Assesment_ID',
    'Seq', 'Sequence_name', 'N_files', 'DATE'
])

# Dictionary of expected sequence file counts (all lowercased)
expected_files = {
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

# Clean sequence names for comparison: remove 'WIP ' and lowercase
def clean_sequence_name(name):
    if name:
        name = str(name)
        return name.replace('WIP ', '').lower().strip()
    return None

data['Sequence_name_clean'] = data['Sequence_name'].apply(clean_sequence_name)

# Function to check if N_files is complete
def is_complete(row):
    sequence_clean = row['Sequence_name_clean']
    if sequence_clean in expected_files:
        return 1 if row['N_files'] >= expected_files[sequence_clean] else 0
    else:
        return -1

data['N_files_Complete'] = data.apply(is_complete, axis=1)

# Save modified data
modified_data_file = '/DICOM_information/modified/modified_data.csv'
data.to_csv(modified_data_file, index=False)
print('Modified data saved to %s' % modified_data_file)

# Build a mapping from cleaned names to original ones
clean_to_original = dict(
    data.groupby('Sequence_name_clean')['Sequence_name']
    .agg(lambda x: x.dropna().unique()[0] if len(x.dropna().unique()) else x.iloc[0])
)

# Group data by subject and check missing sequences
missing_sequences = defaultdict(list)
for subject, group in data.groupby('SUBJ'):
    missing = []
    group_clean = group.set_index('Sequence_name_clean')
    for sequence_clean, expected_count in expected_files.items():
        if sequence_clean not in group_clean.index:
            original_name = clean_to_original.get(sequence_clean, sequence_clean)
            missing.append(original_name)
        elif group_clean.loc[sequence_clean, 'N_files'].sum() < expected_count:
            original_name = clean_to_original.get(sequence_clean, sequence_clean)
            missing.append(original_name)
    if missing:
        missing_sequences[subject].extend(missing)
    elif subject not in missing_sequences:
        missing_sequences[subject].append('NIL')

# Create DataFrame for missing sequences
missing_data = []
for subject, sequences in missing_sequences.items():
    subject_data = data[data['SUBJ'] == subject]
    missing_data.append([
        subject,
        subject_data['ANCID'].iloc[0],
        subject_data['Name'].iloc[0],
        subject_data['ADBS_ID'].iloc[0],
        subject_data['Assesment_ID'].iloc[0],
        subject_data['DATE'].iloc[0],
        ','.join(sorted(set(sequences)))  # Sorted for readability
    ])

missing_df = pd.DataFrame(missing_data, columns=[
    'SUBJ', 'ANCID', 'Name', 'ADBS_ID', 'Assesment_ID', 'Date', 'Missing Sequences'
])

# Export missing sequences
missing_sequences_file = '/DICOM_information/missing/missing_data.csv'
missing_df.to_csv(missing_sequences_file, index=False)
print('Missing sequences saved to %s' % missing_sequences_file)
