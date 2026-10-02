import hashlib
def blind_id(relative_path,salt):
    h=hashlib.blake2b((salt+"::"+relative_path).encode(),digest_size=8)
    return "B"+h.hexdigest().upper()
