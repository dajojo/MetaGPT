from metagpt.actions.write_prd import WritePRD
from metagpt.logs import logger
from metagpt.schema import Message
from pathlib import Path
import shutil
from metagpt.const import WORKSPACE_ROOT
from metagpt.utils.common import CodeParser

### get workspace
def parse_workspace(prd_msg: Message) -> str:
    if prd_msg.instruct_content:
        return prd_msg.instruct_content.dict().get("Project name").strip().strip("'").strip('"')
    return CodeParser.parse_str(block="Project name", text=prd_msg.content)


def recreate_workspace( workspace: Path):
    try:
        shutil.rmtree(workspace)
    except FileNotFoundError:
        pass  # Folder does not exist, but we don't care
    workspace.mkdir(parents=True, exist_ok=True)


def get_workspace_name(agent) -> str:
    msg = agent._rc.memory.get_by_action(WritePRD)[-1]
    if not msg:
        return WORKSPACE_ROOT / "src"
    workspace = parse_workspace(msg)
    return workspace

def get_workspace(agent) -> Path:
    workspace = get_workspace_name(agent)

    ws = WORKSPACE_ROOT / workspace

    return ws