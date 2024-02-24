from pytest_httpserver import HTTPServer

import aircloudy.api


def test_get_interior_units(httpserver: HTTPServer):
    httpserver.expect_request(
        "/rac/ownership/groups/4444/idu-list",
        "GET",
        headers={"Authorization": "Bearer xxxxToken"},
    ).respond_with_json([
        {"userId": "1234",
         "serialNumber": "XXXX-XXXX-XXXX",
         "model": "HITACHI",
         "id": 1234,
         "vendorThingId": "JCH-666ffee",
         "name": "Salon",
         "roomTemperature": 18.0,
         "mode": "HEATING",
         "iduTemperature": 22.0,
         "humidity": 126,
         "power": "ON",
         "relativeTemperature": 2.147483648E9,
         "fanSpeed": "AUTO",
         "fanSwing": "BOTH",
         "updatedAt": 9999,
         "lastOnlineUpdatedAt": 99998,
         "racTypeId": 155,
         "iduFrostWash": False,
         "specialOperation": False,
         "criticalError": False,
         "zoneId": "Europe/Paris",
         "scheduleType": "SCHEDULE_DISABLED",
         "online": True},
        {"userId": "1235",
         "serialNumber": "XXXX-XXXX-XXXX",
         "model": "HITACHI",
         "id": 1235,
         "vendorThingId": "JCH-666ffef",
         "name": "Chambre",
         "roomTemperature": 20.0,
         "mode": "HEATING",
         "iduTemperature": 17.0,
         "humidity": 126,
         "power": "OFF",
         "relativeTemperature": 0,
         "fanSpeed": "LV1",
         "fanSwing": "OFF",
         "updatedAt": 6666,
         "lastOnlineUpdatedAt": 6667,
         "racTypeId": 155,
         "iduFrostWash": False,
         "specialOperation": False,
         "criticalError": False,
         "zoneId": "Europe/Paris",
         "scheduleType": "SCHEDULE_DISABLED",
         "online": True},
    ])
    res = aircloudy.api.get_interior_units("xxxxToken", 4444, httpserver.host, httpserver.port)
    assert res[0].id == 1234
    assert res[0].name == "Salon"
    assert res[0].mode == "HEATING"
    assert res[0].requested_temperature == 22.0
    assert res[0].humidity == 126
    assert res[0].power == "ON"
    assert res[0].fan_speed == "AUTO"
    assert res[0].fan_swing == "BOTH"
    assert res[0].updated_at == 9999
    assert res[0].online_updated_at == 99998
    assert res[0].room_temperature == 18
    assert res[0].online == True
