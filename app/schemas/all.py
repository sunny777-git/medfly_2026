from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date as dt_date, datetime
from typing import Generic, List, TypeVar
from pydantic.generics import GenericModel

T = TypeVar("T")


class HospitalBase(BaseModel):
    name: str
    email: str
    mobile: str
    location: Optional[str] = '--'
    has_branch: Optional[bool] = False
    branch_name: Optional[str] = None
    branch_type: Optional[str] = 'Main'
    owner_name: str
    logo: Optional[str] = None
    account_type: Optional[str] = 'Demo'
    account_start_date: Optional[dt_date] = dt_date.today()
    account_expiry_date: Optional[str] = None
    installation_date: Optional[str] = None
    login_name: Optional[str] = None
    login_password: Optional[str] = None
    quoted: Optional[str] = None
    final_cost: Optional[str] = None
    payment_mode: Optional[str] = None
    due: Optional[str] = None
    paid_by: Optional[str] = None
    lead_by: Optional[str] = None
    contact_person: Optional[str] = None
    payment_process: Optional[str] = None
    total_devices: Optional[int] = 0
    status: Optional[str] = 'Active'
    prefix: Optional[str] = 'MEDF'
    total_patients: Optional[int] = 0
    parent_id: Optional[int] = None


class HospitalCreate(HospitalBase):
    pass


class HospitalResponse(HospitalBase):
    id: int
    
    class Config:
        from_attributes = True


class Hospital(HospitalBase):
    id: int

    class Config:
        from_attributes = True


class DeviceBase(BaseModel):
    hospital_id: int
    device_id: str
    is_default: Optional[bool] = False


class DeviceCreate(DeviceBase):
    pass


class Device(DeviceBase):
    id: int

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    devices: List[Device]


class DepartmentBase(BaseModel):
    hospital_id: int
    name: str


class DepartmentCreate(DepartmentBase):
    pass


class Department(DepartmentBase):
    id: int

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    hospital_id: int
    name: str
    department_id: int
    department_name: str
    permissions: str


class RoleCreate(RoleBase):
    pass


class Role(RoleBase):
    id: int

    class Config:
        from_attributes = True


class ProcedureBase(BaseModel):
    hospital_id: int
    department_id: int
    department_name: str
    name: str
    status: Optional[str] = 'Active'


class ProcedureCreate(ProcedureBase):
    pass


class Procedure(ProcedureBase):
    id: int

    class Config:
        from_attributes = True


class TemplateBase(BaseModel):
    hospital_id: int
    department_id: int
    department_name: str
    procedure_id: int
    procedure_name: str
    name: str
    status: Optional[str] = 'Created'
    image: Optional[int] = 3


class TemplateCreate(TemplateBase):
    pass


class Template(TemplateBase):
    id: int

    class Config:
        from_attributes = True


class ParameterBase(BaseModel):
    hospital_id: int
    procedure_id: int
    procedure_name: str
    template_id: int
    template_name: str
    is_non_parameter: Optional[bool] = False
    name: str
    value: str


class ParameterCreate(ParameterBase):
    pass


class Parameter(ParameterBase):
    id: int

    class Config:
        from_attributes = True


class ReportBase(BaseModel):
    hospital_id: int
    uid: str
    doctor_id: int
    doctor_name: str
    name: str
    department_id: int
    department_name: str
    procedure_id: int
    procedure_name: str
    procedure_datetime: str
    template_id: int
    template_name: str
    report_images: str
    parameters: str
    extra_doctors: Optional[str] = ""


class ReportCreate(ReportBase):
    pass


class Report(ReportBase):
    id: int

    class Config:
        from_attributes = True


class PatientInfoBase(BaseModel):
    hospital_id: int
    uid: str
    name: str
    mobile: str
    age: int
    gender: str
    alt_id: Optional[str] = "--"
    registered_on: str
    total_visits: Optional[int] = 1
    entry_date: Optional[dt_date] = dt_date.today()


class PatientInfoCreate(PatientInfoBase):
    pass


class PatientInfo(PatientInfoBase):
    id: int

    class Config:
        from_attributes = True


# -----------------------------------------------------------
# FIXED PatientRegistration Section
# -----------------------------------------------------------

class PatientRegistrationBase(BaseModel):
    hospital_id: int
    uid: str
    alt_id: Optional[str] = "--"
    procedure_id: int
    procedure_name: str
    doctor_id: str
    doctor_name: str
    anesthesian_id: Optional[str] = "--"
    anesthesian_name: Optional[str] = "--"
    referrer_id: str
    referrer_name: str
    nurse_id: Optional[str] = "--"
    nurse_name: Optional[str] = "--"
    status: Optional[str] = "--"

    # API field "date" maps DB "procedure_date"
    date: Optional[str] = Field(None, alias="procedure_date")

    activity_status: Optional[str] = "1"
    activity_date: Optional[str] = None
    activity_log: Optional[str] = ""
    entry_date: Optional[dt_date] = dt_date.today()
    visit_id: Optional[int] = 1

    class Config:
        from_attributes = True
        validate_by_name = True


class PatientRegistrationCreate(BaseModel):
    uid: str
    alt_id: Optional[str] = "--"
    procedure_id: int
    procedure_name: str
    doctor_id: str
    doctor_name: str
    anesthesian_id: Optional[str] = "--"
    anesthesian_name: Optional[str] = "--"
    referrer_id: str
    referrer_name: str
    nurse_id: Optional[str] = "--"
    nurse_name: Optional[str] = "--"
    status: Optional[str] = "--"
    date: str   # input field (will be mapped to procedure_date)


class PatientRegistration(PatientRegistrationBase):
    id: int

    class Config:
        from_attributes = True
        validate_by_name = True


# -----------------------------------------------------------

class PaginatedResponse(GenericModel, Generic[T]):
    total: int
    limit: int
    offset: int
    items: List[T]


class SnapshotsBase(BaseModel):
    hospital_id: int
    uid: str
    visit_id: int
    procedure_id: int
    procedure_datetime: str
    file_src: Optional[str] = None
    file_thumbnail: Optional[str] = None
    file_type: Optional[str] = "snap"
    file_status: Optional[str] = "main"
    annotation_data: Optional[str] = ""


class SnapshotsCreate(SnapshotsBase):
    Img: str
    filename: Optional[str] = None


class Snapshots(SnapshotsBase):
    id: int

    class Config:
        from_attributes = True


class MenuItemBase(BaseModel):
    hospital_id: int
    user_id: str
    name: str
    path: str
    icon: str
    status: Optional[str] = "Active"


class MenuItemCreate(MenuItemBase):
    pass


class MenuItem(MenuItemBase):
    id: int

    class Config:
        from_attributes = True


class RoleBasedMenuBase(BaseModel):
    hospital_id: int
    menu_list: str
    user_id: int
    role_permissions: int


class RoleBasedMenuCreate(RoleBasedMenuBase):
    pass


class RoleBasedMenu(RoleBasedMenuBase):
    id: int

    class Config:
        from_attributes = True


class IceServerBase(BaseModel):
    urls: str
    username: Optional[str] = None
    credential: Optional[str] = None


class IceServerCreate(IceServerBase):
    pass


class IceServer(IceServerBase):
    id: int

    class Config:
        from_attributes = True


class IceServerPublic(BaseModel):
    id: int
    urls: str
    username: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------
# USERS
# ---------------------------------------------------

class UserBase(BaseModel):
    hspId: Optional[str]
    fullname: str
    mobile: str
    login_name: Optional[str] = None
    roleId: Optional[int]
    role_name: Optional[str]
    department: Optional[int]
    staff: Optional[bool] = True
    admin: Optional[bool] = False
    degree: Optional[str]
    active: Optional[bool] = False
    is_hadmin: Optional[bool] = False
    is_sadmin: Optional[bool] = False
    show_pwd: Optional[str]
    is_active: Optional[bool] = True
    last_logout: Optional[datetime]


class UserCreateAdmin(UserBase):
    pass


class UserRegister(BaseModel):
    fullname: str
    mobile: str
    login_name: str
    password: str


class UserLogin(BaseModel):
    login_name: str
    password: str


class UserResponse(UserBase):
    id: int
    date_joined: datetime

    class Config:
        from_attributes = True


class UserRead(BaseModel):
    id: int
    fullname: str
    mobile: str

    class Config:
        from_attributes = True
