import pickle
import random
import string
import hashlib

def generate_secret_key(length=32):
    """Generate a random secret key."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def hash_password(password):
    """Create a SHA-256 hash of the password."""
    return hashlib.sha256(password.encode()).hexdigest()

def save_secret_data(username, password, filename='./secret.pkl'):
    """Generate and save a secret key and user credentials to a pickle file."""
    secret_key = generate_secret_key()
    password_hash = hash_password(password)
    data = {
        'secret_key': secret_key,
        'users': {username: password_hash}
    }
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    print(f"Secret data saved to {filename}")

if __name__ == "__main__":
    username = input("Enter the username: ")
    password = input("Enter the password: ")
    save_secret_data(username, password)