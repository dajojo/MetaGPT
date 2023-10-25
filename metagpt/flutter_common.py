from metagpt.actions.write_prd import WritePRD
from metagpt.logs import logger
from metagpt.schema import Message
from pathlib import Path
import shutil
from metagpt.const import WORKSPACE_ROOT
from metagpt.utils.common import CodeParser

### get workspace
def recreate_workspace( workspace: Path):
    try:
        shutil.rmtree(workspace)
    except FileNotFoundError:
        pass  # Folder does not exist, but we don't care
    workspace.mkdir(parents=True, exist_ok=True)

def get_workspace_name(agent) -> str:
    return agent._rc.env.project_name

def get_workspace(agent) -> Path:
    workspace = get_workspace_name(agent)
    ws = WORKSPACE_ROOT / workspace
    return ws

def read_file(filename):
    with open(filename, 'r') as file:
        content = file.read()
    return content

def to_camel_case(snake_str):
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))

def read_markdown_file(filename):
    with open(filename, 'r') as file:
        content = file.read()
    return content

def get_context(agent) -> str:
    ws = get_workspace(agent)

    core_spec = read_file(ws/ "packages"/"float_core"/"docs"/ "system_design.md")
    apis_spec = read_file(ws/ "packages"/"float_apis"/"docs"/ "system_design.md")
    sys_spec = read_file(ws/ "docs"/ "system_design.md")
    frontend_sys_spec = read_file(ws / "docs" / "frontend_system_design.md")

    context = f"The following section enclosed by '******' defines important existing code. It does NOT define what the output should look like. \n ****** \n"
    context = context + f"## Float Core Description:\n{core_spec}\n Use these provided functions as much as possible. \n## Float Apis Description: \n {apis_spec} \n Use these provided functions as much as possible. BUT DO NOT MODIFY THEM \n ****** \n"
    context = context + f"## Architecture \n {sys_spec} \n ## Frontend Architecture \n {frontend_sys_spec} \n"
    context = context + f"## Project name: \n {get_workspace_name(agent)} \n Use that for import statements! \n"

    return context