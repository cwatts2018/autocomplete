"""
6.1010 Spring '23 Lab 9: Autocomplete
"""

# NO ADDITIONAL IMPORTS!
import doctest
from text_tokenize import tokenize_sentences

import os.path
import lab
import json
import types
import pickle

TEST_DIRECTORY = os.path.dirname(__file__)


class PrefixTree:
    """
    Creates a prefix tree of letters mapped to children letters, each 
    with a value (or None)
    """
    def __init__(self):
        """
        Creates a prefix tree with a value and a dictionary of children trees.
        """
        self.value = None
        self.children = {}

    def __setitem__(self, key, value):
        """
        Add a key with the given value to the prefix tree,
        or reassign the associated value if it is already present.
        Raise a TypeError if the given key is not a string.
        """

        if not isinstance(key, str):
            raise TypeError
        if len(key) == 1 and key in self.children:  # 'i'
            self.children[key].value = value
        elif len(key) == 0:
            self.value = value
            self.children = {}
        else:
            if key[0] in self.children:
                self.children[key[0]][key[1:]] = value
            else:
                t = PrefixTree()
                t[key[1:]] = value
                self.children[key[0]] = t

    def __getitem__(self, key):
        """
        Return the value for the specified prefix.
        Raise a KeyError if the given key is not in the prefix tree.
        Raise a TypeError if the given key is not a string.
        """

        if not isinstance(key, str):
            raise TypeError
        tree = self
        for i in range(len(key)):
            if key[i] in tree.children:
                tree = tree.children[key[i]]
                if i == len(key)-1:
                    value = tree.value
            else:
                raise KeyError
        if not isinstance(value, type(None)):
            return value
        else:
            raise KeyError

    def __delitem__(self, key):
        """
        Delete the given key from the prefix tree if it exists.
        Raise a KeyError if the given key is not in the prefix tree.
        Raise a TypeError if the given key is not a string.
        """
        if not isinstance(key, str):
            raise TypeError
        try:
            x = self[key]
        except:
            raise KeyError
        self[key] = None

    def __contains__(self, key):
        """
        Is key a key in the prefix tree?  Return True or False.
        Raise a TypeError if the given key is not a string.
        """
        if not isinstance(key, str):
            raise TypeError
        try:
            x = self[key]
            return True
        except:
            return False

    def __iter__(self):
        """
        Generator of (key, value) pairs for all keys/values in this prefix tree
        and its children.  Must be a generator!
        """
        for child in self.children:
            if not isinstance(self.children[child].value, type(None)):
                yield (child, self.children[child].value)
            def create_children():
                yield from self.children[child] #('at', 'kitten')
            for children in create_children():
                yield (child+children[0], children[1])

    def increment_item(self, key):
        """
        Increments the value at key in the prefix tree by 1
        """
        if not isinstance(key, str):
            raise TypeError
        try:
            self[key] = self[key] + 1
        except:
            self[key] = 1


def word_frequencies(text):
    """
    Given a piece of text as a single string, create a prefix tree whose keys
    are the words in the text, and whose values are the number of times the
    associated word appears in the text.
    """
    sentences = tokenize_sentences(text)
    tree = PrefixTree()
    for sentence in sentences:
        words = sentence.split(" ")
        for word in words:
            tree.increment_item(word)
    return tree


def autocomplete_helper(tree, prefix, max_count=None):
    """
    Helps autocomplete by recursing through potential autocompletions.
    """
    cur_tree = tree
    for letter in prefix:
        if letter in cur_tree.children:
            cur_tree = cur_tree.children[letter]
        else:
            return []

    words = set()
    if not isinstance(cur_tree.value, type(None)):
        words.add(prefix)
    for letter in cur_tree.children:
        next_tree = cur_tree.children[letter]
        if len(next_tree.children) != 0:
            words.update(autocomplete_helper(tree, prefix+letter, max_count))
        elif not isinstance(next_tree.value, type(None)):
            words.add(prefix+letter)

    return words


def autocomplete(tree, prefix, max_count=None):
    """
    Return the list of the most-frequently occurring elements that start with
    the given prefix.  Include only the top max_count elements if max_count is
    specified, otherwise return all.

    Raise a TypeError if the given prefix is not a string.
    """
    if not isinstance(prefix, str):
        raise TypeError

    words = autocomplete_helper(tree, prefix, max_count)

    if isinstance(max_count, type(None)):
        return list(words)

    most_freq = ""
    refined_words = []

    while max_count > 0 and len(words) != 0:
        freq = 0
        for elt in words:
            if tree[elt] > freq:
                freq = tree[elt]
                most_freq = elt

        refined_words.append(most_freq)
        words.remove(most_freq)
        max_count -= 1

    return refined_words


def autocorrect(tree, prefix, max_count=None):
    """
    Return the list of the most-frequent words that start with prefix or that
    are valid words that differ from prefix by a small edit.  Include up to
    max_count elements from the autocompletion.  If autocompletion produces
    fewer than max_count elements, include the most-frequently-occurring valid
    edits of the given word as well, up to max_count total elements.
    """

    completed = autocomplete(tree, prefix, max_count)
    # if prefix == "mon" and max_count == 20:
    #     print(completed)
    if not isinstance(max_count, type(None)) and len(completed) == max_count:
        return completed
    suggestions = []
    suggestions.extend(del_autocorrections(tree, prefix))
    # print('1', suggestions)
    suggestions.extend(insertion_autocorrections(tree, prefix))
    # print('2', suggestions)
    suggestions.extend(replace_autocorrections(tree, prefix))
    suggestions.extend(transpose_autocorrections(tree, prefix))

    if isinstance(max_count, type(None)):
        completed.extend(suggestions)
        return remove_duplicates(completed)

    suggestions = remove_duplicates(suggestions)
    most_freq = ""

    max_count -= len(completed)

    while max_count > 0 and len(suggestions) != 0:

        freq = 0
        for elt in suggestions:
            # print(elt)
            if tree[elt] > freq:
                freq = tree[elt]
                most_freq = elt

        if most_freq not in completed:
            completed.append(most_freq)
            max_count -= 1
        # print(max_count, most_freq)
        suggestions.remove(most_freq)

        

    return completed


def remove_duplicates(words):
    """
    Removes all duplicates in the list, words.
    """
    words = set(words)
    new_words = set()
    for word in words:
        if word not in new_words:
            new_words.add(word)

    return list(new_words)


def del_autocorrections(tree, prefix):
    """
    Makes all the autocorrections to prefix given a tree that delete a char.
    """
    corrections = []
    for i, letter in enumerate(prefix):  # c - "a" - n
        if prefix[:i]+prefix[i+1:] in tree:
            corrections.append(prefix[:i]+prefix[i+1:])
    return corrections


def insertion_autocorrections(tree, prefix):
    """
    Makes all the autocorrections to prefix given a tree that insert a char.
    """
    corrections = []
    for letter in tree.children:  # add first letter
        if letter+prefix in tree:
            corrections.append(letter+prefix)

    if prefix[0] in tree.children:
        cur_tree = tree.children[prefix[0]]
        for i, letter in enumerate(prefix):  # c - "a" - n
            for next_letter in cur_tree.children:  # for every child
                # add last letter
                if i == len(prefix)-1 and len(cur_tree.children[next_letter].children) == 0:
                    corrections.append(prefix+next_letter)
                elif prefix[:i+1]+next_letter+prefix[i+1:] in tree:
                    # if child leads to next prefix letter, add valid word
                    corrections.append(prefix[:i+1]+next_letter+prefix[i+1:])
            if i == len(prefix)-1:
                break
            elif prefix[i+1] in cur_tree.children:
                cur_tree = cur_tree.children[prefix[i+1]]
            else:
                break
    return corrections


def replace_autocorrections(tree, prefix):
    """
    Makes all the autocorrections to prefix given a tree that replace a char.
    """
    corrections = []
    cur_tree = tree
    for i, letter in enumerate(prefix):  # c - "a" - n
        for replacement in cur_tree.children:
            if prefix[:i]+replacement + prefix[i+1:] in tree:
                corrections.append(prefix[:i]+replacement+prefix[i+1:])
        if letter in cur_tree.children:
            cur_tree = cur_tree.children[letter]
        else:
            break
    return corrections


def transpose_autocorrections(tree, prefix):
    """
    Makes all the autocorrections to prefix given a tree that switches 2 chars.
    """
    corrections = []
    for i, letter in enumerate(prefix):
        for i2, letter2 in enumerate(prefix):
            transpose = prefix[:i]+letter2+prefix[i+1:i2]+letter+prefix[i2+1:]
            if transpose in tree:
                corrections.append(transpose)
    return corrections
        
def add_letter(tree, pattern, result):
    """
    Adds letter to result given tree and pattern.
    """
    if not isinstance(tree.children[pattern].value, type(None)):
        result.append((pattern, tree.children[pattern].value))
        
def add_children(tree, pattern, result):
    """
    Adds children to result given tree and pattern.
    """
    for child in tree.children:
        child_filters = word_filter(tree.children[child], pattern)
        for grandchild in child_filters:
            if (child+grandchild[0], grandchild[1]) not in result:
                result.append((child+grandchild[0], grandchild[1]))
    
def word_filter(tree, pattern):
    """
    Return list of (word, freq) for all words in the given prefix tree that
    match pattern.  pattern is a string, interpreted as explained below:
         * matches any sequence of zero or more characters,
         ? matches any single character,
         otherwise char in pattern char must equal char in word.
    """
    result = []
    if pattern[0] == "*":
        while len(pattern) > 1 and pattern[1] == "*":
            pattern = pattern[0]+pattern[2:]
    if len(pattern) == 1:
        if pattern == "?":
            for child in tree.children:
                add_letter(tree, child, result)
        elif pattern == "*":
            all_words = list(tree)
            for word in all_words:
                result.append((word[0], tree[word[0]]))
            if not isinstance(tree.value, type(None)):
                result.append(("", tree.value))
        elif pattern not in tree.children:
            return []
        else:
            add_letter(tree, pattern, result)
    else:
        if pattern[0] == "?":
            add_children(tree, pattern[1:], result)
        
        elif pattern[0] == "*":
            if pattern[1] in tree.children or pattern[1] == "?":
                child_filters = word_filter(tree, pattern[1:])
                for grandchild in child_filters:
                    result.append((grandchild[0], grandchild[1]))
            add_children(tree, pattern, result)
        
        elif pattern[0] not in tree.children:
            return []
        
        else:
            child_filters = word_filter(tree.children[pattern[0]], pattern[1:])
            for child in child_filters:
                result.append((pattern[0]+child[0], child[1]))
    return result

# you can include test cases of your own in the block below.
if __name__ == "__main__":
    doctest.testmod()
    



