#!/usr/bin/env python
# -*- coding: utf-8 -*-


from metagpt.actions.flutter_design_api import WriteFlutterDesign
from metagpt.actions.flutter_project_management import WriteFlutterTasks
from metagpt.roles import Role


class FlutterProjectManager(Role):
    """
    Represents a Project Manager role responsible for overseeing project execution and team efficiency.

    Attributes:
        name (str): Name of the project manager.
        profile (str): Role profile, default is 'Project Manager'.
        goal (str): Goal of the project manager.
        constraints (str): Constraints or limitations for the project manager.
    """

    def __init__(
        self,
        name: str = "Paul",
        profile: str = "Flutter Project Manager",
        goal: str = "Improve team efficiency and deliver with quality and quantity",
        constraints: str = "",
    ) -> None:
        """
        Initializes the ProjectManager role with given attributes.

        Args:
            name (str): Name of the project manager.
            profile (str): Role profile.
            goal (str): Goal of the project manager.
            constraints (str): Constraints or limitations for the project manager.
        """
        super().__init__(name, profile, goal, constraints)
        self._init_actions([WriteFlutterTasks])
        self._watch([WriteFlutterDesign])
