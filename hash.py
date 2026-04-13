import streamlit_authenticator as stauth
# Type the password you WANT to use here
password = 'admin123' 
hash = stauth.Hasher([password]).generate()
print(f"New Hash: {hash}")