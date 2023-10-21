#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : product_manager.py
"""
from metagpt.actions import BossRequirement, WritePRD
from metagpt.roles import Role
from metagpt.const import WORKSPACE_ROOT
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.utils.common import CodeParser
from metagpt.logs import logger
from metagpt.schema import Message
from pathlib import Path
from metagpt.actions.action_output import ActionOutput
import shutil
import subprocess

class ProductManager(Role):
    """
    Represents a Product Manager role responsible for product development and management.

    Attributes:
        name (str): Name of the product manager.
        profile (str): Role profile, default is 'Product Manager'.
        goal (str): Goal of the product manager.
        constraints (str): Constraints or limitations for the product manager.
    """

    def __init__(
        self,
        name: str = "Alice",
        profile: str = "Product Manager",
        goal: str = "Efficiently create a successful product",
        constraints: str = "",
    ) -> None:
        """
        Initializes the ProductManager role with given attributes.

        Args:
            name (str): Name of the product manager.
            profile (str): Role profile.
            goal (str): Goal of the product manager.
            constraints (str): Constraints or limitations for the product manager.
        """
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WritePRD])
        self._watch([BossRequirement])




    ### save files
    async def _save_prd(self, docs_path, resources_path, msg):
        prd_file = docs_path / "prd.md"
        if msg.instruct_content and msg.instruct_content.dict()["Competitive Quadrant Chart"]:
            quadrant_chart = msg.instruct_content.dict()["Competitive Quadrant Chart"]
            if False:
                await mermaid_to_file(quadrant_chart, resources_path / "competitive_analysis")

        if msg.instruct_content:
            try:
                logger.info(f"Saving PRD to {prd_file}")
                #logger.info(f"MD: {json_to_markdown(msg.instruct_content.dict())}")
                prd_file.write_text(json_to_markdown(msg.instruct_content.dict()))
            except Exception as e:
                logger.error(f"Error at saving PRD: {e}")


    async def _create_project(self):
        ws_name = get_workspace_name(self)
        try:
            await subprocess.run(["flutter", "create",ws_name]) 
        except Exception as e:
            logger.error(f"Error at creating Project: {e}")



    async def _save(self,workspace, context, msg):
        docs_path = workspace / "docs"
        resources_path = workspace / "resources"
        docs_path.mkdir(parents=True, exist_ok=True)
        resources_path.mkdir(parents=True, exist_ok=True)
        await self._save_prd(docs_path, resources_path, msg)
        await self._create_project()





    async def _act(self) -> Message:

        logger.info(f"{self._setting}: ready to {self._rc.todo}")

        context = self._rc.important_memory
        response = await self._rc.todo.run(context)
        
        if isinstance(response, ActionOutput):
            msg = Message(content=response.content, instruct_content=response.instruct_content,
                        role=self.profile, cause_by=type(self._rc.todo))
        else:
            msg = Message(content=response, role=self.profile, cause_by=type(self._rc.todo))
        self._rc.memory.add(msg)

        ws = get_workspace(self)        
                
        logger.info(f"Workspace: {ws}")
        
        await self._save(ws,context,msg)

        return msg
    


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

