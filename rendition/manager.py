import argparse
import csv
import os.path
import sys
import traceback
import rendition.parser as parser
import rendition.youtube as youtube

FILE_COMPLETED = "/Users/srikanth/Code/sahityam/renditions/completed.txt"
FILE_FAILED = "/Users/srikanth/Code/sahityam/renditions/failed.txt"
PATH_INPUT = "/Users/srikanth/Code/sahityam/renditions/input/"
PATH_CONVERTED = "/Users/srikanth/Code/sahityam/renditions/output/"

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
    with open(os.path.join(PATH_CONVERTED, "{}".format(name)), "w") as f:
        f.write(content)

def main():
    argpar = argparse.ArgumentParser(description="Process a file path.")
    argpar.add_argument('-f', '--file', required=False, help='Path to the input file')
    argpar.add_argument('-s', '--song', required=False, help='The song file to process')
    args = argpar.parse_args()

    completed = SongList("Completed", FILE_COMPLETED)
    failed = SongList("Failed", FILE_FAILED)
    queue = get_queue(args)
    from pprint import pprint
    for song in queue:
        if song in completed:
            print("Skipping {} since it's already processed.".format(song))
            continue

        try:
            print("\nProcessing", song)
            parsed_song = parser.parse(PATH_INPUT + song)[0]
            if parsed_song.is_valid():
                print("The song {} has valid renditions. Skipping".format(song))
                completed.append(song)
                continue

            query_exp = "{} {}".format(song.replace("-", " ").replace(".md", ""), parsed_song.raga())
            print("Searching for '{}'".format(query_exp))
            video_id = youtube.find_renditions(query_exp)
            if not video_id:
                print("Skipping ()".format(song))
                continue
            parsed_song.set_renditions("{{<youtube \"%s\" >}}\n" % (video_id,))
            write_file(song, parsed_song.to_new())
            completed.append(song)
        except Exception as e:
            print("Failed converting or writing song {} due to {}".format(song, e))
            failed.append(song)
            traceback.print_exc()

if __name__ == '__main__':
    main()
