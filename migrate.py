import json
import glob
import os
from typing import Dict, Any, List
import pprint

def walk(data: Dict[str, Any] | List[Any]):
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if key.startswith("bloqade.analog."):
                new_dict[key] = walk(value)
            elif key.startswith("bloqade."):
                new_dict[key.replace("bloqade.", "bloqade.analog.")] = walk(value)
            else:
                new_dict[key] = walk(value)
                
        return new_dict
    elif isinstance(data, list):
        return [walk(item) for item in data]
    else:
        return data


path = os.path.dirname(__file__)

files = glob.glob(os.path.join(path,"*.json"))

for file in files:
    with open(file, "r") as f:
        data = json.load(f)
        new_data = walk(data)
    
    with open(file, "w") as f:
        json.dump(new_data, f)

        
        





