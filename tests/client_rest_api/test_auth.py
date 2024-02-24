from pytest_httpserver import HTTPServer
import aircloudy.api.iam

def test_perform_login(httpserver: HTTPServer):
    httpserver.expect_request(
        "/iam/auth/sign-in",
        "POST",
        json={
            "email": "foo@example.com",
            "password": "supersecret",
        },
    ).respond_with_json({
        "token": "xxxxToken",
        "refreshToken": "xxxxRefresh",
        "newUser": True,
        "errorState": "NONE",
        "access_token_expires_in": 10,
        "refresh_token_expires_in": 20,
    })
    res = aircloudy.api.iam.perform_login("foo@example.com", "supersecret", httpserver.host, httpserver.port)
    assert res.token == "xxxxToken"
    assert res.refreshToken == "xxxxRefresh"
    assert res.newUser == True
    assert res.errorState == "NONE"
    assert res.access_token_expires_in == 10
    assert res.refresh_token_expires_in == 20


def test_fetch_profile(httpserver: HTTPServer):
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
    res = aircloudy.api.iam.fetch_profile("xxxxToken", httpserver.host, httpserver.port)
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
