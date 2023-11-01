#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : __init__.py
"""

from metagpt.roles.role import Role
from metagpt.roles.architect import Architect
from metagpt.roles.flutter_architect import FlutterArchitect
from metagpt.roles.flutter_frontend_architect import FlutterFrontendArchitect
from metagpt.roles.project_manager import ProjectManager
from metagpt.roles.flutter_project_manager import FlutterProjectManager
from metagpt.roles.flutter_documentator import FlutterDocumentator
from metagpt.roles.product_manager import ProductManager
from metagpt.roles.engineer import Engineer
from metagpt.roles.flutter_engineer import FlutterEngineer
from metagpt.roles.qa_engineer import QaEngineer
from metagpt.roles.flutter_qa_engineer import FlutterQaEngineer
from metagpt.roles.seacher import Searcher
from metagpt.roles.sales import Sales
from metagpt.roles.customer_service import CustomerService


__all__ = [
    "Role",
    "Architect",
    "FlutterArchitect",
    "FlutterFrontendArchitect",
    "ProjectManager",
    "FlutterProjectManager",
    "ProductManager",
    "Engineer",
    "FlutterEngineer",
    "QaEngineer",
    "FlutterQaEngineer",
    "FlutterDocumentator",
    "Searcher",
    "Sales",
    "CustomerService",
]
