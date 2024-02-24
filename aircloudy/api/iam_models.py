from dataclasses import dataclass
from typing import List, Literal


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
    roles: List[Role]
    middleName: None
    id: int
    email: str

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)


@dataclass
class AuthenticationSuccess:
    token: str
    refreshToken: str
    newUser: bool
    errorState: Literal["NONE"]
    access_token_expires_in: int
    refresh_token_expires_in: int

    def __init__(self, data: dict) -> None:
        self.__dict__.update(data)
