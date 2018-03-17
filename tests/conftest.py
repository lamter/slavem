# -*- coding: utf-8 -*-

import pytest
import json
import slavem


@pytest.fixture(scope='session', autouse=True)
def monitor_kwarg():
    settingPath = '../tmp/slavem_setting.json'
    with open(settingPath, 'r') as f:
        kwarg = json.load(f)
    return kwarg


@pytest.fixture
def monitor(monitor_kwarg):
    return slavem.Monitor(**monitor_kwarg)
