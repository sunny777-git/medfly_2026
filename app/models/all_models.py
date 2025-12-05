from datetime import date

from sqlalchemy import Column, ForeignKey, String, Integer, Boolean, Date, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from app.models.database import Base
from datetime import datetime

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(50), nullable=False)
    mobile = Column(String(15), nullable=False)
    location = Column(String(100), default='--')
    has_branch = Column(Boolean, default=False)
    branch_name = Column(String(100))
    branch_type = Column(String(100), default='Main')
    owner_name = Column(String(100), nullable=False)
    logo = Column(String(50))
    account_type = Column(String(20), default="Demo")
    account_start_date = Column(Date, default=date.today)
    account_expiry_date = Column(String(20))
    installation_date = Column(String(20))
    admin_username = Column(String(20))
    owner_username = Column(String(20), default="Medfly@admin")
    owner_password = Column(String(20), default="Medyadmin")
    quoted = Column(String(20))
    final_cost = Column(String(20))
    payment_mode = Column(String(20))
    due = Column(String(20))
    paid_by = Column(String(20))
    lead_by = Column(String(20))
    contact_person = Column(String(20))
    payment_process = Column(String(20))
    total_devices = Column(Integer, default=0)
    status = Column(String(10), default="Active")
    prefix = Column(String(4), default="MEDF")
    total_patients = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey("hospitals.id"), nullable=True)  # new


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    device_id = Column(String(20), nullable=False)
    is_default = Column(Boolean, default=False)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    name = Column(String(120))


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    name = Column(String(20))
    department_id = Column(Integer)
    department_name = Column(String(100))
    permissions = Column(String(20))


class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    department_id = Column(Integer)
    department_name = Column(String(120))
    name = Column(String(120))
    status = Column(String(20), default="Active")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    department_id = Column(Integer)
    department_name = Column(String(120))
    procedure_id = Column(Integer)
    procedure_name = Column(String(120))
    name = Column(String(120))
    status = Column(String(20), default="Created")
    image = Column(Integer, default=3)


class Parameter(Base):
    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    procedure_id = Column(Integer)
    procedure_name = Column(String(120))
    template_id = Column(Integer)
    template_name = Column(String(120))
    is_non_parameter = Column(Boolean, default=False)
    name = Column(String(50))
    value = Column(String(50))


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    mf_id = Column(String(100))
    doctor_id = Column(Integer)
    doctor_name = Column(String(100))
    name = Column(String(100))
    department_id = Column(Integer)
    department_name = Column(String(120))
    procedure_id = Column(Integer)
    procedure_name = Column(String(120))
    procedure_datetime = Column(String(100))
    template_id = Column(Integer)
    template_name = Column(String(120))
    report_images = Column(String(2000))
    parameters = Column(String(5000))
    extra_doctors = Column(String(200), default="")


class PatientInfo(Base):
    __tablename__ = "patient_info"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    mf_id = Column(String(100))
    name = Column(String(100))
    mobile = Column(String(15))
    age = Column(Integer)
    gender = Column(String(10))
    alt_id = Column(String(100), default="--")
    registered_on = Column(String(120))
    total_visits = Column(Integer, default=1)
    entry_date = Column(Date, default=date.today)


class PatientRegistration(Base):
    __tablename__ = "patient_registration"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    mf_id = Column(String(100))
    alt_id = Column(String(100), default="--")
    procedure_id = Column(Integer)
    procedure_name = Column(String(100))
    doctor_id = Column(String(100))
    doctor_name = Column(String(100))
    anesthesian_id = Column(String(10), default="--")
    anesthesian_name = Column(String(100), default="--")
    referrer_id = Column(String(100))
    referrer_name = Column(String(100))
    nurse_id = Column(String(10), default="--")
    nurse_name = Column(String(100), default="--")
    status = Column(String(100), default="--")
    procedure_date = Column(String(120))
    activity_status = Column(String(120), default="1")
    activity_date = Column(String(120))
    activity_log = Column(Text, default='')
    entry_date = Column(Date, default=date.today)
    visit_id = Column(Integer, default=1)


class Snapshots(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    mf_id = Column(String(100))
    visit_id = Column(Integer)
    procedure_id = Column(Integer)
    procedure_datetime = Column(String(100))
    file_src = Column(String(100))
    file_thumbnail = Column(String(100))
    file_type = Column(String(10), default="snap")
    file_status = Column(String(10), default="main")
    annotation_data = Column(Text, default='')


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    user_id = Column(String(100))
    name = Column(String(100))
    path = Column(String(100))
    icon = Column(String(100))
    status = Column(String(100), default="Active")


class RoleBasedMenu(Base):
    __tablename__ = "role_based_menu"

    id = Column(Integer, primary_key=True)
    hospital_id = Column(Integer)
    menu_list = Column(String(100))
    user_id = Column(Integer)
    role_permissions = Column(Integer)


class IceServer(Base):
    __tablename__ = "ice_servers"

    id = Column(Integer, primary_key=True, index=True)
    urls = Column(String, nullable=False)  # comma-separated string of STUN/TURN URLs
    username = Column(String, nullable=True)
    credential = Column(String, nullable=True)



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    hspId = Column(String(50), nullable=True)
    fullname = Column(String(100), nullable=False)
    mobile = Column(String(50), unique=True, nullable=False)
    # ✅ NEW: login_name for username-like login (e.g., APLH001)
    login_name = Column(String(50), unique=True, nullable=True, index=True)
    roleId = Column(Integer, nullable=True)
    role_name = Column(String(50), nullable=True)
    department = Column(Integer, nullable=True)
    staff = Column(Boolean, default=True)
    admin = Column(Boolean, default=False)
    degree = Column(String(70), nullable=True)
    active = Column(Boolean, default=False)
    is_hadmin = Column(Boolean, default=False)
    is_sadmin = Column(Boolean, default=False)
    show_pwd = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    date_joined = Column(DateTime, default=datetime.utcnow)
    last_logout = Column(DateTime, nullable=True)
    hashed_password = Column(String(200), nullable=True)

   
