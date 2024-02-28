import asyncio
import logging

import pytest
from pytest_httpserver import HTTPServer

import aircloudy.api
import aircloudy.api.rac
from aircloudy.utils import awaitable


@pytest.mark.asyncio
async def test_command_state_monitor(httpserver: HTTPServer):
    httpserver.expect_ordered_request(
        "/rac/status/command",
        "POST",
        json=[{
            "commandId": "a1",
            "thingId": "fooBar"
        }],
    ).respond_with_json([
        {"commandId": "a1",
         "status": "SENDING"},
    ])
    httpserver.expect_ordered_request(
        "/rac/status/command",
        "POST",
        json=[{
            "commandId": "a1",
            "thingId": "fooBar"},
            {"commandId": "a2",
             "thingId": "youp"},
        ],
    ).respond_with_json([
        {"commandId": "a1",
         "status": "SENDING"},
        {"commandId": "a2",
         "status": "SENDING"},
    ])
    httpserver.expect_ordered_request(
        "/rac/status/command",
        "POST",
        json=[{
            "commandId": "a1",
            "thingId": "fooBar"},
            {"commandId": "a2",
             "thingId": "youp"},
        ],
    ).respond_with_json([
        {"commandId": "a1",
         "status": "SENDING"},
        {"commandId": "a2",
         "status": "DONE"},
    ])
    httpserver.expect_ordered_request(
        "/rac/status/command",
        "POST",
        json=[{
            "commandId": "a1",
            "thingId": "fooBar"},
        ],
    ).respond_with_json([
        {"commandId": "a1",
         "status": "DONE"},
    ])

    command_manager = aircloudy.api.CommandStateMonitor(lambda: awaitable("tokenXXX"), host=httpserver.host, port=httpserver.port)
    a1 = await command_manager.watch_command(aircloudy.api.CommandResponse({"commandId": "a1", "thingId": "fooBar"}))
    await asyncio.sleep(2)
    a2 = await command_manager.watch_command(aircloudy.api.CommandResponse({"commandId": "a2", "thingId": "youp"}))
    await a2.wait_done()
    await a1.wait_done()
