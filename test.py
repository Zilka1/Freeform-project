import bcrypt

# Generate a random salt
salt = bcrypt.gensalt()

# Hash a password using the salt
hashed_password = bcrypt.hashpw(b"my_password", salt)

# Verify a password by comparing the hashed password with the stored salt
if bcrypt.checkpw(b"my_password", hashed_password):
    print("Password is correct.")
else:
    print("Password is incorrect.")