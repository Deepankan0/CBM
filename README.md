# DICOM to NIfTI Converter according to BIDS format

This script processes DICOM files, converts them to NIfTI format, renames them and organizes them into specific directories accoedance to the BIDS, based on information stored in a text file.
for this code we need the path to the directory containing the DICOM files and the text file containing information such as ADBS_ID and ASSESSMENT_ID


## Purpose
The purpose of this script is to simplify the process of converting DICOM files to NIfTI format and keep it according to BIDS, which is commonly used in neuroimaging research.

## Usage
1. Place your DICOM files in the specified directory.
2. Ensure the text file containing additional data is available at the specified path.
3. Run the script.

## Dependencies
- dcm2niix: DICOM to NIfTI converter tool.

## Example Usage
it will give the data in this format:
ADBS_ID/ASSESSMENT_ID/Sequence/(ADBS_ID)_(ASSESMENT_ID)_run-xx_protocol.ext
