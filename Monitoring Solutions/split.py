import os

def split_file(input_file, chunk_size_mb=20):
    """
    Splits a large text file into smaller files of specified size.

    :param input_file: Path to the input file.
    :param chunk_size_mb: The size of each chunk in MB.
    """
    chunk_size = chunk_size_mb * 1024 * 1024  # Convert MB to bytes
    output_dir = 'output'

    # Create directory for output files
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, 'r', encoding='utf-8') as file:
        chunk_number = 1
        while True:
            # Read a chunk of data from the file
            chunk_data = file.read(chunk_size)

            # If no more data is left, stop the loop
            if not chunk_data:
                break

            # Create a new file for the current chunk
            chunk_file_name = f'{output_dir}/chunk_{chunk_number}.txt'
            with open(chunk_file_name, 'w', encoding='utf-8') as chunk_file:
                chunk_file.write(chunk_data)

            print(f'Created {chunk_file_name} with size {len(chunk_data)} bytes.')

            # Increment the chunk number
            chunk_number += 1

    print('File splitting complete.')

if __name__ == "__main__":
    input_file_path = 'Snapshot_details.txt'  # Replace with the path to your large file
    split_file(input_file_path)
