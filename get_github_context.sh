#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Check if a repository URL is provided
if [ $# -lt 1 ]; then
    log_message "Usage: $0 <github_repo_url> [branch_name]"
    exit 1
fi

# GitHub repository URL
repo_url="$1"

# Branch name (default to 'main' if not provided)
branch_name=${2:-main}

# Extract repository name from URL
repo_name=$(basename -s .git "$repo_url")

# Save the original working directory
original_dir=$(pwd)
log_message "Original directory: $original_dir"

# Output file
output_file="${repo_name}_${branch_name}_context.md"
log_message "Output file will be: $output_file"

# Remove the output file if it already exists
rm -f "$output_file"

# Function to process each file
process_file() {
    local file="$1"
    log_message "Processing file: $file"
    echo "Path: $file" >> "$output_file"
    echo "" >> "$output_file"

    # Determine the file extension
    extension="${file##*.}"

    # Set the appropriate language for the code block
    case "$extension" in
        py) language="python" ;;
        js) language="javascript" ;;
        html) language="html" ;;
        css) language="css" ;;
        md) language="" ;;
        *) language="plaintext" ;;
    esac

    echo "\`\`\`$language" >> "$output_file"
    cat "$file" >> "$output_file"
    echo "\`\`\`" >> "$output_file"
    echo "" >> "$output_file"
    echo "-----------" >> "$output_file"
    echo "" >> "$output_file"
}

# Check if required tools are installed
for tool in git fd; do
    if ! command -v $tool &> /dev/null; then
        log_message "Error: $tool is not installed. Please install $tool and try again."
        exit 1
    fi
done

# Create a temporary directory for cloning
temp_dir=$(mktemp -d)
log_message "Temporary directory created: $temp_dir"

# Clone the repository
log_message "Cloning repository (branch: $branch_name)..."
if ! git clone -b "$branch_name" "$repo_url" "$temp_dir"; then
    log_message "Failed to clone repository or branch. Please check the URL and branch name."
    exit 1
fi

# Change to the cloned repository directory
cd "$temp_dir"
log_message "Changed to directory: $(pwd)"

# List all files in the cloned repository
log_message "Files in the cloned repository:"
find . -type f

# Find files using fd, sort them by depth, then process each file
log_message "Finding and processing files..."
log_message "fd command: fd -H -t f -e py -e js -e html -e css -e md"
files=$(fd -H -t f -e py -e js -e html -e css -e md)
if [ -z "$files" ]; then
    log_message "No files found matching the specified extensions."
    log_message "Trying with all files..."
    files=$(fd -H -t f)
fi

if [ -z "$files" ]; then
    log_message "No files found at all. This is unexpected."
else
    log_message "Files found:"
    echo "$files"
    echo "$files" | sort -n -t'/' -k'1' | while read -r file; do
        process_file "$file"
    done
fi

# Check if the output file was created
if [ -f "$output_file" ]; then
    log_message "Output file created successfully."
    log_message "Moving output file to original directory..."
    if mv "$output_file" "$original_dir/"; then
        log_message "Successfully moved $output_file to $original_dir/"
    else
        log_message "Failed to move $output_file to $original_dir/"
        log_message "Attempting to copy instead..."
        if cp "$output_file" "$original_dir/"; then
            log_message "Successfully copied $output_file to $original_dir/"
        else
            log_message "Failed to copy $output_file to $original_dir/"
            log_message "Output file remains in $(pwd)/$output_file"
        fi
    fi
else
    log_message "Error: Output file $output_file not created."
fi

# Change back to the original directory
cd "$original_dir"
log_message "Changed back to original directory: $(pwd)"

# Clean up: remove the temporary directory
log_message "Cleaning up temporary directory..."
rm -rf "$temp_dir"

log_message "Script execution completed."

# Final check
if [ -f "$output_file" ]; then
    log_message "Output file $output_file successfully created."
    log_message "File contents (first 10 lines):"
    head -n 10 "$output_file"
else
    log_message "Error: Output file $output_file not found in the current directory."
    log_message "Current directory contents:"
    ls -la
fi
