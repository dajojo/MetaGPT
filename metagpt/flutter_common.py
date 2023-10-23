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

def to_camel_case(snake_str):
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))
