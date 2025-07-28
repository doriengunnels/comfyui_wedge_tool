import argparse
from datetime import datetime, timedelta
from itertools import product
import json
import logging
import os
from pprint import pprint as pp
import random
import sys
import urllib.request
import urllib.parse
import uuid
import websocket

def calc_elapsed_time(start_ts, end_ts):
    start_seconds = start_ts / 1000
    end_seconds = end_ts / 1000
    elapsed = timedelta(seconds=(end_seconds - start_seconds))
    hours, remainder = divmod(elapsed.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    return hours, minutes, seconds, elapsed

def confirm(prompt="Are you sure? (y/n): "):
    while True:
        response = input(prompt).strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'.")

def estimate_time_remaining(elapsed_times, total_iterations):
    logged_count = len(elapsed_times)
    average_time = sum(elapsed_times, timedelta()) / logged_count
    remaining_iterations = total_iterations - logged_count
    remaining_time = average_time * remaining_iterations
    return remaining_time

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(SERVER_ADDRESS, prompt_id)) as response:
        return json.loads(response.read())
    
def get_node_number(loaded_workflow, name_search, print_if_not_exist=True):
    for node in loaded_workflow:
        if loaded_workflow[node]['_meta']['title'] == name_search:
            return node
    if print_if_not_exist == True:
        print(f"No node with title: {name_search}")
        print(f"Operation cancelled.")
        sys.exit(0)

def get_highest_node_number(loaded_workflow):
    node_numbers = []
    for item in loaded_workflow.items():
        node_numbers.append(int(item[0]))
    node_numbers.sort()
    highest_node_number = node_numbers[-1]
    return highest_node_number

def get_out_img_path(prompt_id):
    history = get_history(prompt_id)[prompt_id]
    image_outs = []
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output:
            image_outs.append(node_output)
    out_img_data = image_outs[-1]["images"][0]
    return os.path.join(out_img_data["subfolder"], out_img_data["filename"])

def get_parameter_value(loaded_workflow, node_title, parameter):
    node_number = get_node_number(loaded_workflow, node_title)
    return loaded_workflow[node_number]["inputs"][parameter]

def load_json(json_file=str):
    with open(json_file, "r", encoding="utf-8") as f:
        return json.loads(f.read())

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": CLIENT_ID}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/prompt".format(SERVER_ADDRESS), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def set_parameter(loaded_workflow, node_title, parameter, value):
    node_number = get_node_number(loaded_workflow, node_title)
    loaded_workflow[node_number]["inputs"][parameter] = value

def add_wedge_config_string_node(loaded_workflow, wedge_config, node_title="WEDGE_string"):
    if get_node_number(loaded_workflow, node_title, print_if_not_exist=False) == None:
        highest_node_number = get_highest_node_number(loaded_workflow)
        new_node_key = str(highest_node_number + 1)
        new_node_dict = {
            "inputs": {
                "value": json.dumps(wedge_config)
                },
            "class_type": "PrimitiveString",
            "_meta": {
                "title":node_title
                }
            }
        loaded_workflow[new_node_key] = new_node_dict
    else:
        set_parameter(loaded_workflow, node_title, "value", json.dumps(wedge_config))

def get_wedge_config_from_loaded_workflow_metadata(loaded_workflow):
    for node in loaded_workflow:
        if loaded_workflow[node]['_meta']['title'] == "WEDGE_string":
            value = loaded_workflow[node]['inputs']['value']
            value_dict = json.loads(value)
    return value_dict

def frange(start, stop, step):
    values = []
    while start <= stop:
        values.append(round(start, 10))
        start += step
    return values

def generate_combinations(params_dict):
    param_names = list(params_dict.keys())
    param_values = []
    for param in param_names:
        node_name, values_config, mode = params_dict[param]
        if mode == "minmax":
            min_val, max_val, step = values_config
            values = frange(min_val, max_val, step)
        elif mode == "explicit":
            values = values_config
        else:
            raise ValueError(f"Unknown mode '{mode}' for parameter '{param}'")
        param_values.append(values)
    return [dict(zip(param_names, combo)) for combo in product(*param_values)]


def submit_iterations(loaded_workflow, params, out_folder, filename_prefix, _confirmation=True, _for_testing=False, _print_combinations=False):

    # --- Generate all wedge parameter combinations ---
    all_combinations = generate_combinations(params)

    # --- Prints all combinations to the terminal ---
    if _print_combinations:
        for i, combo in enumerate(all_combinations, 1):
            print(combo)

    # --- Yes/No Confirmation before submitting ---
    if _confirmation:
        total_to_submit = len(all_combinations) if not _for_testing else 1
        if not confirm(f"Total submissions = {total_to_submit}\nSubmit all? (y/n): "):
            print("Operation cancelled.")
            sys.exit(0)

    # --- Open the websocket ---
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(SERVER_ADDRESS, CLIENT_ID))

    # --- Set wedge param values and submit ---
    elapsed_times = []
    for i, combo in enumerate(all_combinations, 1):

        # --- set iteration of total (for logging) ---
        i_of_all = f"{i}/{len(all_combinations)} ==== "

        # --- set values, build the file name, and queue the prompt ---
        filename = filename_prefix
        for key, value in combo.items():
            node_name = params[key][0]
            set_parameter(loaded_workflow, node_name, key, value)
            filename += f"__{key}-{str(value).replace(' ', '_')}"
        
        out_path = os.path.join(out_folder, filename)
        set_out_path(loaded_workflow, out_path, node_title="OUT_image")

        logging.info(f"{i_of_all} SUBMITTING")
        prompt_id = queue_prompt(loaded_workflow)["prompt_id"]

        # --- For Terminal printing ------------------------------------------
        # --- Doesn't continue the loop until the image is done generating ---
        while True:
            out = ws.recv()
            if isinstance(out, str):
                logging.debug(f"{i_of_all} {out}")
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break
            else:
                continue

        # --- Calc elapsed time and print confirmation logging ---
        hrs, mins, secs, elapsed = calc_elapsed_time(
            get_history(prompt_id)[prompt_id]["status"]["messages"][0][1]["timestamp"],
            get_history(prompt_id)[prompt_id]["status"]["messages"][2][1]["timestamp"]
            )
        elapsed_times.append(elapsed)
        logging.info(f"{i_of_all} DONE - Elapsed time: {int(hrs)}h {int(mins)}m {secs:.3f}s")
        logging.info(f"{i_of_all} Path: {get_out_img_path(prompt_id)}")
        logging.info(f"Estimated time remaining: {estimate_time_remaining(elapsed_times, len(all_combinations))}")

        # --- Stops the script after the first loop if _for_testing is True ---
        if _for_testing:
            ws.close()
            break

    # --- close the websocket after all images are generated ---
    ws.close()

def set_out_path(loaded_workflow, out_path, node_title="OUT_image"):

    named_out_node_number = get_node_number(loaded_workflow, node_title,print_if_not_exist=False)
    if named_out_node_number != None:
        set_parameter(loaded_workflow, node_title,"filename_prefix",out_path)   
    else:
        save_image_nodes = {k: v for k, v in loaded_workflow.items() if v["class_type"] == "SaveImage"}
        if len(save_image_nodes) == 1:
            node_title = save_image_nodes[list(save_image_nodes.keys())[0]].get('_meta').get('title')
            set_parameter(loaded_workflow, node_title,"filename_prefix",out_path)
        else:
            print(f"Could not identify OUT node. Please specify which to use by naming it '{node_title}'")

#########################################################################################################
#########################################################################################################
#########################################################################################################

# ------------------ LOGGING CONFIG ------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s ==== %(message)s',
    handlers=[
        #logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# ------------------ MAIN ENTRY ------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run wedge parameter sweep")
    parser.add_argument("--json-folder", required=True, help="Path to folder containing workflow_api.json and wedge_config.json")
    args = parser.parse_args()

    # Load workflow_api.json and wedge_config.json
    json_folder = args.json_folder
    workflow_api_filename = "workflow_api.json"
    wedge_config_filename = "wedge_config.json"
    workflow_api_path = os.path.join(json_folder, workflow_api_filename)
    wedge_config_path = os.path.join(json_folder, wedge_config_filename)
    loaded_workflow = load_json(workflow_api_path)
    wedge_config = load_json(wedge_config_path)

    SERVER_ADDRESS = wedge_config['url']
    CLIENT_ID = str(uuid.uuid4())
    project_name = wedge_config['project_name']
    out_filename_prefix = wedge_config['filename_prefix']
    for_testing = wedge_config['for_testing']
    show_confirmation = wedge_config['show_confirmation']

    for param_override in wedge_config["param_overrides"]:
        node_name, input_param, value = param_override
        set_parameter(loaded_workflow, node_name, input_param, value)

    wedge_params = wedge_config["param_wedges"]

    # Add an adhoc node into workflow_api.json that contains the wedge_config info.
    # This will get saved along with the rest of the workflow into the png metadata.
    add_wedge_config_string_node(loaded_workflow, wedge_config)

    out_folder = os.path.join(project_name, "images")

    submit_iterations(loaded_workflow, wedge_params, out_folder, out_filename_prefix, _confirmation=show_confirmation, _for_testing=for_testing, _print_combinations=False)

