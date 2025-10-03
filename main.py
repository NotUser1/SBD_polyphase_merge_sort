import random


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
    tape_count = 3
    for i in range(tape_count):
        record_pack_count = random.randint(1, 5)
        print(f"Generating tape {i + 1} with {record_pack_count} record packs")
        with open(f"tape_{i + 1}.txt", "w") as f:
            for _ in range(record_pack_count):
                records = generate_records()
                for record in records:
                    f.write(f"{record['x']},{record['y']}\n")
                f.write("_\n")


def calculate_distance(x, y):
    return (x ** 2 + y ** 2) ** 0.5


def polyphase_merge_sort():
    print("xd")


def main():
    generate_data()
    polyphase_merge_sort()


main()
