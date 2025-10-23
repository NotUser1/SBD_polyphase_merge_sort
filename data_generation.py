import random

RECORD_COUNT = 100
TAPE_COUNT = 2
PAGE_SIZE = 10


def calculate_distance(record):
    if record is None:
        return 0
    return (record['x'] ** 2 + record['y'] ** 2) ** 0.5


def fibonacci_pair(n):
    a, b = 1, 1
    while n > (a + b):
        a, b = b, a + b
    return a, b


def generate_record():
    record = {
        "x": random.randint(1, 1000) / 100.0,
        "y": random.randint(1, 1000) / 100.0
        # "x": random.randint(0, 4),
        # "y": 0
    }
    return record


def generate_data():
    records = []
    for _ in range(RECORD_COUNT):
        records.append(generate_record())

    tape_1_run_count, tape_2_run_count, dummy_run_count = split_records_into_tapes(records)
    return tape_1_run_count, tape_2_run_count, dummy_run_count, records


def handle_data_from_file(filename):
    records = []
    with open(f"{filename}", "r") as f:
        for line in f:
            line = line.strip()
            if line == "":
                continue
            x, y = map(float, line.split(','))
            records.append({"x": x, "y": y})
    tape_1_run_count, tape_2_run_count, dummy_run_count = split_records_into_tapes(records)
    return tape_1_run_count, tape_2_run_count, dummy_run_count, records


def get_run_count(runs):
    if not runs:
        return 0
    count = 1
    prev_record = runs[0]
    for record in runs[1:]:
        if calculate_distance(record) < calculate_distance(prev_record):
            count += 1
        prev_record = record
    return count


def split_records_into_tapes(records):
    def write_records_to_tape(tape_number, records_arr, records_count):
        for _ in range(records_count):
            if not records_arr:
                break
            record = records_arr.pop(0)
            tape_number.write(f"{record['x']},{record['y']}\n")
            prev_record = record
            while records_arr:
                record = records_arr[0]
                if calculate_distance(record) >= calculate_distance(prev_record):
                    tape_number.write(f"{record['x']},{record['y']}\n")
                    prev_record = record
                    records_arr.pop(0)
                else:
                    break

    run_count = get_run_count(records)
    a, b = fibonacci_pair(run_count)
    dummy_records_count = (a + b) - run_count
    print("t1: ", b, " t2: ", a, " dummy: ", dummy_records_count)
    # write a records to tape 2 and b - dummy records to tape 2
    with open("tape_1.txt", "w") as tape1, open("tape_2.txt", "w") as tape2:
        write_records_to_tape(tape2, records, a)
        write_records_to_tape(tape1, records, b)
        return b, a, dummy_records_count


def read_manual_input():
    for i in range(TAPE_COUNT):
        print(f"Input tape {i + 1}/2")
        records = []
        while True:
            line = input()
            if line.strip() == "":
                break
            x, y = line.strip().split(',')
            records.append({"x": float(x), "y": float(y)})
        with open(f"tape_{i + 1}.txt", "w") as f:
            for record in records:
                f.write(f"{record['x']},{record['y']}\n")


def generate_archive(parameter, tapes):
    with open(f"./archive/archive_{parameter}.txt", "w+") as archive:
        for tape in tapes:
            tape.file.flush()
            pos = tape.file.tell()
            tape.file.seek(0)
            archive.write(f"--- {tape.filename} ---\n")
            archive.write(tape.file.read())
            archive.write("\n")
            tape.file.seek(pos)
    archive.close()
