import argparse
import csv
import os.path
import sys
import traceback
import migrator.parser as wikiparser

FILE_COMPLETED = "/Users/srikanth/Code/sahityam/completed.txt"
FILE_FAILED = "/Users/srikanth/Code/sahityam/failed.txt"
FILE_CORRECTIONS = "/Users/srikanth/Code/sahityam/corrections.csv"
PATH_WIKISONGS = "/Users/srikanth/Code/sahityam/songs/"
PATH_CONVERTED = "/Users/srikanth/Code/sahityam/converted"

class SongList:
    def __init__(self, name, filepath):
        self.name = name
        self.file = filepath
        self.songs = set()
        with open(filepath) as f:
            data = f.read().splitlines()
            self.songs = set(data)

    def __contains__(self, song):
        return song in self.songs

    def append(self, song):
        if song in self.songs: return
        with open(self.file, 'a') as f:
            f.write(song + "\n")
        self.songs.add(song)

    def __len__(self):
        return len(self.songs)

class FieldMap:
    def __init__(self, name, filepath):
        self.name = name
        self.file = filepath
        self.map = {}
        reader = csv.reader(self.file)
        for row in reader:
            if len(row) == 2:  # Ensure there are exactly two values
                key, value = row
                self.map[key] = value  # Store as key-value pair

    def __contains__(self, key):
        return key in self.map

    def get(self, key):
        return self.map.get(key)

    def append(self, key, value):
        if key in self.map: return
        with open(self.file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([key, value])
        self.map[key] = value

def get_queue():
    argpar = argparse.ArgumentParser(description="Process a file path.")
    argpar.add_argument('-f', '--file', help='Path to the input file')
    args = argpar.parse_args()
    queue = []

    if args.file:
        file_path = args.file
        print(f"File path provided: {file_path}")

        # File processing logic
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                queue = content.splitlines()
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' does not exist.")
    else:
        args = sys.argv[1:]
        queue = sys.argv[1:]

    return queue


def write_file(name, content):
    with open(os.path.join(PATH_CONVERTED, "{}.md".format(name)), "w") as f:
        f.write(content)

def main():
    completed = SongList("Completed", FILE_COMPLETED)
    failed = SongList("Failed", FILE_FAILED)
    corrections = FieldMap("Corrections", FILE_CORRECTIONS)
    queue = get_queue()
    for song in queue:
        if song in completed:
            print("Skipping {} since it's already migrated.".format(song))
            continue

        try:
            print("Processing", song)
            parsed_song = wikiparser.parse_and_convert(PATH_WIKISONGS + song)

            raga = parsed_song.header_area.raga
            if raga not in corrections:
                corrected_raga = input("Raga [{}]: ".format(parsed_song.header_area.raga))
                if corrected_raga:
                    corrections.append(parsed_song.header_area.raga, corrected_raga)
            parsed_song.header_area.raga = corrections.get(raga)

            filename = parsed_song.new_file
            corrected_filename = input("Filename [{}]: ".format(filename))
            if corrected_filename:
                filename = corrected_filename

            write_file(filename, parsed_song.to_new())
            completed.append(song)
        except Exception as e:
            print("Failed converting or writing song ", song)
            failed.append(song)
            traceback.print_exc()



if __name__ == '__main__':
    main()
