from app.auth import verify_password
hash = "$2b$12$AK8uPKPnibviPlzoMMqry.bdJ6J3MUe9AT74iLLvDELgDPnDGKc/G"
print(f"Verify 'testpass': {verify_password('testpass', hash)}")
