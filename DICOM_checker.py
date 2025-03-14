"""
This script processes DICOM files to extract information and perform analysis.

Requirements:
- pydicom library for DICOM file processing
- csv module for CSV file writing
- os module for file and directory operations
- pandas library for data manipulation

Usage:
- Update the 'path' variable to specify the directory containing DICOM files.
- Ensure that the directory structure conforms to the expected format for processing.
- Run the script.

The script iterates through the specified directory structure to extract DICOM file information.
For each DICOM file found:
- Information such as subject ID, accession number, patient name, sequence name, number of files in the sequence,
  and date are extracted.
- The extracted information is stored in a DataFrame.

After extracting information from all DICOM files, the script performs the following tasks:
1. Calculates completeness of file counts for each sequence based on expected counts.
2. Adds a column to indicate completeness of file counts.
3. Exports the modified DataFrame to a CSV file.

Additionally, the script checks for missing sequences for each subject:
1. Groups the data by subject and checks for missing sequences or sequences with an incorrect number of files.
2. Constructs a DataFrame containing information about missing sequences.
3. Exports the missing sequences DataFrame to a separate CSV file.

Note: Ensure that the expected file counts for each sequence are accurately defined in the 'expected_files' dictionary.
"""


# Import necessary libraries
from pydicom import dcmread as dr
import csv
import os
import pandas as pd
from collections import defaultdict

# Set the path to the DICOM files
path = '/your/file/path'

# List all subjects in the specified path
files = os.listdir(path)
final_info = []  # Initialize an empty list to store the extracted information

# Loop through each subject
for subj in files:
    # List all sequences for the current subject, excluding those with 'S0' in the name
    SeqList = os.listdir(os.path.join(path, subj))
    SeqList = [Seq for Seq in SeqList if 'S0' not in Seq]

    subj_info = []  # Initialize an empty list to store information for the current subject

    # Loop through each sequence for the current subject
    for Seq in SeqList:
        memory_path = os.path.join(path, subj, Seq)
        memory = os.path.getsize(memory_path)

        # Skip 'DIRFILE' sequence
        if Seq == 'DIRFILE':
            print('skipped the DIRFILE')
        else:
            dicom_path = os.path.join(path, subj, Seq, 'I10')
            print('Trying to read DICOM file: %s' % dicom_path)

            # Check if DICOM file exists
            if os.path.exists(dicom_path):
                try:
                    # Read DICOM file and extract relevant information
                    data = dr(dicom_path)
                    data_info = [subj, data.AccessionNumber, data.PatientName, data.StudyDescription,
                                 data.StudyComments, Seq, data.ProtocolName,
                                 len(os.listdir(os.path.join(path, subj, Seq))),
                                 data.PerformedProcedureStepStartDate]

                    subj_info.append(data_info)

                except IOError:
                    print('No I10 file found in %s. Skipping...' % Seq)
            else:
                print('DICOM file %s does not exist. Skipping...' % dicom_path)

    final_info.extend(subj_info)  # Extend the final_info list with information for the current subject

# Convert the collected information into a DataFrame
data = pd.DataFrame(final_info, columns=['SUBJ', 'ANCID', 'Name', 'ADBS_ID', 'Assesment_ID', 'Seq', 'Sequence_name',
                                          'N_files', 'DATE'])

# Dictionary to store expected number of files for each sequence
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

# Function to check if N_files is complete
def is_complete(row):
    sequence = row['Sequence_name']
    if sequence in expected_files:
        expected_count = expected_files[sequence]
        return 1 if row['N_files'] == expected_count else 0
    else:
        return -1  # Indicate unknown sequence

# Insert a new column 'N_files_Complete' to indicate completeness
data['N_files_Complete'] = data.apply(is_complete, axis=1)

# Export the modified data to CSV
modified_data_file = '/file/path/modified.csv'
data.to_csv(modified_data_file, index=False)

print('Modified data saved to %s' % modified_data_file)

# Group data by SUBJECT and check for missing sequences
missing_sequences = defaultdict(list)
for subject, group in data.groupby('SUBJ'):
    missing = []
    for sequence, expected_count in expected_files.items():
        if sequence not in group['Sequence_name'].values:
            missing.append(sequence)
        elif group[group['Sequence_name'] == sequence]['N_files'].iloc[0] != expected_count:
            missing.append(sequence)
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
        ','.join(set(sequences))  # Use set to ensure unique sequences
    ])

missing_df = pd.DataFrame(missing_data, columns=['SUBJ', 'ANCID', 'Name', 'ADBS_ID', 'Assesment_ID', 'Date', 'Missing Sequences'])

# Export missing sequences to CSV
missing_sequences_file = '/file/path/missing/missing_sequences.csv'
missing_df.to_csv(missing_sequences_file, index=False)

print('Missing sequences saved to %s' % missing_sequences_file)
