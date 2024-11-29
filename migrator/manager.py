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
        with open(filepath, newline='') as csvfile:
            reader = csv.reader(csvfile)
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

def get_queue(args):
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
    elif args.song:
        queue = [args.song]

    return queue


def write_file(name, content):
    with open(os.path.join(PATH_CONVERTED, "{}.md".format(name)), "w") as f:
        f.write(content)

def main():
    argpar = argparse.ArgumentParser(description="Process a file path.")
    argpar.add_argument('-f', '--file', required=False, help='Path to the input file')
    argpar.add_argument('-s', '--song', required=False, help='The song file to process')
    argpar.add_argument('-d', '--skip-drafts', action='store_true', help='Skip draft stage songs')
    args = argpar.parse_args()

    completed = SongList("Completed", FILE_COMPLETED)
    failed = SongList("Failed", FILE_FAILED)
    corrections = FieldMap("Corrections", FILE_CORRECTIONS)
    queue = get_queue(args)
    for song in queue:
        if song in completed:
            print("Skipping {} since it's already migrated.".format(song))
            continue

        try:
            print("\nProcessing", song)
            parsed_song = wikiparser.parse_and_convert(PATH_WIKISONGS + song)

            if args.skip_drafts and (parsed_song.is_draft or not parsed_song.is_translated()):
                print("Skipping {} since it's a draft or not translated".format(song))
                continue

            raga = parsed_song.header_area.raga
            if raga not in corrections:
                corrected_raga = input("Raga [{}]: ".format(raga))
                if corrected_raga:
                    corrections.append(parsed_song.header_area.raga, corrected_raga)
            parsed_song.header_area.raga = corrections.get(raga)

            tala = parsed_song.header_area.tala
            if tala not in corrections:
                corrected_tala = input("Tala [{}]: ".format(tala))
                if corrected_tala:
                    corrections.append(parsed_song.header_area.tala, corrected_tala)
            parsed_song.header_area.tala = corrections.get(tala)

            composer = parsed_song.header_area.composer
            if composer not in corrections:
                corrected_composer = input("composer [{}]: ".format(composer))
                if corrected_composer:
                    corrections.append(parsed_song.header_area.composer, corrected_composer)
            parsed_song.header_area.composer = corrections.get(composer)

            language = parsed_song.header_area.language
            if language not in corrections:
                corrected_language = input("language [{}]: ".format(language))
                if corrected_language:
                    corrections.append(parsed_song.header_area.language, corrected_language)
            parsed_song.header_area.language = corrections.get(language)

            format = parsed_song.header_area.format
            if format not in corrections:
                corrected_format = input("format [{}]: ".format(format))
                if corrected_format:
                    corrections.append(parsed_song.header_area.format, corrected_format)
            parsed_song.header_area.format = corrections.get(format)

            title = parsed_song.title
            corrected_title = input("Title [{}]: ".format(title))
            if corrected_title:
                parsed_song.title = corrected_title

            filename = parsed_song.new_file
            corrected_filename = input("Filename [{}]: ".format(filename))
            if corrected_filename:
                filename = corrected_filename

            write_file(filename, parsed_song.to_new())
            completed.append(song)
        except Exception as e:
            print("Failed converting or writing song {} due to {}".format(song, e))
            failed.append(song)
            traceback.print_exc()



if __name__ == '__main__':
    main()
