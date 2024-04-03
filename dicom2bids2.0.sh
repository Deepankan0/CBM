#!/bin/bash
# this is updated versiom of dcm2bids
# DICOM to BIDS Converter

#This Bash script automates the process of converting DICOM files to the Brain Imaging Data Structure (BIDS) format. 
#It organizes the data into subject-specific directories based on information stored in a text file and performs necessary renaming and modifications to ensure BIDS compliance.

## Features
#- Converts DICOM files to NIfTI format.
#- Renames files according to BIDS conventions.
#- Organizes data into subject/session-specific directories.
#- Modifies JSON files to meet BIDS specifications.

# for this code we need the path to the directory containing the DICOM files and the text file containing information such as ADBS_ID and ASSESSMENT_ID

# Specify the directory containing the DICOM files
DICOM_DATA_file_path="/file_path/"
# Path to the text file containing information
text_file="/file_path"
# Directory where processed NUIfTI files will be saved in BIDS format
output_file_path="/file_path/"

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
                        new_filename="sub-${ADBS_ID}_ses-${ASSESSMENT_ID}_run-02_${base_filename%a}.${extension}"
                    elif [[ "$new_filename" =~ b\.[^.]*$ ]]; then
                        # Rename files with 'b' prefix
                        extension="${new_filename##*.}"
                        base_filename="${new_filename%.*}"
                        new_filename="sub-${ADBS_ID}_ses-${ASSESSMENT_ID}_run-03_${base_filename%b}.${extension}"
                    elif [[ "$new_filename" =~ c\.[^.]*$ ]]; then
                        # Rename files with 'c' prefix
                        extension="${new_filename##*.}"
                        base_filename="${new_filename%.*}"
                        new_filename="sub-${ADBS_ID}_ses-${ASSESSMENT_ID}_run-04_${base_filename%c}.${extension}"
                     elif [[ "$new_filename" =~ [^ld]d\.[^.]*$ ]]; then
                        # Rename files with 'd' prefix except 'ld'
                        extension="${new_filename##*.}"
                        base_filename="${new_filename%.*}"
                        new_filename="sub-${ADBS_ID}_ses-${ASSESSMENT_ID}_run-05_${base_filename%d}.${extension}"
                    else
                        # Default naming convention
                        new_filename="sub-${ADBS_ID}_ses-${ASSESSMENT_ID}_run-01_${new_filename}"
                    fi

                    # Move and rename files
                    mv "$NIfTI_file" "$output_file_path/sub-$ADBS_ID/ses-$ASSESSMENT_ID/$new_filename"
                done


                # Rename NIfTI files before moving into directories
                cd "$output_file_path/sub-$ADBS_ID/ses-$ASSESSMENT_ID/$newfilename"
                rename 'fieldmap_e1_ph' 'phase1' *
                rename 'T1w_PSIR' 'acq-psirc_PSIR' *
                rename 'fieldmap_e2_ph' 'phase2' *
                rename 'fieldmap_e1' 'magnitude1' *
                rename 'fieldmap_e2' 'magnitude2' *
                rename 'AP' 'dir-AP_epi' *
                rename 'PA' 'dir-PA_epi' *
                rename 'Ref_rest' 'acq-rest' *
                rename 'Ref_DWI' 'acq-dwi' *
                rename 'DKI' 'acq-80dir_dwi' *
                rename 'DTI_6dir' 'acq-06dir_dwi' *
                rename 'Ref_TRENDS' 'acq-trends' *
                rename 'Ref_VFT' 'acq-vft' *

                # Rename them properly
                for file in *epi.json *epi.nii; do new_name=$(echo "$file" | sed -E 's/_run-([0-9]+)_acq-([a-zA-Z]+)_dir-([a-zA-Z]+)_epi/_acq-\2_dir-\3_run-\1_epi/'); mv "$file" "$new_name"; done
                for file in *dwi.*; do new_name=$(echo "$file" | sed -E 's/_run-([0-9]+)_acq-([0-9]+dir)_dwi/_acq-\2_run-\1_dwi/'); mv "$file" "$new_name"; done
                for file in *bold.nii *bold.json ; do new_name=$(echo "$file" | sed -E 's/_run-([0-9]+)_task-([a-zA-Z]+)_bold/_task-\2_run-\1_bold/'); mv "$file" "$new_name"; done
                for file in *PSIR.nii *PSIR.json ; do new_name=$(echo "$file" | sed -E 's/_run-([0-9]+)_acq-([a-zA-Z]+)_PSIR/_acq-\2_run-\1_PSIR/'); mv "$file" "$new_name"; done


                # Add required lines to various json files
                find *task-rest_bold*.json -exec \
                sed -i '/"PhaseEncodingAxis": "j",/a\\t"PhaseEncodingDirection": "j",' {} \;
                find *dir-AP_epi*.json -exec \
                sed -i 's/"PhaseEncodingAxis": "j",/&\n\t"PhaseEncodingDirection": "j-",/' {} \;
                find *dir-PA_epi*.json -exec \
                sed -i 's/"PhaseEncodingAxis": "j",/&\n\t"PhaseEncodingDirection": "j",/' {} \;



                # Create directories and move files
                mkdir -p fmap dwi func anat survey
                mv -f *Survey* survey/
                mv -f *task* func/
                mv -f *T1* anat/
                mv -f *T2* anat/
                mv -f *FLAIR* anat/
                mv -f *06dir* dwi/
                mv -f *80dir* dwi/
                mv -f *_dir-* fmap/
                mv -f *magnitude* fmap/
                mv -f *phase* fmap/
                mv -f *PSIR* anat/
                cd -
            fi
        fi
    else
        echo "No match found for $filename in $text_file"
    fi
done

echo "SCRIPT COMPLETE"
