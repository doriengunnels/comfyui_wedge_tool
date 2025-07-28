# ComfyUI Wedge Tool

A toolset used to render and view wedges from ComfyUI. This can be used with any workflow as long as there is a single output node.

### This requires a folder containing two files:
- **workflow_api.json** - an api export of the ComfyUI workflow you intend to wedge.
- **wedge_config.json** - A copy of the wedge_config file. This drives the parameters being wedged. This can be copied from the **/templates/examples/** folder and renamed.

You can use the **work/** folder for convenience.

# Quick Start (Windows)

### Setup

1. Create a python virtual environment
```
python -m venv .venv
```
2. Activate the environment
```
.venv\Scripts\activate
```
3. Install requirements
```
pip install -r requirements.txt
```


### Creating Wedges
1. Create a folder that will contain the workflow_api.json and wedge_config.json file.
2. Export an api version of your workflow from ComfyUI and save it in this folder.
3. Copy **example_wedge_config.json** from the **templates/examples/** folder and modify.
4. Make sure your ComfyUI server is running.
5. Run  **_RUN_submit_wedges.bat**
6. Click "Select Config Folder" and navigate to the folder containing the two json files. This should load the config into the text window.
7. Click "Submit Wedges". If "show_confirmation" is True in the config, look for the confirmation in the terminal and press "y" to submit. All images should be written to the ComfyUI output folder.

### Viewing Wedges
1. Run **_RUN_view_wedges.bat**
2. Click "Load Image"
3. Navigate to any image rendered with the wedge submit tool.
4. When the image is loaded, sliders will be populated using image metadata. Modify sliders and dropdown menus to explore the image dataset.





# wedge_config.json

Example wedge_config.json contents:

```json
{
    "project_name": "_DEMO_wedge",
    "filename_prefix": "wedge",
    "for_testing": false,
    "show_confirmation": true,
    "url": "127.0.0.1:8000",
    "param_overrides": [
      ["CLIP Text Encode (Prompt) - POS", "text", "A cute dog wearing sunglasses riding a skateboard down a mountainside during a storm at night with an errupting volcano in the background, pouring rain, lava, fire, apocalypse, explosions, danger, dynamic angle, red chaotic lighting, cinematic, masterpiece, view from below"]
    ],
    "param_wedges": {
      "steps": ["KSampler", [14, 20, 2], "minmax"],
      "sampler_name": ["KSampler", ["euler", "dpmpp_2m", "dpmpp_2m_sde"], "explicit"]
    }
}
```

### Parameters
- **project_name** - the folder name used to contain all the output images.
- **filename_prefix** - used to prefix all images.
- **for_testing** - set to true to submit a dummy job. 
- **show_confirmation** - enables a confirmation dialogue showing the number of images about to be submitted.
- **url** - address of the running ComfyUI server.
- **param_overrides** - An optional parameter that overrides a given paremeter of the workflow_api.json file for all wedge outputs. Can also be set directly in the workflow_api.json file and left blank in this config.
- **param_wedges** - parameters set to be wedged.

### param_wedges
This is used to set the wedge parameters. This follows this structure:
"(Parameter)": ["(Node Name)", [(Values)], "(Mode)"]

If Mode is set to "minmax", Values is a list containing [min, max, step]. The wedge tool will iterate over this Parameter from min to max based on the step value.

If Mode is set to "explicit", Values is a list of explicit values to be iterated over.
