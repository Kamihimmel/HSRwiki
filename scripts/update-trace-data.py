#!/usr/bin/env python

import copy
import json
import re
import sys
from pprint import pprint
from deepdiff import DeepDiff
from jsonmerge import Merger


# Declaration
class TraceDataItem:
    def __init__(self, name, description, type):
        self.name = name
        self.description = description
        self.type = type

    @classmethod
    def from_json(cls, json_obj):
        name = json_obj.get('ENname')
        description = json_obj.get('DescriptionEN')
        type = json_obj.get('ttype')
        if name is not None and description is not None and type is not None:
            return cls(name, description, type)
        else:
            return None
    
    def parse_number_from_name(self):
        match = re.search(r'(\d+(\.\d+)?)', self.name)
        if match:
            number = float(match.group(1))
            if number.is_integer():
                return int(number)
            else:
                return number
        else:
            return None
        
    def generate_effect_nodes(self):
        multiplier = self.parse_number_from_name()
        if multiplier is None:
            return None
        nodes = {
            'tags': ['buff', 'self', self.type],
            'effect': [
                {
                    'iid': "1",
                    'type': "buff",
                    'addtarget': self.type,
                    'multiplier': multiplier,
                    'tag': ["buff", "self", self.type]
                }
            ]
        }
        return nodes

# Define a schema that specifies the merge strategy
schema = {
    "properties": {
        "tracedata": {
            "mergeStrategy": "append"
        }
    }
}
     
# Create a merger with the schema
merger = Merger(schema)

# Program
# 
# read the character tracedata and auto append the tags and effect

file_path = './lib/aventurine.json'

# load the JSON data
with open(file_path) as f:
    data = json.load(f)

# Create a copy of the original data
original_data = copy.deepcopy(data)

# Update tracedata effect (A1~A6, Lv1~Lv80)
if 'tracedata' in data and isinstance(data['tracedata'], list):
    for item in data['tracedata']:
        traceDataItem = TraceDataItem.from_json(item)
        if traceDataItem is None:
            continue
        effect_nodes = traceDataItem.generate_effect_nodes()
        if effect_nodes is None:
            continue
        # merge nodes
        item['tags'] = merger.merge(item.get('tags', {}), effect_nodes['tags'])
        item['effect'] = merger.merge(item.get('effect', {}), effect_nodes['effect'])

# Compare the original and the modified data
if original_data == data:
    print("No changes were made to the data.")
    sys.exit()
else:
    print("The data was modified.")

    # Compare the original and the modified data
    diff = DeepDiff(original_data, data)

    # Print the differences
    pprint(diff)

    # Ask the user whether they want to continue
    user_input = input("Do you want to update the file? (yes/no): ")

    # If the user doesn't want to continue, abort the program
    if user_input.lower() != "yes":
        print("Aborting.")
        sys.exit()

# Write the data back to the JSON file
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)