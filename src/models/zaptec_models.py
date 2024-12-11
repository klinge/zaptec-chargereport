from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID

"""Models for the response from the /api/chargehistory endpoint"""


class ChargerFirmware(BaseModel):
    Major: int
    Minor: int
    Build: int
    Revision: int
    MajorRevision: int
    MinorRevision: int


class ChargingSession(BaseModel):
    UserUserName: str
    Id: str
    DeviceId: str
    StartDateTime: datetime
    EndDateTime: datetime
    Energy: float
    CommitMetadata: int
    CommitEndDateTime: datetime
    UserFullName: str
    ChargerId: str
    DeviceName: str
    UserEmail: str
    UserId: str
    TokenName: Optional[str] = None
    ExternallyEnded: bool
    ChargerFirmwareVersion: ChargerFirmware


class ChargingSessionResponse(BaseModel):
    Pages: int
    Data: List[ChargingSession]


"""Models for the response from the /api/installation endpoint"""


class InstallationUser(BaseModel):
    UserId: UUID
    UserFullName: str
    UserEmail: str
    UserTokens: List[str]


class EnergySensor(BaseModel):
    UniqueId: str
    Type: int
    Provider: str
    Vendor: str
    Model: str
    SerialNo: str
    Id: UUID


class EnergySensorReading(BaseModel):
    PartitionKey: str
    RowKey: str
    Timestamp: datetime
    ETag: str
    UniqueId: str
    ObservedAt: datetime
    CurrentPhase1: float
    CurrentPhase2: float
    CurrentPhase3: float
    ChargeCurrentPhase1: float
    ChargeCurrentPhase2: float
    ChargeCurrentPhase3: float
    AvailableCurrentPhase1: float
    AvailableCurrentPhase2: float
    AvailableCurrentPhase3: float
    AvailableCurrentChanged: bool
    CurrentNeutral: float
    VoltagePhase1: float
    VoltagePhase2: float
    VoltagePhase3: float
    StatusCode: str
    StatusMessage: str
    Ripple: float


class SupportGroup(BaseModel):
    Id: UUID
    Name: str
    CreatedOn: datetime
    UpdatedOn: datetime
    LookupKey: str
    CurrentUserRoles: int
    Protected: bool
    ServiceLevelSupport: bool
    ServiceLevelAllowOcppNative: bool
    ServiceLevelTechnicalRead: bool
    LogoId: Optional[UUID]
    LogoContentType: Optional[str]
    LogoBase64: Optional[str]
    SupportUrl: Optional[str]
    SupportEmail: Optional[str]
    SupportPhone: Optional[str]
    SupportDetails: Optional[str]
    PropertyMessagingAllowed: bool
    PropertyMessagingEnabled: bool
    TransferrableExperimentalFeatures: int


class Installation(BaseModel):
    Id: UUID
    Name: str
    Address: str
    ZipCode: str
    City: str
    CountryId: UUID
    VatNumber: Optional[str] = None
    ContactEmail: Optional[str] = None
    InstallationType: int
    MaxCurrent: float
    AvailableCurrent: float
    AvailableCurrentPhase1: float
    AvailableCurrentPhase2: float
    AvailableCurrentPhase3: float
    AvailableCurrentMode: int
    AvailableCurrentScheduleWeekendActive: bool
    ThreeToOnePhaseSwitchCurrent: Optional[float] = None
    InstallationCategoryId: UUID
    InstallationCategory: str
    UseLoadBalancing: bool
    IsRequiredAuthentication: bool
    Latitude: float
    Longitude: float
    Notes: Optional[str] = None
    Active: bool
    NetworkType: int
    AvailableInternetAccessPLC: bool
    AvailableInternetAccessWiFi: bool
    CreatedOnDate: datetime
    UpdatedOn: datetime
    CurrentUserRoles: int
    AuthenticationType: int
    WebhooksAuthPayload: Optional[str] = None
    WebhooksAuthUrl: Optional[str] = None
    WebhooksSessionStartUrl: Optional[str] = None
    WebhooksSessionEndUrl: Optional[str] = None
    MessagingEnabled: bool
    RoutingId: str
    OcppCloudUrl: Optional[str] = None
    OcppCloudUrlVersion: int
    OcppInitialChargePointPassword: Optional[str] = None
    OcppCentralSystemUrl: Optional[str] = None
    TimeZoneName: Optional[str] = None
    TimeZoneIanaName: Optional[str] = None
    UpdateStatusCode: Optional[int] = None
    Notifications: Optional[int] = None
    IsSubscriptionsAvailableForCurrentUser: bool
    InstallationUsers: Optional[List[InstallationUser]] = None
    AvailableFeatures: int
    EnabledFeatures: int
    ActiveChargerCount: Optional[int] = None
    EnergySensor: Optional[EnergySensor] = None
    StorageEnergySensorLastReading: Optional[EnergySensorReading] = None
    SupportGroup: Optional[SupportGroup] = None


"""Models for the response from the /api/charger endpoint"""


class Charger(BaseModel):
    OperatingMode: int
    IsOnline: bool
    Id: UUID
    MID: str
    DeviceId: str
    SerialNo: str
    Name: str
    CreatedOnDate: datetime
    CircuitId: UUID
    Active: bool
    CurrentUserRoles: int
    Pin: str
    DeviceType: int
    InstallationName: str
    InstallationId: UUID
    AuthenticationType: int
    IsAuthorizationRequired: bool


class ChargersResponse(BaseModel):
    Pages: int
    Data: List[Charger]


"""Models for the response from the /api/installation/report endpoint"""


class UserDetails(BaseModel):
    Id: str
    Email: str
    FullName: str


class TotalUserChargerReport(BaseModel):
    GroupAsString: str
    UserDetails: UserDetails
    TotalChargeSessionCount: int
    TotalChargeSessionEnergy: float
    TotalChargeSessionDuration: float


class InstallationReport(BaseModel):
    InstallationName: str
    InstallationAddress: str
    InstallationZipCode: str
    InstallationCity: str
    InstallationTimeZone: str
    GroupedBy: str
    Fromdate: str
    Enddate: str
    totalUserChargerReportModel: List[TotalUserChargerReport]
