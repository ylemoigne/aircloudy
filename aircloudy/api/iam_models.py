from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Literal

import jwt


@dataclass
class UserProfile:
    @dataclass
    class Settings:
        outOfHomeAddress: None
        sensitiveToCold: bool
        temperatureUnit: Literal["degC"]
        outOfHomeLongitude: float
        homeOnWeekdays: bool
        language: Literal["en"]
        outOfHomeRadius: float
        homeOnWeekends: bool
        outOfHomeRemainderEnabled: bool
        outOfHomeLatitude: float

        def __init__(self, data: dict) -> None:
            self.__dict__.update(data)

    @dataclass
    class Address:
        zipCode: str
        city: str
        street: str
        countryCode: str
        state: str
        addressLine: str

        def __init__(self, data: dict) -> None:
            self.__dict__.update(data)

    @dataclass
    class Role:
        level: int
        name: Literal["OWNER"]
        id: int

        def __init__(self, data: dict) -> None:
            self.__dict__.update(data)

    familyId: int
    firstName: str
    lastName: str
    settings: Settings
    address: Address
    phoneNumber: None
    pictureData: None
    familyName: str
    roles: list[Role]
    middleName: None
    id: int
    email: str

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


@dataclass
class JWTToken:
    value: str
    sub: str
    scopes: list[str]
    iss: str
    aud: str
    jti: str | None
    iat: datetime.datetime
    exp: datetime.datetime

    def __init__(self, value: str, data: dict) -> None:
        self.value = value
        self.sub = data["sub"]
        self.scopes = data["scopes"]
        self.iss = data["iss"]
        self.aud = data["aud"]
        self.jti = data.get("jti")
        self.iat = datetime.datetime.fromtimestamp(data["iat"], datetime.UTC)
        self.exp = datetime.datetime.fromtimestamp(data["exp"], datetime.UTC)


@dataclass
class AuthenticationSuccess:
    token: JWTToken
    refresh_token: JWTToken
    new_user: bool
    error_state: Literal["NONE"]
    access_token_expires_in: int
    refresh_token_expires_in: int

    def __init__(self, data: dict) -> None:
        self.token = JWTToken(data["token"], jwt.decode(data["token"], options={"verify_signature": False}))
        self.refresh_token = JWTToken(
            data["refreshToken"], jwt.decode(data["refreshToken"], options={"verify_signature": False})
        )
        self.new_user = data["newUser"]
        self.error_state = data["errorState"]
        self.access_token_expires_in = data["access_token_expires_in"]
        self.refresh_token_expires_in = data["refresh_token_expires_in"]


@dataclass
class TokenRefreshSuccess:
    token: JWTToken
    refresh_token: JWTToken
    error_state: Literal["NONE"]
    access_token_expires_in: int

    def __init__(self, data: dict) -> None:
        self.token = JWTToken(data["token"], jwt.decode(data["token"], options={"verify_signature": False}))
        self.refresh_token = JWTToken(
            data["refreshToken"], jwt.decode(data["refreshToken"], options={"verify_signature": False})
        )
        self.error_state = data["errorState"]
        self.access_token_expires_in = data["access_token_expires_in"]
