find . -type f -name "*.py" | while read file; do echo "========$file=========" >> output.txt ; cat "$file" >> output.txt; echo >> output.txt; done
