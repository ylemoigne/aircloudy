import asyncio

import pytest
from pytest_httpserver import HTTPServer

import aircloudy.api
import aircloudy.api.rac
from aircloudy.utils import awaitable


@pytest.mark.asyncio
async def test_command_manager(httpserver: HTTPServer):
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

    command_manager = aircloudy.api.CommandManager(lambda: awaitable("tokenXXX"), host=httpserver.host, port=httpserver.port)
    command_manager.add_command_watch(aircloudy.api.CommandResponse({"commandId": "a1", "thingId": "fooBar"}))
    await asyncio.sleep(2)
    res = await command_manager.wait_ack(aircloudy.api.CommandResponse({"commandId": "a2", "thingId": "youp"}))
    assert res == "DONE"
