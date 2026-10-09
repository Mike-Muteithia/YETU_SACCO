import bcrypt
from faker import Faker
from database import get_session, engine
from models import Base, User, Role, Permission, Member

def seed_database():
    print("Resetting database...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    
    session = get_session()
    
    # 1. Recreate Permissions
    perms = {
        'PROFILE_READ': Permission(name='PROFILE_READ'),
        'TX_CREATE': Permission(name='TX_CREATE'),
        'SYSTEM_CONFIG': Permission(name='SYSTEM_CONFIG')
    }
    session.add_all(perms.values())
    
    # 2. Recreate Roles
    roles = {
        'Teller': Role(name='Teller', permissions=[perms['PROFILE_READ'], perms['TX_CREATE']]),
        'SystemAdmin': Role(name='SystemAdmin', permissions=[perms['SYSTEM_CONFIG'], perms['PROFILE_READ']])
    }
    session.add_all(roles.values())
    session.commit() # Commit to generate IDs
    
    # 3. Seed Staff Users with bcrypt
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(b'pass123', salt).decode('utf-8')
    
    session.add(User(username='teller_01', password_hash=hashed_pw, role_id=roles['Teller'].id))
    session.add(User(username='admin_01', password_hash=hashed_pw, role_id=roles['SystemAdmin'].id))
    
    # 4. Generate Dummy Members
    fake = Faker()
    print("Generating dummy members...")
    for i in range(1, 11):
        m = Member(
            member_no=f'M{i:03d}',
            full_name=fake.name(),
            national_id=str(fake.unique.random_number(digits=8, fix_len=True)),
            phone=fake.numerify(text='07########'),
            email=fake.email()
        )
        session.add(m)
        
    session.commit()
    print("Database seeded! You can now log in with username: admin_01, password: pass123")

if __name__ == '__main__':
    seed_database()