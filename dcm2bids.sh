#!/bin/bash

# This script processes DICOM files, converts them to NIfTI format, renames them and organizes them into specific directories accoedance to the BIDS, based on information stored in a text file.
# for this code we need the path to the directory containing the DICOM files and the text file containing information such as ADBS_ID and ASSESSMENT_ID

# Specify the directory containing the DICOM files
DICOM_DATA_file_path="/home/deepankan/DICOM_DATA"
# Path to the text file containing information
text_file="/home/deepankan/subject_data.txt"
# Directory where processed NUIfTI files will be saved in BIDS format
output_file_path="/home/deepankan/NIfTI"

# Iterate through the files in the source directory
cd "$DICOM_DATA_file_path" || exit 1
for filename in *; do
    # Extract digits from the filename and remove leading zeros
    digits=$(echo "$filename" | grep -oE '[1-9][0-9]*')

    # Check if the digits match with the first column in the text file
    if grep -q -w "^$digits" "$text_file"; then
        # If there is a match, extract the 2nd (ADBS_ID) and 3rd (ASSESSMENT_ID) columns and store them as variables
        columns=$(grep -w "^$digits" "$text_file" | tr -d '\r')  # Remove Windows-style carriage return
        ADBS_ID=$(echo "$columns" | awk '{print $2}')
        ASSESSMENT_ID=$(echo "$columns" | awk '{print $3}' | cut -c 1-3)  # Extract only the first three digits

        # before conversion check if the BIDS file already exists, if yes, skip processing
        if [ -d "$output_file_path/sub-$ADBS_ID/ses-$ASSESSMENT_ID" ]; then
            echo "Directory $output_file_path/sub-$ADBS_ID/ses-$ASSESSMENT_ID already exists. Skipping processing for $filename"
            continue
        else
            # Make a new directory by the file name
            if [ -d "$DICOM_DATA_file_path/$filename" ]; then
                mkdir -p "$output_file_path/sub-$ADBS_ID/ses-$ASSESSMENT_ID"

                # Convert DICOM files to NIfTI in the current directory 
                dcm2niix -f "%p" -o "$output_file_path/sub-$ADBS_ID/ses-$ASSESSMENT_ID" "$DICOM_DATA_file_path/$filename"

                # Rename the NIfTI files by prepending ADBS_ID and ASSESSMENT_ID
                for NIfTI_file in "$output_file_path/sub-$ADBS_ID/ses-$ASSESSMENT_ID"/*.*; do
                    original_filename=$(basename "$NIfTI_file")
                    new_filename="$original_filename"

                    # Rename files based on run count
                    if [[ "$new_filename" =~ a\.[^.]*$ ]]; then
                        # Rename files with 'a' prefix
                        extension="${new_filename##*.}"
                        base_filename="${new_filename%.*}"
                        new_filename="sub-${ADBS_ID}_ses-${ASSESSMENT_ID}_run-02-${base_filename%a}.${extension}"
                    elif [[ "$new_filename" =~ b\.[^.]*$ ]]; then
                        # Rename files with 'b' prefix
                        extension="${new_filename##*.}"
                        base_filename="${new_filename%.*}"
                        new_filename="sub-${ADBS_ID}_ses-${ASSESSMENT_ID}_run-03-${base_filename%b}.${extension}"
                    elif [[ "$new_filename" =~ c\.[^.]*$ ]]; then
                        # Rename files with 'c' prefix
                        extension="${new_filename##*.}"
                        base_filename="${new_filename%.*}"
                        new_filename="sub-${ADBS_ID}_ses-${ASSESSMENT_ID}_run-04-${base_filename%c}.${extension}"
                     elif [[ "$new_filename" =~ [^ld]d\.[^.]*$ ]]; then
                        # Rename files with 'd' prefix except 'ld'
                        extension="${new_filename##*.}"
                        base_filename="${new_filename%.*}"
                        new_filename="sub-${ADBS_ID}_ses-${ASSESSMENT_ID}_run-05-${base_filename%d}.${extension}"
                    else
                        # Default naming convention
                        new_filename="sub-${ADBS_ID}_ses-${ASSESSMENT_ID}_run-01-${new_filename}"
                    fi

                    # Move and rename files
                    mv "$NIfTI_file" "$output_file_path/sub-$ADBS_ID/ses-$ASSESSMENT_ID/$new_filename"
                done

                # Organize files into specific directories based on their type
                cd "$output_file_path/sub-$ADBS_ID/ses-$ASSESSMENT_ID" || exit
                for f in *task* *fieldmap* *Ref* *T1* *T2* *FLAIR* *DKI* *DTI*; do
                    if [ ! -e "$f" ]; then
                        echo "Error: File '$f' not found"
                    fi
                done

                # Create directories and move files
                mkdir -p fmap dwi func anat survey
                mv -f *Survey* survey/
                mv -f *task* func/
                mv -f *fieldmap* fmap/
                mv -f *Ref* fmap/
                mv -f *T1* anat/
                mv -f *T2* anat/
                mv -f *FLAIR* anat/
                mv -f *DKI* dwi/
                mv -f *DTI* dwi/
                cd -
            fi
        fi
    else
        echo "No match found for $filename in $text_file"
    fi
done

echo "SCRIPT COMPLETE"
