"""
Local Dictionary
"""

import json
import time
import requests
from enum import Enum

from datalist import *


class DictionaryEntry:
    def __init__(self, word, part_of_speech, definition, example=None):
        self.word = word
        self.part_of_speech = part_of_speech
        self.definition = definition
        self.example = example

    def __str__(self):
        return f"Word          : {self.word}\n" \
               f"Part of speech: {self.part_of_speech}\n" \
               f"Definition    : {self.definition}\n" \
               f"Example       : {self.example}"


class LocalDictionary:
    def __init__(self, dictionary_json_name="dictionary.json"):
        with open(dictionary_json_name) as file:
            self.dictionary = {}
            data = json.load(file, object_hook=self.dictionary_entry_decoder)
            for d in data["entries"]:
                if isinstance(d, DictionaryEntry):
                    # If entry doesn't have all the required fields, it's not
                    # converted to DictionaryEntry, so we don't add it to dict.
                    self.dictionary[d.word] = d

    def dictionary_entry_decoder(self, o):
        try:
            if "example" in o:
                example = o["example"]
            else:
                example = None

            # This line works, but we haven't talked about ** by this point.
            # return DictionaryEntry(**o)
            return DictionaryEntry(word=o["word"],
                                   part_of_speech=o["part_of_speech"],
                                   definition=o["definition"],
                                   example=example)
        except:
            # If there's an error deserialize o, just return it as is, otherwise
            # it won't get deserialized at all.
            return o

    def search(self, word):
        return self.dictionary[word]


class DictionaryEntryCache(DataList):
    def __init__(self, capacity=1):
        super().__init__()
        if capacity < 1:
            raise ValueError("Capacity should be at least 1")
        self.capacity = capacity
        self.count = 0
        # self.set_list_type(DictionaryEntry)

    def add(self, entry):
        if not isinstance(entry, DictionaryEntry):
            raise TypeError("entry should be DictionaryEntry")
        self.add_to_head(entry)
        self.count += 1
        if self.count > self.capacity:
            self.remove_tail()

    def remove_tail(self):
        self.reset_current()
        current = self.iterate()
        # While we typically shouldn't mix iteration with modification to the list being
        # iterated, we stop iteration as soon as we remove the last node, so that's ok.
        while current:
            if not current.next:
                # If this is true, there's only 1 data node, which should never happen
                # because we ensure capacity is at least 1, and we call remove_tail()
                # only after adding another entry, so there are always at least 2.
                raise RuntimeError("Something's very wrong")

            if not current.next.next:
                # current.next is the last (oldest) one, remove it
                current.remove_after()
                break
            current = self.iterate()
        self.count -= 1

    def search(self, word):
        self.reset_current()
        current = self.iterate()
        while current:
            if current.data.word == word:
                # Found the entry with the right word, remove it from the list,
                # and insert it at the head.  Return it.
                entry = current.data
                self.remove(entry)
                self.add_to_head(entry)
                return entry
            current = self.iterate()
        raise KeyError(f"Cannot find {word}")


class DictionarySource(Enum):
    LOCAL = 1
    CACHE = 2
    OXFORD_ONLINE = 3

    def __str__(self):
        return self.name


class Dictionary:
    def __init__(self, source=DictionarySource.OXFORD_ONLINE):
        # Local dictionary
        self.dictionary = OxfordDictionary()
        self.source = source
        if self.source == DictionarySource.OXFORD_ONLINE:
            self.dictionary = OxfordDictionary()
        elif self.source == DictionarySource.LOCAL:
            self.dictionary = LocalDictionary()
        else:
            raise ValueError
        self.dictionary_entry_cache = DictionaryEntryCache(1)

    def search(self, word):
        try:
            entry = self.dictionary_entry_cache.search(word)
            return (entry, DictionarySource.CACHE)
        except KeyError:
            # If there's a KeyError, we'll search in local dictionary.
            # This may also fail to find the word, at which point we give up
            # (so allow the exception to be raised)
            entry = self.dictionary.search(word)
            self.dictionary_entry_cache.add(entry)
            return (entry, self.source)


class OxfordDictionary:
    def __init__(self):
        self.APP_ID = "5a065188"
        self.APP_KEY = "cb986155975e3c58923550cdd197660c"


    def search(self, word):
        language = "en-gb"
        word_id = word

        url = "https://od-api.oxforddictionaries.com:443/api/v2/entries/" + language+ "/ "+ word_id.lower()

        r = requests.get(url, headers = { "app_id": self.APP_ID , "app_key": self.APP_KEY})

        json_resp = r.json()
        status_resp = r.status_code

        if status_resp is not 200:
            raise KeyError("code {}".format(r.status_code))

        try:
            word_resp = json_resp["id"]
        except KeyError:
            return "word not found"

        part_of_speech_resp = json_resp["results"][0]["lexicalEntries"][0]["lexicalCategory"]["id"]

        definition_resp = json_resp["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0]['definitions'][0]

        try:
            example_resp = json_resp["results"][0]["lexicalEntries"][0]["entries"][0]["senses"][0]["examples"][0]["text"]
        except KeyError:
            example_resp = None

        return DictionaryEntry(word=word_resp,
                                   part_of_speech= part_of_speech_resp,
                                   definition= definition_resp,
                                   example= example_resp)



def time_func(func, word):
    start = time.perf_counter()
    result = func(word)
    duration = time.perf_counter() - start
    return result, duration


def main():
    dictionary = Dictionary()
    while True:
        word = input("Enter a word to lookup: ")
        try:
            entry, source = dictionary.search(word)
            delta_time = time_func(dictionary.search, word)
            print(f"{entry}\n(Found in {source} in {delta_time[1]:3f} seconds)\n")
        except KeyError as e:
            print(f"Error when searching: {str(e)}\n")


if __name__ == '__main__':
    main()

