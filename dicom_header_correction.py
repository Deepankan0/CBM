"""
DICOM Header Modifier Script

This script is designed to modify DICOM header values based on the provided new values.
It traverses through a directory containing DICOM files, reads each DICOM file, modifies
the specified header tags with new values, and saves the modified DICOM files.

Dependencies:
    - pydicom: Library for working with DICOM files
    - os: Module for handling file paths

Functions:
    - modify_dicom_header: Function to modify the DICOM header with new values.
    - Main Script: Traverses through a directory containing DICOM files, identifies
                   subdirectories, filters DICOM files starting with 'I', and calls
                   the modify_dicom_header function for each DICOM file.

Usage:
    - Ensure pydicom library is installed (pip install pydicom).
    - Modify the 'file_path' variable to specify the directory containing DICOM files.
    - Specify the new header values to be set in the 'new_values' dictionary.
    - Run the script.

"""

import pydicom
import os

def modify_dicom_header(dicom_path, new_values):
    """
    Modifies the DICOM header with new values.

    Parameters:
        dicom_path (str): Path to the DICOM file.
        new_values (dict): Dictionary containing tag-value pairs to be set in the DICOM header.
    """
    if os.path.exists(dicom_path):
        # Load the DICOM file
        dicom_data = pydicom.dcmread(dicom_path)

        # Modify the DICOM header with new values
        for tag, value in new_values.items():
            dicom_data[tag].value = value

        # Save the modified DICOM file
        dicom_data.save_as(dicom_path)
        print("Modified DICOM header for %s" % dicom_path)
    else:
        print("File or directory not found: %s" % dicom_path)

# Define the file path:
file_path = "Your/file/path"

# Specify the new values you want to set in the header
new_values = {
#     "StudyDescription" : "ADBSID",
#    "StudyComments" : "ASSESMENTID",
#    "AccessionNumber" : "ANCID"
}

SeqList = os.listdir(file_path)
for Seq in SeqList:
    if Seq == 'DIRFILE':
        print('Skipped the DIRFILE')
    else:
        subdirectory_path = os.path.join(file_path, Seq)
        print('Processing subdirectory: %s' % subdirectory_path)

        # Get the list of files in the subdirectory
        file_list = os.listdir(subdirectory_path)

        # Filter out only the files starting with 'I'
        dicom_files = [file for file in file_list if file.startswith('I')]

        for dicom_file in dicom_files:
            dicom_path = os.path.join(subdirectory_path, dicom_file)
            print('Trying to read DICOM file: %s' % dicom_path)

            # Call the function to modify the DICOM header
            modify_dicom_header(dicom_path, new_values)
