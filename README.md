# ComfyUI Wedge Tool

A toolset used to render and view wedges from ComfyUI. This can be used with any workflow as long as there is a single output node.

### This requires a folder containing two files:
- **workflow_api.json** - an api export of the ComfyUI workflow you intend to wedge.
- **wedge_config.json** - A copy of the wedge_config file. This drives the parameters being wedged. This can be copied from the **/templates/examples/** folder and renamed.

You can use the **work/** folder for convenience.

## Quick Start (Windows)

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