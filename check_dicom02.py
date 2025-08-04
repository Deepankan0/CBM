#updated check_dicom.py to account for WIP_sequencies
# Import necessary libraries
from pydicom import dcmread as dr
import os
import pandas as pd
from collections import defaultdict

# Define the path to the directory containing the DICOM files
path = '/path/to/your/scan'

# Initialize a list to store final information
final_info = []

# Loop through each subject
for subj in os.listdir(path):
    subj_path = os.path.join(path, subj)
    if os.path.isdir(subj_path):
        for seq in os.listdir(subj_path):
            seq_path = os.path.join(subj_path, seq)
            if os.path.isdir(seq_path) and 'S0' not in seq and seq != 'DIRFILE':

                all_files = os.listdir(seq_path)
                dcm_files = [file for file in all_files if file.endswith('.dcm')]

                if dcm_files:
                    dcm_file_path = os.path.join(seq_path, dcm_files[0])
                    print('Trying to read DICOM file:', dcm_file_path)
                    try:
                        data = dr(dcm_file_path, force=True)
                        data_info = [
                            subj,
                            getattr(data, 'AccessionNumber', None),
                            getattr(data, 'PatientName', None),
                            getattr(data, 'StudyDescription', None),
                            getattr(data, 'StudyComments', None),
                            seq,
                            getattr(data, 'ProtocolName', None),
                            len(all_files),
                            getattr(data, 'PerformedProcedureStepStartDate', None)
                        ]
                        final_info.append(data_info)
                    except IOError:
                        print('Failed to read DICOM file:', dcm_file_path)
                else:
                    print('No .dcm file found in {}. Skipping...'.format(seq_path))

# Convert the collected information into a DataFrame
data = pd.DataFrame(final_info, columns=[
    'SUBJ', 'ANCID', 'Name', 'ADBS_ID', 'Assesment_ID',
    'Seq', 'Sequence_name', 'N_files', 'DATE'
])

# Filter out rows where Seq is 'secondary'
data = data[data['Seq'].str.lower() != 'secondary'].reset_index(drop=True)


# Create a cleaned version of Sequence_name for comparison only
data['Sequence_name_clean'] = data['Sequence_name'].str.replace(r'^WIP\s+', '', regex=True).str.lower()

# Dictionary to store expected number of files for each sequence (keys must be lowercase)
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
    'survey': 9,
    'fieldmap': 176,
    'task-rest_bold': 12100,
    'task-trends_bold': 6720,
    't1w': 192,
    'ref_vft_ap': 88,
    'ref_vft_pa': 88,
    'task-vft_bold': 4752
}

# Function to check if N_files is complete using cleaned name
def is_complete(row):
    sequence = row['Sequence_name_clean']
    if sequence in expected_files:
        expected_count = expected_files[sequence]
        return 1 if row['N_files'] >= expected_count else 0
    else:
        return -1  # Indicate unknown sequence

# Add completeness column
data['N_files_Complete'] = data.apply(is_complete, axis=1)

# Export modified data with original sequence names
modified_data_file = '/modified_test.csv'
data.drop(columns=['Sequence_name_clean']).to_csv(modified_data_file, index=False)
print('Modified data saved to %s' % modified_data_file)

# Group data by subject and check missing sequences
missing_sequences = defaultdict(list)
for subject, group in data.groupby('SUBJ'):
    missing = []
    group_clean = group.set_index('Sequence_name_clean')
    for sequence_clean, expected_count in expected_files.items():
        if sequence_clean not in group_clean.index:
            missing.append(sequence_clean)
        elif group_clean.loc[sequence_clean, 'N_files'].max() < expected_count:
            missing.append(sequence_clean)
    if missing:
        missing_sequences[subject].extend(missing)
    elif subject not in missing_sequences:
        missing_sequences[subject].append('NIL')

# Create missing sequence DataFrame using original names
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
        ','.join(sorted(set(sequences)))  # still in lowercase
    ])

missing_df = pd.DataFrame(missing_data, columns=[
    'SUBJ', 'ANCID', 'Name', 'ADBS_ID', 'Assesment_ID', 'Date', 'Missing Sequences'
])

# Export missing sequences
missing_sequences_file = '/missing_test.csv'
missing_df.to_csv(missing_sequences_file, index=False)
print('Missing sequences saved to %s' % missing_sequences_file)
