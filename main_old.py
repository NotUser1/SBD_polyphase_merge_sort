import random

global NUM_OF_RECORD_READS, NUM_OF_WRITES, NUM_OF_PHASES

TAPE_COUNT = 2
PAGE_SIZE = 4
NUM_OF_RECORD_READS = 0
NUM_OF_WRITES = 0
NUM_OF_PHASES = 0


def generate_records():
    # generate a random number of records between 1 and 5
    record_count = random.randint(1, 5)
    data = []
    for _ in range(record_count):
        record = {
            "x": random.randint(1, 1000) / 100.0,
            "y": random.randint(1, 1000) / 100.0
        }
        data.append(record)
    return data


def generate_data():
    # generate 3 tapes of 1 to 3 record packs each, each tape gets written to a distinct file
    for i in range(TAPE_COUNT):
        record_pack_count = random.randint(1, 5)
        print(f"Generating tape {i + 1} with {record_pack_count} record packs")
        with open(f"tape_{i + 1}.txt", "w") as f:
            for _ in range(record_pack_count):
                records = generate_records()
                records.sort(key=lambda r: calculate_distance(r))
                for record in records:
                    f.write(f"{record['x']},{record['y']}\n")


def generate_archive(parameter):
    if parameter == 1:
        f_name = "archive_before"
    else:
        f_name = "archive_after"
    with open(f"{f_name}.txt", "w") as archive:
        for i in range(1, TAPE_COUNT + 2):
            tape_file = f"tape_{i}.txt"
            archive.write(f"{tape_file}\n")
            with open(tape_file, "r") as tape:
                archive.write(tape.read())
            archive.write("\n")


def read_manual_input():
    for i in range(TAPE_COUNT):
        print(f"Tape {i + 1}/3")
        with open(f"tape_{i + 1}.txt", "w") as f:
            while True:
                x = input("Enter x: ")
                y = input("Enter y: ")
                f.write(f"{x},{y}\n")
                cont = input("To add another record press '1', to end this tape press any other key: ")
                if cont == '1':
                    continue
                else:
                    break


def calculate_distance(record):
    return (record['x'] ** 2 + record['y'] ** 2) ** 0.5


def write_one_record(output_file, record, source_file):
    global NUM_OF_WRITES
    NUM_OF_WRITES += 1
    output_file.write(f"{record['x']},{record['y']}\n")
    delete_written_record(source_file)


def read_one_record(file):
    global NUM_OF_RECORD_READS
    NUM_OF_READS += 1
    line = file.readline()
    if not line:
        return None
    x, y = map(float, line.strip().split(','))
    return {"x": x, "y": y}


def read_page(file):
    page = []
    for _ in range(PAGE_SIZE):
        record = read_one_record(file)
        if record is None:
            break
        page.append(record)
    return page


def delete_written_record(file):
    # deletes the first line of the file
    file.seek(0)  # Move to the start of the file
    lines = file.readlines()  # Read all lines
    file.seek(0)  # Move back to the start of the file
    file.truncate(0)  # Clear the file
    file.writelines(lines[1:])  # Write back all lines except the first one
    file.seek(0)  # Reset the file pointer to the start




def merge_two_files(input_tape_1, input_tape_2, output_tape):
    global NUM_OF_PHASES
    NUM_OF_PHASES += 1
    page_1 = read_page(input_tape_1)
    page_2 = read_page(input_tape_2)
    previous_record_1 = None
    previous_record_2 = None






def polyphase_merge_sort():
    with open("tape_1.txt", "r+") as tape_1, \
            open("tape_2.txt", "r+") as tape_2, \
            open("tape_3.txt", "w+") as tape_3:
        merge_two_files(tape_1, tape_2, tape_3)


def main():
    global NUM_OF_RECORD_READS, NUM_OF_WRITES, NUM_OF_PHASES
    NUM_OF_READS = 0
    NUM_OF_WRITES = 0
    NUM_OF_PHASES = 0

    # key = input("Enter 'm' to input records manually otherwise press any key to continue: ")
    # if key == 'm':
    #     print("Manual input")
    #     read_manual_input()
    # else:
    #     print("Generating random data")
    #     generate_data()
    generate_data()

    with open(f"tape_{TAPE_COUNT + 1}.txt", "w") as _:
        pass

    # archive file before sorting
    generate_archive(1)

    polyphase_merge_sort()

    # archive file after sorting
    generate_archive(2)

    print(f"Number of reads: {NUM_OF_READS}")
    print(f"Number of writes: {NUM_OF_WRITES}")
    print(f"Number of phases: {NUM_OF_PHASES}")


if __name__ == "__main__":
    main()
