from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship, object_session
from sqlalchemy import func
from datetime import datetime

Base = declarative_base()

# Normalized RBAC Mapping
role_permissions = Table('role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    permissions = relationship('Permission', secondary=role_permissions, lazy='subquery')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=True)
    
    role = relationship('Role')

    def has_permission(self, perm_name):
        return any(p.name == perm_name for p in self.role.permissions)

class Member(Base):
    __tablename__ = 'members'
    id = Column(Integer, primary_key=True)
    member_no = Column(String(20), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    national_id = Column(String(20), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    date_joined = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    transactions = relationship('FinancialTransaction', backref='member', cascade="all, delete-orphan")
    loans = relationship('Loan', backref='member', cascade="all, delete-orphan")

    @property
    def total_savings(self):
        session = object_session(self)
        deposits = session.query(func.coalesce(func.sum(FinancialTransaction.amount), 0)).filter_by(member_id=self.id, transaction_type='Savings').scalar()
        withdraws = session.query(func.coalesce(func.sum(FinancialTransaction.amount), 0)).filter_by(member_id=self.id, transaction_type='Withdrawal').scalar()
        return float(deposits - withdraws)

    @property
    def active_loans_total(self):
        session = object_session(self)
        total = session.query(func.coalesce(func.sum(Loan.principal), 0)).filter_by(member_id=self.id, status='Approved').scalar()
        return float(total)

class FinancialTransaction(Base):
    __tablename__ = 'financial_transactions'
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    transaction_type = Column(String(50), nullable=False) # Savings, Share Capital, Withdrawal
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    reference = Column(String(50), nullable=True)

class Loan(Base):
    __tablename__ = 'loans'
    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.id'), nullable=False)
    principal = Column(Numeric(12, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), default=12.0)
    duration_months = Column(Integer, nullable=False)
    status = Column(String(20), default='Pending')
    application_date = Column(DateTime, default=datetime.utcnow)
    
    repayments = relationship('LoanRepayment', backref='loan', cascade="all, delete-orphan")

    @property
    def monthly_installment(self):
        r = (float(self.interest_rate) / 100) / 12
        n = self.duration_months
        p = float(self.principal)
        return p / n if r == 0 else (p * r * (1 + r)**n) / ((1 + r)**n - 1)

    @property
    def total_payable(self):
        return self.monthly_installment * self.duration_months
        
    @property
    def total_repaid(self):
        # Replaces db.session with object_session(self)
        session = object_session(self)
        total = session.query(func.coalesce(func.sum(LoanRepayment.amount), 0)).filter_by(loan_id=self.id).scalar()
        return float(total)

    @property
    def remaining_balance(self):
        return self.total_payable - self.total_repaid

class LoanRepayment(Base):
    __tablename__ = 'loan_repayments'
    id = Column(Integer, primary_key=True)
    loan_id = Column(Integer, ForeignKey('loans.id'), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    reference = Column(String(50), nullable=True)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(255), nullable=False)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', backref='logs')