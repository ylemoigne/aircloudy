from datetime import datetime, timedelta

import jwt
import pytest
from pytest_httpserver import HTTPServer
import aircloudy.api.iam
from aircloudy.utils import awaitable


@pytest.mark.asyncio
async def test_perform_login(httpserver: HTTPServer):
    auth_token = jwt.encode({
        "sub": "foo",
        "scopes": ["auth"],
        "iss": "test-fixture",
        "aud": "test-consumer",
        "iat": datetime.now(),
        "exp": datetime.now()+timedelta(hours=1)
    }, "secret")
    refresh_token = jwt.encode({
        "sub": "foo",
        "scopes": ["refresh"],
        "iss": "test-fixture",
        "aud": "test-consumer",
        "jti": "lala",
        "iat": datetime.now(),
        "exp": datetime.now()+timedelta(hours=1)
    }, "secret")

    httpserver.expect_request(
        "/iam/auth/sign-in",
        "POST",
        json={
            "email": "foo@example.com",
            "password": "supersecret",
        },
    ).respond_with_json({
        "token": auth_token,
        "refreshToken": refresh_token,
        "newUser": True,
        "errorState": "NONE",
        "access_token_expires_in": 10,
        "refresh_token_expires_in": 20,
    })
    res = await aircloudy.api.iam.perform_login("foo@example.com", "supersecret", httpserver.host, httpserver.port)
    assert res.token.value == auth_token
    assert res.refresh_token.value == refresh_token
    assert res.new_user == True
    assert res.error_state == "NONE"
    assert res.access_token_expires_in == 10
    assert res.refresh_token_expires_in == 20

@pytest.mark.asyncio
async def test_fetch_profile(httpserver: HTTPServer):
    httpserver.expect_request(
        "/iam/user/v2/who-am-i",
        "GET",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "Host": httpserver.host,
            "User-Agent": "okhttp/4.2.2",
            "Authorization": "Bearer xxxxToken",
        },
    ).respond_with_json({
        "id": 1,
        "familyId": 2,
        "firstName": "Alice",
        "lastName": "Crypto",
        "address": {
            "zipCode": "53000",
            "city": "Laval",
            "street": "street",
            "countryCode": "FR",
            "state": "aa",
            "addressLine": "ddddd",
        },
        "phoneNumber": None,
        "pictureData": None,
        "familyName": "Plouf",
        "roles": [{"level": 1, "name": "OWNER", "id": 2}],
        "middleName": None,
        "email": "foo@example.com",
        "settings": {
            "outOfHomeAddress": None,
            "sensitiveToCold": False,
            "temperatureUnit": "degC",
            "homeOnWeekdays": True,
            "language": 'en',
            "outOfHomeRadius": 0.1,
            "homeOnWeekends": True,
            "outOfHomeRemainderEnabled": False,
            "outOfHomeLatitude": 0.2,
            "outOfHomeLongitude": 0.3,
        },
    })
    res = await aircloudy.api.iam.fetch_profile(lambda : awaitable("xxxxToken"), httpserver.host, httpserver.port)
    assert res.id == 1
    assert res.familyId == 2
    assert res.firstName == "Alice"
    assert res.lastName == "Crypto"
    assert res.phoneNumber is None
    assert res.pictureData is None
    assert res.familyName == "Plouf"
    assert res.roles[0].level == 1
    assert res.roles[0].name == "OWNER"
    assert res.roles[0].id == 2
    assert res.middleName is None
    assert res.email == "foo@example.com"
    assert res.settings.outOfHomeAddress is None
    assert res.settings.sensitiveToCold == False
    assert res.settings.temperatureUnit == "degC"
    assert res.settings.homeOnWeekdays == True
    assert res.settings.language == "en"
    assert res.settings.outOfHomeRadius == 0.1
    assert res.settings.homeOnWeekends == True
    assert res.settings.outOfHomeRemainderEnabled == False
    assert res.settings.outOfHomeLatitude == 0.2
    assert res.settings.outOfHomeLongitude == 0.3
